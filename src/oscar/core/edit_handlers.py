"""
Custom panels are pulled here and should be imported from here so their
implementations can be modified or replaced as needed


"""
import functools
from django import forms
from django.core.exceptions import ValidationError
from django.db import models
from django.template.loader import render_to_string
from django.utils.html import escape, format_html, mark_safe
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from wagtail.admin import compare
from wagtail.admin.edit_handlers import *
from wagtail.core.utils import camelcase_to_underscore
from wagtail.documents.edit_handlers import DocumentChooserPanel
from wagtail.images.edit_handlers import ImageChooserPanel


from oscar.forms import widgets
from oscar.vendor.modelchooser.edit_handlers import ModelChooserPanel
from modelcluster.fields import ParentalKey
from wagtailautocomplete.edit_handlers import AutocompletePanel


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
        return child_edit_handler.bind_to(model=self.db_field.related_model)

    def on_form_bound(self):
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
                child_edit_handler.bind_to(instance=subform.instance,
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
        self.empty_child = self.empty_child.bind_to(
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
        if 'template' in kwargs:
            self.template = kwargs.pop('template')
        super().__init__(*args, **kwargs)

    def clone(self):
        panel = super().clone()
        panel.headings = self.headings
        panel.template = self.template
        return panel


class AddOnlyInlineTablePanel(InlineTablePanel):
    can_edit_existing = False


class ViewOnlyInlineTablePanel(InlineStackedPanel):
    can_edit_existing = False
    can_add_new = False


class ModelListPanel(HelpPanel):
    """ A panel which simulates a dashboard index page for the given field name
    """
    template = "dashboard/edit_handlers/model_list_panel.html",

    def __init__(self, field_name, *args, **kwargs):
        self.field_name = field_name
        self.exclude = kwargs.pop('exclude', None)
        self.label = kwargs.pop('label', None)
        self.list_display = kwargs.pop('list_display', ['__str__'])
        self.sortable_by = kwargs.pop('sortable_by', None)
        if 'template' not in kwargs:
            kwargs['template'] = self.template
        super().__init__(*args, **kwargs)

    def clone_kwargs(self):
        kwargs = super().clone_kwargs()
        kwargs.update({
            'field_name': self.field_name,
            'exclude': self.exclude,
            'label': self.label,
            'template': self.template,
            'list_display': self.list_display,
            'sortable_by': self.sortable_by,
        })
        return kwargs

    @cached_property
    def db_field(self):
        try:
            model = self.model
        except AttributeError:
            raise ImproperlyConfigured(
                "%r must be bound to a model before calling db_field" % self)
        return model._meta.get_field(self.field_name)

    def render(self):
        # Clone and bind to the related field  model
        view = self.bind_to(model=self.db_field.related_model,
                            instance=self.instance)
        view.model_admin = view
        view.verbose_name_plural = self.model._meta.verbose_name_plural
        return mark_safe(render_to_string(self.template, {
            'self': view,
            'view': view,
            'request': self.request,
            'object_list': self.get_queryset()
        }))

    # ========================================================================
    # Modeladmin API
    # ========================================================================
    def get_queryset(self):
        return getattr(self.instance, self.field_name).all()[:10]

    def get_query_string(self, params):
        return ''

    def get_empty_value_display(self, field_name):
        return '-'

    def get_ordering_field_columns(self):
        return {}

    def get_extra_class_names_for_field_col(self, result, field_name):
        return []

    def get_extra_attrs_for_field_col(self, result, field_name):
        return {}

    def get_extra_attrs_for_row(self, result, context):
        return {}

    def get_buttons_for_obj(self, obj):
        return []

    def get_list_display_add_buttons(self, request):
        pass

    def get_list_display(self, request):
        return self.list_display


class CustomFieldPanel(EditHandler):
    """ Use this to add custom form fields to the form. This should be used
    in with custom form processing.

    Example
    -------
        CustomFieldPanel('benefit_range', forms.ModelChoiceField(
            label=_('Which products get a discount?'),
            queryset=get_model('offer', 'Range').objects.all(),
        )),

    """
    object_template = "wagtailadmin/edit_handlers/single_field_panel.html"
    field_template = "wagtailadmin/edit_handlers/field_panel_field.html"

    def __init__(self, field_name, form_field, *args, **kwargs):
        widget = kwargs.pop('widget', None)
        if widget is not None:
            self.widget = widget
        super().__init__(*args, **kwargs)
        self.field_name = field_name
        self.form_field = form_field

    def required_fields(self):
        """ Hack to work-around the fields being rendered as missing
        """
        if hasattr(self, 'bound_field'):
            return [self.field_name]
        return []

    def clone_kwargs(self):
        kwargs = super().clone_kwargs()
        kwargs['field_name'] = self.field_name
        kwargs['form_field'] = self.form_field
        return kwargs

    def on_form_bound(self):
        self.form.fields[self.field_name] = self.form_field
        self.bound_field = self.form[self.field_name]
        self.heading = self.bound_field.label
        self.help_text = self.bound_field.help_text

    def field_type(self):
        return camelcase_to_underscore(self.form_field.__class__.__name__)

    def render_as_object(self):
        return mark_safe(render_to_string(self.object_template, {
            'self': self,
            'field_panel': self,
            'field': self.bound_field}))

    def render_as_field(self):
        return mark_safe(render_to_string(self.field_template, {
            'field': self.bound_field,
            'field_type': self.field_type()}))


class RowPanel(ObjectList):
    template = "oscar/dashboard/edit_handlers/row_panel.html"


class AddressChooserPanel(ModelChooserPanel):
    object_template = 'oscar/dashboard/edit_handlers/field_no_label.html'
    choice_template = 'oscar/dashboard/edit_handlers/address_chooser_choice.html'


class InlineFormPanel(BaseChooserPanel):
    """ This is a mix of a ChooserPanel and InlinePanel which displays
    a form with a prefix for the inline model. It works for ForeignKeys
    and for OneToOneFields.

    """
    # Hide the label
    object_type_name = 'object'
    object_template = 'oscar/dashboard/edit_handlers/field_no_label.html'

    def __init__(self, field_name, panels=None, exclude=None, initial=None,
                 *args, **kwargs):
        if 'widget' not in kwargs:
            # Always use hidden widget
            kwargs['widget'] = forms.HiddenInput()
        super().__init__(field_name, *args, **kwargs)
        self.panels = panels
        self.exclude = exclude or []
        self.initial = initial or {}

        # Hide the choice field heading and pass it to the inline form
        self.child_heading = self.heading
        self.heading = ''

    def clone(self):
        panel = super().clone()
        panel.panels = self.panels
        panel.initial = self.initial
        panel.exclude = self.exclude
        #panel.child_heading = self.child_heading
        return panel

    @cached_property
    def related_model(self):
        return self.db_field.related_model

    def get_panel_definitions(self):
        """ Get the panels for the inline form. """
        # Look for a panels definition in the InlinePanel declaration
        if self.panels is not None:
            return self.panels
        # Failing that, get it from the model
        return extract_panel_definitions_from_model_class(
            self.related_model,
            exclude=self.exclude)

    def get_child_edit_handler(self):
        """ Get the panels for the inline form. """
        panels = self.get_panel_definitions()
        child_edit_handler = ObjectList([
            MultiFieldPanel(panels, heading='',
                            classname='inline-form')
        ])
        return child_edit_handler.bind_to(model=self.related_model)

    # =========================================================================
    # FormMixin API
    # =========================================================================
    def get_initial(self):
        """Return the initial data to use for forms on this view."""
        return self.initial.copy()

    def get_prefix(self):
        """Return the prefix to use for forms."""
        return self.field_name

    def get_instance(self):
        """ Return an instance of the form to be used in this view."""
        return self.get_chosen_item() or self.related_model()

    def get_form_class(self):
        """Return the form class to use."""
        return self.get_child_edit_handler().get_form_class()

    def get_form_kwargs(self):
        """Return the keyword arguments for instantiating the form."""
        kwargs = {
            'initial': self.get_initial(),
            'prefix': self.get_prefix(),
            'instance': self.get_instance()
        }

        if self.request.method in ('POST', 'PUT'):
            kwargs.update({
                'data': self.request.POST,
                'files': self.request.FILES,
            })
        return kwargs

    def get_form(self, form_class=None):
        """ Return an instance of the form to be used in this view."""
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(**self.get_form_kwargs())

    # =========================================================================
    # EditHandler API
    # =========================================================================

    def on_form_bound(self):
        """ When an instance is bound to this panel, bind
        the child edit handler to the related object and create a form
        using a prefix of the field_name.

        """
        super().on_form_bound()

        # Add a hook to clean and save related fields by wrapping
        # the form field's clean method with the one in this panel.
        # In order for this to work properly this panel MUST
        # be bound to the form before form.is_valid is called.
        field = self.form.fields[self.field_name]
        clean_method = functools.partial(
            self.clean, default_clean=getattr(field, 'clean'))
        setattr(field, 'clean', clean_method)

        # Bind the child edit handler to the related object
        edit_handler = self.get_child_edit_handler()
        form = self.get_form(edit_handler.get_form_class())
        self.bound_panel = edit_handler.bind_to(
            instance=form.instance, form=form, request=self.request)

    def clean(self, value, default_clean):
        """ Validate the inline form then run the default field's
        clean method.  If the form is valid save it and pass the pk
        as the value.

        """
        form = self.bound_panel.form
        if form.is_valid():
            value = form.save().pk
        return default_clean(value)

    def render_as_object(self):
        return mark_safe("".join((
            self.bound_panel.render_as_field(),
            super().render_as_object()
        )))

    def render_as_field(self):
        return mark_safe("".join((
            self.bound_panel.render_as_field(),
            super().render_as_field()
        )))


class GenericInlineFormPanel(InlineFormPanel):
    def __init__(self, field_name, content_type_field="content_type",
                 content_object_field="content_object", *args, **kwargs):
        super().__init__(field_name, *args, **kwargs)
        self.content_type_field = content_type_field
        self.content_object_field = content_object_field

    def clone(self):
        panel = super().clone()
        panel.content_type_field = self.content_type_field
        panel.content_object_field = self.content_object_field
        return panel

    def get_chosen_item(self):
        return getattr(self.instance, self.content_object_field)

    @property
    def related_model(self):
        content_type = getattr(self.instance, self.content_type_field)
        return content_type.model_class()


class ModelFormPanel(ObjectList):
    initial = {}
    prefix = None

    def __init__(self, children, initial=None, prefix=None, *args, **kwargs):
        super().__init__(children, *args, **kwargs)
        if initial is not None:
            self.initial = initial
        if prefix is not None:
            self.prefix = prefix

    def clone_kwargs(self):
        kwargs = super().clone_kwargs()
        kwargs['initial'] = self.initial
        kwargs['prefix'] = self.prefix
        return kwargs

    def clone(self, **kwargs):
        """ Shortcut to bind parameters easier

        """
        new = super().clone()
        for k, v in kwargs.items():
            setattr(new, k, v)
        return new

    def get_initial(self):
        """Return the initial data to use for forms on this view."""
        return self.initial.copy()

    def get_prefix(self):
        """Return the prefix to use for forms."""
        return self.prefix

    def get_form_kwargs(self):
        """Return the keyword arguments for instantiating the form."""
        kwargs = {
            'initial': self.get_initial(),
            'prefix': self.get_prefix(),
        }

        if self.request and self.request.method in ('POST', 'PUT'):
            kwargs.update({
                'data': self.request.POST,
                'files': self.request.FILES,
            })

        if self.instance is not None:
            kwargs.update({'instance': self.instance})

        return kwargs

    def get_form(self):
        Form = self.get_form_class()
        return Form(**self.get_form_kwargs())
