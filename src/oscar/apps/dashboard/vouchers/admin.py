from django.utils.translation import gettext_lazy as _
from oscar.apps.dashboard.base import DashboardAdmin
from oscar.core.loading import get_model


Voucher = get_model('voucher', 'Voucher')
VoucherSet = get_model('voucher', 'VoucherSet')


class VouchersAdmin(DashboardAdmin):
    model = Voucher
    menu_label = _('Voucher')
    menu_icon = 'ticket'
    list_display = ('name', 'code', 'is_active', 'usage', 'start_datetime',
                    'end_datetime', 'num_basket_additions', 'num_orders',
                    'total_discount', 'date_created')
    list_filter = ('usage', 'date_created')
    search_fields = ('name', 'code')

    def get_queryset(self, request):
        return self.model._default_manager.exclude(
            offer_type=ConditionalOffer.VOUCHER)


class VoucherSetsAdmin(DashboardAdmin):
    model = VoucherSet
    menu_label = _('Voucher Set')
    menu_icon = 'bookmark'
    list_display = ('name', 'is_active', 'count', 'offer', 'start_datetime',
                    'end_datetime', 'num_basket_additions', 'num_orders',
                    'total_discount', 'date_created')
    list_filter = ('count', 'date_created')
    search_fields = ('name',)
