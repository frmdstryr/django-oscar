from datetime import timedelta
from django.contrib.admin.utils import quote
from django.contrib.humanize.templatetags import humanize
from django.db.models import Avg, Count, Sum
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from oscar.apps.dashboard.base import DashboardAdmin
from oscar.core.loading import get_class, get_model
from oscar.core.compat import AUTH_USER_MODEL


Basket = get_model('basket', 'Basket')
ProductRecord = get_model('analytics', 'ProductRecord')
UserRecord = get_model('analytics', 'UserRecord')
UserSearch = get_model('analytics', 'UserSearch')


class IndexOnlyAdmin(DashboardAdmin):
    class_views = ['index']
    instance_views = []
    restricted_actions = ['create', 'edit', 'delete']


class AbandonedCartsAdmin(IndexOnlyAdmin):
    model = Basket
    menu_label = _('Abandoned Carts')
    menu_icon = 'shopping-cart'
    list_display = ('owner', 'num_lines', 'num_items',  'cart_total',
                    'offers_applied', 'when_abandoned')

    def get_queryset(self, request):
        self.request = request
        date = timezone.now() - timedelta(days=7)
        return Basket.objects.filter(status=Basket.OPEN,
                                     date_created__lte=date)

    def offers_applied(self, obj):
        offers = obj.applied_offers()
        if offers:
            return ', '.join(map(str, offers.values()))

    def cart_total(self, obj):
        if not obj.currency:
            return None
        if not obj.has_strategy:
            obj.strategy = self.request.strategy
        return format_html('<span class="price">{} {}</span>',
                           obj.currency, obj.total_incl_tax)

    def when_abandoned(self, obj):
        return humanize.naturaltime(obj.date_created)


class ProductAnalyticsAdmin(IndexOnlyAdmin):
    model = ProductRecord
    menu_label = _('Product Analytics')
    menu_icon = 'cubes'
    list_display = ('_product', 'num_views', 'num_basket_additions',
                    'num_purchases')

    _product_admin = None

    def get_product_url(self, product):
        if self._product_admin is None:
            self._product_admin = get_class(
                'dashboard.catalogue.admin', 'ProductAdmin').instance()
        return self._product_admin.get_action_url('inspect', product.pk)

    def _product(self, record):
        p = record.product
        url = self.get_product_url(p)
        return format_html('<a href="{}">{}</a>', url, p)


class CustomerAnalyticsAdmin(IndexOnlyAdmin):
    model = UserRecord
    menu_label = _('Customer Analytics')
    menu_icon = 'users'
    list_display = ('user', 'num_product_views', 'num_basket_additions',
                    'num_orders', 'num_order_lines', 'num_order_items',
                    'total_spent', 'date_last_order')


class SearchesAdmin(IndexOnlyAdmin):
    model = UserSearch
    menu_label = _('Search Analytics')
    menu_icon = 'search'
    list_display = ('user', 'query', 'result_count')


class BasketAdmin(DashboardAdmin):
    model = Basket
    menu_label = _('Baskets')
    menu_icon = 'shopping-cart'
    class_views = ['index']
    list_display = ('owner', 'status', 'num_items', 'total_incl_tax')
    list_filter = ('status',)
