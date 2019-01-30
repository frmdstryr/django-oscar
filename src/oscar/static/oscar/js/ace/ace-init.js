$(document).ready(function(){
    $('textarea.ace-editor').each(function aceInit(i, e) {
        // Add a div before the textarea
        var textarea = $(e);

        var config = textarea.data('ace-config') || {
            mode: 'ace/mode/html',
            basePath: '/static/oscar/js/ace/',
            autoScrollEditorIntoView: true,
            maxLines: 30,
            minLines: 10
        };

        var div = $('<div>', {'class': 'form-control'}).insertBefore(textarea);
        var editor = ace.edit(div[0], config);

        // Sync all editor changes to the textarea
        editor.getSession().setValue(textarea.val());
        editor.getSession().on('change', function(){
            textarea.val(editor.getSession().getValue());
        });
        // Hide the textarea
        textarea.hide();
    });
});
