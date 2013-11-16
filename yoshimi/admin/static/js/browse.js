(function ( $ ) {
    $.fn.yMoveDialog = function() {
        setContent = function(url, node) {
            $.ajax(url).done(function(data) {
                node.find('.browse-container').unbind();
                node.find('.browse-container').html(data);
                node.find('.browse-container a').click(function(event) {
                    if (this.href.indexOf("#") > 0)
                        return false;
                    setContent(this.href, node);
                    return false;
                });
                node.find('button').click(function() {
                    $(this).button('loading');
                });
                
                /* Default button state is disabled */
                node.find('button').attr('disabled', 'disabled');
                /* Then enable button when clicking a input (radio/checkbox) */
                node.find('.input input').click(function() {
                    if ($(this).checked) {
                        node.find('button').attr('disabled', 'disabled');
                    } else {
                        node.find('button').removeAttr('disabled');
                    }
                });
            });

            /* Reposition the arrow */
            var pos = $(node).position().top - $(node).find('.popover').position().top;
            pos += ($(node).height() / 2) - 1; /* Center the arrow on the click target */
            $(node).find('.arrow').css({top: pos});
        };

        var visible = false;
        this.click(function(event) {
            $(this).popover('toggle')
            visible = visible ? false : true;
            if (visible)
                setContent(this.href, $(this).parent());

            return false;
        });
        return this;
    };
}( jQuery ));

(function () {
    $('[data-dialog="move"]').yMoveDialog().popover({
        'html': true,
        'placement': 'left',
        'title': 'Choose a new location...',
        'trigger': 'manual',
        'content': function() {
            return $('#move-dialog').html()
        }
    })
})();
