<%namespace name="paginator" file="_paginator.mako"/>

% if children.items:
    <table class="table-admin">
        <thead>
            <th class="tight input table-admin-no-border"></th>
            <th>Name</th>
            <th>Created</th>
            <th>Creator</th>
            <th class="tight"></th>
        </thead>
        <tbody>
            % for child in children.items:
                <tr>
                    <td class="tight input table-admin-no-border">
                        <input type="checkbox"
                            id="inlineCheckbox1"
                            value="option1">
                    </td>
                    <td><a href="${req.y_url(child, parent=req.context)}">${child.name}</td>
                    <td class="tight">03/01/2013 12:12</td>
                    <td class="tight">Ole Morten Halvorsen</td>
                    <td class="tight table-admin-right">
                        <a class="action" href="${req.y_url(child, 'edit', parent=req.context, back=req.path_qs)}">
                            Edit
                        </a>
                    </td>
                </tr>
            % endfor
        </tbody>
    </table>

    ${paginator.paginate(children, classes=['pagination-right', 'paginator-attached'])}

% else:
    <p class="muted">No sub items</p>
% endif
