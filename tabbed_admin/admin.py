from django.conf import settings
from django.contrib.admin.options import ModelAdmin
from django.utils.translation import gettext_lazy as _

from .settings import JQUERY_UI_CSS, JQUERY_UI_JS, USE_JQUERY_UI


class TabbedModelAdmin(ModelAdmin):
    tabs = None
    formatted_tabs = {}

    # Needs a specific template to display the tabs
    change_form_template = "tabbed_admin/change_form.html"
    tabbed_admin_base_template = "admin/change_form.html"

    def get_fieldsets(self, request, obj=None):
        """
        Overwrites BaseModelAdmin fieldsets to add fieldsets passed by the
        tabs.
        If the tabs attribute is not set, use the default ModelAdmin method.
        """
        tabs_fieldsets = self.get_formatted_tabs(request, obj)["fieldsets"]
        if self.tabs is not None:
            self.fieldsets = ()
        self.fieldsets = self.add_tabbed_item(tabs_fieldsets, self.fieldsets)
        return super().get_fieldsets(request, obj)

    def get_inline_instances(self, request, obj=None):
        """
        Overwrites BaseModelAdmin inline_instances to add inlines passed by
        the tabs.
        If the tabs attribute is not set, use the default ModelAdmin method.
        """
        if self.tabs is not None:
            self.inlines = ()
        tabs_inlines = self.get_formatted_tabs(request, obj)["inlines"]
        self.inlines = self.add_tabbed_item(tabs_inlines, self.inlines)
        return super().get_inline_instances(request, obj)

    def add_tabbed_item(self, items_to_add, collection):
        """
        Adds tabbed items (inlines or fieldsets) to their corresponding
        attribute.
        """
        if items_to_add:
            for item in items_to_add:
                if item not in collection:
                    if isinstance(collection, tuple):
                        collection = collection + (item,)
                    elif isinstance(collection, list):
                        collection.append(item)
        return collection

    def get_tabs(self, request, obj=None):
        """
        Returns the tabs attribute.
        """
        return self.tabs

    def get_formatted_tabs(self, request, obj=None):
        """
        Returns the formatted tabs attribute.
        """
        if self.tabs:
            self.parse_fieldsets_inlines_from_tabs(request, obj)
        else:
            self.formatted_tabs = {"fields": [], "fieldsets": (), "inlines": ()}
        return self.formatted_tabs

    def parse_fieldsets_inlines_from_tabs(self, request, obj=None):
        """
        Parses the self.tabs attribute. Checks its integrity and populates
        self._tabs_fieldsets and self._tabs_inlines attributes.
        """
        tabs_fieldsets = ()
        tabs_inlines = ()
        self.formatted_tabs = {"fields": []}
        for tab in self.get_tabs(request, obj):
            # Checks that each tab is formatted with 2 arguments: verbose name
            # of the tab and the tab configuration.
            if not isinstance(tab, (tuple, list)):
                raise TypeError(_("Each tab entry must be either a list or a tuple"))
            if len(tab) != 2:
                raise ValueError(_("Each tabs entry must contain 2 arguments: a verbose name and the tab setup."))
            if not isinstance(tab[1], (tuple, list)):
                raise TypeError(_("A tab definition must be either a list or a tuple"))
            # Parse the tab configuration: if an entry is a tuple or a list
            # it's a fieldset, otherwise it's an inline class.
            formatted_tab = {"name": tab[0], "entries": []}
            for tab_entry in tab[1]:
                if isinstance(tab_entry, (tuple, list)):
                    tabs_fieldsets = tabs_fieldsets + (tab_entry,)
                    formatted_tab_entry = {
                        "type": "fieldset",
                        "name": tab_entry[0],
                        "config": tab_entry[1],
                        "index": len(tabs_fieldsets) - 1,
                    }
                else:
                    tabs_inlines = tabs_inlines + (tab_entry,)
                    formatted_tab_entry = {
                        "type": "inline",
                        "name": tab_entry.__name__,
                    }
                formatted_tab["entries"].append(formatted_tab_entry)
            self.formatted_tabs["fields"].append(formatted_tab)
        self.formatted_tabs["fieldsets"] = tabs_fieldsets
        self.formatted_tabs["inlines"] = tabs_inlines

    def render_change_form(self, request, context, add=False, change=False, form_url="", obj=None):
        context = {
            **context,
            "tabs": self.get_formatted_tabs(request, obj),
            "tabbed_admin_base_template": context.get("tabbed_admin_base_template", self.tabbed_admin_base_template),
        }
        return super().render_change_form(
            request,
            context,
            add=add,
            change=change,
            form_url=form_url,
            obj=obj,
        )

    class Media:
        """
        Extends media class to add custom jquery ui if
        TABBED_ADMIN_USE_JQUERY_UI is set to True.
        """

        if "grappelli" in settings.INSTALLED_APPS:
            css = {"all": ("tabbed_admin/css/tabbed_grappelli_admin.css",)}

        if USE_JQUERY_UI:
            css = {
                "all": (
                    JQUERY_UI_CSS,
                    "tabbed_admin/css/tabbed_admin.css",
                )
            }
            js = (JQUERY_UI_JS,)
