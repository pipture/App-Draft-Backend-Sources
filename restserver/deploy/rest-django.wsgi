#/usr/bin/python
# -*- coding: utf-8 -*-
import os, sys

dn = os.path.dirname
PROJECT_ROOT = os.path.abspath( dn(dn(__file__)) )
DJANGO_PROJECT_ROOT = os.path.join(PROJECT_ROOT, 'restserver')
sys.path.append( DJANGO_PROJECT_ROOT )
sys.path.append("/var/pipture-backend/restserver")
sys.path.append("/var/pipture-backend")

os.environ['DJANGO_SETTINGS_MODULE'] = 'restserver.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()