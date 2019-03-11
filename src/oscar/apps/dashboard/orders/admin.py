from decimal import Decimal as D
from django.contrib.admin.utils import quote
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.shortcuts import get_object_or_404
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from oscar.apps.dashboard.base import DashboardAdmin
from oscar.core.loading import get_class, get_model
from oscar.core.compat import AUTH_USER_MODEL
from oscar.templatetags.currency_filters import currency

from wagtail.admin.edit_handlers import ObjectList
from wagtail.admin.modal_workflow import render_modal_workflow


Order = get_model('order', 'Order')
Customer = get_model(*AUTH_USER_MODEL.split('.'))
Partner = get_model('partner', 'Partner')
CommunicationEventType = get_model('customer', 'CommunicationEventType')


class OrderAdmin(DashboardAdmin):
    model = Order
    menu_label = _('Orders')
    menu_icon = 'list-alt'
    dashboard_url = 'orders'
    instance_views = []
    restricted_actions = ['edit', 'delete']
    list_display = ('number', 'status', 'num_items', 'order_total',
                    'paid_in_full', 'bill_to', 'ship_to', 'date_placed')
    list_filter = ('date_placed', 'status')
    search_fields = ('number', 'user__email')

    inspect_view_enabled = True
    inspect_view_class = get_class(
        'dashboard.orders.views', 'OrderDetailsView')
    inspect_template_name = 'oscar/dashboard/orders/details.html'
    instance_views = DashboardAdmin.instance_views + [
        'inspect', 'edit_billing_address', 'edit_shipping_address']

    address_template = 'dashboard/partials/modal_editor.html'

    # =========================================================================
    # Display fields
    # =========================================================================
    def render_address(self, address):
        fields = '</br>'.join(address.active_address_fields())
        return format_html('<address>%s</address>' % fields)

    def bill_to(self, order):
        address = order.billing_address
        if address:
            return self.render_address(address)

    def ship_to(self, order):
        address = order.shipping_address
        if address:
            return self.render_address(address)

    def order_total(self, order):
        return currency(order.total_incl_tax, order.currency)

    def paid_in_full(self, order):
        paid = order.total_due == D(0.0)
        icon = 'admin/img/icon-{}.svg'.format('yes' if paid else 'no')
        return format_html('<img src="{}" alt="{}">', static(icon),
                           currency(order.total_due, order.currency))

    # =========================================================================
    # Search results
    # =========================================================================
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

    # =========================================================================
    # Address edit views
    # =========================================================================
    def get_address_form(self, request, address):
        handler = ObjectList(address.panels).bind_to(instance=address)
        Form = handler.get_form_class()
        if request.method == 'POST':
            return Form(request.POST, instance=address)
        return Form(instance=address)

    def edit_billing_address_view(self, request, instance_pk):
        order = get_object_or_404(Order, pk=instance_pk)
        form = self.get_address_form(request, order.billing_address)
        if request.method == 'POST' and form.is_valid():
            form.save()
            order.billing_address = form.instance
            order.save()
            html = self.render_address(form.instance)
            return render_modal_workflow(request, None, None, None, {
                'step': 'done',
                'update': {'id': 'billing-address', 'html': html},
                'message': _('Billing address updated!')})

        title = _('Edit billing address')
        return render_modal_workflow(request, self.address_template, None, {
                'form': form, 'request': request, 'title': title}, {
                    'step': 'edit'})

    def edit_shipping_address_view(self, request, instance_pk):
        order = get_object_or_404(Order, pk=instance_pk)
        form = self.get_address_form(request, order.shipping_address)
        if request.method == 'POST' and form.is_valid():
            form.save()
            order.shipping_address = form.instance
            order.save()
            html = self.render_address(form.instance)
            return render_modal_workflow(request, None, None, None, {
                'step': 'done',
                'update': {'id': 'shipping-address', 'html': html},
                'message': _('Shipping address updated!')})

        title = _('Edit shipping address')
        return render_modal_workflow(request, self.address_template, None, {
                'form': form, 'request': request, 'title': title}, {
                    'step': 'edit'})



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

    # =========================================================================
    # Display fields
    # =========================================================================
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



