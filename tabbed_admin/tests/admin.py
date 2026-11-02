from django.contrib import admin

from tabbed_admin import TabbedModelAdmin
from tabbed_admin.tests.models import Album, Band, Concert, Interview, Musician


class MusicianInline(admin.StackedInline):
    model = Musician


class ConcertInline(admin.TabularInline):
    model = Concert


class AlbumInline(admin.TabularInline):
    model = Album


class InterviewInline(admin.TabularInline):
    model = Interview


class BandAdmin(TabbedModelAdmin):
    model = Band

    tab_overview = (
        (None, {"fields": ("name", "bio", "style")}),
        MusicianInline,
        ("Contact", {"fields": ("agent", "phone", "email")}),
    )
    tab_ressources = (ConcertInline, AlbumInline)
    tabs = [("Overview", tab_overview), ("Ressources", tab_ressources)]
