from django.contrib.admin.utils import unquote
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from oscar.core.loading import get_model
from wagtail.contrib.modeladmin.views import CreateView, EditView


Product = get_model('catalogue', 'Product')
ProductClass = get_model('catalogue', 'ProductClass')


class ProductCreateView(CreateView):
    """ Creates a product for the given product class.

    """
    product_class = None

    def __init__(self, model_admin, product_class):
        super().__init__(model_admin)
        product_slug = unquote(product_class)
        self.product_class = get_object_or_404(ProductClass, slug=product_slug)

    def get_instance(self):
        """ Make sure the product_class is always set as it's needed
        to generate the attributes form.
        """
        instance = super().get_instance()
        if instance.product_class is None:
            instance.product_class = self.product_class
        return instance

    @cached_property
    def create_url(self):
        url_name = self.url_helper.get_action_url_name('create')
        kwargs = {'product_class': self.product_class.slug}
        return reverse(url_name, kwargs=kwargs)
