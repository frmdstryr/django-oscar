"""
Custom panels are pulled here and should be imported from here so their
implementations can be modified or replaced as needed


"""
import functools
from django import forms
from django.db import models
from django.template.loader import render_to_string
from django.utils.html import escape, format_html, mark_safe
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from wagtail.admin import compare
from wagtail.admin.edit_handlers import *
from wagtail.core.models import Page
from wagtail.core.rich_text.pages import PageLinkHandler as BasePageLinkHandler

from oscar.forms import widgets
from modelcluster.fields import ParentalKey
from oscar.vendor.modelchooser.edit_handlers import ModelChooserPanel
from wagtailautocomplete.edit_handlers import AutocompletePanel


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
        # Used to format the value
        self.formatter = kwargs.pop('formatter', None)
        self.ignore_errors = kwargs.pop('ignore_errors', True)
        self.show_heading = kwargs.pop('show_heading', True)

        super().__init__(*args, **kwargs)
        self.field_name = field_name
        self.heading = kwargs.pop('heading', field_name.replace("_", " "))

    def clone(self):
        return self.__class__(
            field_name=self.field_name,
            heading=self.heading,
            classname=self.classname,
            help_text=self.help_text,
            formatter=self.formatter,
            show_heading=self.show_heading,
            ignore_errors=self.ignore_errors,
        )

    def field_type(self):
        return "readonly_field"

    def lookup_value(self):
        value = None
        try:
            if hasattr(self.instance, self.field_name):
                value = getattr(self.instance, self.field_name)
            elif '__' in self.field_name:
                # Lookup related fields
                value = self.instance
                for attr in self.field_name.split("__"):
                    value = getattr(value, attr)
        except:
            if not self.ignore_errors:
                raise
        return value

    def format_value(self, value):
        if self.formatter:
            try:
                value = self.formatter(self.instance, value)
            except:
                if not self.ignore_errors:
                    raise
        return value

    def render(self):
        value = self.lookup_value()
        if callable(value):
            value = value()
        value = self.format_value(value)
        return format_html('<div>{}</div>', value)

    def render_as_object(self):
        if not self.show_heading:
            return self.render()
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


class MultiFieldTablePanel(MultiFieldPanel):
    template = "oscar/dashboard/edit_handlers/multi_field_table_panel.html"

    def __init__(self, *args, **kwargs):
        self.colspan = kwargs.pop('colspan', 2)
        super().__init__(*args, **kwargs)

    def clone(self):
        panel = super().clone()
        panel.colspan = self.colspan
        return panel


class ReadOnlyMultiFieldPanel(MultiFieldPanel):

    def render_missing_fields(self):
        """ Make all missing fields hidden

        """
        rendered_fields = self.required_fields()
        for field_name in self.form.fields:
            if field_name not in rendered_fields:
                self.form.fields[field_name].widget = forms.HiddenInput()
        return super().render_missing_fields()


class InlineStackedPanel(InlinePanel):
    template = "oscar/dashboard/edit_handlers/inline_panel.html"

    # If false readonly panels are used for existing rows
    can_edit_existing = True

    #: If false no add button will be shown
    can_add_new = True

    # Custom panels for existing items
    readonly = None
    exclude = None

    # Autofill data for new rows (aka formset form kwargs)
    autofill = None

    def __init__(self, *args, **kwargs):
        self.autofill = kwargs.pop('autofill', None)
        self.exclude = kwargs.pop('exclude', None)
        self.readonly = kwargs.pop('readonly', None)
        super().__init__(*args, **kwargs)

    def clone(self):
        panel = super().clone()
        panel.autofill = self.autofill
        panel.exclude = self.exclude
        panel.readonly = self.readonly
        return panel

    def get_readonly_panel_definitions(self):
        # Look for a panels definition in the InlinePanel declaration
        if self.readonly is not None:
            return self.readonly
        # Failing that, get it from the model
        fields = fields_for_model(
            self.db_field.related_model,
            exclude=[self.db_field.field.name],# + (self.exclude or []),
            formfield_callback=formfield_for_dbfield)
        return [ReadOnlyPanel(field_name) for field_name in fields]

    def get_child_readonly_handler(self):
        panels = self.get_readonly_panel_definitions()
        child_edit_handler = ReadOnlyMultiFieldPanel(
            panels, heading=self.heading)
        return child_edit_handler.bind_to_model(self.db_field.related_model)

    def on_instance_bound(self):
        self.formset = self.form.formsets[self.relation_name]

        self.children = []
        for subform in self.formset.forms:
            # override the DELETE field to have a hidden input
            subform.fields[DELETION_FIELD_NAME].widget = forms.HiddenInput()

            # ditto for the ORDER field, if present
            if self.formset.can_order:
                subform.fields[ORDERING_FIELD_NAME].widget = forms.HiddenInput()

            if self.can_edit_existing:
                child_edit_handler = self.get_child_edit_handler()
            else:
                child_edit_handler = self.get_child_readonly_handler()
            self.children.append(
                child_edit_handler.bind_to_instance(instance=subform.instance,
                                                    form=subform,
                                                    request=self.request))

        # if this formset is valid, it may have been re-ordered; respect that
        # in case the parent form errored and we need to re-render
        if self.formset.can_order and self.formset.is_valid():
            self.children.sort(
                key=lambda child: child.form.cleaned_data[ORDERING_FIELD_NAME] or 1)

        empty_form = self.formset.empty_form
        empty_form.fields[DELETION_FIELD_NAME].widget = forms.HiddenInput()
        if self.formset.can_order:
            empty_form.fields[ORDERING_FIELD_NAME].widget = forms.HiddenInput()

        # Autofill new fields with initial data
        if self.autofill:
            initial_values = {}
            if isinstance(self.autofill, dict):
                initial_values = self.autofill
            elif callable(self.autofill):
                initial_values = self.autofill(self)
            for field_name, initial in initial_values.items():
                empty_form.fields[field_name].initial = initial


        self.empty_child = self.get_child_edit_handler()
        self.empty_child = self.empty_child.bind_to_instance(
            instance=empty_form.instance, form=empty_form, request=self.request)


class AddOnlyInlinePanel(InlineStackedPanel):
    can_edit_existing = False


class ViewOnlyInlinePanel(InlineStackedPanel):
    can_edit_existing = False
    can_add_new = False


class InlineTablePanel(InlineStackedPanel):
    template = "oscar/dashboard/edit_handlers/inline_table_panel.html"

    # List of table headings
    headings = None

    def __init__(self, *args, **kwargs):
        self.headings = kwargs.pop('headings', None)
        super().__init__(*args, **kwargs)

    def clone(self):
        panel = super().clone()
        panel.headings = self.headings
        return panel


class AddOnlyInlineTablePanel(InlineTablePanel):
    can_edit_existing = False


class ViewOnlyInlineTablePanel(InlineStackedPanel):
    can_edit_existing = False
    can_add_new = False


class ReadOnlyTablePanel(InlineTablePanel):
    def __init__(self, *args, **kwargs):
        self.exclude = kwargs.pop('exclude', [])
        super().__init__(*args, **kwargs)

    def clone(self):
        panel = super().clone()
        panel.exclude = self.exclude
        return panel

    def get_panel_definitions(self):
        if self.panels is not None:
            return self.panels
        fields = fields_for_model(
            self.db_field.related_model,
            exclude=[self.db_field.field.name]+self.exclude,
            formfield_callback=formfield_for_dbfield)
        return [ReadOnlyPanel(field_name) for field_name in fields]


class RowPanel(ObjectList):
    template = "oscar/dashboard/edit_handlers/row_panel.html"


class AddressChooserPanel(ModelChooserPanel):
    object_template = 'oscar/dashboard/edit_handlers/field_no_label.html'
    choice_template = 'oscar/dashboard/edit_handlers/address_chooser_choice.html'
