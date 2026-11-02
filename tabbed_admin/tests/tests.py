from unittest.mock import patch

import django
from django.contrib import admin
from django.contrib.auth.models import Permission, User
from django.template import Context
from django.test import RequestFactory, TestCase
from django.urls import reverse

from tabbed_admin import TabbedModelAdmin
from tabbed_admin.settings import JQUERY_UI_CSS, JQUERY_UI_JS
from tabbed_admin.templatetags.tabbed_admin_tags import render_tab_fieldsets_inlines
from tabbed_admin.tests.admin import BandAdmin, InterviewInline
from tabbed_admin.tests.models import Band


class TabbedModelAdminTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_superuser(username="admin", email="admin@example.test", password="test-only")
        cls.band = Band.objects.create(name="Test band", style=Band.STYLE_JAZZ)

    def setUp(self) -> None:
        self.request = RequestFactory().get("/admin/")
        self.request.user = self.user
        self.model_admin = BandAdmin(Band, admin.site)

    def test_fieldsets_inline_attribute_populated(self) -> None:
        fieldsets = self.model_admin.get_fieldsets(self.request)
        inlines = self.model_admin.get_inline_instances(self.request)
        self.assertEqual(len(fieldsets), 2)
        self.assertEqual(len(inlines), 3)
        self.assertEqual(self.model_admin.fieldsets, fieldsets)
        self.assertEqual(len(self.model_admin.inlines), 3)

    def test_fieldsets_inlines_overridden_by_tabs(self) -> None:
        class ConfiguredAdmin(BandAdmin):
            fieldsets = (("Unused", {"fields": ("website",)}),)
            inlines = (InterviewInline,)

        model_admin = ConfiguredAdmin(Band, admin.site)
        self.assertEqual(model_admin.get_fieldsets(self.request), model_admin.formatted_tabs["fieldsets"])
        model_admin.get_inline_instances(self.request)
        self.assertNotIn(InterviewInline, model_admin.inlines)

    def test_dynamic_tabs_receive_current_object(self) -> None:
        class DynamicAdmin(BandAdmin):
            def get_tabs(self, request, obj=None):
                name = obj.name if obj else "New band"
                return [(name, [(None, {"fields": ("name",)})])]

        model_admin = DynamicAdmin(Band, admin.site)
        response = model_admin.change_view(self.request, str(self.band.pk))
        response.render()
        self.assertEqual(response.context_data["tabs"]["fields"][0]["name"], "Test band")
        self.assertEqual(model_admin.get_formatted_tabs(self.request)["fields"][0]["name"], "New band")

    def test_tab_configuration_is_isolated(self) -> None:
        first = self.model_admin.get_formatted_tabs(self.request)
        second = BandAdmin(Band, admin.site).get_formatted_tabs(self.request)
        first["fields"].clear()
        self.assertEqual(len(second["fields"]), 2)
        self.assertEqual(self.model_admin.get_fieldsets(self.request)[0][1]["fields"], ("name", "bio", "style"))

    def test_no_tabs_uses_standard_layout(self) -> None:
        model_admin = TabbedModelAdmin(Band, admin.site)
        response = model_admin.add_view(self.request)
        response.render()
        self.assertContains(response, 'name="name"')
        self.assertNotContains(response, 'id="tabs"')
        self.assertEqual(model_admin.get_inlines(self.request, None), ())

    def test_media_uses_jquery_ui(self) -> None:
        media = self.model_admin.media
        self.assertIn(JQUERY_UI_JS, media._js)
        self.assertIn(JQUERY_UI_CSS, media._css["all"])
        self.assertIn("tabbed_admin/css/tabbed_admin.css", media._css["all"])
        self.assertNotIn("tabbed_admin/js/tabbed_admin.js", media._js)

    def test_custom_parent_template_preserves_controls(self) -> None:
        # A custom parent template must retain its submit controls and tools.
        templates = {
            "custom_change_form.html": '{% extends "admin/change_form.html" %}{% block submit_buttons_bottom %}<button>Custom save</button>{% endblock %}'
        }
        from django.conf import settings

        template_settings = [
            {
                **settings.TEMPLATES[0],
                "APP_DIRS": False,
                "OPTIONS": {
                    **settings.TEMPLATES[0]["OPTIONS"],
                    "loaders": [
                        ("django.template.loaders.locmem.Loader", templates),
                        "django.template.loaders.app_directories.Loader",
                    ],
                },
            }
        ]
        with self.settings(TEMPLATES=template_settings):
            for use_context in (False, True):
                with self.subTest(use_context=use_context):
                    self.model_admin.tabbed_admin_base_template = (
                        "admin/change_form.html" if use_context else "custom_change_form.html"
                    )
                    extra_context = {"tabbed_admin_base_template": "custom_change_form.html"} if use_context else {}
                    response = self.model_admin.change_view(
                        self.request, str(self.band.pk), extra_context=extra_context
                    )
                    response.render()
                    self.assertContains(response, "Custom save")
                    self.assertContains(response, 'class="object-tools"', count=1)
                    self.assertContains(response, 'id="tabs"', count=1)


class TabbedAdminTagsTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_superuser(username="admin", email="admin@example.test", password="test-only")
        cls.band = Band.objects.create(name="Test band", style=Band.STYLE_JAZZ)

    def setUp(self) -> None:
        self.client.force_login(self.user)
        self.change_url = reverse("admin:tests_band_change", args=[self.band.pk])

    def test_view_only_permissions(self) -> None:
        # View-only forms must reuse Django's readonly fields instead of rebuilding them.
        viewer = User.objects.create_user(username="viewer", is_staff=True)
        viewer.user_permissions.add(Permission.objects.get(codename="view_band", content_type__app_label="tests"))
        self.client.force_login(viewer)
        response = self.client.get(self.change_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test band")
        self.assertNotContains(response, 'name="name"')
        self.assertNotContains(response, 'name="_save"')
        self.assertNotContains(response, 'id="musician_set-group"')

    def test_standard_controls_and_popup_fields(self) -> None:
        response = self.client.get(self.change_url)
        self.assertContains(response, 'name="name"', count=1)
        self.assertContains(response, 'class="object-tools"', count=1)
        if django.VERSION >= (5, 1):
            self.assertContains(response, 'id="fieldset-0-1-heading"', count=1)
        self.assertContains(response, 'name="_save"')
        self.assertContains(response, "csrfmiddlewaretoken")
        popup = self.client.get(self.change_url, {"_popup": "1", "_to_field": "id", "_source_model": "tests.band"})
        self.assertContains(popup, 'name="_popup"')
        self.assertContains(popup, 'name="_to_field"')
        self.assertNotContains(popup, 'class="object-tools"')
        if hasattr(admin, "ActionLocation"):
            self.assertContains(popup, 'name="_source_model"')

            @admin.action(description="Example form action", location=admin.ActionLocation.CHANGE_FORM)
            def example_action(model_admin, request, queryset):
                queryset.update(name="Action executed")

            with patch.object(BandAdmin, "actions", [example_action]):
                response = self.client.get(self.change_url)
                self.assertContains(response, "Example form action")
                self.assertContains(response, 'name="CHANGE_FORM-action"')
                self.assertContains(response, 'name="_selected_action"')
                response = self.client.post(
                    self.change_url,
                    {"CHANGE_FORM-action": "example_action", "_selected_action": str(self.band.pk)},
                )
            self.assertEqual(response.status_code, 302)
            self.band.refresh_from_db()
            self.assertEqual(self.band.name, "Action executed")

    def test_inline_rendering_and_form_submission(self) -> None:
        response = self.client.get(self.change_url)
        for name in ("musician", "concert", "album"):
            self.assertContains(response, f'id="{name}_set-group"', count=1)
            self.assertContains(response, f'name="{name}_set-TOTAL_FORMS"', count=1)
        data = {"name": "Changed band", "style": str(Band.STYLE_JAZZ), "_continue": "1"}
        for name in ("musician", "concert", "album"):
            data.update({f"{name}_set-TOTAL_FORMS": "0", f"{name}_set-INITIAL_FORMS": "0"})
        response = self.client.post(self.change_url, data)
        self.assertEqual(response.status_code, 302, getattr(response, "context_data", {}).get("errors"))
        self.band.refresh_from_db()
        self.assertEqual(self.band.name, "Changed band")
        data["name"] = ""
        response = self.client.post(self.change_url, data)
        self.assertContains(response, "errorlist")
        self.assertContains(response, 'id="tabs"')

    def test_unavailable_inline_renders_nothing(self) -> None:
        response = self.client.get(self.change_url)
        context = Context(response.context_data)
        context["request"] = response.wsgi_request
        entry = {"type": "inline", "name": "InterviewInline"}
        self.assertEqual(render_tab_fieldsets_inlines(context, entry), "")
        self.assertNotIn("inline_admin_formset", context)
