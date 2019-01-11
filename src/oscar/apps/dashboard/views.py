from django.utils.translation import ugettext as _

from wagtail.contrib.modeladmin.views import InspectView


class DetailView(InspectView):
    """ Changes "Inspect" to "View"

    """
    page_title = _('Viewing')

    def get_meta_title(self):
        return _('Viewing %s') % self.verbose_name
