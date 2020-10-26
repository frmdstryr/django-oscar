import json
from textwrap import dedent
from datetime import timedelta
from decimal import Decimal as D
from decimal import ROUND_UP

from django.contrib import messages
from django.db.models import Avg, Count, Sum
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


from django.utils.html import format_html
from oscar.core.compat import get_user_model
from oscar.core.loading import get_class, get_model

from wagtail.admin.site_summary import SummaryItem

Partner = get_model('partner', 'Partner')
Product = get_model('catalogue', 'Product')
Order = get_model('order', 'Order')
Line = get_model('order', 'Line')
User = get_user_model()
UserSearch = get_model('analytics', 'UserSearch')

CustomerAdmin = get_class('dashboard.customers.admin', 'CustomerAdmin')
OrderAdmin = get_class('dashboard.orders.admin', 'OrderAdmin')
ProductAdmin = get_class('dashboard.catalogue.admin', 'ProductAdmin')


class DashboardPanel:
    order = 1000
    template = 'oscar/dashboard/partials/dashboard_list.html'
    title = None
    classnames = 'col12'


    def __init__(self, request):
        self.request = request

    def render(self):
        ctx = self.get_context()
        return render_to_string(self.template, ctx, request=self.request)

    def get_context(self):
        return {
            'title': self.title,
            'classnames': self.classnames,
        }


class DashboardList(DashboardPanel):
    limit = 5
    headings = []

    def get_queryset(self):
        return []

    def get_context(self):
        ctx = super().get_context()
        queryset = self.get_queryset()[0:self.limit]
        ctx.update({
            'headings': self.headings,
            'data': [self.result_row(result) for result in queryset],
        })
        return ctx

    def result_row(self, result):
        return []


class DashboardSummaryItem(SummaryItem):
    model_admin = None
    template = 'oscar/dashboard/partials/dashboard_summary_item.html'

    def get_queryset(self):
        return self.model_admin.get_queryset(self.request)

    def get_context(self):
        return {
            'total_count': self.get_queryset().count(),
            'icon': self.model_admin.menu_icon,
            'title': self.model_admin.menu_label,
            'url': self.model_admin.get_action_url('index')
        }


class OrdersMixin:
    model_admin = OrderAdmin.instance()

    def get_queryset(self):
        return self.model_admin.get_queryset(self.request)

    def render_order_total(self, order):
        return format_html('<span class="price">{} {}</span>',
                           order.currency, order.total_incl_tax)

    def render_order_link(self, order):
        url = self.model_admin.get_action_url('inspect', instance_pk=order.pk)
        return format_html('<a href="{}">{}</a>', url, order)


class RecentOrdersChart(OrdersMixin, DashboardPanel):
    order = 300
    template = 'oscar/dashboard/partials/dashboard_chart.html'
    classnames = 'col8'
    title = _('Recent Orders')

    def get_context(self):
        ctx = super().get_context()
        orders = self.get_queryset()
        ctx.update(self.get_chart_data(orders))
        return ctx

    def get_chart_data(self, orders, segments=14):
        """
        Get report of order revenue split up in hourly chunks. A report is
        generated for the last *hours* (default=24) from the current time.
        The report provides ``max_revenue`` of the hourly order revenue sum,
        ``y-range`` as the labeling for the y-axis in a template and
        ``order_total_hourly``, a list of properties for hourly chunks.
        *segments* defines the number of labeling segments used for the y-axis
        when generating the y-axis labels (default=10).
        """
        time_now = timezone.now().replace(minute=0, second=0)
        start_time = time_now - timedelta(days=segments)

        order_total_daily = []
        for i in range(0, segments):
            end_time = start_time + timedelta(days=1)
            daily_orders = orders.filter(date_placed__gte=start_time,
                                          date_placed__lt=end_time)
            total = daily_orders.aggregate(
                Sum('total_incl_tax'))['total_incl_tax__sum'] or D('0.0')
            order_total_daily.append({
                'end_time': end_time,
                'total_incl_tax': total,
                #'count': daily_orders.count(),
            })
            start_time = end_time

        max_value = max([x['total_incl_tax'] for x in order_total_daily])
        divisor = 1
        while divisor < max_value / 50:
            divisor *= 10
        max_value = (max_value / divisor).quantize(D('1'), rounding=ROUND_UP)
        max_value *= divisor
        if max_value:
            segment_size = (max_value) / D('100.0')
            for item in order_total_daily:
                item['percentage'] = int(item['total_incl_tax'] / segment_size)

            y_range = []
            y_axis_steps = max_value / D(str(segments))
            for idx in reversed(range(segments + 1)):
                y_range.append(idx * y_axis_steps)
        else:
            y_range = []
            for item in order_total_daily:
                item['percentage'] = 0
        data = {
            'labels': [d['end_time'].strftime("%b %d") for d in order_total_daily],
            'datasets': [
                {
                    'label': 'Order Totals',
                    'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                    'borderColor': 'rgba(75, 192, 192, 1)',
                    'borderWidth': 1,
                    'data': [float(d['total_incl_tax']) for d in order_total_daily],
                },
                #{
                    #'label': 'Number of Orders',
                    #'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                    #'borderColor': 'rgb(75, 192, 192)',
                    #'borderWidth': 1,
                    #'data': [d['count'] for d in order_total_daily],
                #}
            ]
        }

        # Chart.js
        chart = {
            'type': 'bar',
            'data': data,
            'options': {
                'scales': {
                    'yAxes': [{
                        'ticks': {
                            'beginAtZero': True
                        }
                    }],
                    #'xAxes': [{
                        #'type': 'time',
                        #'time': {
                            #'unit': 'day'
                        #}
                    #}]
                }
            },
        }
        return {'chart': json.dumps(chart)}


class LastOrdersList(OrdersMixin, DashboardList):
    order = 300
    classnames = 'col4'
    title = _('Latest Orders')
    headings = (_('Customer'), _('Items'), _('Total'), _('Order'))

    def result_row(self, order):
        return (
            order.shipping_address.name,
            order.num_items,
            self.render_order_total(order),
            self.render_order_link(order)
        )



class LastSearchTermsList(DashboardList):
    order = 350
    classnames = 'col4'
    title = _('Latest Search Terms')
    headings = (_('Search Term'), _('Uses'))

    def get_queryset(self):
        # This is not working as intended...
        return UserSearch.objects.exclude(query="").values('query').annotate(
            uses=Count('query')).order_by('-date_created')

    def result_row(self, search):
        return (search['query'], search['uses'])


class TopSearchTermsList(LastSearchTermsList):
    order = 340
    title = _('Top Search Terms')

    def get_queryset(self):
        return UserSearch.objects.exclude(query="").values('query').annotate(
            uses=Count('query')).order_by('-uses')


class OrdersSummaryItem(DashboardSummaryItem):
    model_admin = OrderAdmin.instance()


class ProductsSummaryItem(DashboardSummaryItem):
    model_admin = ProductAdmin.instance()


class CustomersSummaryItem(DashboardSummaryItem):
    model_admin = CustomerAdmin.instance()
