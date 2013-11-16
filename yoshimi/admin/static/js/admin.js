$(function() {
    //function strect(id) {
        //var maxHeight = 0;
        //$(id).each(function() {
            //maxHeight = Math.max(maxHeight, $(this).height());
        //});

        //var newHeight = maxHeight + ($(window).height() - $('body').height());
        //$(id).each(function() {
            //$(this).height(newHeight);
        //});
    //};

    //function adjust(outer, inner) {
        //$(outer).each(function() {
            //var childrenHeight = 0;
            //$(this).children().each(function() {
                //childrenHeight += $(this).height();
            //});
            //var gap = $(this).height() - childrenHeight;
            //var innerNode = $(this).find(inner);
            //innerNode.height(innerNode.height() + gap);
        //});
    //}

    //strect('.main-col');
    //adjust('.main-col', '.inner-col');
    //$(window).resize(function() {
        //strect('.main-col');
        //adjust('.main-col', '.inner-col');
    //});
    
    var openedIcon = '<i class="triangle-open" />';
    var closedIcon = '<i class="triangle-closed" />';

    var library_data = [
        { label: 'Content', children: [{label: 'test'}]},
        { label: 'Site Messages', children: [{label: 'test'}]},
        { label: 'Media', children: [{label: 'test'}]},
        { label: 'Users', children: [{label: 'test'}]}
    ];
    var recent_data = [
        { label: 'Today'},
        { label: 'Yesterday'},
        { label: 'This week'},
        { label: 'Last week'},
        { label: '2013', children: [{label: 'test'}]},
        { label: '2012', children: [{label: 'test'}]},
        { label: '2011', children: [{label: 'test'}]},
        { label: '2010', children: [{label: 'test'}]}
    ];
    var $library = $('.tree.library').tree({
        data: library_data,
        openedIcon: openedIcon,
        closedIcon: closedIcon
    });
    var $recent = $('.tree.recent').tree({
        data: recent_data,
        openedIcon: openedIcon,
        closedIcon: closedIcon,
        onCreateLi: function(node, $li) {
            if (node.header)
                $li.find('.jqtree-title').addClass('header');
        }
    });
});
