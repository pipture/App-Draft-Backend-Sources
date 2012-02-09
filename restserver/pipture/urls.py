from django.conf.urls.defaults import *
from django.conf import settings
from restserver.pipture import views as pipture_view


urlpatterns = patterns('',
                       #(r'^get_all_series/', pipture_view.get_all_series_get),
                       #(r'^new_series/', pipture_view.set_new_series_post),
                       #(r'^new_album/', pipture_view.set_new_album_post),
                       #(r'^get_albums_by_series/', pipture_view.get_albums_by_series_get),
                       (r'^get_albums_by_series/', pipture_view.get_albums_by_series_get),
                       #(r'^get_timeslots/', pipture_view.get_timeslots),
                       #(r'^get_albums/', pipture_view.get_albums),
                       (r'^get_timeslot_videos/', pipture_view.get_timeslot_videos),
                       (r'^get_album_videos/', pipture_view.get_album_videos),
                       #(r'^get_trailers/', pipture_view.get_trailers),
                       (r'^set_timeslot/', pipture_view.set_timeslot),
                       (r'', pipture_view.index),
                       )