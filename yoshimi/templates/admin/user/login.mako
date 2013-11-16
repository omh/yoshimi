<%inherit file="../layout.mako"/>

<div class="pure-g-r">
    <div class="pure-u-2-3">
        <h1>Log in</h1>

        <form class="pure-form pure-form-aligned" method="POST" action="">
            <fieldset>
                % for field in form:
                    % if not field.widget.input_type == 'hidden':
                        % if field.errors:
                            <div class="pure-control-group error">
                        % else:
                            <div class="pure-control-group">
                        % endif
                            ${field.label(**{'class': "control-label"})}
                            ${field(**{'class': "pure-input-1-3", 'placeholder': field.name})}
                            % for error in field.errors:
                                <span class="help-inline error">${error}</span>
                            % endfor
                        </div>
                    % endif
                % endfor
                <div class="pure-controls">
                    <button type="submit" class="pure-button pure-button-primary">Log in</button>
                </div>
            </fieldset>
        </form>
    </div>
</div>
