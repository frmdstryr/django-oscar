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


class VisitorAdmin(DashboardAdmin):
    model = Visitor
    menu_label = _('Visitor Analytics')
    menu_icon = 'line-chart'
    inspect_view_enabled = True
    instance_views = ['inspect', 'delete']
    restricted_actions = ['create', 'edit']
    search_fields = ('ip_address', 'session_key', 'user_agent')
    list_filter = ('start_time', 'is_bot')
    list_display = ('id', 'user', 'start_time',
        '_time_on_site', 'client', 'device', 'location', 'is_bot',
        'actions', 'landing_page')

    excluded_params = ('p', 'o')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        query = request.GET
        excluded = self.excluded_params
        for k, v in query.items():
            if k in excluded:
                continue
            qs = qs.filter({k: v})
        return qs

    # =========================================================================
    # Display fields
    # =========================================================================
    def id(self, obj):
        label = str(obj.identity)[0:8]
        url = self.get_visitor_url(identity=obj.identity)
        return format_html('<a href="{}">{}</a>', url, label)

    def session_over(self, obj):
        return obj.session_ended() or obj.session_expired()
    session_over.boolean = True

    def _time_on_site(self, obj):
        if obj.time_on_site is not None:
            return timedelta(seconds=obj.time_on_site)

    def client(self, obj):
        url = self.get_pageview_url(visitor__ip_address=obj.ip_address)
        reverse_ip = obj.reverse_lookup()
        return format_html(
            '<a href="{}">{}</a></br><span>{}</span>',
            url, obj.ip_address, reverse_ip)

    def landing_page(self, obj):
        visit = obj.pageviews.last()
        return format_html('<a href="{}">{}</a>', visit.url, visit.url)

    def device(self, obj):
        data = obj.data
        if not data:
            return ''

        template = []
        params = []
        dev = data.get('device')
        if dev:
            template.append('Device: <a href="{}">{}</a>')
            if dev.get('brand'):
                brand = dev.get('brand')
                model = dev.get('model')
                label = '{brand} {model}'.format(**dev)
                filters = {}
                if brand:
                    filters['visitor__data__device__brand'] = brand
                if model:
                    filters['visitor__data__device__model'] = model
            else:
                label = dev.get('family', '')
                filters = {'visitor__data__device__family': label}
            url = self.get_pageview_url(**filters)
            params.extend((url, label))
        os_data = data.get('os')
        if os_data:
            template.append('OS: <a href="{}">{}</a>')
            label = os_data.get('family', '')
            url = self.get_pageview_url(visitor__data__os__family=label)
            params.extend((url, label))

        browser = data.get('user_agent')
        if browser:
            template.append('Browser: <a href="{}">{}</a>')
            label = browser.get('family', '')
            url = self.get_pageview_url(
                visitor__data__user_agent__family=label)
            params.extend((url, label))
        if not template:
            return ''

        return format_html('</br>'.join(template), *params)

    def flag(self, code):
        if not code:
            return u''
        OFFSET = ord('🇦') - ord('A')
        points = tuple(map(lambda x: ord(x) + OFFSET, code.upper()))
        try:
            return chr(points[0]) + chr(points[1])
        except ValueError:
            return ('\\U%08x\\U%08x' % tuple(points)).decode('unicode-escape')

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

    def get_visitor_url(self, **query):
        url = self.get_action_url('index')
        if query:
            url += "?" + "&".join(["%s=%s"% it for it in query.items()])
        return url

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
    list_display = ('visitor', 'path', 'view_time')
    excluded_params = ('p', 'o')

    def path(self, obj):
        url = obj.url
        if obj.query_string:
            url += "?" + obj.query_string
        return format_html('<a href="{}" target="_blank">{}</a>', url, url)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        query = request.GET
        excluded = self.excluded_params
        for k, v in query.items():
            if k in excluded:
                continue
            qs = qs.filter({k: v})
        return qs


class BasketAdmin(DashboardAdmin):
    model = Basket
    menu_label = _('Baskets')
    menu_icon = 'shopping-cart'
    class_views = ['index']
    list_display = ('owner', 'status', 'num_items', 'total_incl_tax')
    list_filter = ('status',)
