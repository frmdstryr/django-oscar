from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from oscar.apps.dashboard.base import DashboardAdmin
from oscar.core.loading import get_model
from wagtail.admin import messages


Partner = get_model('partner', 'Partner')
StockAlert = get_model('partner', 'StockAlert')


class PartnerAdmin(DashboardAdmin):
    model = Partner
    menu_label = _('Partners')
    menu_icon = 'briefcase'
    dashboard_url = 'partners'
    list_display = ('name', 'user_list')
    search_fields = ('name', 'users__email')

    def user_list(self, obj):
        return ', '.join(map(str, obj.users.all()))


class StockAlertAdmin(DashboardAdmin):
    model = StockAlert
    menu_label = _('Stock Alerts')
    menu_icon = 'bell-o'
    dashboard_url = 'stock-alerts'
    restricted_actions = ['create', 'delete']
    list_display = ('product', 'partner', 'num_in_stock', 'threshold',
                    'status', 'date_created', 'date_closed')
    list_filter = ('status', 'stockrecord__partner', 'date_created')
    search_fields = ('stockrecord__product__title', )

    bulk_actions = ['mark_closed']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_staff:
            return qs
        return qs.filter(stockrecord__partner__user=request.user)

    def num_in_stock(self, obj):
        return obj.stockrecord.num_in_stock

    def partner(self, obj):
        return obj.stockrecord.partner

    def product(self, obj):
        product = obj.stockrecord.product
        kwargs = {'instance_pk': product.pk}
        url = reverse('catalogue_product_modeladmin_edit', kwargs=kwargs)
        return format_html('<a href="{}">{}</a>', url, product)

    def do_bulk_action_mark_closed(self, request, form):
        queryset = form.cleaned_data['selection']
        now = timezone.now()
        result = queryset.filter(status=StockAlert.OPEN).update(
            status=StockAlert.CLOSED, date_closed=now)
        messages.success(request, _('%s alerts marked as closed' % result))
