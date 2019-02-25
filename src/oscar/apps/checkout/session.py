from decimal import Decimal as D

from django import http
from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from oscar.core import prices
from oscar.core.loading import get_class, get_model

from . import exceptions

ShippingRepository = get_class('shipping.repository', 'Repository')
PaymentRepository = get_class('payment.repository', 'Repository')

OrderTotalCalculator = get_class(
    'checkout.calculators', 'OrderTotalCalculator')

Country = get_model('address', 'Country')
Basket = get_model('basket', 'Basket')
BillingAddress = get_model('order', 'BillingAddress')
ShippingAddress = get_model('order', 'ShippingAddress')
UserAddress = get_model('address', 'UserAddress')


class CheckoutSessionData(object):
    """
    Responsible for marshalling all the checkout session data

    Multi-stage checkouts often require several forms to be submitted and their
    data persisted until the final order is placed. This class helps store and
    organise checkout form data until it is required to write out the final
    order.
    """
    SESSION_KEY = 'checkout_data'

    def __init__(self, request):
        self.request = request
        if self.SESSION_KEY not in self.request.session:
            self.request.session[self.SESSION_KEY] = {}

    def _check_namespace(self, namespace):
        """
        Ensure a namespace within the session dict is initialised
        """
        if namespace not in self.request.session[self.SESSION_KEY]:
            self.request.session[self.SESSION_KEY][namespace] = {}

    def _get(self, namespace, key, default=None):
        """
        Return a value from within a namespace
        """
        self._check_namespace(namespace)
        if key in self.request.session[self.SESSION_KEY][namespace]:
            return self.request.session[self.SESSION_KEY][namespace][key]
        return default

    def _set(self, namespace, key, value):
        """
        Set a namespaced value
        """
        self._check_namespace(namespace)
        self.request.session[self.SESSION_KEY][namespace][key] = value
        self.request.session.modified = True

    def _unset(self, namespace, key):
        """
        Remove a namespaced value
        """
        self._check_namespace(namespace)
        if key in self.request.session[self.SESSION_KEY][namespace]:
            del self.request.session[self.SESSION_KEY][namespace][key]
            self.request.session.modified = True

    def _flush_namespace(self, namespace):
        """
        Flush a namespace
        """
        self.request.session[self.SESSION_KEY][namespace] = {}
        self.request.session.modified = True

    def flush(self):
        """
        Flush all session data
        """
        self.request.session[self.SESSION_KEY] = {}

    # Guest checkout
    # ==============

    def set_guest_email(self, email):
        self._set('guest', 'email', email)

    def get_guest_email(self):
        return self._get('guest', 'email')

    # Shipping address
    # ================
    # Options:
    # 1. No shipping required (eg digital products)
    # 2. Ship to new address (entered in a form)
    # 3. Ship to an address book address (address chosen from list)

    def reset_shipping_data(self):
        self._flush_namespace('shipping')

    def ship_to_user_address(self, address):
        """
        Use an user address (from an address book) as the shipping address.
        """
        self.reset_shipping_data()
        self._set('shipping', 'user_address_id', address.id)

    def ship_to_new_address(self, address_fields):
        """
        Use a manually entered address as the shipping address
        """
        self._unset('shipping', 'new_address_fields')
        phone_number = address_fields.get('phone_number')
        if phone_number:
            # Phone number is stored as a PhoneNumber instance. As we store
            # strings in the session, we need to serialize it.
            address_fields = address_fields.copy()
            address_fields['phone_number'] = phone_number.as_international
        country = address_fields.get('country')
        if country:
            address_fields = address_fields.copy()
            address_fields['country'] = country.code
        self._set('shipping', 'new_address_fields', address_fields)

    def new_shipping_address_fields(self):
        """
        Return shipping address fields
        """
        addr_data = self._get('shipping', 'new_address_fields')
        if addr_data:
            country = addr_data.pop('country', None)
            if country:
                addr_data = addr_data.copy()
                try:
                    addr_data['country'] = Country.objects.get(
                        iso_3166_1_a2=country)
                except Country.DoesNotExist:
                    pass
        return addr_data

    def shipping_user_address_id(self):
        """
        Return user address id
        """
        return self._get('shipping', 'user_address_id')

    # Legacy accessor
    user_address_id = shipping_user_address_id

    def is_shipping_address_set(self):
        """
        Test whether a shipping address has been stored in the session.

        This can be from a new address or re-using an existing address.
        """
        new_fields = self.new_shipping_address_fields()
        has_new_address = new_fields is not None
        user_address_id = self.shipping_user_address_id()
        has_old_address = user_address_id is not None and user_address_id > 0
        return has_new_address or has_old_address

    # Shipping method
    # ===============

    def use_free_shipping(self):
        """
        Set "free shipping" code to session
        """
        self._set('shipping', 'method_code', '__free__')

    def use_shipping_method(self, code):
        """
        Set shipping method code to session
        """
        self._set('shipping', 'method_code', code)

    def shipping_method_code(self, basket):
        """
        Return the shipping method code
        """
        return self._get('shipping', 'method_code')

    def is_shipping_method_set(self, basket):
        """
        Test if a valid shipping method is stored in the session
        """
        return self.shipping_method_code(basket) is not None

    # Billing address fields
    # ======================
    #
    # There are 3 common options:
    # 1. Billing address is entered manually through a form
    # 2. Billing address is selected from address book
    # 3. Billing address is the same as the shipping address

    def bill_to_new_address(self, address_fields):
        """
        Store address fields for a billing address.
        """
        self._unset('billing', 'new_address_fields')
        phone_number = address_fields.get('phone_number')
        if phone_number:
            # Phone number is stored as a PhoneNumber instance. As we store
            # strings in the session, we need to serialize it.
            address_fields = address_fields.copy()
            address_fields['phone_number'] = phone_number.as_international
        country = address_fields.get('country')
        if country:
            address_fields = address_fields.copy()
            address_fields['country'] = country.code
        self._set('billing', 'new_address_fields', address_fields)

    def bill_to_user_address(self, address):
        """
        Set an address from a user's address book as the billing address

        :address: The address object
        """
        self._flush_namespace('billing')
        self._set('billing', 'user_address_id', address.id)

    def bill_to_shipping_address(self):
        """
        Record fact that the billing address is to be the same as
        the shipping address.
        """
        self._flush_namespace('billing')
        self._set('billing', 'billing_address_same_as_shipping', True)

    # Legacy method name
    billing_address_same_as_shipping = bill_to_shipping_address

    def is_billing_address_same_as_shipping(self):
        return self._get('billing', 'billing_address_same_as_shipping', False)

    def billing_user_address_id(self):
        """
        Return the ID of the user address being used for billing
        """
        return self._get('billing', 'user_address_id')

    def new_billing_address_fields(self):
        """
        Return fields for a billing address
        """
        addr_data = self._get('billing', 'new_address_fields')

        if addr_data:
            country = addr_data.pop('country', None)
            if country:
                addr_data = addr_data.copy()
                try:
                    addr_data['country'] = Country.objects.get(
                        iso_3166_1_a2=country or 'US')
                except Country.DoesNotExist:
                    pass
        return addr_data

    def is_billing_address_set(self):
        """
        Test whether a billing address has been stored in the session.

        This can be from a new address or re-using an existing address.
        """
        if self.is_billing_address_same_as_shipping():
            return True
        new_fields = self.new_billing_address_fields()
        has_new_address = new_fields is not None
        user_address_id = self.billing_user_address_id()
        has_old_address = user_address_id is not None and user_address_id > 0
        return has_new_address or has_old_address

    # Payment methods
    # ===============

    def pay_by(self, method):
        self._set('payment', 'method', method)

    def payment_method(self):
        return self._get('payment', 'method')

    def set_payment_data(self, data):
        self._set('payment', 'data', data)

    def get_payment_data(self):
        return self._get('payment', 'data')

    # Submission methods
    # ==================

    def set_order_number(self, order_number):
        self._set('submission', 'order_number', order_number)

    def get_order_number(self):
        return self._get('submission', 'order_number')

    def set_submitted_basket(self, basket):
        self._set('submission', 'basket_id', basket.id)

    def get_submitted_basket(self):
        basket_id = self._get('submission', 'basket_id')
        if basket_id is None:
            return None
        try:
            return Basket._default_manager.get(pk=basket_id)
        except Basket.DoesNotExist:
            return None  # Should never happen


class CheckoutSessionMixin(object):
    """
    Mixin to provide common functionality shared between checkout views.

    All checkout views subclass this mixin. It ensures that all relevant
    checkout information is available in the template context.
    """

    # A pre-condition is a condition that MUST be met in order for a view
    # to be available. If it isn't then the customer should be redirected
    # to a view *earlier* in the chain.
    # pre_conditions is a list of method names that get executed before the
    # normal flow of the view. Each method should check some condition has been
    # met. If not, then an exception is raised that indicates the URL the
    # customer will be redirected to.

    pre_conditions = None

    # A *skip* condition is a condition that MUST NOT be met in order for a
    # view to be available. If the condition is met, this means the view MUST
    # be skipped and the customer should be redirected to a view *later* in
    # the chain.
    # Skip conditions work similar to pre-conditions, and get evaluated after
    # pre-conditions have been evaluated.
    skip_conditions = None

    def dispatch(self, request, *args, **kwargs):
        # Assign the checkout session manager so it's available in all checkout
        # views.
        self.checkout_session = CheckoutSessionData(request)

        # Enforce any pre-conditions for the view.
        try:
            self.check_pre_conditions(request)
        except exceptions.FailedPreCondition as e:
            for message in e.messages:
                messages.warning(request, message)
            return http.HttpResponseRedirect(e.url)

        # Check if this view should be skipped
        try:
            self.check_skip_conditions(request)
        except exceptions.PassedSkipCondition as e:
            return http.HttpResponseRedirect(e.url)

        return super().dispatch(
            request, *args, **kwargs)

    def check_pre_conditions(self, request):
        pre_conditions = self.get_pre_conditions(request)
        for method_name in pre_conditions:
            if not hasattr(self, method_name):
                raise ImproperlyConfigured(
                    "There is no method '%s' to call as a pre-condition" % (
                        method_name))
            getattr(self, method_name)(request)

    def get_pre_conditions(self, request):
        """
        Return the pre-condition method names to run for this view
        """
        if self.pre_conditions is None:
            return []
        return self.pre_conditions

    def check_skip_conditions(self, request):
        skip_conditions = self.get_skip_conditions(request)
        for method_name in skip_conditions:
            if not hasattr(self, method_name):
                raise ImproperlyConfigured(
                    "There is no method '%s' to call as a skip-condition" % (
                        method_name))
            getattr(self, method_name)(request)

    def get_skip_conditions(self, request):
        """
        Return the skip-condition method names to run for this view
        """
        if self.skip_conditions is None:
            return []
        return self.skip_conditions

    # Re-usable pre-condition validators
    def check_basket_is_not_empty(self, request):
        if request.basket.is_empty:
            raise exceptions.FailedPreCondition(
                url=reverse('basket:summary'),
                message=_(
                    "You need to add some items to your basket to checkout")
                )

    def check_basket_is_not_empty(self, request):
        if request.basket.is_empty:
            raise exceptions.FailedPreCondition(
                url=reverse('basket:summary'),
                message=_(
                    "You need to add some items to your basket to checkout")
            )

    def check_basket_is_valid(self, request):
        """
        Check that the basket is permitted to be submitted as an order. That
        is, all the basket lines are available to buy - nothing has gone out of
        stock since it was added to the basket.
        """
        messages = []
        strategy = request.strategy
        for line in request.basket.all_lines():
            result = strategy.fetch_for_line(line)
            is_permitted, reason = result.availability.is_purchase_permitted(
                line.quantity)
            if not is_permitted:
                # Create a more meaningful message to show on the basket page
                msg = _(
                    "'%(title)s' is no longer available to buy (%(reason)s). "
                    "Please adjust your basket to continue"
                ) % {
                    'title': line.product.get_title(),
                    'reason': reason}
                messages.append(msg)
        if messages:
            raise exceptions.FailedPreCondition(
                url=reverse('basket:summary'),
                messages=messages
            )

    def check_user_email_is_captured(self, request):
        if not request.user.is_authenticated \
                and not self.checkout_session.get_guest_email():
            raise exceptions.FailedPreCondition(
                url=reverse('checkout:index'),
                message=_(
                    "Please either sign in or enter your email address")
            )

    def check_shipping_data_is_captured(self, request):
        if not request.basket.is_shipping_required():
            # Even without shipping being required, we still need to check that
            # a shipping method code has been set.
            if not self.checkout_session.is_shipping_method_set(
                    self.request.basket):
                raise exceptions.FailedPreCondition(
                    url=reverse('checkout:shipping-method'),
                )
            return

        # Basket requires shipping: check address and method are captured and
        # valid.
        self.check_a_valid_shipping_address_is_captured()
        self.check_a_valid_shipping_method_is_captured()

    def check_a_valid_shipping_address_is_captured(self):
        # Check that shipping address has been completed
        if not self.checkout_session.is_shipping_address_set():
            raise exceptions.FailedPreCondition(
                url=reverse('checkout:shipping-address'),
                message=_("Please choose a shipping address")
            )

        # Check that the previously chosen shipping address is still valid
        shipping_address = self.get_shipping_address(
            basket=self.request.basket)
        if not shipping_address:
            raise exceptions.FailedPreCondition(
                url=reverse('checkout:shipping-address'),
                message=_("Your previously chosen shipping address is "
                          "no longer valid.  Please choose another one")
            )

    def check_a_valid_shipping_method_is_captured(self):
        # Check that shipping method has been set
        if not self.checkout_session.is_shipping_method_set(
                self.request.basket):
            raise exceptions.FailedPreCondition(
                url=reverse('checkout:shipping-method'),
                message=_("Please choose a shipping method")
            )

        # Check that a *valid* shipping method has been set
        shipping_address = self.get_shipping_address(
            basket=self.request.basket)
        shipping_method = self.get_shipping_method(
            basket=self.request.basket,
            shipping_address=shipping_address)
        if not shipping_method:
            raise exceptions.FailedPreCondition(
                url=reverse('checkout:shipping-method'),
                message=_("Your previously chosen shipping method is "
                          "no longer valid.  Please choose another one")
            )

    def check_payment_method_is_captured(self, request):
        self.check_a_valid_payment_method_is_captured()

    def check_a_valid_payment_method_is_captured(self):
        # Check that payment method has been set
        if not self.checkout_session.payment_method():
            raise exceptions.FailedPreCondition(
                url=reverse('checkout:payment-method'),
                message=_("Please choose a payment method")
            )

        basket = self.request.basket
        # Check that a *valid* payment method has been set
        payment_method = self.get_payment_method(
            basket=basket,
            order_total=self.get_order_totals_with_shipping(basket))
        if not payment_method:
            raise exceptions.FailedPreCondition(
                url=reverse('checkout:payment-method'),
                message=_("Your previously chosen payment method is "
                          "no longer valid.  Please choose another one")
            )

    def check_payment_data_is_captured(self, request):
        # We don't collect payment data by default so we don't have anything to
        # validate here. If your shop requires forms to be submitted on the
        # payment details page, then override this method to check that the
        # relevant data is available. Often just enforcing that the preview
        # view is only accessible from a POST request is sufficient.
        if not self.checkout_session.get_payment_data():
            raise exceptions.FailedPreCondition(
                url=reverse('checkout:payment-details'),
                message=_("Please provide valid payment details")
            )

    # Re-usable skip conditions

    def skip_unless_basket_requires_shipping(self, request):
        # Check to see that a shipping address is actually required.  It may
        # not be if the basket is purely downloads
        if not request.basket.is_shipping_required():
            raise exceptions.PassedSkipCondition(
                url=reverse('checkout:shipping-method')
            )

    def skip_unless_payment_is_required(self, request):
        # Check to see if payment is actually required for this order.
        shipping_address = self.get_shipping_address(request.basket)
        shipping_method = self.get_shipping_method(
            request.basket, shipping_address)
        if shipping_method:
            shipping_charge = shipping_method.calculate(request.basket)
        else:
            # It's unusual to get here as a shipping method should be set by
            # the time this skip-condition is called. In the absence of any
            # other evidence, we assume the shipping charge is zero.
            shipping_charge = prices.Price(
                currency=request.basket.currency, excl_tax=D('0.00'),
                tax=D('0.00')
            )
        total = self.get_order_totals(request.basket, shipping_charge)
        if total.excl_tax == D('0.00'):
            raise exceptions.PassedSkipCondition(
                url=reverse('checkout:preview')
            )

    # Helpers

    def get_context_data(self, **kwargs):
        # Use the proposed submission as template context data.  Flatten the
        # order kwargs so they are easily available too.
        ctx = super().get_context_data(**kwargs)
        ctx.update(self.build_submission(**kwargs))
        ctx.update(kwargs)
        ctx.update(ctx['order_kwargs'])
        return ctx

    def build_submission(self, **kwargs):
        """
        Return a dict of data that contains everything required for an order
        submission.  This includes payment details (if any).

        This can be the right place to perform tax lookups and apply them to
        the basket.
        """
        # Pop the basket if there is one, because we pass it as a positional
        # argument to methods below
        basket = kwargs.pop('basket', self.request.basket)
        shipping_address = self.get_shipping_address(basket)
        shipping_method = self.get_shipping_method(
            basket, shipping_address)
        billing_address = self.get_billing_address(shipping_address)
        shipping_charge = self.get_shipping_charge(basket, shipping_method)
        total = self.get_order_totals(
            basket, shipping_charge=shipping_charge, **kwargs)
        submission = {
            'user': self.request.user,
            'basket': basket,
            'shipping_address': shipping_address,
            'shipping_method': shipping_method,
            'shipping_charge': shipping_charge,
            'billing_address': billing_address,
            'order_total': total,
            'order_kwargs': {},
            'payment_kwargs': {}}

        # If there is a billing address, add it to the payment kwargs as calls
        # to payment gateways generally require the billing address. Note, that
        # it normally makes sense to pass the form instance that captures the
        # billing address information. That way, if payment fails, you can
        # render bound forms in the template to make re-submission easier.
        if billing_address:
            submission['payment_kwargs']['billing_address'] = billing_address

        # Allow overrides to be passed in
        submission.update(kwargs)

        # Set guest email after overrides as we need to update the order_kwargs
        # entry.
        user = submission['user']
        if (not user.is_authenticated
                and 'guest_email' not in submission['order_kwargs']):
            email = self.checkout_session.get_guest_email()
            submission['order_kwargs']['guest_email'] = email
        return submission

    def get_shipping_address(self, basket):
        """
        Return the (unsaved) shipping address for this checkout session.

        If the shipping address was entered manually, then we instantiate a
        ``ShippingAddress`` model with the appropriate form data (which is
        saved in the session).

        If the shipping address was selected from the user's address book,
        then we convert the ``UserAddress`` to a ``ShippingAddress``.

        The ``ShippingAddress`` instance is not saved as sometimes you need a
        shipping address instance before the order is placed.  For example, if
        you are submitting fraud information as part of a payment request.

        The ``OrderPlacementMixin.create_shipping_address`` method is
        responsible for saving a shipping address when an order is placed.
        """
        if not basket.is_shipping_required():
            return None

        addr_data = self.checkout_session.new_shipping_address_fields()
        if addr_data:
            # Load address data into a blank shipping address model
            return ShippingAddress(**addr_data)
        addr_id = self.checkout_session.shipping_user_address_id()
        if addr_id:
            try:
                address = UserAddress._default_manager.get(pk=addr_id)
            except UserAddress.DoesNotExist:
                # An address was selected but now it has disappeared.  This can
                # happen if the customer flushes their address book midway
                # through checkout.  No idea why they would do this but it can
                # happen.  Checkouts are highly vulnerable to race conditions
                # like this.
                return None
            else:
                # Copy user address data into a blank shipping address instance
                shipping_addr = ShippingAddress()
                address.populate_alternative_model(shipping_addr)
                return shipping_addr

    def get_shipping_method(self, basket, shipping_address=None, **kwargs):
        """
        Return the selected shipping method instance from this checkout session

        The shipping address is passed as we need to check that the method
        stored in the session is still valid for the shipping address.
        """
        code = self.checkout_session.shipping_method_code(basket)
        methods = ShippingRepository().get_shipping_methods(
            basket=basket, user=self.request.user,
            shipping_addr=shipping_address, request=self.request)
        for method in methods:
            if method.code == code:
                return method

    def get_payment_method(self, basket, order_total, **kwargs):
        """
        Return the selected payment method instance from this checkout session

        The shipping charge is passed as we may need to calculate fees based on
        the method chosen.
        """
        code = self.checkout_session.payment_method()
        methods = PaymentRepository().get_payment_methods(
            basket=basket, user=self.request.user,
            order_total=order_total, request=self.request)
        for method in methods:
            if method.code == code:
                return method

    def get_default_billing_address(self):
        """
        Return default billing address for user

        This is useful when the payment details view includes a billing address
        form - you can use this helper method to prepopulate the form.

        Note, this isn't used in core oscar as there is no billing address form
        by default.
        """
        if not self.request.user.is_authenticated:
            return None
        try:
            return self.request.user.addresses.get(is_default_for_billing=True)
        except UserAddress.DoesNotExist:
            return self.request.user.addresses.all().first()

    def get_billing_address(self, shipping_address):
        """
        Return an unsaved instance of the billing address (if one exists)

        This method only returns a billing address if the session has been used
        to store billing address information. It's also possible to capture
        billing address information as part of the payment details forms, which
        never get stored in the session. In that circumstance, the billing
        address can be set directly in the build_submission dict.
        """
        if not self.checkout_session.is_billing_address_set():
            return None
        if self.checkout_session.is_billing_address_same_as_shipping():
            if shipping_address:
                address = BillingAddress()
                shipping_address.populate_alternative_model(address)
                return address

        addr_data = self.checkout_session.new_billing_address_fields()
        if addr_data:
            # A new billing address has been entered - load address data into a
            # blank billing address model.
            return BillingAddress(**addr_data)

        addr_id = self.checkout_session.billing_user_address_id()
        if addr_id:
            # An address from the user's address book has been selected as the
            # billing address - load it and convert it into a billing address
            # instance.
            try:
                user_address = UserAddress._default_manager.get(pk=addr_id)
            except UserAddress.DoesNotExist:
                # An address was selected but now it has disappeared.  This can
                # happen if the customer flushes their address book midway
                # through checkout.  No idea why they would do this but it can
                # happen.  Checkouts are highly vulnerable to race conditions
                # like this.
                return None
            else:
                # Copy user address data into a blank shipping address instance
                billing_address = BillingAddress()
                user_address.populate_alternative_model(billing_address)
                return billing_address

    def get_shipping_charge(self, basket, shipping_method, **kwargs):
        """
        Returns the shipping charge for the order
        """
        if shipping_method:
            return shipping_method.calculate(basket)

    def get_order_totals(self, basket, shipping_charge, **kwargs):
        """
        Returns the total for the order with and without tax
        """
        return OrderTotalCalculator(self.request).calculate(
            basket, shipping_charge, **kwargs)

    def get_order_totals_with_shipping(self, basket, **kwargs):
        """
        Calculates the shipping and returns the total for the order
        with and without tax.
        """
        shipping_address = self.get_shipping_address(basket)
        shipping_method = self.get_shipping_method(
            basket, shipping_address)
        billing_address = self.get_billing_address(shipping_address)
        if not shipping_method:
            shipping_charge = None
        else:
            shipping_charge = shipping_method.calculate(basket)
        return self.get_order_totals(
            basket, shipping_charge=shipping_charge, **kwargs)
