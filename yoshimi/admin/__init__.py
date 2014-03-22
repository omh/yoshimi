from yoshimi.views import (
    edit,
    login,
    logout,
    browse,
    delete,
    move
)
from yoshimi.admin.views import (
    index,
    trash_index,
    trash_empty,
    trash_restore,
)


def include_views(config):
    config.add_route('y.admin.trash.index', '/trash')
    config.add_view(
        trash_index,
        route_name='y.admin.trash.index',
        renderer='trash/index.jinja2'
    )
    config.add_route('y.admin.trash.empty', '/trash/_empty')
    config.add_view(
        trash_empty,
        route_name='y.admin.trash.empty',
        request_method='POST',
    )
    config.add_route('y.admin.trash.restore', '/trash/_restore')
    config.add_view(
        trash_restore,
        route_name='y.admin.trash.restore',
        request_method='POST',
    )

    config.add_route('y.admin.login', '/user/login')
    config.add_view(
        login, route_name='y.admin.login', renderer='admin/user/login.jinja2'
    )
    config.add_route('y.admin.logout', '/user/logout')
    config.add_view(
        logout,
        route_name='y.admin.logout',
        renderer='admin/user/logout.jinja2'
    )

    config.add_route('y_admin', '*traverse')
    config.add_view(
        edit, route_name='y_admin', name='edit', renderer='admin/edit.jinja2'
    )
    config.add_view(
        browse,
        route_name='y_admin',
        name='browse',
        renderer='admin/browse.jinja2'
    )
    config.add_view(
        delete,
        route_name='y_admin',
        name='delete',
        request_method='POST',
        renderer='json'
    )
    config.add_view(
        move, route_name='y_admin', name='move', renderer='json'
    )
    config.add_view(
        index, route_name='y_admin', renderer='admin/index.jinja2'
    )


def setup_template(config):
    config.add_jinja2_search_path('yoshimi.admin:templates')


def includeme(config):
    include_views(config)
    setup_template(config)
