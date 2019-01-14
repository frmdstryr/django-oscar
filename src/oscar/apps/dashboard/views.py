from django import forms
from django.shortcuts import redirect
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import FormView

from wagtail.admin import messages
from wagtail.contrib.modeladmin.views import IndexView, InspectView


class ListView(IndexView, FormView):
    """ Add actions and allow related lookups

    """
    bulk_actions = []

    # Don't use action as lookup params
    IGNORED_PARAMS = IndexView.IGNORED_PARAMS + ('action', 'selection')

    def __init__(self, model_admin):
        super().__init__(model_admin)
        self.bulk_actions = model_admin.get_bulk_actions()

    def get_success_url(self):
        return self.index_url

    def get_form_class(self):
        return self.model_admin.get_bulk_actions_form_class(
            self.bulk_actions, self.queryset)

    def get_context_data(self, **kwargs):
        context = {
            'has_bulk_actions': bool(self.bulk_actions),
        }
        context.update(kwargs)
        return super().get_context_data(**context)

    def form_valid(self, form):
        result = self.model_admin.do_bulk_action(self.request, form)
        if result:
            return result
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        if not form.cleaned_data.get('action'):
            messages.error(self.request, _('No action was selected.'))
        if not form.cleaned_data.get('selection'):
            messages.error(self.request, _('No items were selected.'))
        context = self.get_context_data(form=form)
        return self.render_to_response(context)


class DetailView(InspectView):
    """ Changes "Inspect" to "View"

    """
    page_title = _('Viewing')

    def get_meta_title(self):
        return _('Viewing %s') % self.verbose_name
