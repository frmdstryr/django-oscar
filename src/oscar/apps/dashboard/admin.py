from django.utils.translation import gettext_lazy as _
from oscar.core.loading import get_class, get_classes, feature_hidden

from .base import DashboardAdminGroup


class CatalogueGroup(DashboardAdminGroup):
    menu_label = _('Catalogue')
    menu_icon = 'sitemap'
    menu_order = 200  # will put in 3rd place (000 being 1st, 100 2nd)

    @property
    def items(self):
        return get_classes('dashboard.catalogue.admin', (
            'ProductAdmin',
            'ProductClassAdmin',
            'ProductAttributeAdmin',
            'AttributeOptionGroupAdmin',
            'ProductOptionAdmin',
            'AddToCartOptionGroupAdmin',
        ))


class FulfillmentGroup(DashboardAdminGroup):
    menu_label = _('Fullfillment')
    menu_icon = 'shopping-cart'
    menu_order = 300

    @property
    def items(self):
        return (
            get_class('dashboard.orders.admin', 'OrderAdmin'),
            get_class('dashboard.partners.admin', 'PartnerAdmin'),
            get_class('dashboard.shipments.admin', 'ShippingMethodsAdmin'),
            get_class('dashboard.partners.admin', 'StockAlertAdmin'),
        )


class CustomersGroup(DashboardAdminGroup):
    menu_label = _('Customers')
    menu_icon = 'group'
    menu_order = 400

    @property
    def items(self):
        return (
            get_class('dashboard.customers.admin', 'CustomerAdmin'),
            get_class('dashboard.catalogue.admin', 'ProductReviewAdmin'),
        )


class OffersGroup(DashboardAdminGroup):
    menu_label = _('Offers')
    menu_icon = 'tags'
    menu_order = 500

    @property
    def items(self):
        return (
            get_class('dashboard.offers.admin', 'OffersAdmin'),
            get_class('dashboard.offers.admin', 'RangesAdmin'),
            get_class('dashboard.vouchers.admin', 'VouchersAdmin'),
            get_class('dashboard.vouchers.admin', 'VoucherSetsAdmin'),
        )


class ContentGroup(DashboardAdminGroup):
    menu_label = _('Content')
    menu_icon = 'map-o'
    menu_order = 600

    @property
    def items(self):
        if feature_hidden('pages'):
            return []
        return get_classes('dashboard.pages.admin', (
            'PagesAdmin',
            'PagePromotionAdmin',
            'KeywordPromotionAdmin',
            'HtmlPromotionAdmin',
            'ImagePromotionAdmin',
            'MultiImagePromotionAdmin',
            'SingleProductPromotionAdmin',
            'HandPickedProductListPromotionAdmin',
        ))


class ReportsGroup(DashboardAdminGroup):
    menu_label = _('Analytics')
    menu_icon = 'bar-chart'
    menu_order = 700
    @property
    def items(self):
        return (
            get_class('dashboard.reports.admin', 'AbandonedCartsAdmin'),
            get_class('dashboard.reports.admin', 'ProductAnalyticsAdmin'),
            get_class('dashboard.reports.admin', 'CustomerAnalyticsAdmin'),
            get_class('dashboard.reports.admin', 'SearchesAdmin'),
            get_class('dashboard.reports.admin', 'VisitorAdmin'),
            get_class('dashboard.reports.admin', 'PageViewAdmin'),
        )


class DashboardSite:
    """ This simple class serves as a basic hook for wagtail that can
    be overridden with class loading.

    See wagtail_hooks
    """
    _instance = None

    # Django uses this to do lookup of different admins
    _registry = {}

    # List of all model admins
    model_admins = []

    @classmethod
    def instance(cls):
        if not cls._instance:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        """ Register using instance to ensure only one exists """
        if DashboardSite._instance:
            name = self.__class__.__name__
            raise RuntimeError("Only one instance of %s can exist,"
                               "please use instance()" % name)

    @property
    def panels(self):
        return (
            get_class('dashboard.panels', 'RecentOrdersChart'),
            get_class('dashboard.panels', 'LastOrdersList'),
            get_class('dashboard.panels', 'LastSearchTermsList'),
            get_class('dashboard.panels', 'TopSearchTermsList'),
        )

    @property
    def summary_items(self):
        return (
            get_class('dashboard.panels', 'OrdersSummaryItem'),
            get_class('dashboard.panels', 'CustomersSummaryItem'),
            get_class('dashboard.panels', 'ProductsSummaryItem'),
        )

    def construct_main_menu(self, request, menu_items):
        # Remove user settings menu
        if not request.user.is_superuser:
            excluded = ('users', 'groups')
            for item in menu_items:
                if item.name in excluded:
                    menu_items.remove(item)
                    continue

                # Check nested menus
                if item.menu:
                    sub_menu_items = item.menu._registered_menu_items
                    for sub_item in sub_menu_items:
                        if sub_item.name in excluded:
                            sub_menu_items.remove(sub_item)
                    if not item.is_shown(request):
                        menu_items.remove(item)

    def construct_panels(self, request, panels):
        for Panel in self.panels:
            panels.append(Panel(request))

    def construct_summary_items(self, request, summary_items):
        # Just ignore the default ones
        summary_items[:] = [
            SummaryItem(request) for SummaryItem in self.summary_items
        ]

    def register(self):
        for Group in get_classes('dashboard.admin', (
                    'CatalogueGroup',
                    'FulfillmentGroup',
                    'CustomersGroup',
                    'OffersGroup',
                    'ContentGroup',
                    'ReportsGroup',
                )):
            admin_group = Group()
            if admin_group.items:
                admin_group.register_with_wagtail()
                for ModelAdmin in admin_group.items:
                    self.register_model_admin(ModelAdmin.instance())

    def register_model_admin(self, model_admin):
        """ This saves a reference to the model_admin and associates it
        with this site instance.

        """
        if model_admin in self.model_admins:
            raise ImproperlyConfigured(
                "%s is already registered!" % model_admin)

        # TODO: This blows away and admin that exists there
        if hasattr(model_admin, 'model'):
            self._registry[model_admin.model] = model_admin

        model_admin.admin_site = self
        self.model_admins.append(model_admin)

