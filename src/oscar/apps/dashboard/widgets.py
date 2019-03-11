import copy
import re

from django.forms import Widget, MultipleHiddenInput, Textarea
from django.urls import reverse


class BulkActionHiddenInput(MultipleHiddenInput):
    """ Adds a script that will pull the selected checkboxes from the IndexView
    result list and append them to the bulk edit form list.

    """
    class Media:
        js = [
            'oscar/js/oscar/bulk-actions.js',
        ]


class AceEditorWidget(Textarea):
    def __init__(self, attrs=None):
        # Use slightly better defaults than HTML's 20x2 box
        default_attrs = {'class': 'ace-editor'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)

    class Media:
        js = [
            'oscar/js/ace/ace.js',
            'oscar/js/ace/ace-init.js',
        ]
