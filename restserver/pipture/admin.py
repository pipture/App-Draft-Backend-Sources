# -*- coding: utf-8 -*-

from django.contrib import admin
from restserver.pipture.models import Videos, Trailers, Series, Albums, Episodes, TimeSlots 
from restserver.pipture.models import PiptureSettings, PipUsers, AppleProducts,Transactions, PurchaseItems 
from restserver.pipture.models import UserPurchasedItems,SendMessage, AlbumScreenshotGallery


admin.site.register(TimeSlots)
admin.site.register(PiptureSettings)
admin.site.register(PipUsers)
admin.site.register(AppleProducts)
admin.site.register(Transactions)
admin.site.register(PurchaseItems)
admin.site.register(UserPurchasedItems)
admin.site.register(SendMessage)
#from restserver.pipture.models import TimeSlotVideos
#admin.site.register(TimeSlotVideos)


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

class AlbumsAdmin(DeleteForbidden):
     
    fieldsets = [
        ('Related objects', {'fields': ['SeriesId', 'TrailerId']}),
        ('Information', {'fields': ['Description', 'Season', 'Title', 'Rating', 'Credits']}),
        ('Pictures:', {'fields': ['Cover', 'Thumbnail', 'CloseUpBackground', 'SquareThumbnail']}),
    ]
        
    inlines = [AlbumScreenshotGalleryInline]

admin.site.register(Albums, AlbumsAdmin)
    
admin.site.register(Videos, DeleteForbidden)
admin.site.register(Trailers, DeleteForbidden)
admin.site.register(Episodes, DeleteForbidden)
admin.site.register(Series, DeleteForbidden)