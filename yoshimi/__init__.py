from functools import partial
from yoshimi import auth
from yoshimi.db import get_db
from yoshimi import url
from yoshimi.config import add_query_directive
from yoshimi.content import Content
from yoshimi.repo import Repo
from yoshimi.utils import context_redirect_back_url
from yoshimi.url import (
    ResourceUrlAdapter,
    RootFactory
)


def includeme(config):
    auth.register_auth(config)

    config.include('pyramid_mako')
    config.add_settings({'mako.directories': 'yoshimi:templates'})

    config.add_directive('add_query_directive', add_query_directive)
    config.add_resource_url_adapter(ResourceUrlAdapter)
    config.set_root_factory(RootFactory(
        partial(content_getter, config.registry)
    ))

    config.add_request_method(get_db, name='y_db', reify=True)
    config.add_request_method(repo_maker, name='y_repo', reify=True)
    config.add_request_method(url.path, name='y_path', reify=False)
    config.add_request_method(url.url, name='y_url', reify=False)
    config.add_request_method(
        context_redirect_back_url, name='y_context_back_url', reify=False
    )


def repo_maker(request):
    return Repo(request.registry, request.y_db)


def content_getter(registry, id):
    return Repo(registry, get_db()).query(Content).load_path().get(id)
