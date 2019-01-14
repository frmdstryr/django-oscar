from django import forms
from django.db import transaction
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from django.utils.text import capfirst

from wagtail.admin import messages
from .widgets import BulkActionHiddenInput


class BulkActionsMixin:
    #: Actions that may be performed on the items selcted in the list view
    bulk_actions = []
    bulk_actions_form_class = None
    bulk_action_empty_title = _('Choose an action')

    def action_checkbox(self, obj):
        return format_html(
            '<input type="checkbox" name="selection" class="bulk-action" '
            'value="{}"/>', obj.pk)
    action_checkbox.short_description = format_html(
        '<input type="checkbox" class="bulk-action select-all"/>')

    def get_bulk_actions(self):
        """ Get a list of bulk actions that can be applied on a selected
        queryset.

        """
        return self.bulk_actions

    def get_bulk_action_name(self, action):
        return _(capfirst(action.replace("_", " ")))

    def get_bulk_actions_form_class(self, actions, queryset):
        """ Use this if you want to render a custom actions form

        """
        if self.bulk_actions_form_class:
            return self.bulk_actions_form_class

        action_choices = [('', self.bulk_action_empty_title)] + [
            (action, self.get_bulk_action_name(action))
            for action in self.get_bulk_actions()
        ]
        fields = {
            'action': forms.ChoiceField(choices=action_choices),
            'selection': forms.ModelMultipleChoiceField(
                queryset=queryset, widget=BulkActionHiddenInput())
        }
        name = '%sBulkActionsForm' % self.__class__.__name__
        BulkActionsForm = type(name, (forms.Form,), fields)
        return BulkActionsForm

    def do_bulk_action(self, request, form):
        """ Invoke the bulk action handler. It looks up handlers using the
        format `do_action_<action_name>` or `do_bulk_action_<action_name>`

        """
        action = form.cleaned_data['action']
        handler = getattr(self, 'do_bulk_action_%s' % action,
                          getattr(self, 'do_action_%s' % action, None))
        if not handler:
            messages.error(
                request, _('No handler is defined for action "%s"' % action))
            return

        # Handlers should define their own message and response if needed
        with transaction.atomic():
            return handler(request, form)

