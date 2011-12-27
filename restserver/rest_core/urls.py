from django.conf.urls.defaults import *
from django.conf import settings
from restserver.rest_core import views as rest_view


urlpatterns = patterns('',
                       (r'^getTimeslots$', rest_view.getTimeslots),
                       (r'^getVideo$', rest_view.getVideo),
                       (r'^getPlaylist$', rest_view.getPlaylist),
                       (r'^getAlbums$', rest_view.getAlbums),
                       (r'^getAlbumDetail$', rest_view.getAlbumDetail),
                       (r'^register$', rest_view.register),
                       (r'^login$', rest_view.login),
                       (r'^buy$', rest_view.buy),
                       (r'^getBalance$', rest_view.getBalance),
                       (r'^sendMessage$', rest_view.sendMessage),
                       (r'^getAlbumScreenshots$', rest_view.getAlbumScreenshots),
                       (r'', rest_view.index),
                       )