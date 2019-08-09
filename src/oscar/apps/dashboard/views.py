from django import forms
from django.db import transaction
from django.http import Http404
from django.shortcuts import redirect
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import FormView

from wagtail.admin import messages
from wagtail.admin.modal_workflow import render_modal_workflow
from wagtail.contrib.modeladmin.views import (
    IndexView as BaseIndexView,
    InspectView,
    EditView as BaseEditView,
    CreateView as BaseCreateView
)


class IndexView(BaseIndexView, FormView):
    """ Add actions and allow related lookups

    """
    bulk_actions = []
    inline_editable = []

    # Don't use action as lookup params
    IGNORED_PARAMS = BaseIndexView.IGNORED_PARAMS + ('action', 'selection')

    def __init__(self, model_admin):
        super().__init__(model_admin)

        # Support BulkActions
        self.bulk_actions = model_admin.get_bulk_actions()

        # Support InlineEditable
        self.inline_editable = model_admin.get_inline_editable()

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
    def get_page_title(self):
        return _('%s') % (self.verbose_name,)

    def get_meta_title(self):
        return _('%s %s') % (self.verbose_name, self.instance)


class BoundFormMixin:
    """ The bound form lets edit handlers customize the form
    on a per instance basis so the InlineFormPanel works.
    """

    def get_bound_form(self):
        edit_handler = self.get_edit_handler().bind_to(
            instance=self.get_instance(),
            form=self.get_form(),
            request=self.request)
        return edit_handler.form


class CreateView(BaseCreateView, BoundFormMixin):

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        form = self.get_bound_form()
        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)


class EditView(BaseEditView, BoundFormMixin):

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        form = self.get_bound_form()
        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)
