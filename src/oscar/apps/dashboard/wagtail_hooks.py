import os
import logging
from glob import glob
from django.conf import settings
from oscar.core.loading import get_class
from wagtail.core import hooks

log = logging.getLogger('oscar')

# Register site
DashboardSite = get_class('dashboard.admin', 'DashboardSite')
dashboard = DashboardSite()
dashboard.register()


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


@hooks.register('register_icons')
def register_icons(icons):
    for icon_dir in dashboard.icon_dirs:
        results = []
        for template_config in settings.TEMPLATES:
            for template_dir in template_config.get('DIRS', []):
                pattern = os.path.join(template_dir, icon_dir, '*.svg')
                log.debug(f"Searching for icons in {pattern}")
                results.extend(glob(pattern))
        if not results:
            log.warning(f"No icons found in {icon_dir}")
            continue
        results = list(set(results))
        log.debug(f"Found {len(results)} icons in {icon_dir}")
        icons.extend(results)
    return icons
