# -*- coding: utf-8 -*-

from django.contrib import admin
from restserver.pipture.models import Videos, Trailers, Series, Albums, Episodes, TimeSlots 
from restserver.pipture.models import PiptureSettings, PipUsers, AppleProducts,Transactions, PurchaseItems 
from restserver.pipture.models import UserPurchasedItems,SendMessage, AlbumScreenshotGallery,UserProfile


admin.site.register(PiptureSettings)
admin.site.register(PipUsers)
admin.site.register(AppleProducts)
admin.site.register(Transactions)
admin.site.register(PurchaseItems)
admin.site.register(UserPurchasedItems)
admin.site.register(SendMessage)
admin.site.register(UserProfile)

#from restserver.pipture.models import TimeSlotVideos
#admin.site.register(TimeSlotVideos)

from pytz import timezone
import pytz
import datetime

def from_local_to_utc (tz, date):
    user_tz = pytz.timezone(tz)
    local_time =  date
    utc_time = user_tz.normalize(user_tz.localize(local_time)).astimezone(pytz.utc)
    return datetime.datetime(utc_time.year, utc_time.month, utc_time.day,
                            utc_time.hour, utc_time.minute, utc_time.second)
    
def from_utc_to_local (tz, date):
    user__tz = pytz.timezone(tz)
    utc_time =  date
    local_time = pytz.utc.normalize(pytz.utc.localize(utc_time)).astimezone(user__tz)
    return datetime.datetime(local_time.year, local_time.month, local_time.day,
                            local_time.hour, local_time.minute, local_time.second)

class TimeSlotsAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        user_tz = request.user.get_profile().timezone
        obj.StartTime = from_local_to_utc (user_tz, obj.StartTime)
        obj.EndTime = from_local_to_utc (user_tz, obj.EndTime)
        obj.save()
    
    def get_form(self, request, obj=None, **kwargs):
        from restserver.pipture.middleware import threadlocals
        from restserver.pipture.admin import from_utc_to_local
        user = threadlocals.get_current_user()
        user_tz = user.get_profile().timezone

        form = super(self.__class__, self).get_form(request, obj, **kwargs)
        obj.StartTime = from_utc_to_local (user_tz, obj.StartTime)
        obj.EndTime = from_utc_to_local (user_tz, obj.EndTime)
        return form    


class DeleteForbidden(admin.ModelAdmin):
    '''
    There is a problem.
    Timeslotvideos has LinkId/TypeId on Episode or Trailer and there is no cascade deleting.
    If delete Episode then Timeslotvideos become to invalide status with API getPlaylist error.
    Fastest way - forbid delete.
    '''
    def get_actions(self, request):
        return []

    def has_delete_permission(self, request, obj=None):
        return False
    
class AlbumScreenshotGalleryInline(admin.TabularInline):
    model = AlbumScreenshotGallery
    verbose_name = "Screensot gallery:"
    ordering = ['Description']

class AlbumsAdmin(DeleteForbidden):
     
    fieldsets = [
        ('Related objects', {'fields': ['SeriesId', 'TrailerId']}),
        ('Information', {'fields': ['Description', 'Season', 'Title', 'Rating', 'Credits']}),
        ('Pictures:', {'fields': ['Cover', 'Thumbnail', 'CloseUpBackground', 'SquareThumbnail']}),
    ]
        
    inlines = [AlbumScreenshotGalleryInline]


from django.contrib.admin.views.main import ChangeList


DIRTY_HACK = '''
For multiplying sorting by list of sort in admin panel there is a trick:  

http://stackoverflow.com/questions/4560913/django-admin-second-level-ordering-in-list-display

from django.contrib import admin
from django.contrib.admin.views.main import ChangeList


class SpecialOrderingChangeList(ChangeList):
    def get_query_set(self):
        queryset = super(SpecialOrderingChangeList, self).get_query_set()
        return queryset.order_by(*self.model._meta.ordering)

class CustomerAdmin(admin.ModelAdmin):
    def get_changelist(self, request, **kwargs):
        return SpecialOrderingChangeList

admin.site.register(Customer, CustomerAdmin)
'''

class SpecialOrderingChangeList(ChangeList):
    def get_query_set(self):
        queryset = super(SpecialOrderingChangeList, self).get_query_set()
        return queryset.order_by(*self.model._meta.ordering)

    
class EpisodesAdmin(DeleteForbidden):
    
    fieldsets = [
        ('Related objects:', {'fields': ['VideoId','AlbumId']}),
        ('Information:', {'fields': ['Title', 'EpisodeNo', 'Script', 'DateReleased',
                    'Subject', 'Keywords', 'SenderToReceiver']}),
        ('Pictures:', {'fields': ['CloseUpThumbnail', 'SquareThumbnail']}),
    ]

    special_ordering = {'default': ("AlbumId__SeriesId__Title","AlbumId__Season","AlbumId__Title", "EpisodeNo", "Title")}
    
    def get_changelist(self, request, **kwargs):
        return SpecialOrderingChangeList
            

    def save_model(self, request, obj, form, change):
        user_tz = request.user.get_profile().timezone
        obj.DateReleased = from_local_to_utc (user_tz, obj.DateReleased)
        obj.save()
    
    def get_form(self, request, obj=None, **kwargs):
        from restserver.pipture.middleware import threadlocals
        from restserver.pipture.admin import from_utc_to_local
        user = threadlocals.get_current_user()
        user_tz = user.get_profile().timezone

        form = super(self.__class__, self).get_form(request, obj, **kwargs)
        obj.DateReleased = from_utc_to_local (user_tz, obj.DateReleased)
        return form    

    
admin.site.register(Albums, AlbumsAdmin)
    
admin.site.register(Videos, DeleteForbidden)
admin.site.register(Trailers, DeleteForbidden)
admin.site.register(Episodes, EpisodesAdmin)
admin.site.register(Series, DeleteForbidden)
admin.site.register(TimeSlots, TimeSlotsAdmin)