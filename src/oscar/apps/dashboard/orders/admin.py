from django.contrib.admin.utils import quote
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from oscar.apps.dashboard.base import DashboardAdmin
from oscar.core.loading import get_class, get_model
from oscar.core.compat import AUTH_USER_MODEL

Order = get_model('order', 'Order')
Customer = get_model(*AUTH_USER_MODEL.split('.'))
Partner = get_model('partner', 'Partner')


class OrderAdmin(DashboardAdmin):
    model = Order
    menu_label = _('Orders')
    menu_icon = 'list-alt'
    dashboard_url = 'orders'
    instance_views = ['inspect']
    restricted_actions = ['edit', 'delete']
    list_display = ('number', 'date_placed', 'total_incl_tax', 'num_items',
                    'billing_address', 'shipping_address', 'status', 'user')
    list_filter = ('date_placed', 'status')
    search_fields = ('number', 'user__email')

    inspect_view_enabled = True
    inspect_template_name = 'oscar/dashboard/orders/details.html'
    instance_views = DashboardAdmin.instance_views + ['inspect']

    def get_queryset(self, request):
        """
        Returns a queryset of all orders that a user is allowed to access.
        A staff user may access all orders.
        To allow access to an order for a non-staff user, at least one line's
        partner has to have the user in the partner's list.
        """
        queryset = Order._default_manager.select_related(
            'billing_address', 'billing_address__country',
            'shipping_address', 'shipping_address__country',
            'user'
        ).prefetch_related('lines', 'status_changes')
        if request.user.is_staff:
            return queryset
        partners = Partner._default_manager.filter(users=user)
        return queryset.filter(lines__partner__in=partners).distinct()


class CustomerAdmin(DashboardAdmin):
    model = Customer
    menu_label = _('Customers')
    menu_icon = 'user'
    dashboard_url = 'customers'
    inspect_view_enabled = True
    list_display = ('name', 'email', 'number_of_orders', 'last_order',
                    'last_login', 'date_joined')
    list_filter = ('date_joined', 'is_active', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name')

    def name(self, obj):
        return obj.get_full_name()

    def number_of_orders(self, obj):
        return obj.orders.count()

    def last_order(self, obj):
        order = obj.orders.all().order_by('date_placed').first()
        if order:
            url = OrderAdmin.instance().get_action_url(
                'view', quote(order.pk))
            return format_html('<a href="{}">{}</a>', url, order)

