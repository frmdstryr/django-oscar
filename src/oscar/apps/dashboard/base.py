from django.conf.urls import url
from django.utils.translation import ugettext as _
from django.core.exceptions import ImproperlyConfigured

from oscar.core.loading import get_class

from wagtail.contrib.modeladmin.helpers import (
    PermissionHelper, ButtonHelper, AdminURLHelper, PageAdminURLHelper,
    PagePermissionHelper
)
from wagtail.contrib.modeladmin.options import ModelAdmin, ModelAdminGroup

from .mixins import BulkActionsMixin, InlineEditableMixin


class DashboardURLHelper(AdminURLHelper):
    model_admin = None

    def _get_base_url(self, action):
        if action == 'inspect':
            action = 'details'
        ctx = dict(meta=self.opts, self=self, action=action, model=self.model)
        pattern = self.model_admin.get_dashboard_url().strip("/")
        if action != 'index':
            pattern += "/{action}"
        return pattern.format(**ctx)

    def _get_action_url_pattern(self, action):
        return r'^%s/$' % self._get_base_url(action)

    def _get_object_specific_action_url_pattern(self, action):
        return r'^%s/(?P<instance_pk>[-\w]+)/$' % self._get_base_url(action)

    def get_action_url_pattern(self, action, specific=None):
        if specific is None:
            return super().get_action_url_pattern(action)
        if specific is True:
            return self._get_object_specific_action_url_pattern(action)
        return self._get_action_url_pattern(action)

    def get_action_url(self, action, *args, **kwargs):
        if action not in self.model_admin.get_dashboard_views():
            return '#'
        return super().get_action_url(action, *args, **kwargs)


class DashboardButtonHelper(ButtonHelper):

    def inspect_button(self, *args, **kwargs):
        ctx = super().inspect_button(*args, **kwargs)
        ctx.update({
            'label': _('View'),
            'title': _('View this %s') % self.verbose_name,
        })
        return ctx


class DashboardPermissionHelper(PermissionHelper):

    def is_action_restricted(self, *actions):
        """ Check if the action(s) has been explicitly restricted from the
        modeladmin page.
        """
        restricted_actions = self.model_admin.restricted_actions
        for action in actions:
            if action in restricted_actions:
                return True
        return False

    def user_can_create(self, user):
        if self.is_action_restricted('create'):
            return False
        return super().user_can_create(user)

    def user_can_inspect_obj(self, user, obj):
        if self.is_action_restricted('inspect', 'view'):
            return False
        return super().user_can_inspect_obj(user, obj)

    def user_can_edit_obj(self, user, obj):
        if self.is_action_restricted('edit'):
            return False
        return super().user_can_edit_obj(user, obj)

    def user_can_delete_obj(self, user, obj):
        if self.is_action_restricted('delete'):
            return False
        return super().user_can_delete_obj(user, obj)


class DashboardAdmin(ModelAdmin, BulkActionsMixin, InlineEditableMixin):
    """ To add a new view create a method <action>_view and add it in
    the dashboard_views or instance_views list.

    """
    _instances = {}
    url_helper_class = DashboardURLHelper
    permission_helper_class = DashboardPermissionHelper
    button_helper_class = DashboardButtonHelper

    #: Use this for the admin to use a more friendly url
    #: the action will be appended by default but you can override
    #: get_url_helper_class if needed
    dashboard_url = '{meta.app_label}/{meta.model_name}'

    # List of action views that are created
    # It will look for '<view>_view'
    class_views = ['index', 'create']

    #: List of view types that require a url which accepts an instance_pk
    instance_views = ['edit', 'delete', 'inspect', 'inline']
    inspect_view_class = get_class('dashboard.views', 'DetailView')
    index_view_class = get_class('dashboard.views', 'IndexView')
    create_view_class = get_class('dashboard.views', 'CreateView')
    edit_view_class = get_class('dashboard.views', 'EditView')
    index_template_name = 'oscar/dashboard/index.html'

    #: Actions which are explicitly restricted from being performed on
    #: this model admin.
    restricted_actions = []

    #: Set during registration
    admin_site = None

    def __init__(self, parent=None):
        """ Create the dashboard admin and save an instance that can be
        used as a singleton to retrieve.

        """
        super().__init__(parent)
        self.permission_helper.model_admin = self
        self.url_helper.model_admin = self

        if DashboardAdmin._instances.get(self.__class__):
            name = self.__class__.__name__
            raise RuntimeError("Only one instance of %s can exist,"
                               "please use instance()" % name)

    def get_list_display(self, request):
        """ Add an selection checkbox to each row

        """
        list_display = self.list_display
        if self.get_bulk_actions():
            return ('action_checkbox',) + list_display
        return list_display

    def get_list_display_add_buttons(self, request):
        """
        Return the name of the field/method from list_display where action
        buttons should be added. Defaults to the first item from
        get_list_display()
        """
        if self.list_display_add_buttons:
            return self.list_display_add_buttons
        list_display = self.get_list_display(request)
        if list_display[0] == 'action_checkbox':
            return list_display[1]
        return list_display[0]

    @classmethod
    def instance(cls):
        """ In order to prevent different instances of the ModelAdmins from
        floating around use this method to get or create one.

        """
        if cls not in DashboardAdmin._instances:
            DashboardAdmin._instances[cls] = cls()
        return DashboardAdmin._instances[cls]

    def get_dashboard_url(self):
        """ Used by the url_helper to retrieve a friendly url for this
        model admin.
        """
        return self.dashboard_url

    def get_dashboard_views(self):
        views = list(set(self.class_views+self.instance_views))
        # To stay consistent with wagtail

        if self.inspect_view_enabled and 'inspect' not in views:
            views.append('inspect')

        if self.is_pagemodel and 'choose_parent' not in views:
            views.append('choose_parent')
        return views

    def get_action_view(self, action):
        """ Get a view for the given action name. By default it looks for
        the `<action>_view` of the DashboardAdmin class.
        """
        return getattr(self, '%s_view' % action)

    def get_action_url(self, action,  *args, **kwargs):
        """ Shortcut
        """
        return self.url_helper.get_action_url(action,  *args, **kwargs)

    def get_action_url_name(self, action,  *args, **kwargs):
        """ So admin classes can override the urls without needing to
        subclass the url_helper.
        """
        return self.url_helper.get_action_url_name(action,  *args, **kwargs)

    def get_action_url_pattern(self, action, *args, **kwargs):
        """ So admin classes can override the urls without needing to
        subclass the url_helper.
        """
        return self.url_helper.get_action_url_pattern(action, *args, **kwargs)

    def get_admin_urls_for_registration(self):
        """ Makes it easier to add and remove dashboard views. Wagtail
        requires this to return a tuple.
        """
        urls = []
        dashboard_views = self.get_dashboard_views()
        for action in dashboard_views:
            view = self.get_action_view(action)
            # Check if the view url requires an object instance pk
            is_specific = action in self.instance_views
            pattern = self.get_action_url_pattern(action, specific=is_specific)
            view_name = self.get_action_url_name(action)

            # Add url to the dashboard
            urls.append(url(pattern, view, name=view_name))
        return tuple(urls)

    def get_extra_class_names_for_field_col(self, result, field_name):
        """ Add a modal-edit class if this is in the editable list

        See wagtail's modeladmin_tags

        """
        classes = super().get_extra_class_names_for_field_col(
            result, field_name)
        if field_name in self.inline_editable_fields:
            classes.append('modal-editor')
        return classes

    def get_extra_attrs_for_field_col(self, result, field_name):
        """ Add a data-url class if this is in the editable list

        See wagtail's modeladmin_tags

        """
        attrs = super().get_extra_attrs_for_field_col(result, field_name)
        if field_name in self.inline_editable_fields:
            url = self.get_action_url('inline', result.pk)
            attrs['data-url'] = f'{url}?fields={field_name}'
        return attrs


class DashboardAdminGroup(ModelAdminGroup):
    """ Extends the base model admin to ensure that only a single instance
    of each admin exists and also supports nested groups by accepting a parent.

    """
    _instances = {}

    def __init__(self, parent=None):
        """ Register using instance to ensure only one exists """

        if DashboardAdminGroup._instances.get(self.__class__):
            name = self.__class__.__name__
            raise RuntimeError("Only one instance of %s can exist,"
                               "please use instance()" % name)

        self.parent = parent
        self.modeladmin_instances = []
        for ModelAdminClass in self.items:
            instance = ModelAdminClass.instance()
            instance.parent = self
            self.modeladmin_instances.append(instance)

    @classmethod
    def instance(cls):
        """ In order to prevent different instances of the ModelAdminGroups
        from floating around use this method to get or create one.

        """
        if cls not in DashboardAdminGroup._instances:
            DashboardAdminGroup._instances[cls] = cls()
        return DashboardAdminGroup._instances[cls]

    def get_menu_item(self, order=0):
        """ TODO: Nested submenus don't workk
        """
        return super().get_menu_item()

