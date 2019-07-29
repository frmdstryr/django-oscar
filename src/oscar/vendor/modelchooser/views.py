import re
from django.core import signing
from django.core.paginator import Paginator
from django.apps import apps
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.http import Http404
from django.shortcuts import render
from wagtail.admin.edit_handlers import BaseChooserPanel
from wagtail.admin.modal_workflow import render_modal_workflow
from wagtail.search.index import Indexed



from . import registry


@login_required
def chooser(request, signed_data):
    try:
        # Load the data generated by the panel
        # This contains the id of the panel used to retrieve it
        data = signing.loads(signed_data)
        chooser = registry.choosers[data['chooser_id']]
        model = apps.get_model(data['app_label'], data['model_name'])

        # Edit handlers need to be bound first
        if isinstance(chooser, BaseChooserPanel):
            panel = chooser
            panel = panel.bind_to(model=model, request=request)
            panel.generic_name = data['generic_name']

            if panel.generic_name:
                ct_pk = request.GET.get('content_type')
                panel.content_type = ContentType.objects.get_for_id(int(ct_pk))

            instance = panel.get_instance(request, data)
            Form = panel.get_form_class()

            chooser = panel.bind_to(instance=instance,
                                    form=Form(instance=instance))


    except (LookupError, ValueError, KeyError, signing.BadSignature) as e:
        print(e)
        raise Http404

    # If content types are used, lookup the selected content type
    model = chooser.target_model
    if not model:
        raise LookupError("Invalid model")

    # Now get the queryset
    qs = chooser.get_queryset(request)

    search_term = request.GET.get('q')
    is_searchable = bool(chooser.search_fields) or isinstance(model, Indexed)
    is_searching = is_searchable and search_term

    if is_searching:
        if isinstance(model, Indexed):
            qs = qs.search(search_term)
        else:
            qs, use_distinct = chooser.get_search_results(
                request, qs, search_term)
            if use_distinct:
                qs = qs.distinct()

    paginator = Paginator(qs, per_page=10)
    page = paginator.get_page(request.GET.get('p'))
    ajax = 'ajax' in request.GET
    context = {
        'chooser': chooser,
        'chooser_url': request.path,
        'opts': model._meta,
        'paginator': paginator,
        'page': page,
        'object_list': page.object_list,
        'is_searchable': is_searchable,
        'is_searching': is_searching,
    }

    if ajax:
        return render(request, chooser.results_template, context)

    js_data = {'step': 'initModal'}
    return render_modal_workflow(
        request, chooser.modal_template, None, context, js_data)