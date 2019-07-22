from django.db import transaction
from django.shortcuts import redirect
from django.utils.translation import ugettext as _
from django.views.generic import FormView

from oscar.apps.dashboard.views import DetailView
from oscar.core.loading import get_model
from oscar.core.edit_handlers import ModelFormPanel, FieldPanel

from wagtail.admin import messages


OrderNote = get_model('order', 'OrderNote')


class OrderDetailsView(DetailView):

    order_note_handler = ModelFormPanel([
        FieldPanel('message'),
        #FieldPanel('notify_by_email'), # TODO: Support this
        FieldPanel('visible_on_frontend'),
    ], prefix='order_note')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if 'order_forms' not in ctx:
            ctx['order_forms'] = self.get_order_forms()
        return ctx

    def get_order_forms(self):
        order = self.instance
        edit_handler = self.order_note_handler.bind_to(
                instance=OrderNote(user=self.request.user, order=order),
                request=self.request)
        return {
            'note_form': edit_handler.get_form(),
        }

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        for form_name, form in self.get_order_forms().items():
            if not form.has_changed():
                continue
            if form.is_valid():
                return self.form_valid(form, form_name)
            else:
                return self.form_invalid(form, form_name)
        messages.error(self.request, 'No action was given')
        return self.render_to_response(self.get_context_data())

    def get_success_message(self, form, form_name, instance=None):
        if isinstance(instance, OrderNote):
            return _('Note added')
        return _('Action completed')

    def get_error_message(self, form):
        return _("The action could not be completed due to errors.")

    def process_form(self, form, form_anme):
        """ Subclasses should override this to process custom forms """
        raise NotImplementedError()

    def form_valid(self, form, form_name):
        if hasattr(form, 'save'):
            instance = form.save()
            message = self.get_success_message(form, form_name, instance)
        else:
            handler = getattr(
                self, 'process_%s' % form_name, self.process_form)
            message = handler(form)
        messages.success(self.request, message)
        return redirect(self.request.path)

    def form_invalid(self, form, form_name):
        message = self.get_error_message(form)
        messages.validation_error(self.request, message, form)
        return self.render_to_response(self.get_context_data())
