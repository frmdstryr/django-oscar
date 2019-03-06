from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.db.models.query import EmptyQuerySet
from django.shortcuts import reverse
from django.template.loader import render_to_string
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from wagtail.admin.edit_handlers import BaseChooserPanel, get_form_for_model
from django.contrib.contenttypes.fields import GenericForeignKey


from .widgets import AdminModelChooser
from . import registry, ModelChooserMixin


class ModelChooserPanel(BaseChooserPanel, ModelChooserMixin):
    # Model this panel will be bound to
    model = None
    request = None

    # Field of the model this panel is for
    field_name = None
    generic_name = None
    content_type = None  # This is set by the chooser view

    # Links to add a new item or edit the current item
    # the edit url may be callable to generate a url based on the current object
    show_add_link = False
    show_edit_link = False
    link_to_add_url = None
    link_to_edit_url = None

    icon = 'placeholder'
    header_icon = None

    def __init__(self, field_name, search_fields=None,
                 show_add_link=None, show_edit_link=None,
                 link_to_add_url=None, link_to_edit_url=None,
                 show_label=None, default_filters=None, generic_name=None,
                 display_fields=None, **kwargs):
        super().__init__(field_name, **kwargs)
        if search_fields is not None:
            self.search_fields = search_fields
        if default_filters is not None:
            self.default_filters = default_filters
        if display_fields is not None:
            self.display_fields = display_fields
        if show_add_link is not None:
            self.show_add_link = show_add_link
        if show_edit_link is not None:
            self.show_edit_link = show_edit_link
        if link_to_add_url is not None:
            self.link_to_add_url = link_to_add_url
        if link_to_edit_url is not None:
            self.link_to_edit_url = link_to_edit_url
        if generic_name is not None:
            self.generic_name = generic_name

    # ========================================================================
    # Panel API
    # ========================================================================
    def clone(self):
        panel = self.__class__(
            field_name=self.field_name,
            generic_name=self.generic_name,
            widget=self.widget if hasattr(self, 'widget') else None,
            heading=self.heading,
            classname=self.classname,
            help_text=self.help_text,
            search_fields=self.search_fields,
            show_add_link=self.show_add_link,
            show_edit_link=self.show_edit_link,
            link_to_add_url=self.link_to_add_url,
            link_to_edit_url=self.link_to_edit_url,
            default_filters=self.default_filters,
            display_fields=self.display_fields,
        )
        panel.content_type = self.content_type
        return panel

    def on_form_bound(self):
        """ Use the registry as a temporary cache to hold the chooser
        with it's instance. This works since the panel is cloned each
        time it's bound to an instance.

        """
        super().on_form_bound()
        db_field = self.db_field

        field = self.form.fields[self.field_name]
        widget = field.widget

        if self.chooser_template:
            widget.chooser_template = self.chooser_template
        if self.choice_template:
            widget.choice_template = self.choice_template

        chooser_id = self.get_chooser_id()
        if not chooser_id:
            raise ImproperlyConfigured(
                "get_chooser_id must return a unique value")

        if chooser_id not in registry.choosers:
            registry.choosers[chooser_id] = self

        # Create data that can be used by the chooser view
        ctx = self.get_chooser_context()
        ctx['chooser_id'] = chooser_id
        widget.chooser_ctx = ctx

        # If it's a generic foreign key set the id of the content_type field
        if self.is_generic:
            ct_id = self.form[self.db_field.ct_field].id_for_label
            widget.content_type_field_id = ct_id

    def required_fields(self):
        if self.is_generic:
            db_field = self.db_field
            return [db_field.ct_field, db_field.fk_field]
        return super().required_fields()

    def widget_overrides(self):
        return {self.field_name: AdminModelChooser(
            model=self.target_model,
            display_fields=self.display_fields,
            link_to_add_url=self.get_link_to_add_url(),
            link_to_edit_url=self.get_link_to_edit_url(),
            show_add_link=self.show_add_link,
            show_edit_link=self.show_edit_link)}

    @cached_property
    def db_field(self):
        """ If a generic foreign key is given use that as the field

        """
        try:
            model = self.model
        except AttributeError:
            raise ImproperlyConfigured(
                "%r must be bound to a model before calling db_field" % self)

        return model._meta.get_field(self.generic_name or self.field_name)

    @cached_property
    def is_generic(self):
        return isinstance(self.db_field, GenericForeignKey)

    @cached_property
    def target_model(self):
        db_field = self.db_field
        if self.is_generic:
            if self.content_type:
                return self.content_type.model_class()
            return None
        return db_field.remote_field.model

    def render_as_field(self):
        instance_obj = self.get_chosen_item()
        return mark_safe(render_to_string(self.field_template, {
            'field': self.bound_field,
            'instance': instance_obj,
        }))

    # ========================================================================
    # Chooser API
    # ========================================================================
    def get_chooser_id(self):
        """ Generate a key to use to store this chooser in the registry such
        that it is repeatable (if scaling to multiple processes) and is unique
        per panel within the application.
        """
        if self.chooser_id:
            return self.chooser_id
        cls = self.__class__
        opts = self.model._meta
        return '.'.join((
            cls.__module__, cls.__name__, opts.app_label, opts.model_name,
            self.field_name))

    def get_chooser_context(self):
        """ Generate data that can be used by the chooser view to
        re-populate the original panel information on the other side of the
        request. This is used so the view can lookup the exact object and
        field that this panel uses.

        """
        return {
            'field_name': self.field_name,
            'generic_name': self.generic_name,
            'instance_pk': self.instance.pk,
            'app_label': self.model._meta.app_label,
            'model_name': self.model._meta.model_name,
        }

    def get_link_to_add_url(self):
        if self.link_to_add_url:
            return self.link_to_add_url
        target_model = self.target_model
        if not target_model:
            return '#'
        url_name = '{opts.app_label}_{opts.model_name}_modeladmin_create'
        return url_name.format(opts=target_model._meta)

    def get_link_to_edit_url(self):
        if self.link_to_edit_url:
            return self.link_to_edit_url
        target_model = self.target_model
        if not target_model:
            return '#'
        url_name = '{opts.app_label}_{opts.model_name}_modeladmin_edit'
        return url_name.format(opts=target_model._meta)

    # ========================================================================
    # Chooser queryset
    # ========================================================================
    def get_instance(self, request, panel_data):
        """ Get the original instance for the chooser or create an empty
        model if no pk is given.

        """
        pk = panel_data['instance_pk']
        if pk is not None:
            return self.model._default_manager.get(pk=pk)
        return self.model()

    def get_form_class(self):
        """ This is used by the chooser view to recreate the panel
        """
        return get_form_for_model(self.model,
                                  fields=self.required_fields(),
                                  widgets=self.widget_overrides())
