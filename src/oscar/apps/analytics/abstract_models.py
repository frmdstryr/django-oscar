import uuid
import logging
import socket

from decimal import Decimal

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from django.contrib.postgres.fields import JSONField

from oscar.core.compat import AUTH_USER_MODEL
from oscar.core.loading import get_class



try:
    from django.contrib.gis.geoip2 import (
        HAS_GEOIP2 as HAS_GEOIP,
        GeoIP2 as GeoIP,
        GeoIP2Exception as GeoIPException,
    )
except ImportError:
    HAS_GEOIP = False

try:
    from ua_parser import user_agent_parser
    HAS_UAPARSER = True
except ImportError:
    HAS_UAPARSER = False


log = logging.getLogger('django')

GEOIP_CACHE_TYPE = settings.GEOIP_CACHE_TYPE
PageViewManager = get_class('analytics.managers', 'PageViewManager')
VisitorManager = get_class('analytics.managers', 'VisitorManager')


class AbstractPageView(models.Model):
    """ Taken directly from django-tracking2

    """
    visitor = models.ForeignKey(
        'analytics.Visitor',
        related_name='pageviews',
        on_delete=models.CASCADE,
    )
    url = models.TextField(null=False, editable=False)
    referer = models.TextField(null=True, editable=False)
    query_string = models.TextField(null=True, editable=False)
    method = models.CharField(max_length=20, null=True)
    view_time = models.DateTimeField()

    objects = PageViewManager()

    class Meta:
        abstract = True
        app_label = 'analytics'
        ordering = ('-view_time',)


class AbstractProductRecord(models.Model):
    """
    A record of a how popular a product is.

    This used be auto-merchandising to display the most popular
    products.
    """

    product = models.OneToOneField(
        'catalogue.Product', verbose_name=_("Product"),
        related_name='stats', on_delete=models.CASCADE)

    # Data used for generating a score
    num_views = models.PositiveIntegerField(_('Views'), default=0)
    num_basket_additions = models.PositiveIntegerField(
        _('Basket Additions'), default=0)
    num_purchases = models.PositiveIntegerField(
        _('Purchases'), default=0, db_index=True)

    # Product score - used within search
    score = models.FloatField(_('Score'), default=0.00)

    class Meta:
        abstract = True
        app_label = 'analytics'
        ordering = ['-num_purchases']
        verbose_name = _('Product record')
        verbose_name_plural = _('Product records')

    def __str__(self):
        return _("Record for '%s'") % self.product


class AbstractUserRecord(models.Model):
    """
    A record of a user's activity.
    """

    user = models.OneToOneField(AUTH_USER_MODEL, verbose_name=_("User"),
                                on_delete=models.CASCADE)

    # Browsing stats
    num_product_views = models.PositiveIntegerField(
        _('Product Views'), default=0)
    num_basket_additions = models.PositiveIntegerField(
        _('Basket Additions'), default=0)

    # Order stats
    num_orders = models.PositiveIntegerField(
        _('Orders'), default=0, db_index=True)
    num_order_lines = models.PositiveIntegerField(
        _('Order Lines'), default=0, db_index=True)
    num_order_items = models.PositiveIntegerField(
        _('Order Items'), default=0, db_index=True)
    total_spent = models.DecimalField(_('Total Spent'), decimal_places=2,
                                      max_digits=12, default=Decimal('0.00'))
    date_last_order = models.DateTimeField(
        _('Last Order Date'), blank=True, null=True)

    class Meta:
        abstract = True
        app_label = 'analytics'
        verbose_name = _('User record')
        verbose_name_plural = _('User records')


class AbstractUserProductView(models.Model):

    user = models.ForeignKey(
        AUTH_USER_MODEL, verbose_name=_("User"),
        on_delete=models.CASCADE)
    product = models.ForeignKey(
        'catalogue.Product',
        on_delete=models.CASCADE,
        verbose_name=_("Product"))
    date_created = models.DateTimeField(_("Date Created"), auto_now_add=True)

    class Meta:
        abstract = True
        app_label = 'analytics'
        verbose_name = _('User product view')
        verbose_name_plural = _('User product views')

    def __str__(self):
        return _("%(user)s viewed '%(product)s'") % {
            'user': self.user, 'product': self.product}


class AbstractUserSearch(models.Model):

    user = models.ForeignKey(
        AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,  # Allow anonymous searches
        verbose_name=_("User"))
    query = models.CharField(_("Search term"), max_length=255, db_index=True)
    date_created = models.DateTimeField(_("Date Created"), auto_now_add=True)
    result_count = models.PositiveIntegerField(default=0)

    class Meta:
        abstract = True
        app_label = 'analytics'
        verbose_name = _("User search query")
        verbose_name_plural = _("User search queries")

    def __str__(self):
        return _("%(user)s searched for '%(query)s'") % {
            'user': self.user,
            'query': self.query}


class AbstractVisitor(models.Model):
    """ Taken directly from django-tracking2

    """
    # Unique session
    session_key = models.CharField(max_length=40, primary_key=True)

    # The visitor
    identity = models.UUIDField(default=uuid.uuid4, editable=False)

    # User
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='visit_history',
        null=True,
        editable=False,
        on_delete=models.CASCADE,
    )
    # Update to GenericIPAddress in Django 1.4
    ip_address = models.GenericIPAddressField(editable=False)
    user_agent = models.TextField(null=True, editable=False)
    start_time = models.DateTimeField(default=timezone.now, editable=False)
    expiry_age = models.IntegerField(null=True, editable=False)
    expiry_time = models.DateTimeField(null=True, editable=False)
    time_on_site = models.IntegerField(null=True, editable=False)
    end_time = models.DateTimeField(null=True, editable=False)
    hostname = models.CharField(max_length=256, default="")
    is_bot = models.BooleanField(default=False)
    data = JSONField(null=True)

    objects = VisitorManager()

    # If the user agenet contains any of these consider it to be a bot
    bot_patterns = getattr(
        settings, 'OSCAR_USER_AGENT_BOT_PATTERNS',
        ('bot', 'python', 'headless', 'crawl', 'spider', 'facebook'))

    def session_expired(self):
        """The session has ended due to session expiration."""
        if self.expiry_time:
            return self.expiry_time <= timezone.now()
        return False
    session_expired.boolean = True

    def session_ended(self):
        """The session has ended due to an explicit logout."""
        return bool(self.end_time)
    session_ended.boolean = True

    def save(self, *args, **kwargs):
        """ Load data when created """
        if not self.data:
            data = self.ua_data or {}
            data['geo'] = self.geoip_data or {}
            self.data = data
            self.is_bot = self.detect_bot()

        super().save(*args, **kwargs)

    @cached_property
    def geoip_data(self):
        """Attempt to retrieve MaxMind GeoIP data based on visitor's IP."""
        if not HAS_GEOIP or not settings.TRACK_USING_GEOIP:
            return
        try:
            gip = GeoIP(cache=GEOIP_CACHE_TYPE)
            return gip.city(self.ip_address)
        except Exception:
            msg = 'Error getting GeoIP data for IP "{0}"'.format(
                self.ip_address)
            log.debug(msg)

    @cached_property
    def ua_data(self):
        if not HAS_UAPARSER or not self.user_agent:
            return
        try:
            ua_data = user_agent_parser.Parse(self.user_agent)
            return ua_data
        except Exception:
            msg = 'Error parsing UA string "%s"' % self.user_agent
            log.debug(msg)

    def detect_bot(self):
        """ Attempt to determine if this visitor is a bot """
        if self.user_agent is None:
            return True
        user_agent = self.user_agent.lower()
        for pattern in self.bot_patterns:
            if pattern in user_agent:
                return True
        return False

    def reverse_lookup(self):
        if not self.hostname:
            try:
                fqdn, _, _ = socket.gethostbyaddr(self.ip_address)
                self.hostname = fqdn
                self.is_bot = self.detect_bot()
                self.save()
            except Exception as e:
                pass
        return self.hostname


    class Meta:
        abstract = True
        app_label = 'analytics'
        ordering = ('-expiry_time',)
        permissions = (
            ('visitor_log', 'Can view visitor'),
        )
