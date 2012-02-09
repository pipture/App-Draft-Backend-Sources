from django.views.generic.simple import direct_to_template
from django.shortcuts import render_to_response, redirect
from django.template.context import RequestContext
from django.http import HttpResponse
import json
import time
import datetime
import calendar
import random
import uuid
import hashlib

from django.conf import settings
from urlparse import urlparse

from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal
from django.db.models import Q

import urllib2
import urllib

def local_date_time_date_time_to_UTC_sec (datetime_datetime):
    """
    time.mktime - for local to UTC
    calendar.timegm - for UTC tuple to UTC sec
    settings.py - TIME_ZONE = 'UTC' then calendar.timegm 
    
    """
    return calendar.timegm(datetime_datetime.timetuple())

def _test_rest (request):
    return HttpResponse ("It's me!")

def index (request):

    response = {}
    response["Error"] = {"ErrorCode": "888", "ErrorDescription": "Unknown API method."}
    return HttpResponse (json.dumps(response))        
        

def getTimeslots (request):
    keys = request.GET.keys()
    response = {}
    if "API" not in keys:
        response["Error"] = {"ErrorCode": "666", "ErrorDescription": "There is no API parameter."}
        return HttpResponse (json.dumps(response))
    else:
        api_ver = request.GET.get("API")
    if api_ver != "1":
        response["Error"] = {"ErrorCode": "777", "ErrorDescription": "Wrong API version."}
        return HttpResponse (json.dumps(response))
    else:
        response["Error"] = {"ErrorCode": "", "ErrorDescription": ""}
    timeslots_json = []

    today = datetime.datetime.utcnow()
    sec_utc_now = calendar.timegm(today.timetuple())
    today_utc = datetime.datetime.utcfromtimestamp(sec_utc_now)
    timedelta_1 = datetime.timedelta(days=settings.ACTIVE_DAYS_TIMESLOTS)
    tomorrow = today_utc + timedelta_1
    yesterday = today_utc - timedelta_1

    from restserver.pipture.models import TimeSlots

    try:
        timeslots = TimeSlots.objects.select_related(depth=2).filter(Q(EndTime__gt=yesterday,
                                EndTime__lt=tomorrow)|Q(StartTime__gt=yesterday,
                                StartTime__lt=tomorrow)).order_by('StartTime')
                                
    except Exception as e:
        response["Error"] = {"ErrorCode": "777", "ErrorDescription": "Internal error %s (%s)." % (e, type (e))}
        return HttpResponse (json.dumps(response))
    current_ts = False
    wait_next_ts = True
    for ts in timeslots:
        slot = {}
        slot["TimeSlotId"] = ts.TimeSlotsId
        slot["StartTime"] = ts.StartTimeUTC 
        slot["EndTime"] = ts.EndTimeUTC
        slot["ScheduleDescription"] = ts.ScheduleDescription
        slot["Title"] = ts.AlbumId.SeriesId.Title
        slot["AlbumId"] = ts.AlbumId.AlbumId
        slot["CloseupBackground"] = (ts.AlbumId.CloseUpBackground._get_url()).split('?')[0]
        if ts.is_current():
            slot["TimeslotStatus"] = 2
            current_ts = True
        elif wait_next_ts and (current_ts or ts.StartTimeUTC > sec_utc_now):
            current_ts = False
            wait_next_ts = False
            slot["TimeslotStatus"] = 1
        else:
            slot["TimeslotStatus"] = 0
        
        timeslots_json.append(slot)
    response['Timeslots'] = timeslots_json
    response['CurrentTime'] = sec_utc_now
    return HttpResponse (json.dumps(response))
        
def get_video_url_from_episode_or_trailer (id, type_r, is_url = True):
    
    from restserver.pipture.models import Trailers
    from restserver.pipture.models import Episodes

    
    """is_url - needs to return url or video instance"""
    try:
        id = int (id)
    except ValueError as e:
        return None, "There is internal error - %s (%s)." % (e, type (e))
    if type_r not in ['E', 'T']:
        return None, "There is unknown type %s" % (type_r)
    if type_r == "E":
        try:
            video = Episodes.objects.select_related(depth=1).get(EpisodeId=id)
        except Episodes.DoesNotExist as e:
            return None, "There is no episode with id %s" % (id)
    else:
        try:
            video = Trailers.objects.get(TrailerId=id)
        except Trailers.DoesNotExist as e:
            return None, "There is no trailer with id %s" % (id)
    if is_url:
        video_url_i = video.VideoId.VideoUrl
        video_url= (video_url_i._get_url()).split('?')[0]
        return video_url, None
    else:
        video_instance = video.VideoId
        return video_instance, None
        
                


def getVideo (request):
    keys = request.GET.keys()
    response = {}
    if "API" not in keys:
        response["Error"] = {"ErrorCode": "666", "ErrorDescription": "There is no API parameter."}
        return HttpResponse (json.dumps(response))
    else:
        api_ver = request.GET.get("API")
    if api_ver != "1":
        response["Error"] = {"ErrorCode": "777", "ErrorDescription": "Wrong API version."}
        return HttpResponse (json.dumps(response))
    else:
        response["Error"] = {"ErrorCode": "", "ErrorDescription": ""}
    timeslot_id = request.GET.get('TimeslotId', None)
    episode_id = request.GET.get('EpisodeId', None)
    trailer_id = request.GET.get('TrailerId', None)
    force_buy = request.GET.get('ForceBuy', None)
    purchaser = request.GET.get('Key', None)
    
    from restserver.pipture.models import TimeSlots
    from restserver.pipture.models import TimeSlotVideos

    
    if force_buy and not purchaser:
        response["Error"] = {"ErrorCode": "4", "ErrorDescription": "Wrong authentication error"}
        return HttpResponse (json.dumps(response))
    if not (timeslot_id or force_buy) and not trailer_id:
        response["Error"] = {"ErrorCode": "888", "ErrorDescription": "There are TimeslotId and TrailerId. Should be only one param."}
        return HttpResponse (json.dumps(response))
    if episode_id and trailer_id:
        response["Error"] = {"ErrorCode": "888", "ErrorDescription": "There are EpisodeId and TrailerId. Should be only one param."}
        return HttpResponse (json.dumps(response))
    if not episode_id and not trailer_id:
        response["Error"] = {"ErrorCode": "888", "ErrorDescription": "There are no EpisodeId or TrailerId. Should be one param."}
        return HttpResponse (json.dumps(response))
    if trailer_id and not timeslot_id:
        video_url, error = get_video_url_from_episode_or_trailer (id = trailer_id, type_r = "T")
        if error:
            response["Error"] = {"ErrorCode": "888", "ErrorDescription": "There is error: %s." % (error)}
            return HttpResponse (json.dumps(response))
        response['VideoURL'] = video_url
        return HttpResponse (json.dumps(response))

    elif timeslot_id:

        if episode_id:
            video_type = "E"
        else:
            video_type = "T"
        
        if TimeSlots.timeslot_is_current(timeslot_id) and TimeSlotVideos.is_contain_id (timeslot_id, episode_id or trailer_id, video_type):
            video_url, error = get_video_url_from_episode_or_trailer (id = episode_id or trailer_id, type_r = video_type)
            if error:
                response["Error"] = {"ErrorCode": "888", "ErrorDescription": "There is error: %s." % (error)}
                return HttpResponse (json.dumps(response))
            response['VideoURL'] = video_url
            return HttpResponse (json.dumps(response))
        else:
            response["Error"] = {"ErrorCode": "1", "ErrorDescription": "Timeslot expired"}
            return HttpResponse (json.dumps(response))


    else:
        force_buy = force_buy or "0"
        if force_buy not in ["1", "0"]:
            response["Error"] = {"ErrorCode": "888", "ErrorDescription": "There is wrong ForceBuy %s (not 0 or 1)" % (force_buy)}
            return HttpResponse (json.dumps(response))

        from restserver.pipture.models import PipUsers
        
        try:
            purchaser = PipUsers.objects.get(Token=purchaser)
        except PipUsers.DoesNotExist:
            response["Error"] = {"ErrorCode": "100", "ErrorDescription": "Authentication error."}
            return HttpResponse (json.dumps(response))

        from restserver.pipture.models import UserPurchasedItems
        from restserver.pipture.models import PurchaseItems
        WATCH_EP = PurchaseItems.objects.get(Description="WatchEpisode")
        SEND_EP = PurchaseItems.objects.get(Description="SendEpisode")

        
        
        is_purchased = UserPurchasedItems.objects.filter(UserId=purchaser, ItemId=episode_id, PurchaseItemId = WATCH_EP).count()
        
        video_url, error = get_video_url_from_episode_or_trailer (id = episode_id, type_r = "E")
        if error:
            response["Error"] = {"ErrorCode": "888", "ErrorDescription": "There is internal error. Wrong video URL"}
            return HttpResponse (json.dumps(response))
            
        
        if is_purchased:
            response['VideoURL'] = video_url
            response['Balance'] = "%s" % (purchaser.Balance)
            return HttpResponse (json.dumps(response))
        else:
            if force_buy == "0":
                response["Error"] = {"ErrorCode": "2", "ErrorDescription": "Video not purchased."}
                return HttpResponse (json.dumps(response))
            else:
                if (purchaser.Balance - WATCH_EP.Price) >= 0:
                    new_p = UserPurchasedItems(UserId=purchaser, ItemId=episode_id, PurchaseItemId = WATCH_EP, ItemCost=WATCH_EP.Price)
                    new_p.save()
                    purchaser.Balance = Decimal (purchaser.Balance - WATCH_EP.Price)
                    purchaser.save()
                    response['VideoURL'] = video_url
                    response['Balance'] = "%s" % (purchaser.Balance)
                    return HttpResponse (json.dumps(response))
                else:
                    response["Error"] = {"ErrorCode": "3", "ErrorDescription": "Not enough money."}
                    return HttpResponse (json.dumps(response))
    

def getPlaylist (request):
    keys = request.GET.keys()
    response = {}
    if "API" not in keys:
        response["Error"] = {"ErrorCode": "666", "ErrorDescription": "There is no API parameter."}
        return HttpResponse (json.dumps(response))
    else:
        api_ver = request.GET.get("API")
    if api_ver != "1":
        response["Error"] = {"ErrorCode": "777", "ErrorDescription": "Wrong API version."}
        return HttpResponse (json.dumps(response))
    else:
        response["Error"] = {"ErrorCode": "", "ErrorDescription": ""}
    timeslot_id = request.GET.get('TimeslotId', None)
    try:
        timeslot_id = int(timeslot_id)
    except Exception as e:
        response["Error"] = {"ErrorCode": "2", "ErrorDescription": "TimeslotId is not integer."}
        return HttpResponse (json.dumps(response))

    from restserver.pipture.models import TimeSlots
    from restserver.pipture.models import TimeSlotVideos

    try:
        timeslot = TimeSlots.objects.get(TimeSlotsId=timeslot_id)
    except Exception as e:
        response["Error"] = {"ErrorCode": "2", "ErrorDescription": "There is no timeslot with id %s" % (timeslot_id)}
        return HttpResponse (json.dumps(response))
    
    today = datetime.datetime.utcnow()
    sec_utc_now = calendar.timegm(today.timetuple())
    if timeslot.StartTimeUTC > sec_utc_now:
        response["Error"] = {"ErrorCode": "3", "ErrorDescription": "Timeslot in future"}
        return HttpResponse (json.dumps(response))         

    if  sec_utc_now > timeslot.EndTimeUTC:
        response["Error"] = {"ErrorCode": "1", "ErrorDescription": "Timeslot is no current"}
        return HttpResponse (json.dumps(response))         

    
    try:
        timeslot_videos_list = TimeSlotVideos.objects.filter(TimeSlotsId=timeslot).order_by('Order')
    except TimeSlotVideos.DoesNotExist as e:
        response["Error"] = {"ErrorCode": "2", "ErrorDescription": "There are no videos in timeslot with id %s (%s)" % (timeslot_id, e)}
        return HttpResponse (json.dumps(response))
    response["Videos"] = []

    from restserver.pipture.models import Trailers
    from restserver.pipture.models import Episodes
    from restserver.pipture.models import Albums


    for timeslot_video in timeslot_videos_list:
        if timeslot_video.LinkType == "T":
            try:
                video = Trailers.objects.get (TrailerId=timeslot_video.LinkId) 
            except Exception as e:
                response["Error"] = {"ErrorCode": "2", "ErrorDescription": "There is no trailer with id %s" % (timeslot_video.LinkId)}
                return HttpResponse (json.dumps(response))
            else:
                response["Videos"].append({"Type": "Trailer", "TrailerId": video.TrailerId, 
                                           "Title": video.Title, "Line1": video.Line1,
                                           "Line2": video.Line2,
                                           "SquareThumbnail": (video.SquareThumbnail._get_url()).split('?')[0]})

        elif timeslot_video.LinkType == "E":
            try:
                video = Episodes.objects.select_related(depth=2).get (EpisodeId=timeslot_video.LinkId) 
            except Exception as e:
                response["Error"] = {"ErrorCode": "2", "ErrorDescription": "There is no episode with id %s" % (timeslot_video.LinkId)}
                return HttpResponse (json.dumps(response))
            else:
                response["Videos"].append({"Type": "Episode", "EpisodeId": video.EpisodeId, 
                                           "Title": video.Title, "Script": video.Script,
                                           "DateReleased": local_date_time_date_time_to_UTC_sec(video.DateReleased), "Subject": video.Subject,
                                           "SenderToReceiver": video.SenderToReceiver, 
                                           "EpisodeNo": video.EpisodeNo,
                                           "CloseUpThumbnail": (video.CloseUpThumbnail._get_url()).split('?')[0],
                                           
                                           'AlbumTitle': video.AlbumId.Title,
                                           'SeriesTitle': video.AlbumId.SeriesId.Title,
                                           'AlbumSeason': video.AlbumId.Season,
                                           'AlbumSquareThumbnail': (video.AlbumId.SquareThumbnail._get_url()).split('?')[0],

                                           "SquareThumbnail": (video.SquareThumbnail._get_url()).split('?')[0]})
    return HttpResponse (json.dumps(response))

def get_album_status (album, get_date_only=False):
    from django.db.models import Min
    from restserver.pipture.models import PiptureSettings
    from restserver.pipture.models import Episodes

    
    res = Episodes.objects.filter(AlbumId=album).aggregate(Min('DateReleased'))
    min_date = res['DateReleased__min']
    if get_date_only:
        min_date = min_date or datetime.datetime(1970, 1, 1, 00, 00)
        return local_date_time_date_time_to_UTC_sec(min_date)
    if not min_date: return 1#"NORMAL" It means that albums hasn't any episodes 
    date_utc_now = datetime.datetime.utcnow()#.date()
    if min_date > date_utc_now: return 3#"COMMING SOON"
    premiere_days = PiptureSettings.objects.all()[0].PremierePeriod
    timedelta_4 = datetime.timedelta(days=premiere_days)
    if min_date >= (date_utc_now - timedelta_4): return 2#"PREMIERE"
    return 1#"NORMAL"
    

def getAlbums (request):
    
    from restserver.pipture.models import Albums
    
    keys = request.GET.keys()
    response = {}
    if "API" not in keys:
        response["Error"] = {"ErrorCode": "666", "ErrorDescription": "There is no API parameter."}
        return HttpResponse (json.dumps(response))
    else:
        api_ver = request.GET.get("API")
    if api_ver != "1":
        response["Error"] = {"ErrorCode": "777", "ErrorDescription": "Wrong API version."}
        return HttpResponse (json.dumps(response))
    else:
        response["Error"] = {"ErrorCode": "", "ErrorDescription": ""}
    albums_json = []
 
    try:
        albums_list = Albums.objects.select_related(depth=1).all()
    except Exception as e:
        response["Error"] = {"ErrorCode": "2", "ErrorDescription": "There is internal error: %s." % (e)}
        return HttpResponse (json.dumps(response))
    for album in albums_list:
        album_each = {}
        album_each['AlbumId'] = album.AlbumId
        album_each['Thumbnail'] =  (album.Thumbnail._get_url()).split('?')[0]
        album_each['SquareThumbnail'] =  (album.SquareThumbnail._get_url()).split('?')[0]
        album_each['SeriesTitle'] = album.SeriesId.Title
        album_each['Title'] = album.Title
        album_each['AlbumStatus'] = get_album_status (album)
        album_each['ReleaseDate'] = get_album_status (album, get_date_only=True)
        
        albums_json.append(album_each)
    response['Albums'] = albums_json
    return HttpResponse (json.dumps(response))


def album_json_by_id (album):
    
    album_json = {}
    album_json['AlbumId'] = album.AlbumId
    album_json['Season'] = album.Season
    album_json['Cover'] =  (album.Cover._get_url()).split('?')[0]
    album_json['SeriesTitle'] = album.SeriesId.Title
    album_json['Title'] = album.Title
    album_json['SquareThumbnail'] = (album.SquareThumbnail._get_url()).split('?')[0]
    album_json['Description'] = album.Description
    album_json['Rating'] = album.Rating
    album_json['Credits'] = album.Credits
    album_json['ReleaseDate'] = get_album_status (album, get_date_only=True) 
    return album_json


def is_episode_on_air (episode, today):

    from restserver.pipture.models import TimeSlotVideos
    
    if episode.DateReleased.date() > today:
        return False
    if episode.DateReleased.date() < today:
        return True
    
    timeslotvideos = TimeSlotVideos.objects.select_related(depth=1).filter(LinkType="E", LinkId=episode.EpisodeId)

    today = datetime.datetime.utcnow()
    sec_utc_now = calendar.timegm(today.timetuple())
    
    for t in timeslotvideos:
        if t.TimeSlotsId.StartTimeUTC < sec_utc_now: return True
    return False
    
def getAlbumDetail (request):
    keys = request.GET.keys()
    response = {}
    if "API" not in keys:
        response["Error"] = {"ErrorCode": "666", "ErrorDescription": "There is no API parameter."}
        return HttpResponse (json.dumps(response))
    else:
        api_ver = request.GET.get("API")
    if api_ver != "1":
        response["Error"] = {"ErrorCode": "777", "ErrorDescription": "Wrong API version."}
        return HttpResponse (json.dumps(response))
    else:
        response["Error"] = {"ErrorCode": "", "ErrorDescription": ""}

    album_id = request.GET.get('AlbumId', None)
    timeslot_id = request.GET.get('TimeslotId', None)
    include_episodes = request.GET.get('IncludeEpisodes', None)

    
    
    if (album_id and timeslot_id):
        response["Error"] = {"ErrorCode": "888", "ErrorDescription": "There is AlbumId and TimeslotId. Should be only one."}
        return HttpResponse (json.dumps(response))
        
    if not timeslot_id and not album_id:
        response["Error"] = {"ErrorCode": "888", "ErrorDescription": "There is no AlbumId or TimeslotId param."}
        return HttpResponse (json.dumps(response))

    if album_id:
        try:
            album_id = int(album_id)
        except Exception as e:
            response["Error"] = {"ErrorCode": "888", "ErrorDescription": "There is internal error (%s).It seems like AlbumId is not integer." % (e)}
            return HttpResponse (json.dumps(response))
   
        from restserver.pipture.models import Albums    
        
        try:
            album = Albums.objects.select_related(depth=1).get(AlbumId=album_id)
        except Albums.DoesNotExist as e:
            response["Error"] = {"ErrorCode": "2", "ErrorDescription": "There is no Album with id %s." % (album_id)}
            return HttpResponse (json.dumps(response))

    if timeslot_id:        
        try:
            timeslot_id = int(timeslot_id)
        except Exception as e:
            response["Error"] = {"ErrorCode": "888", "ErrorDescription": "There is internal error (%s).It seems like TimeslotId is not integer." % (e)}
            return HttpResponse (json.dumps(response))

        from restserver.pipture.models import TimeSlots

        try:
            timeslot = TimeSlots.objects.select_related(depth=1).get(TimeSlotsId=timeslot_id)
        except TimeSlots.DoesNotExist as e:
            response["Error"] = {"ErrorCode": "2", "ErrorDescription": "There is no timeslot with id %s." % (timeslot_id)}
            return HttpResponse (json.dumps(response))
        else:
            album = timeslot.AlbumId

    
    response['Album'] = album_json_by_id (album)
        
    trailer = album.TrailerId
    
    response["Trailer"] ={"Type": "Trailer", "TrailerId": trailer.TrailerId, 
                               "Title": trailer.Title, "Line1": trailer.Line1,
                               "Line2": trailer.Line2,
                               "SquareThumbnail": (trailer.SquareThumbnail._get_url()).split('?')[0]}
    

    if include_episodes == "1":
        response["Episodes"] = []
        
        from restserver.pipture.models import Episodes

        try:
            episodes = Episodes.objects.filter (AlbumId=album).order_by('EpisodeNo') 
        except Exception as e:
            pass
        else:
            today = datetime.datetime.utcnow()
            sec_utc_now = calendar.timegm(today.timetuple())
            today_utc = datetime.date.fromtimestamp(sec_utc_now)
            for episode in episodes:
                if not is_episode_on_air (episode, today_utc):
                    continue
                response["Episodes"].append({"Type": "Episode", "EpisodeId": episode.EpisodeId, 
                                       "Title": episode.Title, "Script": episode.Script,
                                       "DateReleased": local_date_time_date_time_to_UTC_sec(episode.DateReleased), "Subject": episode.Subject,
                                       "SenderToReceiver": episode.SenderToReceiver, 
                                       "EpisodeNo": episode.EpisodeNo,
                                       "CloseUpThumbnail": (episode.CloseUpThumbnail._get_url()).split('?')[0],
                                       "SquareThumbnail": (episode.SquareThumbnail._get_url()).split('?')[0]
                                       })

    return HttpResponse (json.dumps(response))


def register_pip_user (email, password, first_name,last_name):
    from restserver.pipture.models import PipUsers
    from django.core.exceptions import ValidationError, NON_FIELD_ERRORS

    token = str(uuid.uuid1())
    p = PipUsers(Email=email, Password=password, FirstName=first_name, LastName=last_name, Token=token)
    try:
        p.save()
    except ValidationError:
        return None
    else:
        return token
        
def update_pip_user (pipUsersEmail, password):
    from django.core.exceptions import ValidationError, NON_FIELD_ERRORS
    pipUsersEmail.Password = password
    token = str(uuid.uuid1())
    pipUsersEmail.Token = token
    try:
        pipUsersEmail.save()
    except ValidationError:
        return None
    else:
        return token

@csrf_exempt
def register (request):
    if request.method != 'POST':
        return HttpResponse ("There is POST method only.")

    keys = request.POST.keys()
    response = {}
    if "API" not in keys:
        response["Error"] = {"ErrorCode": "666", "ErrorDescription": "There is no API parameter."}
        return HttpResponse (json.dumps(response))
    else:
        api_ver = request.POST.get("API")
    if api_ver != "1":
        response["Error"] = {"ErrorCode": "777", "ErrorDescription": "Wrong API version."}
        return HttpResponse (json.dumps(response))
    else:
        response["Error"] = {"ErrorCode": "", "ErrorDescription": ""}
    
    from restserver.pipture.models import PipUsers

    user = PipUsers()
    user.save()
        
    response["SessionKey"] = "%s" % (user.Token)
    response["UUID"] = "%s" % (user.UserUID)
    return HttpResponse (json.dumps(response))
    
    
@csrf_exempt    
def login (request):
    if request.method != 'POST':
        return HttpResponse ("There is POST method only.")
    keys = request.POST.keys()
    response = {}
    if "API" not in keys:
        response["Error"] = {"ErrorCode": "666", "ErrorDescription": "There is no API parameter."}
        return HttpResponse (json.dumps(response))
    else:
        api_ver = request.POST.get("API")
    if api_ver != "1":
        response["Error"] = {"ErrorCode": "777", "ErrorDescription": "Wrong API version."}
        return HttpResponse (json.dumps(response))
    else:
        response["Error"] = {"ErrorCode": "", "ErrorDescription": ""}
    
    from restserver.pipture.models import PipUsers

    user_uid = request.POST.get('UUID', None)
    if not user_uid:
        response["Error"] = {"ErrorCode": "1", "ErrorDescription": "There is no UUID."}
        return HttpResponse (json.dumps(response))
                
    try:
        pipUsersUID = PipUsers.objects.get(UserUID=user_uid)
    except PipUsers.DoesNotExist:
        response["Error"] = {"ErrorCode": "1", "ErrorDescription": "Login failed."}
        return HttpResponse (json.dumps(response))
    else:
        pipUsersUID.Token=uuid.uuid1()
        pipUsersUID.save()
        token = pipUsersUID.Token
        response["SessionKey"]="%s" % (token)
        return HttpResponse (json.dumps(response))
        
@csrf_exempt    
def buy (request):
    if request.method != 'POST':
        return HttpResponse ("There is POST method only.")
    keys = request.POST.keys()
    response = {}
    if "API" not in keys:
        response["Error"] = {"ErrorCode": "666", "ErrorDescription": "There is no API parameter."}
        return HttpResponse (json.dumps(response))
    else:
        api_ver = request.POST.get("API")
    if api_ver != "1":
        response["Error"] = {"ErrorCode": "777", "ErrorDescription": "Wrong API version."}
        return HttpResponse (json.dumps(response))
    else:
        response["Error"] = {"ErrorCode": "", "ErrorDescription": ""}
    
    key = request.POST.get('Key', None)
    apple_purchase = request.POST.get('AppleReceiptData', None)
    
    if not key or not apple_purchase:
        response["Error"] = {"ErrorCode": "100", "ErrorDescription": "Authentication error."}
        return HttpResponse (json.dumps(response))
    
    from restserver.pipture.models import PipUsers
    
    try:
        purchaser = PipUsers.objects.get(Token=key)
    except PipUsers.DoesNotExist:
        response["Error"] = {"ErrorCode": "100", "ErrorDescription": "Authentication error."}
        return HttpResponse (json.dumps(response))

    #-----------------------To Apple Server----------------------------
    data_json = json.dumps({"receipt-data" : "%s" % (apple_purchase)})
    url = 'https://buy.itunes.apple.com/verifyReceipt'
    req = urllib2.Request(url=url, data=data_json)
    response_apple = urllib2.urlopen(req)
    result = response_apple.read()
    result_json = json.loads(result)
    
    if result_json['status'] != 0:
        response["Error"] = {"ErrorCode": "1", "ErrorDescription": "Purchase Validation error."}
        return HttpResponse (json.dumps(response))
    else:
        apple_product_response = result_json['receipt']['product_id']
        apple_product_quantity = int(result_json['receipt']['quantity'])
        apple_transaction_id = result_json['receipt']['transaction_id']
        
    #-----------------------To Apple Server----------------------------
    
    from restserver.pipture.models import AppleProducts
    from restserver.pipture.models import Transactions
    from django.db import IntegrityError
    
    try:
        apple_product = AppleProducts.objects.get (ProductId=apple_product_response)
    except AppleProducts.DoesNotExist:
        response["Error"] = {"ErrorCode": "2", "ErrorDescription": "Wrong product."}
        return HttpResponse (json.dumps(response))
    if apple_product.ProductId == "com.pipture.Pipture.credits":
        try:
            t = Transactions(UserId=purchaser, ProductId=apple_product, Cost=Decimal(apple_product.Price * apple_product_quantity), AppleTransactionId=apple_transaction_id)
            t.save()
        except IntegrityError:
            response["Error"] = {"ErrorCode": "3", "ErrorDescription": "Duplicate transaction Id."}
            return HttpResponse (json.dumps(response))

        purchaser.Balance = Decimal (purchaser.Balance + Decimal(apple_product.Price * apple_product_quantity))
        purchaser.save()
        response["Balance"] = "%s" % (purchaser.Balance)
        return HttpResponse (json.dumps(response))
 
    else:
        response["Error"] = {"ErrorCode": "2", "ErrorDescription": "Wrong product."}
        return HttpResponse (json.dumps(response))


def getBalance (request):
    keys = request.GET.keys()
    response = {}
    if "API" not in keys:
        response["Error"] = {"ErrorCode": "666", "ErrorDescription": "There is no API parameter."}
        return HttpResponse (json.dumps(response))
    else:
        api_ver = request.GET.get("API")
    if api_ver != "1":
        response["Error"] = {"ErrorCode": "777", "ErrorDescription": "Wrong API version."}
        return HttpResponse (json.dumps(response))
    else:
        response["Error"] = {"ErrorCode": "", "ErrorDescription": ""}

    key = request.GET.get('Key', None)
    if not key:
        response["Error"] = {"ErrorCode": "100", "ErrorDescription": "Authentication error."}
        return HttpResponse (json.dumps(response))

    from restserver.pipture.models import PipUsers
    
    try:
        purchaser = PipUsers.objects.get(Token=key)
    except PipUsers.DoesNotExist:
        response["Error"] = {"ErrorCode": "100", "ErrorDescription": "Authentication error."}
        return HttpResponse (json.dumps(response))
    response["Balance"] = "%s" % (purchaser.Balance)
    return HttpResponse (json.dumps(response))

def new_send_message (user, video_id, message, video_type, user_name, screenshot_url = ''):
    from restserver.pipture.models import SendMessage
    try:
        s = SendMessage (UserId=user,Text=message,LinkId= video_id,LinkType=video_type, UserName=user_name, ScreenshotURL=screenshot_url)
        s.save()
    except Exception as e:
        print "%s" % (e)
        raise
    return s.Url


@csrf_exempt    
def sendMessage (request):
    if request.method != 'POST':
        return HttpResponse ("There is POST method only.")
    keys = request.POST.keys()
    response = {}
    if "API" not in keys:
        response["Error"] = {"ErrorCode": "666", "ErrorDescription": "There is no API parameter."}
        return HttpResponse (json.dumps(response))
    else:
        api_ver = request.POST.get("API")
    if api_ver != "1":
        response["Error"] = {"ErrorCode": "777", "ErrorDescription": "Wrong API version."}
        return HttpResponse (json.dumps(response))
    else:
        response["Error"] = {"ErrorCode": "", "ErrorDescription": ""}
    
    key = request.POST.get('Key', None)
    episode_id = request.POST.get('EpisodeId', None)
    trailer_id = request.POST.get('TrailerId', None)
    message = request.POST.get('Message', None)
    timeslot_id = request.POST.get('TimeslotId', None)
    screenshot_url = request.POST.get('ScreenshotURL', None)
    user_name = request.POST.get('UserName', None)

    if episode_id and trailer_id:
        response["Error"] = {"ErrorCode": "888", "ErrorDescription": "There are EpisodeId and TrailerId. Should be only one param."}
        return HttpResponse (json.dumps(response))
    
    if not episode_id and not trailer_id:
        response["Error"] = {"ErrorCode": "888", "ErrorDescription": "There are no EpisodeId or TrailerId. Should be one param."}
        return HttpResponse (json.dumps(response))

    if not message:
        response["Error"] = {"ErrorCode": "4", "ErrorDescription": "Message is empty."}
        return HttpResponse (json.dumps(response))

    if len(message) >= 200:
        response["Error"] = {"ErrorCode": "4", "ErrorDescription": "Message is too long."}
        return HttpResponse (json.dumps(response))

    if not user_name:
        response["Error"] = {"ErrorCode": "4", "ErrorDescription": "There is no UserName param."}
        return HttpResponse (json.dumps(response))

    if not key:
        response["Error"] = {"ErrorCode": "100", "ErrorDescription": "Authentication error."}
        return HttpResponse (json.dumps(response))
    
    from restserver.pipture.models import PipUsers
    
    try:
        purchaser = PipUsers.objects.get(Token=key)
    except PipUsers.DoesNotExist:
        response["Error"] = {"ErrorCode": "100", "ErrorDescription": "Authentication error."}
        return HttpResponse (json.dumps(response))
    

    from restserver.pipture.models import PurchaseItems
    SEND_EP = PurchaseItems.objects.get(Description="SendEpisode")
        
    if trailer_id:
        video_url, error = get_video_url_from_episode_or_trailer (id=trailer_id, type_r="T")
        if error:
            response["Error"] = {"ErrorCode": "888", "ErrorDescription": "There is error: %s." % (error)}
            return HttpResponse (json.dumps(response))
        else:
            u_url = new_send_message (user=purchaser, video_id=trailer_id, message=message, video_type="T", user_name=user_name, screenshot_url=(screenshot_url or ''))
            response['MessageURL'] = "/videos/%s/" % (u_url)
            response['Balance'] = "%s" % (purchaser.Balance)
            return HttpResponse (json.dumps(response))
    
    from restserver.pipture.models import TimeSlots
    from restserver.pipture.models import TimeSlotVideos
   
    if timeslot_id and TimeSlots.timeslot_is_current(timeslot_id) and TimeSlotVideos.is_contain_id (timeslot_id, episode_id, "E"):
        u_url = new_send_message (user=purchaser, video_id=episode_id, message=message, video_type="E", user_name=user_name, screenshot_url=(screenshot_url or ''))
        response['MessageURL'] = "/videos/%s/" % (u_url)
        response['Balance'] = "%s" % (purchaser.Balance)
        return HttpResponse (json.dumps(response))

    from restserver.pipture.models import UserPurchasedItems

    video_url, error = get_video_url_from_episode_or_trailer (id=episode_id, type_r="E")
    if error:
        response["Error"] = {"ErrorCode": "888", "ErrorDescription": "There is error: %s." % (error)}
        return HttpResponse (json.dumps(response))


    is_purchased = UserPurchasedItems.objects.filter(UserId=purchaser, ItemId=episode_id, PurchaseItemId = SEND_EP).count()
        
    if is_purchased:
        u_url = new_send_message (user=purchaser, video_id=episode_id, message=message, video_type="E", user_name=user_name, screenshot_url=(screenshot_url or ''))
        response['MessageURL'] = "/videos/%s/" % (u_url)
        response['Balance'] = "%s" % (purchaser.Balance)
        return HttpResponse (json.dumps(response))

    else:
        if (purchaser.Balance - SEND_EP.Price) >= 0:
            new_p = UserPurchasedItems(UserId=purchaser, ItemId=episode_id, PurchaseItemId = SEND_EP, ItemCost=SEND_EP.Price)
            new_p.save()
            purchaser.Balance = Decimal (purchaser.Balance - SEND_EP.Price)
            purchaser.save()
            u_url = new_send_message (user=purchaser, video_id=episode_id, message=message, video_type="E", user_name=user_name, screenshot_url=(screenshot_url or ''))
            response['MessageURL'] = "/videos/%s/" % (u_url)
            response['Balance'] = "%s" % (purchaser.Balance)
            return HttpResponse (json.dumps(response))
        else:
            response["Error"] = {"ErrorCode": "3", "ErrorDescription": "Not enough money."}
            return HttpResponse (json.dumps(response))


def getAlbumScreenshotByEpisodeId (EpisodeId):
    from restserver.pipture.models import AlbumScreenshotGallery
    response = {}
    try:
        EpisodeId = int (EpisodeId)
    except:
        response["Error"] = {"ErrorCode": "1", "ErrorDescription": "EpisodeId is not int."}
        return HttpResponse (json.dumps(response))        
    
    from restserver.pipture.models import Episodes
    try:
        episode = Episodes.objects.select_related(depth=1).get (EpisodeId=EpisodeId)
    except Episodes.DoesNotExist:
        response["Error"] = {"ErrorCode": "2", "ErrorDescription": "There is no episode with id %s." % (EpisodeId)}
        return HttpResponse (json.dumps(response))

    response["Screenshots"] = []
    try:
        screenshots = AlbumScreenshotGallery.objects.filter (AlbumId=episode.AlbumId).extra(order_by = ['Description'])
    except AlbumScreenshotGallery.DoesNotExist:
        return HttpResponse (json.dumps(response))
    else:
        for screenshot in screenshots:
            response["Screenshots"].append ({"URL": screenshot.ScreenshotURL, "Description": screenshot.Description})
        return HttpResponse (json.dumps(response))

def getAlbumScreenshots (request):
    keys = request.GET.keys()
    response = {}
    if "API" not in keys:
        response["Error"] = {"ErrorCode": "666", "ErrorDescription": "There is no API parameter."}
        return HttpResponse (json.dumps(response))
    else:
        api_ver = request.GET.get("API")
    if api_ver != "1":
        response["Error"] = {"ErrorCode": "777", "ErrorDescription": "Wrong API version."}
        return HttpResponse (json.dumps(response))
    else:
        response["Error"] = {"ErrorCode": "", "ErrorDescription": ""}

    EpisodeId = request.GET.get('EpisodeId', None)
    
    if not EpisodeId:
        response["Error"] = {"ErrorCode": "100", "ErrorDescription": "There is no EpisodeId."}
        return HttpResponse (json.dumps(response))

    return getAlbumScreenshotByEpisodeId (EpisodeId)
