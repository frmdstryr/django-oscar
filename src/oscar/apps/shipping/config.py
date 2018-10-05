from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


STRIPE_API_KEY = "sk_test_4eC39HqLyjWDarjtT1zdp7dc"


class ShippingConfig(AppConfig):
    label = 'shipping'
    name = 'oscar.apps.shipping'
    verbose_name = _('Shipping')
