<%namespace name="lineage" file="_lineage.mako"/>
<%namespace name="paginator" file="_paginator.mako"/>

<div class="controls browse-search">
    <input type="text"
           class="search-query small-search-query input-small"
           placeholder="Search...">
</div>

<div class="clearfix">
    ${lineage.list(req.context.lineage, url_func=browse_url, classes=['pull-left'])}
</div>

% if children.items:
    <table class="table-admin">
        <thead>
            <th class="tight input"></th>
            <th>Name</th>
            <th>Created</th>
        </thead>
        <tbody>
        % for child in children.items:
            <tr>
                <td class="tight input">
                    <input type="${policy.selection_input_type}" 
                           name="parent_location_id"
                           % if not policy.can_select(child.location_for_parent(req.context)):
                               disabled="disabled"
                           % endif
                           value="${child.location_for_parent(req.context).id}">
                </td>
                <td>
                    % if policy.can_select(child.location_for_parent(req.context)):
                        <a href="${browse_url(child, parent=req.context)}">${child.name}</a>
                    % else:
                        ${child.name}
                    % endif
                </td>
                <td class="tight">03/01/2013 12:12</td>
            </tr>
        % endfor
        </tbody>
    </table>
    % if children.pages > 1:
        ${paginator.paginate(children, url_func=browse_url, classes=['pagination-small', 'pagination-right', 'paginator-attached'])}
    % endif
% else:
    <p class="muted">No sub items</p>
% endif
