from wagtail.core import hooks

from .urls import urlpatterns


@hooks.register('register_admin_urls')
def register_model_chooser_admin_urls():
    return urlpatterns

