from decimal import Decimal as D
from django import forms
from django.contrib.admin.utils import quote
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from oscar.apps.dashboard.base import DashboardAdmin
from oscar.core.loading import get_class, get_model
from oscar.core.compat import AUTH_USER_MODEL
from oscar.templatetags.currency_filters import currency

from wagtail.admin.edit_handlers import ObjectList, FieldPanel
from wagtail.admin.modal_workflow import render_modal_workflow


Order = get_model('order', 'Order')
Customer = get_model(*AUTH_USER_MODEL.split('.'))
Partner = get_model('partner', 'Partner')
PaymentSource = get_model('payment', 'Source')
PaymentTransaction = get_model('payment', 'Transaction')
CommunicationEventType = get_model('customer', 'CommunicationEventType')


class OrderAdmin(DashboardAdmin):
    model = Order
    menu_label = _('Orders')
    menu_icon = 'list-alt'
    dashboard_url = 'orders'
    restricted_actions = ['edit', 'delete']
    list_display = ('number', 'status', 'num_items', 'order_total',
                    'paid_in_full', 'bill_to', 'ship_to', 'date_placed')
    list_filter = ('date_placed', 'status')
    search_fields = (
        'number',
        'user__email', 'user__first_name', 'user__last_name',
        'shipping_address__first_name', 'shipping_address__last_name',
        'shipping_address__line4', 'shipping_address__phone_number')

    inspect_view_enabled = True
    inspect_view_class = get_class(
        'dashboard.orders.views', 'OrderDetailsView')
    inspect_template_name = 'oscar/dashboard/orders/details.html'
    instance_views = DashboardAdmin.instance_views + [
        'inspect',
        'edit_billing_address',
        'edit_shipping_address',
        'edit_order_status',
        'add_transaction',
    ]

    modal_template = 'dashboard/partials/modal_editor.html'
    payment_source_template = 'dashboard/orders/order_payment_source.html'

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
        partners = Partner._default_manager.filter(users=request.user)
        return queryset.filter(lines__partner__in=partners).distinct()

    # =========================================================================
    # Address edit views
    # =========================================================================
    def get_order_status_form(self, request, order):
        class StatusForm(forms.Form):
            status = forms.ChoiceField(
                label="Status",
                required=True,
                choices=[(it, it) for it in order.available_statuses()])
        if request.method == 'POST':
            return StatusForm(request.POST)
        return StatusForm()


    def edit_order_status_view(self, request, instance_pk):
        order = get_object_or_404(Order, pk=instance_pk)
        form = self.get_order_status_form(request, order)
        if request.method == 'POST' and form.is_valid():
            status = form.cleaned_data['status']
            order.set_status(status)
            return render_modal_workflow(request, None, None, None, {
                'step': 'done',
                'update': {'id': 'order-status', 'html': order.status},
                'message': _('Order status updated!')})

        title = _('Edit order status')
        return render_modal_workflow(request, self.modal_template, None, {
                'form': form, 'request': request, 'title': title}, {
                    'step': 'edit'})


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
        return render_modal_workflow(request, self.modal_template, None, {
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
        return render_modal_workflow(request, self.modal_template, None, {
                'form': form, 'request': request, 'title': title}, {
                    'step': 'edit'})

    # =========================================================================
    # Transaction add views
    # =========================================================================
    def render_payment_source(self, order, source):
        return render_to_string(
            self.payment_source_template,
            context={'order': order, 'source': source})

    def get_transaction_form(self, request, source):
        txn = PaymentTransaction(
            source=source,
            amount=source.balance,
            txn_type=PaymentTransaction.DEBIT,
        )
        handler = ObjectList(PaymentTransaction.panels).bind_to(instance=txn)
        Form = handler.get_form_class()
        if request.method == 'POST':
            return Form(request.POST, instance=txn)
        return Form(instance=txn)

    def add_transaction_view(self, request, instance_pk):
        order = get_object_or_404(Order, pk=instance_pk)
        source = get_object_or_404(
            PaymentSource, pk=request.GET.get('source'), order=order)
        form = self.get_transaction_form(request, source)
        if request.method == 'POST' and form.is_valid():
            txn = form.instance
            actions = {
                PaymentTransaction.REFUND: source.refund,
                PaymentTransaction.DEBIT: source.debit,
            }
            action = actions.get(txn.txn_type)
            if action:
                action(txn.amount, txn.reference, txn.status)
            else:
                form.save()
            html = self.render_payment_source(order, source)
            return render_modal_workflow(request, None, None, None, {
                'step': 'done',
                'update': {'id': 'payment-source-%s' % source.id, 'html': html},
                'message': _('Transaction details added!')})

        title = _('Add %s transaction details' % source.source_type)
        return render_modal_workflow(request, self.modal_template, None, {
                'form': form, 'request': request, 'title': title}, {
                    'step': 'edit'})
