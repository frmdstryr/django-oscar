from datetime import timedelta
from django.utils import timezone
from django.contrib.admin.utils import quote
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from oscar.apps.dashboard.base import DashboardAdmin
from oscar.core.loading import get_model
from django.contrib.humanize.templatetags import humanize
from oscar.core.compat import AUTH_USER_MODEL


Basket = get_model('basket', 'Basket')


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


class BasketAdmin(DashboardAdmin):
    model = Basket
    menu_label = _('Baskets')
    menu_icon = 'shopping-cart'
    class_views = ['index']
    list_display = ('owner', 'status', 'num_items', 'total_incl_tax')
    list_filter = ('status',)
