$(document).ready(function() {
    $('.course-shifts-update-deadlines').click(function() {
        var self = this;
        if (window.confirm($(this).data('question'))) {
            $(this).addClass('disabled');
            $.ajax({
                type: 'POST',
                url: $(this).data('action-url'),
                success: function(response) {
                    if (response.success) {
                        alert(response.msg);
                        window.location.reload();
                    } else {
                        $(self).removeClass('disabled');
                        alert(response.errorMessage);
                    }
                }
            });
        }
    });
});
