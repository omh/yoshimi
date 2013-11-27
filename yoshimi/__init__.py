from yoshimi import auth
from yoshimi.db import get_db
from yoshimi import url
from yoshimi.content import Location
from yoshimi.utils import context_redirect_back_url
from yoshimi.url import ResourceUrlAdapter
from yoshimi.url import RootFactory


def includeme(config):
    auth.register_auth(config)

    config.include('pyramid_mako')
    config.add_settings({'mako.directories': 'yoshimi:templates'})

    config.add_resource_url_adapter(ResourceUrlAdapter)
    config.set_root_factory(
        RootFactory(
            lambda id: get_db().query(Location).get(id)
        )
    )

    config.add_request_method(get_db, name='y_db', reify=True)
    config.add_request_method(url.url, name='y_url', reify=False)
    config.add_request_method(
        context_redirect_back_url, name='y_context_back_url', reify=False
    )
