<%def name="paginate(children, classes=None, url_func=None)">
<%
    if url_func is None:
        url_func = req.y_url
    if classes is None:
        classes=[]
%>
<%def name="button_class(page, children)">
    % if children.page == page:
        "active"
    % else:
        "ellipsis disabled"
    % endif
</%def>
<ul class="pure-paginator paginator-attached paginator-right">
    % if children.has_prev:
        <li>
            <a class="paginator-item prev" href="${url_func(req.context, page=children.prev_num)}">
                «
            </a>
        </li>
    % else:
        <li class="disabled"><span class="paginator-item prev">«</span></li>
    % endif
    % for page in children.iter_pages():
        % if page:
            <li class="${button_class(page, children)}">
                % if children.page == page:
                    <span class="paginator-item">${page}</span>
                % else:
                    <a class="paginator-item" href="${url_func(req.context, page=page)}">${page}</a>
                % endif
            </li>
        % else:
            <li class="ellipsis disabled"><span class="paginator-item">&hellip;</span></li>
        % endif
    % endfor
    % if children.has_next:
        <li>
            <a class="paginator-item next" href="${url_func(req.context, page=children.next_num)}">
                »
            </a>
        </li>
    % else:
        <li class="disabled"><span class="paginator-item next" href="#">»</span></li>
    % endif
</ul>

</%def>
