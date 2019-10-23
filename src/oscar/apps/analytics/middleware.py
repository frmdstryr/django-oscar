import re
import warnings

from uuid import uuid4

from django.db import IntegrityError, transaction
from django.conf import settings
from django.core import signing
from django.core.exceptions import ValidationError
from django.core.validators import validate_ipv46_address
from django.utils import timezone
from django.utils.encoding import smart_text


from oscar.core.loading import get_model



TRACK_IGNORE_URLS = [re.compile(x) for x in settings.TRACK_IGNORE_URLS]
TRACK_IGNORE_USER_AGENTS = [
    re.compile(x, re.IGNORECASE) for x in settings.TRACK_IGNORE_USER_AGENTS
]


IP_HEADERS = (
    'HTTP_CLIENT_IP', 'HTTP_X_FORWARDED_FOR', 'HTTP_X_FORWARDED',
    'HTTP_X_CLUSTERED_CLIENT_IP', 'HTTP_FORWARDED_FOR', 'HTTP_FORWARDED',
    'REMOTE_ADDR'
)


Visitor = get_model('analytics', 'Visitor')
PageView = get_model('analytics', 'PageView')


def get_ip_address(request):
    for header in IP_HEADERS:
        if request.META.get(header, None):
            ip = request.META[header].split(',')[0]

            try:
                validate_ipv46_address(ip)
                return ip
            except ValidationError:
                pass


def total_seconds(delta):
    day_seconds = (delta.days * 24 * 3600) + delta.seconds
    return (delta.microseconds + day_seconds * 10**6) / 10**6


class VisitorTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return self.process_response(request, response)

    def get_tracking_cookie(self, request):
        """
        Returns the cookie name to use for storing a visitor cookie.

        The method serves as a useful hook in multi-site scenarios where
        different baskets might be needed.
        """
        try:
            signed_cookie = request.COOKIES.get(
                settings.TRACK_VISITOR_COOKIE_NAME, None)
            if signed_cookie is None:
                return {}
            data = signing.loads(
                signed_cookie,
                max_age=settings.TRACK_VISITOR_COOKIE_LIFETIME,
                salt='oscar.apps.analytics.middleware')
            return data
        except Exception as e:
            return {}

    def set_tracking_cookie(self, response, data):
        """ Set visitor tracking cookie data

        """
        response.set_cookie(
            settings.TRACK_VISITOR_COOKIE_NAME,
            signing.dumps(
                data,
                compress=True,
                salt='oscar.apps.analytics.middleware'),
            max_age=settings.TRACK_VISITOR_COOKIE_LIFETIME,
            secure=settings.TRACK_VISITOR_COOKIE_SECURE, httponly=True)


    def _should_track(self, user, request, response):
        # Session framework not installed, nothing to see here..
        if not hasattr(request, 'session'):
            msg = ('VisitorTrackingMiddleware installed without'
                   'SessionMiddleware')
            warnings.warn(msg, RuntimeWarning)
            return False

        # Do not track AJAX requests
        if request.is_ajax() and not settings.TRACK_AJAX_REQUESTS:
            return False

        # Do not track if HTTP HttpResponse status_code blacklisted
        if response.status_code in settings.TRACK_IGNORE_STATUS_CODES:
            return False

        # Do not tracking anonymous users if set
        if user is None and not settings.TRACK_ANONYMOUS_USERS:
            return False

        # Do not track superusers if set
        if user and user.is_superuser and not settings.TRACK_SUPERUSERS:
            return False

        # Do not track ignored urls
        path = request.path_info.lstrip('/')
        for url in TRACK_IGNORE_URLS:
            if url.match(path):
                return False

        # Do not track ignored user agents
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        for user_agent_pattern in TRACK_IGNORE_USER_AGENTS:
            if user_agent_pattern.match(user_agent):
                return False

        # everything says we should track this hit
        return True

    def _refresh_visitor(self, user, request, response, visit_time):

        # A Visitor row is unique by the tracking cookie's session key
        # if that is missing fallback to the session key
        tracking_cookie = self.get_tracking_cookie(request)
        visitor_id = tracking_cookie.get('id')
        session_key = tracking_cookie.get('sk', request.session.session_key)
        expired = tracking_cookie.get('exp', 0) - visit_time.timestamp() <= 0

        # Session is expired or never existed
        if expired or not session_key:
            request.session.save()
            session_key = request.session.session_key

        try:
            visitor = Visitor.objects.get(pk=session_key)
        except Visitor.DoesNotExist:
            # Log the ip address. Start time is managed via the field
            # `default` value
            ip_address = get_ip_address(request)
            visitor = Visitor(pk=session_key, ip_address=ip_address,
                              identity=visitor_id or uuid4())

        # Update the user field if the visitor user is not set. This
        # implies authentication has occured on this request and now
        # the user is object exists. Check using `user_id` to prevent
        # a database hit.
        if user and not visitor.user_id:
            visitor.user_id = user.id

        # update some session expiration details
        visitor.expiry_age = request.session.get_expiry_age()
        visitor.expiry_time = request.session.get_expiry_date()

        # grab the latest User-Agent and store it
        user_agent = request.META.get('HTTP_USER_AGENT', None)
        if user_agent:
            visitor.user_agent = smart_text(
                user_agent, encoding='latin-1', errors='ignore')

        time_on_site = 0
        if visitor.start_time:
            time_on_site = total_seconds(visit_time - visitor.start_time)
        visitor.time_on_site = int(time_on_site)

        # set the cookie
        self.set_tracking_cookie(response, {
            'id': str(visitor.identity),
            'exp': visitor.expiry_time.timestamp(),
            'sk': visitor.session_key
        })

        try:
            with transaction.atomic():
                visitor.save()
        except IntegrityError:
            # there is a small chance a second response has saved this
            # Visitor already and a second save() at the same time (having
            # failed to UPDATE anything) will attempt to INSERT the same
            # session key (pk) again causing an IntegrityError
            # If this happens we'll just grab the "winner" and use that!
            visitor = Visitor.objects.get(pk=session_key)

        return visitor

    def _add_pageview(self, visitor, request, view_time):
        referer = None
        query_string = None

        if settings.TRACK_REFERER:
            referer = request.META.get('HTTP_REFERER', None)

        if settings.TRACK_QUERY_STRING:
            query_string = request.META.get('QUERY_STRING')

        PageView.objects.create(
            visitor=visitor, url=request.path, view_time=view_time,
            method=request.method, referer=referer,
            query_string=query_string)

    def process_response(self, request, response):
        # If dealing with a non-authenticated user, we still should track the
        # session since if authentication happens, tTEST_COOKIE_NAMEhe `session_key` carries
        # over, thus having a more accurate start time of session
        user = getattr(request, 'user', None)
        if user and user.is_anonymous:
            # set AnonymousUsers to None for simplicity
            user = None

        # make sure this is a response we want to track
        if not self._should_track(user, request, response):
            return response

        # Be conservative with the determining time on site since simply
        # increasing the session timeout could greatly skew results. This
        # is the only time we can guarantee.
        now = timezone.now()

        # update/create the visitor object for this request
        visitor = self._refresh_visitor(user, request, response, now)

        if settings.TRACK_PAGEVIEWS:
            self._add_pageview(visitor, request, now)

        return response
