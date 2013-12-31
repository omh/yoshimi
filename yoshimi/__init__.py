from functools import partial
from yoshimi import auth
from yoshimi.db import get_db
from yoshimi.config import add_query_directive
from yoshimi.repo import Repo
from yoshimi.repo import content_getter
from yoshimi.templating import (
    url_filter,
    path_filter,
    path_back_filter,
)
from yoshimi.url import (
    url as url_func,  # done to prevent conflicts with url module
    path,
    back_to_context_url,
    ResourceUrlAdapter,
    RootFactory
)


def includeme(config):
    auth.register_auth(config)

    setup_template(config)

    config.add_directive('add_query_directive', add_query_directive)
    config.add_resource_url_adapter(ResourceUrlAdapter)
    config.set_root_factory(RootFactory(
        partial(content_getter, Repo(config.registry, get_db()))
    ))

    config.add_request_method(get_db, name='y_db', reify=True)
    config.add_request_method(repo_maker, name='y_repo', reify=True)
    config.add_request_method(path, name='y_path', reify=False)
    config.add_request_method(url_func, name='y_url', reify=False)
    config.add_request_method(
        back_to_context_url, name='y_back_to_context_url', reify=False
    )


def setup_template(config):
    config.include('pyramid_jinja2')
    config.add_jinja2_search_path('yoshimi:templates')
    config.get_jinja2_environment().filters.update({
        'y_url': url_filter,
        'y_path': path_filter,
        'y_path_back': path_back_filter,
    })


def repo_maker(request):
    return Repo(request.registry, request.y_db)
