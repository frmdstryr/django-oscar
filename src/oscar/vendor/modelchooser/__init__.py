import operator
from functools import reduce
from django.db import models
from django.contrib.admin.utils import lookup_needs_distinct


class Registry:
    choosers = {}


class ModelChooserMixin:
    """ This is the api used by the chooser view and widget

    """

    # Change the modal chooser template
    chooser_template = None
    modal_template = 'wagtailmodelchooser/modal.html'
    results_template = 'wagtailmodelchooser/results.html'

    # Use this to change how each choice in the result list and the selected
    # value is displayed
    choice_template = 'wagtailmodelchooser/choice.html'

    # Key used to store this chooser in the registry
    chooser_id = None

    # Fields to search
    search_fields = []

    # Fields to display
    display_fields = ['__repr__']

    # Queryset filters
    default_filters = {}

    def get_chooser_id(self):
        raise NotImplementedError

    def get_queryset(self, request):
        """ Get the queryset for the chooser. Override this as necessary.

        `model` is the  original model this panel was bound to and
        `target_model` is the model of the field being chosen.

        """
        qs = self.target_model._default_manager.all()
        if self.default_filters:
            qs = qs.filter(**self.default_filters)
        return qs

    def get_search_results(self, request, queryset, search_term):
        """ This is pulled from the modeladmin IndexView
        """
        use_distinct = False
        opts = self.target_model._meta
        if self.search_fields and search_term:
            orm_lookups = ['%s__icontains' % str(search_field)
                           for search_field in self.search_fields]
            for bit in search_term.split():
                or_queries = [models.Q(**{orm_lookup: bit})
                              for orm_lookup in orm_lookups]
                queryset = queryset.filter(reduce(operator.or_, or_queries))
            if not use_distinct:
                for search_spec in orm_lookups:
                    if lookup_needs_distinct(opts, search_spec):
                        use_distinct = True
                        break

        return queryset, use_distinct


registry = Registry()
