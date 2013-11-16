from pyramid.view import view_config
from yoshimi.views import edit
from yoshimi.views import index
from yoshimi.views import login
from yoshimi.views import logout
from yoshimi.views import browse
from yoshimi.views import move
from yoshimi.url import get_root


def includeme(config):
    config.add_route(
        'y.admin.login',
        '/user/login',
        renderer='admin/user/login.mako',
        view=login
    )
    config.add_route( 'y.admin.logout', '/user/logout', view=logout)

    config.add_route( 'y_admin', '*traverse', factory=get_root)

    config.add_view(
        edit, route_name='y_admin', name='edit', renderer='admin/edit.mako'
    )
    config.add_view(
        browse, route_name='y_admin', name='browse', renderer='admin/browse.mako'
    )
    config.add_view(
        move, route_name='y_admin', name='move', renderer='json'
    )
    config.add_view(
        index, route_name='y_admin', renderer='admin/index.mako'
    )
