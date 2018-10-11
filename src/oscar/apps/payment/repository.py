from decimal import Decimal as D

from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _

from oscar.core.loading import get_class


NoFeePayment = get_class('payment.methods', 'NoFeePayment')
NoPaymentRequired = get_class('payment.methods', 'NoPaymentRequired')


class Repository(object):
    """
    Repository class responsible for returning PaymentMethod
    objects for a given user, basket, shipping, etc
    """

    # We default to just free shipping. Customise this class and override this
    # property to add your own shipping methods. This should be a list of
    # instantiated shipping methods.
    methods = (NoFeePayment(),)

    # API

    def get_payment_methods(self, basket, order_total, **kwargs):
        """
        Return a list of all applicable payment methods instances for a given
        basket, address etc.
        """
        if order_total.incl_tax is not None and order_total.incl_tax <= D('0'):
            # Special case! Baskets that don't require a payment get a special
            # payment method.
            return [NoPaymentRequired()]
        methods = self.get_available_payment_methods(
            basket=basket, order_total=order_total, **kwargs)
        return methods

    def get_default_payment_method(self, basket, order_total, **kwargs):
        """
        Return a 'default' payment method to show on the basket page to give
        the customer an indication of what their order will cost.
        """
        payment_methods = self.get_payment_methods(
            basket, order_total, **kwargs)
        if len(payment_methods) == 0:
            raise ImproperlyConfigured(
                _("You need to define some payment methods"))

        # Assume first returned method is default
        return payment_methods[0]

    # Helpers

    def get_available_payment_methods(self, basket, order_total, **kwargs):
        """
        Return a list of all applicable payment method instances for a given
        basket, address etc. This method is intended to be overridden.
        """
        return self.methods
