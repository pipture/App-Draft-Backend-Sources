# -*- coding: utf-8 -*-

from django.db import models
from django.db.models import F

from restserver.s3.s3FileField import S3EnabledFileField
from restserver.rest_core.views import local_date_time_date_time_to_UTC_sec
import datetime
import calendar


from decimal import Decimal

from django.conf import settings

from django.core.exceptions import ValidationError

from django.db.models.signals import post_save

from django.contrib import admin

import uuid



class Videos(models.Model):
    VideoId = models.AutoField (primary_key=True)
    VideoDescription = models.CharField (unique=True, max_length=100, verbose_name="Video description")
    VideoUrl = S3EnabledFileField (upload_to=u'documents/', verbose_name="Upload video here")

    def __unicode__(self):
        return "%s" % (self.VideoDescription)

    def __str__(self):
        return "%s" % (self.VideoDescription)

    class Admin ():
        pass
    
    
    class Meta:
        verbose_name = "Video"
        verbose_name_plural = "Videos"



            
class Trailers(models.Model):
    TrailerId = models.AutoField(primary_key=True)
    VideoId = models.ForeignKey (Videos, verbose_name="Video for the trailer")
    Title = models.CharField (unique=True, max_length=100)
    Line1 = models.CharField (blank=True, max_length=500)
    Line2 = models.CharField (blank=True, max_length=500)
    SquareThumbnail = S3EnabledFileField (upload_to=u'documents/', verbose_name="Screenshot")


    @property
    def complexName(self):
        return "%s, %s, %s" % (self.Title, self.Line1, self.Line2 )


    def __unicode__(self):
        return self.complexName

    def __str__(self):
        return self.complexName

    class Admin:
        pass
    
    class Meta:
        verbose_name = "Trailer"
        verbose_name_plural = "Trailers"
        ordering = ['Title', 'Line1', 'Line2']

    def delete (self):        
        return "You couldn't delete video. It maybe in timeslot."
        
        
class Series(models.Model):
    SeriesId = models.AutoField (primary_key=True)
    Title = models.CharField (unique=True, max_length=100)

    def __unicode__(self):
        return "%s" % (self.Title)

    def __str__(self):
        return "%s" % (self.Title)

    class Admin:
        pass

    class Meta:
        verbose_name = "Series"
        verbose_name_plural = "Series"
        ordering = ['Title']
        
    
class Albums(models.Model):
    AlbumId = models.AutoField (primary_key=True)
    SeriesId = models.ForeignKey (Series, verbose_name='Series for Album')
    TrailerId = models.ForeignKey (Trailers, verbose_name='Trailer for Album')
    Description = models.CharField (max_length=500)
    Season = models.CharField (max_length=100)
    Title = models.CharField (max_length=100)
    Rating = models.CharField (max_length=100)
    Description = models.CharField (max_length=500)
    Credits = models.CharField (blank=True, max_length=500)
    Cover = S3EnabledFileField (upload_to=u'documents/', verbose_name='Landscape') 
    Thumbnail = S3EnabledFileField (upload_to=u'documents/', verbose_name='Cover Thumbnail')
    CloseUpBackground = S3EnabledFileField (verbose_name='Cover', upload_to=u'documents/')
    SquareThumbnail = S3EnabledFileField (verbose_name='Default Screenshot', upload_to=u'documents/')

    @property
    def complexName(self):
        return "%s, S%s, A%s" % (self.SeriesId.Title, self.Season, self.Title)

    def __unicode__(self):
        return self.complexName

    def __str__(self):
        return self.complexName

    class Admin:
        pass

    class Meta:
        verbose_name = "Album"
        verbose_name_plural = "Albums"    
        ordering = ['SeriesId__Title', 'Season', 'Title']


class AlbumScreenshotGallery(models.Model):
    AlbumId = models.ForeignKey (Albums)
    Description = models.CharField (help_text='Unique description for screenshot.',  max_length=100)
    Screenshot = S3EnabledFileField (upload_to=u'documents/') 

    @property
    def ScreenshotURL(self):
        return (self.Screenshot._get_url()).split('?')[0]  

    def __unicode__(self):
        return "Album: %s; Screenshot: %s." % (self.AlbumId.Description, self.Description)

    def __str__(self):
        return "Album: %s; Screenshot: %s." % (self.AlbumId.Description, self.Description)

    def get_queryset(self):
        return AlbumScreenshotGallery.objects.sort('Description')

    class Admin:
        pass

    class Meta:
        verbose_name = "Album Screenshot Gallery"
        verbose_name_plural = "Album Screenshots Gallery"

class Episodes(models.Model):
    EpisodeId = models.AutoField (primary_key=True)
    Title = models.CharField (unique=True, max_length=100)
    VideoId = models.ForeignKey (Videos, verbose_name='Video for episode')
    AlbumId = models.ForeignKey (Albums, verbose_name='Album for episode')
    CloseUpThumbnail = S3EnabledFileField (verbose_name='Video Thumbnail', upload_to=u'documents/')
    SquareThumbnail = S3EnabledFileField (verbose_name='Screenshot', upload_to=u'documents/')
    EpisodeNo = models.IntegerField ()
    Script = models.CharField (blank=True,max_length=500)
    DateReleased = models.DateTimeField(verbose_name='Date released', help_text="Please, do set Date Release like 2011-11-05 00:00")
    Subject = models.CharField (max_length=500)
    Keywords = models.CharField (max_length=500)
    SenderToReceiver = models.CharField (verbose_name="Sender to receiver", max_length=500)

    @property
    def complexName (self):
        return "%s, S%s, A%s, E%s ,%s" %(self.AlbumId.SeriesId.Title, self.AlbumId.Season, self.AlbumId.Title, self.episodeNoInt, self.Title)
    
    @property
    def episodeNoInt(self):
        return '%0*d' % (4, self.EpisodeNo)

    def __unicode__(self):
        return self.complexName

    def __str__(self):
        return self.complexName

    class Admin:
        pass

    class Meta:
        verbose_name = "Episode"
        verbose_name_plural = "Episodes"  
        ordering = ['AlbumId__SeriesId__Title', 'AlbumId__Season', 'AlbumId__Title', 'EpisodeNo',  'Title']  
        
    def delete (self):        
        return "You couldn't delete video. It maybe in timeslot."


class TimeSlots(models.Model):

    
    TimeSlotsId = models.AutoField(primary_key=True)
    StartTime = models.DateTimeField(verbose_name="Start time")
    EndTime = models.DateTimeField(verbose_name="End time")
    AlbumId = models.ForeignKey (Albums, verbose_name="Choose timeslot album")
    ScheduleDescription = models.CharField (blank=True, max_length=50, verbose_name="Schedule description")
    @property
    def StartDateUTC(self):
        start_date = datetime.datetime.fromtimestamp(self.StartTimeUTC)
        return "%s" % (start_date)  
    
    @property
    def StartTimeUTC(self):
        return local_date_time_date_time_to_UTC_sec(self.StartTime)

    @property
    def EndTimeUTC(self):
        return local_date_time_date_time_to_UTC_sec(self.EndTime)

    @property
    def complexName(self):
        from restserver.pipture.middleware import threadlocals
        from restserver.pipture.admin import from_utc_to_local
        user = threadlocals.get_current_user()
        user_tz = user.get_profile().timezone
        return "%s, A%s, %s" % (self.AlbumId.SeriesId.Title, self.AlbumId.Title, from_utc_to_local (user_tz, self.StartTime))

    
    def __unicode__(self):
        return self.complexName

    def __str__(self):
        return self.complexName
    
    def is_current (self):
        today = datetime.datetime.utcnow()
        sec_utc_now = calendar.timegm(today.timetuple())
        
        if (self.StartTimeUTC < sec_utc_now < self.EndTimeUTC):
            return True
        else:
            return False

    @staticmethod
    def timeslot_is_current (id):
        try:
            id = int (id)
        except:
            return False
        
        today = datetime.datetime.utcnow()
        sec_utc_now = calendar.timegm(today.timetuple())
        today_utc = datetime.datetime.utcfromtimestamp(sec_utc_now)
        timedelta_1 = datetime.timedelta(days=settings.ACTIVE_DAYS_TIMESLOTS)
        tomorrow = today_utc + timedelta_1
        try:
            timeslot = TimeSlots.objects.get(TimeSlotsId=id)
        except:
            return False
        else:
            return timeslot.is_current()
        
    class Admin:
        pass

    class Meta:
        verbose_name = "Time slot"
        verbose_name_plural = "Time slots"    
        ordering = ['AlbumId__SeriesId__Title', 'AlbumId__Title', 'StartTime']

class TimeSlotVideos(models.Model):

    LINKTYPE_CHOICES = (
        ('E', 'Episodes'),
        ('T', 'Trailer'),
    )
    
    TimeSlotVideosId = models.AutoField (primary_key=True)
    TimeSlotsId = models.ForeignKey (TimeSlots)
    Order = models.IntegerField()
    LinkId = models.IntegerField (db_index=True)
    LinkType=  models.CharField(db_index=True, max_length=1, choices=LINKTYPE_CHOICES)
    
    @staticmethod
    def is_contain_id (timeslot_id, video_id, video_type):
        try:
            timeslot_id = int (timeslot_id)
            video_id = int (video_id)
        except:
            return False
        
        try:
            timeslot = TimeSlots.objects.get(TimeSlotsId=timeslot_id)
            is_contain = TimeSlotVideos.objects.filter(TimeSlotsId=timeslot,LinkType=video_type, LinkId= video_id)
        except:
            return False
        else:
            if is_contain:
                return True
            else:
                return False


    def __unicode__(self):
        return "%s" % (self.TimeSlotVideosId)

    def __str__(self):
        return "%s" % (self.TimeSlotVideosId)

    class Admin:
        pass

    class Meta:
        verbose_name = u"Video in time slot"
        verbose_name_plural = u"Videos in time slot"        

class PiptureSettings(models.Model):
    PremierePeriod = models.IntegerField(help_text='Count of days after premiere', verbose_name="Premiere period")

    def validate_unique(self, exclude = None):
        from django.core.exceptions import ValidationError, NON_FIELD_ERRORS
        if PiptureSettings.objects.count() == 1 and self.id != PiptureSettings.objects.all()[0].id:
            raise ValidationError({NON_FIELD_ERRORS: ["There can be only one!"]})

            
    class Admin:
        pass

    class Meta:
        verbose_name = "Pipture setting"
        verbose_name_plural = "Pipture settings"
        
class PipUsers(models.Model):
    UserUID= models.CharField (max_length=36, primary_key=True, default=uuid.uuid1)
    Token = models.CharField (unique=True, max_length=36, default=uuid.uuid1)
    RegDate = models.DateField(auto_now_add=True)
    Balance = models.DecimalField(default=Decimal('0.0000'), max_digits=10, decimal_places=4)
    
    def __unicode__(self):
        return "%s" % (self.UserUID)

    def __str__(self):
        return "%s" % (self.UserUID)

    class Admin:
        pass

    class Meta:
        verbose_name = "Pipture User"
        verbose_name_plural = "Pipture Users"    
        ordering = ['RegDate']

class PurchaseItems(models.Model):
    PurchaseItemId = models.AutoField (primary_key=True)
    Description = models.CharField (max_length=100, editable=False)
    Price = models.DecimalField( max_digits=7, decimal_places=4)
    
    def __unicode__(self):
        return "%s" % (self.Description)

    def __str__(self):
        return "%s" % (self.Description)

    class Admin:
        pass

    class Meta:
        verbose_name = "Purchase Item"
        verbose_name_plural = "Purchase Items"    


class UserPurchasedItems(models.Model):
    UserPurchasedItemsId = models.AutoField (primary_key=True)
    Date = models.DateField(auto_now_add=True)
    UserId = models.ForeignKey (PipUsers, editable=False)
    PurchaseItemId = models.ForeignKey (PurchaseItems, editable=False)
    ItemId = models.CharField (editable=False, max_length=100)
    ItemCost = models.DecimalField(editable=False, max_digits=7, decimal_places=4)
    
    def __unicode__(self):
        return "%s: %s, %s" % (self.UserId.UserUID, self.PurchaseItemId.Description, self.ItemCost)

    def __str__(self):
        return "%s: %s, %s" % (self.UserId.UserUID, self.PurchaseItemId.Description, self.ItemCost)

    class Admin:
        pass

    class Meta:
        verbose_name = "User Purchased Item"
        verbose_name_plural = "User Purchased Items"    

class AppleProducts(models.Model):
    AppleProductId = models.AutoField (primary_key=True)
    ProductId = models.CharField (verbose_name="Apple product Id", help_text='There is the Apple Product Id! Be carefully.',unique=True, max_length=255)
    Description = models.CharField (max_length=100)
    Price = models.DecimalField( max_digits=7, decimal_places=4)
    
    def __unicode__(self):
        return "%s" % (self.Description)

    def __str__(self):
        return "%s" % (self.Description)

    class Admin:
        pass

    class Meta:
        verbose_name = "Apple Product"
        verbose_name_plural = "Apple Products"    

class Transactions(models.Model):
    TransactionId = models.AutoField (primary_key=True)
    UserId = models.ForeignKey (PipUsers, editable=False)
    ProductId = models.ForeignKey (AppleProducts, editable=False)
    AppleTransactionId = models.CharField (unique=True, max_length=36)
    Timestamp = models.DateField(auto_now_add=True)
    Cost = models.DecimalField(editable=False,  max_digits=7, decimal_places=4)
    
    def __unicode__(self):
        return "%s: %s - %s" % (self.Timestamp, self.UserId.UserUID, self.ProductId.Description)

    def __str__(self):
        return "%s: %s - %s" % (self.Timestamp, self.UserId.UserUID, self.ProductId.Description)

    class Admin:
        pass

    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"    
        ordering = ['Timestamp']


import uuid

class SendMessage(models.Model):


    LINKTYPE_CHOICES = (
        ('E', 'Episodes'),
        ('T', 'Trailer'),
    )


    Url = models.CharField(max_length=36, primary_key=True, default=uuid.uuid4)
    UserId = models.ForeignKey (PipUsers)
    Text = models.CharField (max_length=200)
    Timestamp = models.DateTimeField(auto_now_add=True)
    LinkId = models.IntegerField (db_index=True)
    LinkType=  models.CharField(db_index=True, max_length=1, choices=LINKTYPE_CHOICES)
    UserName = models.CharField (max_length=200)
    ScreenshotURL = models.CharField (blank=True, null=True,  max_length=200)

    class Meta:
        verbose_name = "Sent Message"
        verbose_name_plural = "Sent Messages"    
        ordering = ['-Timestamp']


from django.contrib.auth.models import User

US_TIMEZONES = (
                ('America/New_York', 'America/New_York'), 
                ('America/Detroit', 'America/Detroit'), 
                ('America/Kentucky/Louisville', 'America/Kentucky/Louisville'), 
                ('America/Kentucky/Monticello', 'America/Kentucky/Monticello'), 
                ('America/Indiana/Indianapolis', 'America/Indiana/Indianapolis'), 
                ('America/Indiana/Vincennes', 'America/Indiana/Vincennes'), 
                ('America/Indiana/Winamac', 'America/Indiana/Winamac'), 
                ('America/Indiana/Marengo', 'America/Indiana/Marengo'), 
                ('America/Indiana/Petersburg', 'America/Indiana/Petersburg'), 
                ('America/Indiana/Vevay', 'America/Indiana/Vevay'), 
                ('America/Chicago', 'America/Chicago'), 
                ('America/Indiana/Tell_City', 'America/Indiana/Tell_City'), 
                ('America/Indiana/Knox', 'America/Indiana/Knox'), 
                ('America/Menominee', 'America/Menominee'), 
                ('America/North_Dakota/Center', 'America/North_Dakota/Center'), 
                ('America/North_Dakota/New_Salem', 'America/North_Dakota/New_Salem'), 
                ('America/North_Dakota/Beulah', 'America/North_Dakota/Beulah'), 
                ('America/Denver', 'America/Denver'), 
                ('America/Boise', 'America/Boise'), 
                ('America/Shiprock', 'America/Shiprock'), 
                ('America/Phoenix', 'America/Phoenix'), 
                ('America/Los_Angeles', 'America/Los_Angeles'), 
                ('America/Anchorage', 'America/Anchorage'), 
                ('America/Juneau', 'America/Juneau'), 
                ('America/Sitka', 'America/Sitka'), 
                ('America/Yakutat', 'America/Yakutat'), 
                ('America/Nome', 'America/Nome'), 
                ('America/Adak', 'America/Adak'), 
                ('America/Metlakatla', 'America/Metlakatla'), 
                ('Pacific/Honolulu', 'Pacific/Honolulu'),
                ('Asia/Omsk', 'Asia/Omsk'),
                 
                )

class UserProfile(User):  
    user = models.OneToOneField(User, editable=False)  
    #other fields here
    timezone = timezone = models.CharField(max_length=50, default='America/New_York', choices = US_TIMEZONES)

    def __str__(self):  
          return "%s's profile" % self.user

def create_user_profile(sender, instance, created, **kwargs):  
    if created:  
       profile, created = UserProfile.objects.get_or_create(user=instance)  

post_save.connect(create_user_profile, sender=User) 

def install(**kwargs):
    
    if PurchaseItems.objects.count() == 0:
        PurchaseItems(Description="WatchEpisode", Price=Decimal('0.0099')).save()   
        PurchaseItems( Description="SendEpisode", Price=Decimal('0.0099')).save()
    

    if AppleProducts.objects.count() == 0:
        AppleProducts(ProductId="com.pipture.Pipture.credits", Description = "Pipture credits.", Price=Decimal('0.99')).save()   
   
    return

from django.db.models.signals import post_syncdb
post_syncdb.connect(install)