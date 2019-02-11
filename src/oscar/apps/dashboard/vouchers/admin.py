from django.utils.translation import gettext_lazy as _
from oscar.apps.dashboard.base import DashboardAdmin
from oscar.core.loading import get_model


ConditionalOffer = get_model('offer', 'ConditionalOffer')
Voucher = get_model('voucher', 'Voucher')
VoucherSet = get_model('voucher', 'VoucherSet')


class VouchersAdmin(DashboardAdmin):
    model = Voucher
    menu_label = _('Voucher')
    menu_icon = 'ticket'
    dashboard_url = '/offers/coupons/'
    list_display = ('name', 'code', 'is_active', 'usage', 'start_datetime',
                    'end_datetime', 'num_basket_additions', 'num_orders',
                    'total_discount', 'date_created')
    list_filter = ('usage', 'date_created', 'voucher_set')
    search_fields = ('name', 'code')


class VoucherSetsAdmin(DashboardAdmin):
    model = VoucherSet
    menu_label = _('Voucher Set')
    menu_icon = 'bookmark'
    dashboard_url = '/offers/coupons/sets/'
    list_display = ('name', 'is_active', 'count', 'offer', 'start_datetime',
                    'end_datetime', 'num_basket_additions', 'num_orders',
                    'total_discount', 'date_created')
    list_filter = ('count', 'date_created')
    search_fields = ('name',)
