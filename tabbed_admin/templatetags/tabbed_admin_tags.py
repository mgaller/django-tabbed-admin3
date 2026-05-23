from django import template
from django.contrib.admin.helpers import Fieldset
from django.core.exceptions import ImproperlyConfigured
from django.template.loader import render_to_string

register = template.Library()


@register.simple_tag(takes_context=True)
def render_tab_fieldsets_inlines(context, entry):
    """
    Render the fieldsets and inlines for a tab.
    """
    fieldset_template = "admin/includes/fieldset.html"
    admin_form = context["adminform"]
    if "request" not in context:
        raise ImproperlyConfigured(
            '"request" missing from context. Add '
            '"django.template.context_processors.request" to your '
            "TEMPLATES context_processors setting."
        )
    request = context["request"]
    obj = context.get("original", None)
    readonly_fields = admin_form.model_admin.get_readonly_fields(request, obj)
    inline_matching = {}
    if "inline_admin_formsets" in context:
        inline_matching = {
            inline.opts.__class__.__name__: inline
            for inline in context["inline_admin_formsets"]
        }

    if entry["type"] == "fieldset":
        name = entry["name"]
        f = Fieldset(
            admin_form.form,
            name,
            readonly_fields=readonly_fields,
            model_admin=admin_form.model_admin,
            **entry["config"],
        )
        context["fieldset"] = f
        return render_to_string(fieldset_template, context.flatten(), request=request)
    elif entry["type"] == "inline":
        try:
            inline_admin_formset = inline_matching[entry["name"]]
            context["inline_admin_formset"] = inline_admin_formset
            return render_to_string(
                inline_admin_formset.opts.template,
                context.flatten(),
                request=request,
            )
        except KeyError:
            # The user does not have the permission
            pass
    return ""
