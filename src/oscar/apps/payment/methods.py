from decimal import Decimal as D

from django.utils.translation import gettext_lazy as _

from oscar.core import prices


class Base(object):
    """
    Payment method interface class

    This is the superclass to the classes in methods.py, and a de-facto
    superclass to the classes in models.py. This allows using all
    payment methods interchangeably (aka polymorphism).

    The interface is all properties.
    """

    #: Used to store this method in the session.  Each payment method should
    #  have a unique code.
    code = '__default__'

    #: The name of the payment method, shown to the customer during checkout
    name = 'Default payment'

    #: A more detailed description of the paymen method shown to the customer
    #  during checkout.  Can contain HTML.
    description = ''

    #: Whether the charge includes a discount
    is_discounted = False

    def calculate(self, basket, total):
        """
        Return the payment charge for the given basket
        """
        raise NotImplemented()

    def discount(self, basket):
        """
        Return the discount on the standard payment charge
        """
        # The regular payment methods don't add a default discount.
        # For offers and vouchers, the discount will be provided
        # by a wrapper that Repository.apply_payment_offer() adds.
        return D('0.00')


class NoFeePayment(Base):
    """
    This payment method specifies that the payment method incurs no fees.
    """
    code = 'no-fees'
    name = _('No fee')
    
    def calculate(self, basket, total):
        # If the charge is free then tax must be free (musn't it?) and so we
        # immediately set the tax to zero
        return prices.Price(
            currency=basket.currency,
            excl_tax=D('0.00'), tax=D('0.00'))
    

class NoPaymentRequired(NoFeePayment):
    """
    This payment method specifies that the payment method incurs no fees.
    """
    code = 'no-payment-required'
    name = _('No payment required')
    
