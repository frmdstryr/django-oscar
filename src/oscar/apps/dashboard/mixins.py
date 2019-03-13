from django import forms
from django.db import transaction
from django.http import Http404
from django.utils.functional import cached_property
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from django.utils.text import capfirst, Truncator

from wagtail.admin import messages
from wagtail.admin.edit_handlers import ObjectList, FieldPanel
from wagtail.admin.modal_workflow import render_modal_workflow

from .widgets import BulkActionHiddenInput


class BulkActionsMixin:
    #: Actions that may be performed on the items selected in the list view
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


class InlineEditableMixin:
    #: Columns can be edited from the list view
    inline_editable = []

    #: Template used to render the inline edit modal
    inline_editable_template = 'dashboard/partials/modal_editor.html'

    def get_inline_editable(self):
        """ Get a list of field that can be edited inline

        """
        return self.inline_editable

    @cached_property
    def inline_editable_fields(self):
        return self.get_inline_editable()

    def get_inline_editable_form(self, request, instance, fields):
        """ Get the form for the given field
        """
        # TODO: Does this need validated?
        panels = [FieldPanel(f) for f in fields]
        handler = ObjectList(panels).bind_to(instance=instance)
        Form = handler.get_form_class()
        if request.method == 'POST':
            return Form(request.POST, instance=instance)
        return Form(instance=instance)

    def inline_view(self, request, instance_pk):
        """ Render a modal for editing a field of a model

        """
        Model = self.model
        try:
            instance = self.get_queryset(request).get(pk=instance_pk)
        except Model.DoesNotExist:
            raise Http404("{} does not exist")
        fields = request.GET.getlist('fields')
        if not fields:
            raise Http404(f'Fields param {fields} is missing')

        form = self.get_inline_editable_form(request, instance, fields)
        if request.method == 'POST' and form.is_valid():
            form.save()
            html = f'{form.cleaned_data[fields[0]]}'
            data = {'step': 'done', 'update': {'html': html}}
            return render_modal_workflow(request, None, None, None, data)

        fields = ", ".join([f.replace("_", " ") for f in fields])
        name = Truncator(str(instance)).chars(80)
        title = _(f'Edit {fields} of {name}')
        template = self.inline_editable_template
        return render_modal_workflow(request, template, None, {
                'form': form, 'request': request, 'title': title}, {
                    'step': 'edit'})
