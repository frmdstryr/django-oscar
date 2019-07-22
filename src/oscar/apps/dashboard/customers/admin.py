from django.contrib.admin.utils import quote
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from oscar.apps.dashboard.base import DashboardAdmin
from oscar.core.loading import get_class, get_model
from oscar.core.compat import AUTH_USER_MODEL

Customer = get_model(*AUTH_USER_MODEL.split('.'))
Partner = get_model('partner', 'Partner')
Email = get_model('customer', 'Email')


class CustomerAdmin(DashboardAdmin):
    model = Customer
    menu_label = _('Customers')
    menu_icon = 'user'
    dashboard_url = 'customers'
    list_display = ('name', 'email', 'phone_number', 'address',
                    'number_of_orders', 'last_order', 'last_login',
                    'date_joined')
    list_filter = ('date_joined', 'is_active', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name')

    # =========================================================================
    # Display fields
    # =========================================================================
    def name(self, customer):
        return customer.get_full_name()

    def phone_number(self, customer):
        addr = customer.addresses.filter(phone_number__isnull=False).first()
        if addr is not None:
            return addr.phone_number

    def address(self, customer):
        addr = customer.default_billing_address
        if addr is None:
            addr = customer.default_shipping_address
            if addr is None:
                addr = customer.addresses.first()

        if addr is not None:
            fields = '<br/>'.join(addr.active_address_fields()[1:])
            return format_html('<address>%s</address>' % fields)

    def number_of_orders(self, customer):
        return customer.orders.count()

    def last_order(self, customer):
        order = customer.last_order
        if order:
            OrderAdmin = get_class('dashboard.orders.admin', 'OrderAdmin')
            url = OrderAdmin.instance().get_action_url(
                'view', quote(order.pk))
            return format_html('<a href="{}">{}</a>', url, order)

    # =========================================================================
    # Search results
    # =========================================================================
    def get_queryset(self, request):
        """
        Returns a queryset of all customers that a user is allowed to access.
        A staff user may access all orders.
        To allow access to an order for a non-staff user, at least one order
        line's partner has to have the user in the partner's list.
        """
        queryset = Customer._default_manager.all()
        if request.user.is_staff:
            return queryset
        partners = Partner._default_manager.filter(users=request.user)
        return queryset.filter(orders__lines__partner__in=partners).distinct()
