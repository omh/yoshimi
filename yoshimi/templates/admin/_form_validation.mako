<div class="alert alert-validation alert-error">
    <h3 class="alert-header">Unable not save your changes</h3>
    <p>Seems like there was an issue saving your changes. Please review the below issues and try again.</p>
    <ul>
        % for field_name, field_errors in form.errors.items():
            % if field_errors:
                % for error in field_errors:
                    <li>${form[field_name].label} — ${error}
                        % if field_name == "cp_token":
                            <p>To resolve this you must reload this page to bring in the latest content.  <span class="label label-warning">Warning</span> <strong>Reloading will cause any changes you have made to be lost.</strong>
                            </p>
                            <p>
                                <a href="" class="btn btn-small btn-warning">
                                    Click to reload this page with the latest content.
                                </a>
                            </p>
                        % endif
                    </li>
                % endfor
            % endif
        % endfor
    </ul>
</div>

