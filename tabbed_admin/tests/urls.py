from django.contrib import admin
from django.urls import path

from tabbed_admin.tests.admin import BandAdmin
from tabbed_admin.tests.models import Band

admin.site.register(Band, BandAdmin)
urlpatterns = [path("admin/", admin.site.urls)]
