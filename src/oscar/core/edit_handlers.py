"""
Pulled directly from https://github.com/labd/django-oscar-wagtail
"""
import functools
from django.db import models
from django.template.loader import render_to_string
from django.utils.html import escape, format_html, mark_safe
from django.utils.functional import cached_property

from wagtail.admin import compare
from wagtail.admin.edit_handlers import *
from wagtail.core.models import Page
from wagtail.core.rich_text.pages import PageLinkHandler as BasePageLinkHandler

from oscar.forms import widgets
from modelcluster.fields import ParentalKey
from wagtailmodelchooser.edit_handlers import ModelChooserPanel

class ProductChooserPanel(BaseChooserPanel):
    object_type_name = "product"

    _target_content_type = None

    def __init__(self, field_name, product_type=None):
        super().__init__(field_name)
        self.product_type = product_type

    def clone(self):
        return self.__class__(
            field_name=self.field_name,
            product_type=self.product_type,
        )

    def widget_overrides(self):
        return {
            self.field_name: widgets.AdminProductChooser()
        }


class PageLinkHandler(BasePageLinkHandler):
    """Override the default PageLinkHandler to make sure we use the url
    property of the `Category` classes.
    """

    @staticmethod
    def expand_db_attributes(attrs, for_editor):
        try:
            page = Page.objects.get(id=attrs['id']).specific
            if for_editor:
                editor_attrs = 'data-linktype="page" data-id="%d" ' % page.id
            else:
                editor_attrs = ''

            return '<a %shref="%s">' % (editor_attrs, escape(page.url))
        except Page.DoesNotExist:
            return "<a>"


class ReadOnlyPanel(EditHandler):
    def __init__(self, field_name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.field_name = field_name
        self.heading = kwargs.pop('heading', field_name.replace("_", " "))

    def clone(self):
        return self.__class__(
            field_name=self.field_name,
            heading=self.heading,
            classname=self.classname,
            help_text=self.help_text,
        )

    def field_type(self):
        return "readonly_field"

    def render(self):
        value = getattr(self.instance, self.field_name)
        if callable(value):
            value = value()
        return format_html('<div style="padding-top: 1.2em;">{}</div>', value)

    def render_as_object(self):
        return format_html(
            '<fieldset><legend>{}</legend>'
            '<ul class="fields"><li><div class="field">{}</div></li></ul>'
            '</fieldset>',
            self.heading, self.render())

    def render_as_field(self):
        return format_html(
            '<div class="field">'
            '<label>{}{}</label>'
            '<div class="field-content">{}</div>'
            '</div>',
            self.heading, _(':'), self.render())
