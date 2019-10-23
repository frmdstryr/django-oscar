from datetime import timedelta
from django.contrib.admin.utils import quote
from django.contrib.humanize.templatetags import humanize
from django.db.models import Avg, Count, Sum
from django.utils import timezone
from django.utils.html import format_html
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from oscar.apps.dashboard.base import DashboardAdmin
from oscar.core.loading import get_class, get_model
from oscar.core.compat import AUTH_USER_MODEL


Basket = get_model('basket', 'Basket')
ProductRecord = get_model('analytics', 'ProductRecord')
UserRecord = get_model('analytics', 'UserRecord')
UserSearch = get_model('analytics', 'UserSearch')

Visitor = get_model('analytics', 'Visitor')
PageView = get_model('analytics', 'PageView')




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

    @cached_property
    def product_admin(self):
        ProductAdmin = get_class('dashboard.catalogue.admin', 'ProductAdmin')
        return ProductAdmin.instance()

    def get_product_url(self, product):
        return self.product_admin.get_action_url('inspect', product.pk)

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
    list_display = ('user', 'query', 'result_count', 'date_created')


class VisitorAdmin(IndexOnlyAdmin):
    model = Visitor
    menu_label = _('Visitor Analytics')
    menu_icon = 'line-chart'
    search_fields = ('ip_address', 'session_key')
    list_filter = ('start_time',)
    list_display = ('user', 'start_time',
        '_time_on_site', 'ip_address', 'os', 'device', 'browser', 'location',
        'actions', 'landing_page', 'session_over')

    # =========================================================================
    # Display fields
    # =========================================================================

    def session_over(self, obj):
        return obj.session_ended() or obj.session_expired()
    session_over.boolean = True

    def _time_on_site(self, obj):
        if obj.time_on_site is not None:
            return timedelta(seconds=obj.time_on_site)

    def landing_page(self, obj):
        visit = obj.pageviews.last()
        return format_html('<a href="{}">{}</a>', visit.url, visit.url)

    def device(self, obj):
        if not obj.data or 'device' not in obj.data:
            return ''
        dev = obj.data['device']
        if dev.get('brand'):
            return '{brand} {model}'.format(**dev)
        return dev.get('family', '')

    def os(self, obj):
        if not obj.data or 'os' not in obj.data:
            return ''
        os_data = obj.data['os']
        return '{family}'.format(**os_data)

    def flag(self, code):
        if not code:
            return u''
        OFFSET = ord('🇦') - ord('A')
        points = map(lambda x: ord(x) + OFFSET, code.upper())
        try:
            return chr(points[0]) + chr(points[1])
        except ValueError:
            return ('\\U%08x\\U%08x' % tuple(points)).decode('unicode-escape')

    def browser(self, obj):
        if not obj.data or 'user_agent' not in obj.data:
            return ''
        ua_data = obj.data['user_agent']
        return '{family}'.format(**ua_data)

    def location(self, obj):
        if not obj.data or 'geo' not in obj.data:
            return ''
        geo_data = obj.data['geo']
        if not geo_data:
            return ''
        cc = geo_data.get('country_code')
        if cc:
            geo_data['flag'] = self.flag(cc)
        return '{flag} {city} {region}, {country_code}'.format(**geo_data)

    def actions(self, obj):
        url = self.get_pageview_url(visitor=obj.session_key)
        count = obj.pageviews.all().count()
        return format_html('<a href="{}">{} actions</a>', url, count)

    # =========================================================================
    # Extra methods
    # =========================================================================
    @cached_property
    def pageview_admin(self):
        PageViewAdmin = get_class('dashboard.reports.admin', 'PageViewAdmin')
        return PageViewAdmin.instance()

    def get_pageview_url(self, **query):
        url = self.pageview_admin.get_action_url('index')
        if query:
            url += "?" + "&".join(["%s=%s"% it for it in query.items()])
        return url


class PageViewAdmin(IndexOnlyAdmin):
    model = PageView
    menu_label = _('Page Analytics')
    menu_icon = 'area-chart'
    search_fields = ('visitor__session_key', )
    list_display = ('visitor', 'url', 'view_time')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.GET.get('visitor'):
            qs = qs.filter(visitor=request.GET.get('visitor'))
        return qs


class BasketAdmin(DashboardAdmin):
    model = Basket
    menu_label = _('Baskets')
    menu_icon = 'shopping-cart'
    class_views = ['index']
    list_display = ('owner', 'status', 'num_items', 'total_incl_tax')
    list_filter = ('status',)
