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
        #FieldPanel('note_type'),
        FieldPanel('message')
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
                return self.form_valid(form)
            else:
                return self.form_invalid(form)
        messages.error(self.request, 'No action was given')
        return self.render_to_response(self.get_context_data())

    def form_valid(self, form):
        instance = form.save()
        messages.success(self.request, _('Action completed'))
        return redirect(self.index_url)

    def form_invalid(self, form):
        messages.validation_error(
            self.request,
            _("The action could not be completed due to errors."), form
        )
        return self.render_to_response(self.get_context_data())
