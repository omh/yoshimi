<%inherit file="layout.mako"/>

<div class="pure-g-r" id="layout">
    <div class="pure-u" id="nav">
        <div class="inner-col">
            <label>Library</label>
            <div class="tree library">
            </div>
            <label>Filters</label>
            <div class="tree recent">
            </div>
        </div>
    </div>
    <div class="pure-u-1" id="main">
        <div class="content">
            <div class="pure-g-r main-section border">
                <div class="pure-u-2-3">
                    <h1 class="content-header content-name">${req.context.name}</h1>
                    <span class="subtle slug-preview">${req.y_path(req.context)}</span>
                </div>
                <div class="pure-u-1-3 controls">
                    <a href="${req.y_url(req.context, 'edit', back=req.path_qs)}" class="pure-button pure-button-primary">Edit</a>
                    <a href="#" class="pure-button pure-button-warning">Move</a>
                    <a href="#" class="pure-button pure-button-error">Delete</a>
                </div>
            </div>
            <div class="main-section border section-attributes">
                <div class="scroll">
                    <label><b>Intro</b></label>
                    <p>Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo. Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt. </p>
                    <label><b>Body</b></label>
                    <p>Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo. Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt. </p>
                    <p>Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo. Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt. </p>
                    <p>Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo. Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt. </p>
                </div>
            </div>
            <div class="main-section border">
                <%include file='_children_list.mako' />
            </div>
        </div>
</div>
