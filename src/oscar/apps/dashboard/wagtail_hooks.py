from wagtail.core import hooks
from oscar.core.loading import get_class


# Register site
DashboardSite = get_class('dashboard.admin', 'DashboardSite')
dashboard = DashboardSite()
dashboard.register_modeladmins()


# https://docs.wagtail.io/en/latest/reference/hooks.html#construct-main-menu
@hooks.register('construct_main_menu', order=10)
def register_main_menu(request, menu_items):
    dashboard.construct_main_menu(request, menu_items)


@hooks.register('construct_homepage_panels', order=10)
def register_dashboard_panels(request, panels):
    dashboard.construct_panels(request, panels)


@hooks.register('construct_homepage_summary_items', order=10)
def register_dashboard_summary_items(request, summary_items):
    dashboard.construct_summary_items(request, summary_items)


@hooks.register('construct_homepage_summary_items', order=10)
def register_dashboard_summary_items(request, summary_items):
    dashboard.construct_summary_items(request, summary_items)
