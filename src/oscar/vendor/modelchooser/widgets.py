import json
from django.core import signing
from django.core.exceptions import ImproperlyConfigured
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from wagtail.admin.widgets import AdminChooser


class AdminModelChooser(AdminChooser):
    chooser_ctx = None
    choice_template = "wagtailmodelchooser/choice.html"
    chooser_template = "wagtailmodelchooser/model_chooser.html"
    target_model = None  # May be none when using generic models

    # ID of the content_type_field
    content_type_field_id = ''

    def __init__(self, model, **kwargs):
        self.target_model = model
        name = 'a value'
        if self.target_model:
            name = self.target_model._meta.verbose_name
        self.chooser_ctx = kwargs.pop('ctx', None)
        self.choose_one_text = _('Choose %s') % name
        self.choose_another_text = _('Choose another')
        self.link_to_chosen_text = kwargs.pop('link_to_chosen_text', _('Edit'))
        self.link_to_add_text = kwargs.pop('link_to_add_text ', _('Add'))
        self.link_to_edit_url = kwargs.pop('link_to_edit_url', '#')
        self.link_to_add_url = kwargs.pop('link_to_add_url', '#')
        self.show_edit_link = kwargs.get('show_edit_link', False)
        self.show_add_link = kwargs.pop('show_add_link', False)
        self.display_fields = kwargs.pop('display_fields', [])
        super(AdminModelChooser, self).__init__(**kwargs)

    def render_html(self, name, value, attrs):
        instance = None
        if self.target_model:
            instance, value = self.get_instance_and_id(
                self.target_model, value)
        original_field_html = super(AdminModelChooser, self).render_html(
            name, value, attrs)

        if not self.chooser_ctx:
            raise ImproperlyConfigured(
                "The chooser context data was not set before rendering")
        generic_name = self.chooser_ctx.get('generic_name', None)
        if generic_name and not self.content_type_field_id:
            raise ImproperlyConfigured(
                "A generic name was given without a content_type_field_id")
        return render_to_string(self.chooser_template, {
            'widget': self,
            'model_opts': self.target_model._meta if self.target_model else None,
            'original_field_html': original_field_html,
            'attrs': attrs,
            'value': value,
            'item': instance,
            'chooser_url': self.get_chooser_url(),
            'add_url': self.get_add_url(instance, value),
            'edit_url': self.get_edit_url(instance, value)
        })

    def get_chooser_url(self):
        # Use signed data so we can pass data back about which exact object
        # is doing the query
        signed_data = signing.dumps(self.chooser_ctx, compress=True)
        return reverse('model_chooser', args=(signed_data,))

    def get_add_url(self, instance, value):
        # The edit url may change based on what is being edited. Editing may
        # be done on a related model
        if not self.show_add_link:
            return '#'
        if callable(self.link_to_add_url):
            return self.link_to_add_url(instance, value)
        return reverse(self.link_to_add_url)

    def get_edit_url(self, instance, value):
        # The edit url may change based on what is being edited. Editing may
        # be done on a related model
        if not self.show_edit_link:
            return '#'
        if callable(self.link_to_edit_url):
            return self.link_to_edit_url(instance, value)
        return reverse(self.link_to_edit_url, args=(value,))

    class Media:
        js = [
            'oscar/vendor/modelchooser/model-chooser.js'
        ]
