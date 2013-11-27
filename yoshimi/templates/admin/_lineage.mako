<%def name="list(lineage, url_func=None, classes=None, mode=None)">
    <% 
        if classes is None:
            classes=[]
        if url_func is None:
            url_func = req.y_path
    %>
    <ul class="breadcrumb ${" ".join(classes)}">
    % for l in lineage:
        % if loop.first:
            <li>
                <a href="${url_func(l)}"><i class="icon-home"></i></a>
                % if not loop.last:
                    <span class="divider">/</span>
                % endif
            </li>
        % elif loop.last:
            <li class="active">${l.content.slug}</li>
        % else:
            <li>
                <a href="${url_func(l)}">
                    ${l.content.slug}
                </a>
                <span class="divider">/</span>
            </li>
        % endif
    % endfor
    </ul>
</%def>
