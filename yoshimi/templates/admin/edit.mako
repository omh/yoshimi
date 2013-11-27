<%inherit file="layout.mako"/>

<div class="pure-g-r"><div class="pure-u-2-3 content">
    <form method="POST" action="" class="pure-form pure-form-stacked">
        <fieldset>
            <legend class="content-header">
                <span class="content-name">${req.context.content.name}</span>
                <span class="subtle slug-preview">${req.y_path(req.context)}</span>
            </legend>

            % if form.errors:
                <%include file='_form_validation.mako' />
            % endif

            % for field in form:
                % if hasattr(field.widget, 'input_type') and not field.widget.input_type == 'hidden':
                    <div class="control-group${' error' if field.errors else ''}">
                        ${field.label(**{'class': "control-label"})}
                        <span class="help-inline">This is some helper text</span>
                        ${field(**{'class': "pure-input-1"})}
                        % for error in field.errors:
                            <span class="inline-error">${error}</span>
                        % endfor
                    </div>
                % endif
            % endfor
            ${form.render_hidden_tags() | n}
            <button type="submit" class="pure-button pure-button-primary">Store</button>
            <a href="${req.y_context_back_url(req.context)}" class="pure-button pure-button-cancel">Cancel</button>

        </fieldset>
    </form>
</div></div>
