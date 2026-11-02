###################
Django tabbed admin
###################

This is a simple fork of django-tabbed-admin https://github.com/omji/django-tabbed-admin with compatibility updates for modern Django versions.

Version 3.2 adds Django 6.1 support while retaining jQuery UI and the existing
``TABBED_ADMIN_*`` settings. Tests cover Django 4.2, 5.0, 5.1, 5.2, 6.0 and 6.1.
The change-form template now inherits Django's form controls, actions and popup
fields instead of copying them. Projects overriding
``tabbed_admin/change_form.html`` must update their override to use this fix.
For integration with another admin extension, ``TabbedModelAdmin.tabbed_admin_base_template``
can specify a parent template instead of ``admin/change_form.html``.
The ``tabbed_admin_base_template`` context variable takes precedence over this
attribute, allowing other admin extensions to supply the parent template.


Simple library to easilly add tabs to admin forms. It also allows users to re-order inlines and fieldsets.
Django tabbed admin is compatible with django-grappelli and django-gipsy.


*******
Install
*******

It is strongly recommanded to install this theme from GIT with PIP onto you project virtualenv.

From PyPi

.. code-block::  shell-session

    pip install django-tabbed-admin3

From Github

.. code-block::  shell-session

    https://github.com/mgaller/django-tabbed-admin3#egg=tabbed_admin


*****
setup
*****

Simply add the app in your installed apps list in settings.py

.. code-block::  python

    INSTALLED_APPS = (
        ...
        'tabbed_admin'
        ...
    )

Django-tabbed-admin by default requires Jquery UI tabs plugin in order to work. It is packaged with the static files required to make it funcitonnal, however, they are not activated by default to avoid a conflict with other libraries.

In order to activate the Jquery UI statics, add the following line to the project settings:

.. code-block::  python

    TABBED_ADMIN_USE_JQUERY_UI = True


********************
Configure admin tabs
********************

In order to add tabs to a model admin, it should inherit from tabbed_admin.TabbedModelAdmin and contain a tabs attribute.
The tab attribute configuration tries to remain similar to the fieldsets and inlines setup logic.

Basically, a tuple can be created for each tab exactely the same way as for fieldsets, except that inlines can be added anywhere in between.

.. code-block::  python

    tab_overview = (
        (None, {
            'fields': ('name', 'bio', 'style')
        }),
        MusicianInline,
        ('Contact', {
            'fields': ('agent', 'phone', 'email')
        })
    )

Then each tuple have to be passed to a *tabs* attribute prefixed by the verbose name to display within the tab:

.. code-block::  python

    tabs = [
        ('Overview', tab_overview),
        ('Albums', tab_album)
    ]


A full example would give:

.. code-block::  python

    from django.contrib import admin

    from tabbed_admin import TabbedModelAdmin
    from .models import Band, Musician, Album


    class MusicianInline(admin.StackedInline):
        model = Musician
        extra = 1


    class AlbumInline(admin.TabularInline):
        model = Album
        extra = 1


    @admin.register(Band)
    class BandAdmin(TabbedModelAdmin):
        model = Band

        tab_overview = (
            (None, {
                'fields': ('name', 'bio', 'style')
            }),
            MusicianInline,
            ('Contact', {
                'fields': ('agent', 'phone', 'email')
            })
        )
        tab_album = (
            AlbumInline,
        )
        tabs = [
            ('Overview', tab_overview),
            ('Albums', tab_album)
        ]

**************************
Configure tabs dynamically
**************************

Be warned that the tabs will completely reset the fieldsets and inlines attributes in order to avoid conflicts during the form saving. Both attributes are overwritten with the entries passed to the tabs attribute. For the same reasons, it is highly recommanded not to overwrite get_fieldsets or get_inlines.

You can pass and modify the tabs dynamically the same way you would do for fieldsets or inlines.

.. code-block::  python

    def get_tabs(self, request, obj=None):
        tabs = self.tabs
        if obj is not None:
            tab_overview = self.tab_overview + ('Social', {
                'fields': ('website', 'twitter', 'facebook')
            })
            tab_ressources = self.tab_ressources + (InterviewInline, )
            tabs = [
                ('Overview', tab_overview),
                ('Ressources', tab_ressources)
            ]
        self.tabs = tabs
        return super(BandAdmin, self).get_tabs(request, obj)


********************
Change the jquery ui
********************

You can change the jquery ui css and js by either overriding the media in the
admin class

.. code-block:: python

    class Media:
        css = {
            'all': ('css/jquery-ui.theme.min.css',)
        }

or by changing the the following settings,

`TABBED_ADMIN_JQUERY_UI_CSS` and `TABBED_ADMIN_JQUERY_UI_JS`

.. code-block:: python

    TABBED_ADMIN_JQUERY_UI_CSS = 'static/css/my-custom-jquery-ui.css'
    TABBED_ADMIN_JQUERY_UI_JS = 'static/js/my-custom-jquery-ui.js'


Contribution
************

Please feel free to contribute. Any help and advices are much appreciated.
You will find an example application to run and develop the library easily.

Run the standalone test suite with ``PYTHONPATH=. python tabbed_admin/tests/runtests.py``.


*****
LINKS
*****

Development:
    https://github.com/mgaller/django-tabbed-admin3

Package:
    https://pypi.python.org/pypi/django-tabbed-admin3
