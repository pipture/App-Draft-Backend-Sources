from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
                       (r'^media/(?P<path>.*)$', 'django.views.static.serve', { 'document_root': "/".join((settings.MEDIA_ROOT,'admin','media')) }), #for admin module
                       (r'^site_media/(?P<path>.*)$', 'django.views.static.serve', { 'document_root': settings.MEDIA_ROOT }),
                       (r'^admin/', include(admin.site.urls)),
                       (r'^manage/', include('restserver.pipture.urls')),
                       (r'^videos/(?P<u_url>[a-z\d-]+)/$', 'restserver.video_player.views.index'),
                       ('', include('restserver.rest_core.urls')), #there is API
                       )