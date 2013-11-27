% for l in req.context.content.locations:
<ul class="breadcrumb location-widget">
    <li>
        <input type="radio" name="main_location" value="1">
    </li>
    % for a in l.ancestors().all():
        <li % if a == req.context: class="active" % endif>
            % if a == req.context:
                ${a.content.slug}
            % else:
                <a href="${req.y_path(a)}">${a.content.slug}</a>
            % endif
            % if not loop.last:
                <span class="divider">/</span>
            % endif
        </li>
    % endfor
</ul>
% endfor
