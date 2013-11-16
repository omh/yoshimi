<%page args="queue, css_class='error'"/>

% for msg in req.session.pop_flash(queue):
    <div class="container-fluid"><div class="row-fluid"><div class="span12">
    <div class="alert alert-block alert-${css_class}">
        <button type="button" class="close" data-dismiss="alert">&times;</button>
        <p>${msg}</p>
    </div>
    </div></div></div>
% endfor
