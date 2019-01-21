from django.shortcuts import redirect
from wagtail.admin import messages
from wagtail.contrib.modeladmin.views import ModelFormView
from oscar.apps.dashboard.views import DetailView


class OrderDetailsView(ModelFormView, DetailView):
    def form_valid(self, form):
        instance = form.save()
        messages.success(
            self.request, self.get_success_message(instance),
            buttons=self.get_success_message_buttons(instance)
        )
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        messages.validation_error(
            self.request, self.get_error_message(), form
        )
        return self.render_to_response(self.get_context_data())
