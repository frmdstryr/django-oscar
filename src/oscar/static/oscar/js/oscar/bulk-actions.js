$(document).ready(function(){
    $('#changelist-actions').on('submit', function(e) {
        // On submit create a hidden input for each selection
        var form = $(this);
        form.remove('[name="selection"]');
        $('input.bulk-action:not(.select-all):checked').each(function(i, e){
            var input = $('<input type="hidden" name="selection" />');
            input.val($(this).parents('tr').data('object-pk'));
            form.append(input);
        })
    });

    // Select all control
    $('input.bulk-action.select-all').on('change', function(e) {
        $('input.bulk-action').prop('checked', this.checked);
    });
});
