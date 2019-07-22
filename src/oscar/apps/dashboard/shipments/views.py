from django.contrib.admin.utils import unquote
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from oscar.core.loading import get_class, get_model
from oscar.apps.dashboard.views import CreateView, EditView


Repository = get_class('shipping.repository', 'Repository')
ShippingMethod = get_model('shipping', 'Method')


class ShippingMethodCreateView(CreateView):
    """ Creates a product for the given product class.

    """
    shipping_method = None

    def __init__(self, model_admin, shipping_method):
        super().__init__(model_admin)
        class_name = unquote(shipping_method)
        cls = model_admin.get_shipping_method(class_name)
        if cls is None:
            raise Http404("Shipping method does not exist!")
        self.model = self.shipping_method = cls

    def get_edit_handler(self):
        """ Create the form for the selected shipping method """
        edit_handler = self.model_admin.get_edit_handler(
            instance=self.get_instance(), request=self.request,
            model=self.model)
        return edit_handler.bind_to(model=self.model)

    @cached_property
    def create_url(self):
        url_name = self.url_helper.get_action_url_name('create')
        kwargs = {'shipping_method': self.model.__name__.lower()}
        return reverse(url_name, kwargs=kwargs)


class ShippingMethodEditView(EditView):

    def get_edit_handler(self):
        """ Create the form for the selected shipping method """
        instance = self.get_instance()
        edit_handler = self.model_admin.get_edit_handler(
            instance=instance, request=self.request)
        return edit_handler.bind_to(model=type(instance))
