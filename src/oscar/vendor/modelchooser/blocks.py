from django.utils.functional import cached_property, lazy
from wagtail.core.blocks import ChooserBlock
from wagtail.core.utils import resolve_model_string

from . import registry, ModelChooserMixin
from .widgets import AdminModelChooser


class ModelChooserBlock(ChooserBlock, ModelChooserMixin):

    def __init__(self, target_model, search_fields=None, default_filters=None,
                 display_fields=None, **kwargs):
        super().__init__(**kwargs)
        self._target_model = target_model
        if search_fields is not None:
            self.search_fields = search_fields
        if default_filters is not None:
            self.default_filters = default_filters
        if display_fields is not None:
            self.display_fields = display_fields
        chooser_id = self.get_chooser_id()
        if chooser_id not in registry.choosers:
            registry.choosers[chooser_id] = self

    def get_chooser_id(self):
        """ Generate a key to use to store this chooser in the registry such
        that it is repeatable (if scaling to multiple processes) and is unique
        per panel within the application.
        """
        cls = self.__class__
        opts = self.target_model._meta
        return '.'.join((
            cls.__module__, cls.__name__, opts.app_label, opts.model_name))

    @cached_property
    def target_model(self):
        return self._target_model

    @cached_property
    def widget(self):
        target_model = self.target_model
        return AdminModelChooser(target_model, ctx={
            'chooser_id': self.get_chooser_id(),
            'app_label': target_model._meta.app_label,
            'model_name': target_model._meta.model_name,
        }, display_fields=self.display_fields)

    def deconstruct(self):
        name, args, kwargs = super(ModelChooserBlock, self).deconstruct()

        if args:
            args = args[1:]  # Remove the args target_model

        kwargs['target_model'] = self.target_model._meta.label_lower
        return name, args, kwargs

    class Meta:
        icon = "placeholder"
