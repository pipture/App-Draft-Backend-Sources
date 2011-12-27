# -*- coding: utf-8 -*-

from django.db import models
from restserver.s3.s3FileField import S3EnabledFileField
from restserver.rest_core.views import local_date_time_date_time_to_UTC_sec
import datetime
import calendar

from decimal import Decimal

from django.conf import settings

from django.core.exceptions import ValidationError

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
    Line3 = models.CharField (blank=True, max_length=500)
    Thumbnail = S3EnabledFileField (help_text='Thumbnail',upload_to=u'documents/')
    SquareThumbnail = S3EnabledFileField (upload_to=u'documents/', verbose_name="Screenshot")

    def __unicode__(self):
        return "%s" % (self.Title)

    def __str__(self):
        return "%s" % (self.Title)

    class Admin:
        pass
    
    class Meta:
        verbose_name = "Trailer"
        verbose_name_plural = "Trailers"

    def delete (self):        
        return "You couldn't delete video. It maybe in timeslot."
        
        
class Series(models.Model):
    SeriesId = models.AutoField (primary_key=True)
    Title = models.CharField (unique=True, max_length=100)
    CloseupBackground = S3EnabledFileField (verbose_name='Closeup Background', upload_to=u'documents/')

    def __unicode__(self):
        return "%s: %s" % (self.SeriesId, self.Title)

    def __str__(self):
        return "%s: %s" % (self.SeriesId, self.Title)

    class Admin:
        pass

    class Meta:
        verbose_name = "Series"
        verbose_name_plural = "Series"
        ordering = ['SeriesId']
        
    
class Albums(models.Model):
    AlbumId = models.AutoField (primary_key=True)
    SeriesId = models.ForeignKey (Series, verbose_name='Series for Album')
    TrailerId = models.ForeignKey (Trailers, verbose_name='Trailer for Album')
    Description = models.CharField (max_length=500)
    Season = models.CharField (max_length=100)
    Title = models.CharField (unique=True, max_length=100)
    Rating = models.CharField (max_length=100)
    Description = models.CharField (max_length=500)
    Credits = models.CharField (blank=True, max_length=500)
    Cover = S3EnabledFileField (upload_to=u'documents/') 
    Thumbnail = S3EnabledFileField (upload_to=u'documents/')
    CloseUpBackground = S3EnabledFileField (verbose_name='CloseUp Background', upload_to=u'documents/')
    SquareThumbnail = S3EnabledFileField (verbose_name='Screenshot', upload_to=u'documents/')

    def __unicode__(self):
        return "%s: %s" % (self.AlbumId, self.Description)

    def __str__(self):
        return "%s: %s" % (self.AlbumId, self.Description)

    class Admin:
        pass

    class Meta:
        verbose_name = "Album"
        verbose_name_plural = "Albums"    
        ordering = ['SeriesId']


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
    CloseUp = S3EnabledFileField (upload_to=u'documents/')
    CloseUpThumbnail = S3EnabledFileField (verbose_name='CloseUp Thumbnail', upload_to=u'documents/')
    SquareThumbnail = S3EnabledFileField (verbose_name='Screenshot', upload_to=u'documents/')
    EpisodeNo = models.CharField (max_length=10)
    Script = models.CharField (blank=True,max_length=500)
    DateReleased = models.DateField(verbose_name='Date released')
    Subject = models.CharField (max_length=500)
    Keywords = models.CharField (max_length=500)
    SenderToReceiver = models.CharField (verbose_name="Sender to receiver", max_length=500)

    def __unicode__(self):
        return "%s: %s from album %s" %(self.EpisodeId, self.Title, self.AlbumId)

    def __str__(self):
        return "%s: %s from album %s" %(self.EpisodeId, self.Title, self.AlbumId)

    class Admin:
        pass

    class Meta:
        verbose_name = "Episode"
        verbose_name_plural = "Episodes"    
        ordering = ['AlbumId']
        
    def delete (self):        
        return "You couldn't delete video. It maybe in timeslot."

class TimeSlots(models.Model):

    
    TimeSlotsId = models.AutoField(primary_key=True)
    StartTime = models.DateTimeField(verbose_name="Start UTC time")
    EndTime = models.DateTimeField(verbose_name="End UTC time")
    AlbumId = models.ForeignKey (Albums, verbose_name="Choose timeslot album")
    ScheduleDescription = models.CharField (blank=True, max_length=50, verbose_name="Schedule description")

    @property
    def StartDateUTC(self):
        start_date = datetime.datetime.fromtimestamp(self.StartTimeUTC)
        return "%s" % (start_date)#start_date.year,start_date.month, start_date.day)  
    
    @property
    def StartTimeUTC(self):
        return local_date_time_date_time_to_UTC_sec(self.StartTime)

    @property
    def EndTimeUTC(self):
        return local_date_time_date_time_to_UTC_sec(self.EndTime)

    
    def __unicode__(self):
        return "%s at %s - %s" % (self.TimeSlotsId, self.StartTime, self.EndTime)

    def __str__(self):
        return "%s at %s - %s" % (self.TimeSlotsId, self.StartTime, self.EndTime)

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
        ordering = ['-StartTime']
    #===========================================================================
    # def save(self, force_insert=False, force_update=False):
    #    if self.name != self.__original_name:
    #      # name changed - do something
    #    
    #    super(Person, self).save(force_insert, force_update)
    #    self.__orginal_name = self.name
    #===========================================================================
            
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
    Timestamp = models.DateField(auto_now_add=True)
    LinkId = models.IntegerField (db_index=True)
    LinkType=  models.CharField(db_index=True, max_length=1, choices=LINKTYPE_CHOICES)
    UserName = models.CharField (max_length=200)
    ScreenshotURL = models.CharField (blank=True, null=True,  max_length=200)

    class Meta:
        verbose_name = "Sended message"
        verbose_name_plural = "Sended messages"    
        ordering = ['-Timestamp']

def install(**kwargs):
    
    if PurchaseItems.objects.count() == 0:
        PurchaseItems(Description="WatchEpisode", Price=Decimal('0.0099')).save()   
        PurchaseItems( Description="SendEpisode", Price=Decimal('0.0099')).save()
    

    if AppleProducts.objects.count() == 0:
        AppleProducts(ProductId="com.pipture.Pipture.credits", Description = "Pipture credits.", Price=Decimal('0.99')).save()   
   
    return

from django.db.models.signals import post_syncdb
post_syncdb.connect(install)