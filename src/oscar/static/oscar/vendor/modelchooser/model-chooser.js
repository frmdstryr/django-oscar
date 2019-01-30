/**
 * Adapted from wagtailmodelchooser by Copyright (c) 2014, Tim Heap
 * and updated to support InlinePanels and various other changes by
 * Jairus Martin in 2019.
 *
 * See original license under oscar/vendors/modeladmin
 */
function initModalChooser(modal) {

    /**
     * Attach event handlers to the links
     */
    function ajaxifyLinks(context) {
        $('a.model-choice', modal.body).click(function(e) {
            e.preventDefault();
            var instance = $(this);
            modal.respond('instanceChosen', {
                'html': instance.html(),
                'pk': instance.data('pk'),
            });
            modal.close();
        });

        $('.pagination a', context).click(function(e) {
            e.preventDefault();
            var page = this.getAttribute('data-page');
            setPage(page);
        });
    }

    ajaxifyLinks(modal.body);

    /**
     * Search the list
     */
    var searchForm = modal.body.find('form.search-bar');
    var searchField = searchForm.find('#id_q');
    var searchUrl = searchForm.attr('action');
    var searchResults = modal.body.find('#search-results');
    function search() {
        loadResults(searchField.val())
    }

    searchForm.submit(search);
    var searchFieldChange = function(e) {
        clearTimeout($.data(this, 'timer'));
        var wait = setTimeout(search, 100);
        $(this).data('timer', wait);
    }
    searchForm.on('input', searchFieldChange);
    searchForm.on('change', searchFieldChange);
    searchForm.on('keyup', searchFieldChange);

    /**
     * Load page number ``page`` of the results.
     */
    function setPage(page) {
        loadResults(searchField.val(), page)
    }

    /**
     * Actually do the work
     */
    function loadResults(searchTerm, page) {
        var dataObj = {ajax: 1}
        if (window.instance) dataObj['instance'] = window.instance;
        if (searchTerm) dataObj['q'] = searchTerm;
        if (page) dataObj['p'] = page;

        $.ajax({
            url: searchUrl,
            data: dataObj,
            success: function(data, status) {
                console.log(data, status);
                searchResults.html(data);
                ajaxifyLinks(searchResults);
            },
            error: function(e) {
                addMessage('error', 'Could not load results');
            }
        });
    }
}

/**
 * The original design didn't handle inline panels or custom views, this does
 */
$(document).ready(function() {
    $(document).on('click', '.model-chooser .action-choose', function() {
        var chooser = $(this).closest('.model-chooser');
        var choice = chooser.find('.chosen-item');
        var input = $('#'+chooser.data('field-id'));
        var contentTypeId = chooser.data('content-type-field-id');
        var url = chooser.data('url');

        // If a content type is required send it
        if (contentTypeId) {
            var ct = $('#'+contentTypeId).val();
            if (!ct) {
                addMessage('warning', 'Please select a content type first');
                return;
            }
            url += "?"+$.param({'content_type': ct});
        }
        var modal = ModalWorkflow({
            url: url,
            responses: {
                instanceChosen: function(instanceData) {
                    input.val(instanceData.pk);
                    choice.html(instanceData.html);
                    chooser.removeClass('blank');
                }
            },
            onload: {
                initModal: function() {
                    initModalChooser(modal);
                }
            }
        });
        modal.body.on("submit", "form", function (e) { e.preventDefault(); });
    });

    $(document).on('click', '.model-chooser .action-clear', function() {
        var chooser = $(this).closest('.model-chooser');
        var input = $('#'+chooser.data('field-id'));
        input.val('');
        chooser.addClass('blank');
    });
});
