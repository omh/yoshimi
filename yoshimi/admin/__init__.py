from yoshimi.views import edit
from yoshimi.views import index
from yoshimi.views import login
from yoshimi.views import logout
from yoshimi.views import browse
from yoshimi.views import move


def include_views(config):
    config.add_route('y.admin.login', '/user/login')
    config.add_view(
        login, route_name='y.admin.login', renderer='admin/user/login.mako'
    )

    config.add_route('y.admin.logout', '/user/logout')
    config.add_view(
        logout, route_name='y.admin.logout', renderer='admin/user/logout.mako'
    )

    config.add_route('y_admin', '*traverse')
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


def includeme(config):
    include_views(config)
