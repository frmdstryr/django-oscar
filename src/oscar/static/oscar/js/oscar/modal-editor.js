
/**
 * When a tag with class modal-editor is clicked popup the modal and load the
 * form given by the data-url.
 */
$(document).ready(function() {
    $(document).on('click', '.modal-editor', function(e) {
        let url = $(this).data('url');
        if (!url) {return false;}
        ModalWorkflow({
            url: url,
            responses: {},
            onload: {
                edit: function(modal, data){
                    if (data.message) {
                        addMessage('error', data.message);
                    }
                    $('form', modal.body).on('submit', function(e) {
                        modal.postForm(this.action, $(this).serialize());
                        return false;
                    });
                },
                done: function(modal, data) {
                    if (data.message) {
                        addMessage('success', data.message);
                    }
                    if (data.update) {
                        $('#'+data.update.id).html(data.update.html);
                    }
                    modal.close();
                }
            }
        });
    });
    return false;
});
