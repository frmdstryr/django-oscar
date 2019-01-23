import operator
from functools import reduce
from django.core import signing
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.shortcuts import reverse
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from wagtail.admin.edit_handlers import BaseChooserPanel, get_form_for_model
from django.contrib.admin.utils import lookup_needs_distinct

from .widgets import AdminModelChooser
from . import registry


class ModelChooserPanel(BaseChooserPanel):
    # Model this panel will be bound to
    model = None

    # Field of the model this panel is for
    field_name = None

    # Links to add a new item or edit the current item
    # the edit url may be callable to generate a url based on the current object
    show_add_link = False
    show_edit_link = False
    link_to_add_url = None
    link_to_edit_url = None

    icon = 'placeholder'
    header_icon = None

    # Change the modal chooser template
    chooser_template = None
    modal_template = 'wagtailmodelchooser/modal.html'
    results_template = 'wagtailmodelchooser/results.html'

    # Use this to change how each choice in the result list and the selected
    # value is displayed
    choice_template = 'wagtailmodelchooser/choice.html'

    # Key used to store this chooser in the registry
    chooser_id = None

    # Fields to search
    search_fields = []

    def __init__(self, field_name, search_fields=None,
                 show_add_link=None, show_edit_link=None,
                 link_to_add_url=None, link_to_edit_url=None,
                 show_label=None, **kwargs):
        super().__init__(field_name, **kwargs)
        if search_fields is not None:
            self.search_fields = search_fields
        if show_add_link is not None:
            self.show_add_link = show_add_link
        if show_edit_link is not None:
            self.show_edit_link = show_edit_link
        if link_to_add_url is not None:
            self.link_to_add_url = link_to_add_url
        if link_to_edit_url is not None:
            self.link_to_edit_url = link_to_edit_url

    # ========================================================================
    # Panel API
    # ========================================================================

    def clone(self):
        return self.__class__(
            field_name=self.field_name,
            widget=self.widget if hasattr(self, 'widget') else None,
            heading=self.heading,
            classname=self.classname,
            help_text=self.help_text,
            search_fields=self.search_fields,
            show_add_link=self.show_add_link,
            show_edit_link=self.show_edit_link,
            link_to_add_url=self.link_to_add_url,
            link_to_edit_url=self.link_to_edit_url,
        )

    def on_instance_bound(self):
        """ Use the registry as a temporary cache to hold the chooser
        with it's instance. This works since the panel is cloned each
        time it's bound to an instance.

        """
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
        widget.signed_data = signing.dumps(ctx, compress=True)

        super().on_instance_bound()

    def widget_overrides(self):
        return {self.field_name: AdminModelChooser(
            model=self.target_model,
            link_to_add_url=self.get_link_to_add_url(),
            link_to_edit_url=self.get_link_to_edit_url(),
            show_add_link=self.show_add_link,
            show_edit_link=self.show_edit_link)}

    @property
    def target_model(self):
        return self.model._meta.get_field(self.field_name).remote_field.model

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
            'instance_pk': self.instance.pk,
            'app_label': self.model._meta.app_label,
            'model_name': self.model._meta.model_name,
        }

    def get_link_to_add_url(self):
        if self.link_to_add_url:
            return self.link_to_add_url
        opts = self.target_model._meta
        url_name = '{opts.app_label}_{opts.model_name}_modeladmin_create'
        return url_name.format(opts=opts)

    def get_link_to_edit_url(self):
        if self.link_to_edit_url:
            return self.link_to_edit_url
        opts = self.target_model._meta
        url_name = '{opts.app_label}_{opts.model_name}_modeladmin_edit'
        return url_name.format(opts=opts)

    # ========================================================================
    # Chooser queryset
    # ========================================================================
    def get_queryset(self, request):
        """ Get the queryset for the chooser. Override this as necessary.

        `model` is the  original model this panel was bound to and
        `target_model` is the model of the field being chosen.

        """
        return self.target_model._default_manager.all()

    def get_search_results(self, request, queryset, search_term):
        """ This is pulled from the modeladmin IndexView
        """
        use_distinct = False
        opts = self.target_model._meta
        if self.search_fields and search_term:
            orm_lookups = ['%s__icontains' % str(search_field)
                           for search_field in self.search_fields]
            for bit in search_term.split():
                or_queries = [models.Q(**{orm_lookup: bit})
                              for orm_lookup in orm_lookups]
                queryset = queryset.filter(reduce(operator.or_, or_queries))
            if not use_distinct:
                for search_spec in orm_lookups:
                    if lookup_needs_distinct(opts, search_spec):
                        use_distinct = True
                        break

        return queryset, use_distinct

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

