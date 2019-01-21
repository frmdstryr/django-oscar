# flake8: noqa, because URL syntax is more readable with long lines

from django.conf import settings
from django.conf.urls import include, url
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import SetPasswordForm
from django.urls import reverse_lazy

from oscar.core.application import Application
from oscar.core.loading import get_class
from oscar.views.decorators import login_forbidden


import wagtail.admin.urls
import wagtail.core.urls
import wagtail.documents.urls

from wagtailautocomplete.urls.admin import urlpatterns as autocomplete_admin_urls


class Shop(Application):
    name = None

    catalogue_app = get_class('catalogue.app', 'application')
    customer_app = get_class('customer.app', 'application')
    basket_app = get_class('basket.app', 'application')
    checkout_app = get_class('checkout.app', 'application')
    promotions_app = get_class('promotions.app', 'application')
    search_app = get_class('search.app', 'application')
    #dashboard_app = get_class('dashboard.app', 'application')
    offer_app = get_class('offer.app', 'application')

    password_reset_form = get_class('customer.forms', 'PasswordResetForm')
    set_password_form = SetPasswordForm

    def get_urls(self):
        urls = [
            url(r'^dashboard/', include(wagtail.admin.urls)),
            url(r'^documents/', include(wagtail.documents.urls)),
            url(r'^catalogue/', self.catalogue_app.urls),
            url(r'^basket/', self.basket_app.urls),
            url(r'^checkout/', self.checkout_app.urls),
            url(r'^accounts/', self.customer_app.urls),
            url(r'^search/', self.search_app.urls),
            #url(r'^dashboard/', self.dashboard_app.urls),
            url(r'^offers/', self.offer_app.urls),

            # Password reset - as we're using Django's default view functions,
            # we can't namespace these urls as that prevents
            # the reverse function from working.
            url(r'^password-reset/$',
                login_forbidden(
                    auth_views.PasswordResetView.as_view(
                        form_class=self.password_reset_form,
                        success_url=reverse_lazy('password-reset-done')
                    )
                ),
                name='password-reset'),
            url(r'^password-reset/done/$',
                login_forbidden(auth_views.PasswordResetDoneView.as_view()),
                name='password-reset-done'),
            url(r'^password-reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$',
                login_forbidden(
                    auth_views.PasswordResetConfirmView.as_view(
                        form_class=self.set_password_form,
                        success_url=reverse_lazy('password-reset-complete')
                    )
                ),
                name='password-reset-confirm'),
            url(r'^password-reset/complete/$',
                login_forbidden(auth_views.PasswordResetCompleteView.as_view()),
                name='password-reset-complete'),

            url(r'^admin/autocomplete/', include(autocomplete_admin_urls)),

            url(r'', include(wagtail.core.urls)),
        ]

        if settings.DEBUG:
            import debug_toolbar
            urls.insert(-2, url(r'^__debug__/', include(debug_toolbar.urls)))

        if settings.OSCAR_PROMOTIONS_ENABLED:
            urls.insert(-2, url(r'', self.promotions_app.urls))
        return urls

application = Shop()
