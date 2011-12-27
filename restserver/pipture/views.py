from django.shortcuts import render_to_response, redirect
from django.template.context import RequestContext
from django.core.context_processors import csrf
from django.http import HttpResponse
import json
#import os

from django.conf import settings

from restserver.pipture.models import Series 
from restserver.pipture.models import Albums
from restserver.pipture.models import TimeSlots
from restserver.pipture.models import Trailers
from restserver.pipture.models import Episodes
from restserver.pipture.models import TimeSlotVideos
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def index (request):
    data = {}
    return render_to_response('TimeSlotManage.html', data,
                                       context_instance=RequestContext(request))        

#----------------actual----------------------------
@staff_member_required
def get_timeslots(request):
    try:
        timeslots = TimeSlots.objects.all()
    except Exception as e:
        result =  "There is internal error: %s (%s)." % (e, type (e))
    else:
        result =  dict([(timeslot.TimeSlotsId, str(timeslot)) for timeslot in timeslots])
    return HttpResponse (json.dumps(result))

@staff_member_required
def get_albums(request):
    try:
        albums = Albums.objects.all()
    except Exception as e:
        result =  "There is internal error: %s (%s)." % (e, type (e))
    else:
        result =  dict([(album.AlbumId, album.Title) for album in albums])
    return HttpResponse (json.dumps(result))

def get_timeslot_entity_by_id (id):
    try:
        id = int(id)
    except:
        return None
    try:
        timeslot = TimeSlots.objects.get(TimeSlotsId=id)
    except:
        return None
    else:
        return timeslot

def get_album_entity_by_id (id):
    try:
        id = int(id)
    except:
        return None
    try:
        album = Albums.objects.get(AlbumId=id)
    except:
        return None
    else:
        return album


def get_episode_title_by_id (id):
    try:
        episode = Episodes.objects.get(EpisodeId=int(id))
    except:
        return None
    else:
        return episode.Title

def get_trailer_title_by_id (id):
    try:
        trailer = Trailers.objects.get(TrailerId=int(id))
    except:
        return None
    else:
        return trailer.Title    

@staff_member_required    
def get_timeslot_videos(request):
    if request.method != 'GET':
        return HttpResponse ("There is GET method only.")
        
    chosen_timeslot = request.GET.get('chosen_timeslot', None)
    if not chosen_timeslot:
        return HttpResponse ("There is no chosen_timeslot in params.")
    

    timeslot = get_timeslot_entity_by_id(chosen_timeslot)
    
    if not timeslot:
        result = "There is no timeslots for chosen_timeslot in params."
    else:
        result = []
        videos = TimeSlotVideos.objects.filter(TimeSlotsId=timeslot).order_by('Order')
        for video in videos:
            video_slot = {'order': video.Order, 'id': video.LinkId, 'type': video.LinkType }
            if video.LinkType == "T":
                video_slot ['title'] = get_trailer_title_by_id (video.LinkId)
            elif video.LinkType == "E":
                video_slot ['title']  = get_episode_title_by_id (video.LinkId)
            result.append (video_slot)
    return HttpResponse (json.dumps(result))

@staff_member_required
def get_album_videos(request):
    if request.method != 'GET':
        return HttpResponse ("There is GET method only.")
        
    chosen_album = request.GET.get('chosen_album', None)
    if not chosen_album:
        return chosen_album ("There is no chosen_album in params.")
    

    album = get_album_entity_by_id(chosen_album)
    
    if not album:
        result = "There is no album for chosen_album in params."
    else:
        result = []
        episodes = Episodes.objects.filter(AlbumId=album)
        for episode in episodes:
            per_episode = {'id': episode.EpisodeId, 'title': episode.Title }
            result.append (per_episode)
    return HttpResponse (json.dumps(result))

@staff_member_required
def get_trailers(request):
    if request.method != 'GET':
        return HttpResponse ("There is GET method only.")

    result = []
    trailers = Trailers.objects.all()
    for trailer in trailers:
        per_trailer = {'id': trailer.TrailerId, 'title': trailer.Title }
        result.append (per_trailer)
    return HttpResponse (json.dumps(result))

@staff_member_required
def set_timeslot (request):
    if request.method == 'POST':
        searches = request.POST.lists()
        result_json = None
        
        for (k, v) in searches:
            if k == u'csrfmiddlewaretoken': 
                continue
            elif k == u'result_json':
                try:
                    result_json = v[0]
                except Exception as e:
                    return HttpResponse ("There is internal error %s (%s)." % (e, type (e)))

        
        if not result_json:
            return HttpResponse("Nothing to add.")
        result = json.loads(result_json)
        result_keys = result.keys()
        for keys in ['TimeSlotId', 'TimeSlotVideos']:
            if keys not in result_keys:  return HttpResponse ("There is no parameter %s." % (keys))
        timeslot_id = result['TimeSlotId']
        timeslot_videos = result['TimeSlotVideos']
        timeslot = get_timeslot_entity_by_id (timeslot_id)
        if not timeslot:
            return HttpResponse("There is no : %s timeslot." % (timeslot))
        TimeSlotVideos.objects.filter(TimeSlotsId=timeslot).delete()
        for videos in timeslot_videos:
            video = TimeSlotVideos(TimeSlotsId=timeslot, Order=int(videos['Order']), LinkId = int(videos['LinkId']), LinkType=videos['LinkType'])
            try:
                video.save()
            except Exception as e:
                return HttpResponse ("There is internal error %s (%s)." % (e, type (e)))
        
        return HttpResponse("TimeSlot was saved.")

    else:
        return HttpResponse("There is POST method only.")


#----------------actual----------------------------

#old
def get_all_series ():
    try:
        all_series = Series.objects.all()
    except:
        return None
    else:
        return dict([(series.SeriesId, series.Title) for series in all_series])
        
def get_all_series_get (request):
    return HttpResponse (json.dumps(get_all_series()))    
    

def get_series_entity_by_id(id):
    try:
        id = int(id)
    except:
        return None
    
    try:
        series = Series.objects.get(series_id=id)
    except:
        return None
    else:
        return series

@staff_member_required
def set_new_album_post (request):
    if request.method == 'POST':
        searches = request.POST.lists()
        new_album = None
        chosen_series = None
        
        for (k, v) in searches:
            if k == u'csrfmiddlewaretoken': 
                continue
            elif k == u'chosen_series':
                try:
                    chosen_series = int(v[0])
                except Exception as e:
                    return HttpResponse ("There is internal error %s (%s)." % (e, type (e)))
            elif k == u'new_album':
                try:
                    new_album = str(v[0]).strip()
                except Exception as e:
                    return HttpResponse ("There is internal error %s (%s)." % (e, type (e)))
        
        if not new_album:
            return HttpResponse("Nothing to add.")
        elif not chosen_series:
            return HttpResponse("Bad chosen series.")
        chosen_series_entity = get_series_entity_by_id (chosen_series)
        if not chosen_series_entity:
            return HttpResponse("There is no : %s series." % (chosen_series))
        (albums, error) = get_albums_from_series(chosen_series)
        if error:
            return HttpResponse("There is error: %s." % (error)) 

        for id, items in albums.items():
            if items == new_album:
                return HttpResponse("There is '%s' album already." % (new_album))
        album = Albums(Description=new_album, SeriesId=chosen_series_entity)
        try:
            album.save()
        except Exception as e:
            return HttpResponse ("There is internal error %s (%s)." % (e, type (e)))
        else:
            return HttpResponse ("Album '%s' is added." % (new_album))
    else:
        return HttpResponse("There is POST method only.")

@staff_member_required    
def set_new_series_post (request):
    if request.method == 'POST':
        searches = request.POST.lists()
        new_series = ""
        for (k, v) in searches:
            if k == u'csrfmiddlewaretoken': 
                continue
            elif k == u'new_series':
                try:
                    new_series = str(v[0]).strip()
                except Exception as e:
                    return HttpResponse ("There is internal error %s (%s)." % (e, type (e)))
        
        if not new_series:
            return HttpResponse("Nothing to add.")
        all_series = get_all_series()
        for id, items in all_series.items():
            if items.strip() == new_series:
                return HttpResponse("There is '%s' series already." % (new_series))
        series = Series(Title=new_series)
        try:
            series.save()
        except Exception as e:
            return HttpResponse ("There is internal error %s (%s)." % (e, type (e)))
        else:
            return HttpResponse ("Series '%s' is added." % (new_series))
    else:
        return HttpResponse("There is POST method only.")

@staff_member_required
def get_albums_by_series_get (request):
    if request.method == 'GET':
        searches = request.GET.lists()
        chosen_series = None
        for (k, v) in searches:
            if k == u'csrfmiddlewaretoken': 
                continue
            elif k == u'chosen_series':
                try:
                    chosen_series = int(v[0])
                except Exception as e:
                    return HttpResponse ("There is internal error %s (%s)." % (e, type (e)))
        
        if not chosen_series:
            return HttpResponse("Nothing to refresh, there is no 'chosen_series'.")
        (albums, error) = get_albums_from_series(chosen_series)
        if error:
            return HttpResponse("There is error: %s." % (error)) 
        else:
            return HttpResponse(json.dumps(albums))
            
    else:
        return HttpResponse("There is GET method only.")
    
def get_albums_from_series (series_id):
    '''returns (result, error)'''
    try:
        series_entity = get_series_entity_by_id (series_id)
    except Exception as e:
        return (None, "There is error %s (%s) with get entity with id: %s" % (e, type(e), series_id))
    try:
        albums = Albums.objects.filter(SeriesId=series_entity)
    except Exception as e:
        return (None, "There is error %s (%s) with getting albums for series with id: %s" % (e, type(e), series_id))
    if albums:
        return (dict([(album.AlbumId, album.Description) for album in albums]), None)
    else:
        return ({}, None)