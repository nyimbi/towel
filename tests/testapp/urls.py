import os

from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from .api import api_v1
from .views import person_views


admin.autodiscover()


urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^api/v1/', include(api_v1.urls)),
    url(r'^persons/', include(person_views.urls)),
) + staticfiles_urlpatterns()