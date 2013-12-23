"""
    yoshimi.templating
    ~~~~~~~~~~~~~~~~~~

    Implements various template (Jinja2) related functions

    :copyright: (c) 2013 by Ole Morten Halvorsen
    :license: BSD, see LICENSE for more details.
"""
from pyramid.threadlocal import get_current_request
from yoshimi.url import (
    url,
    path,
)


def url_filter(context, *args, **kwargs):
    """Jinja2 filter for generating an absolute url to context

    This method is not meant to be called directly, but used inside Jinja
    templates.

    .. sourcecode:: html+jinja

        {{ context|y_url }}

    :param context: Content type to generate url for
    :type context: :class:`~yoshimi.content.ContentType`
    """
    request = get_current_request()
    return url(request, context, *args, **kwargs)


def url_back_filter(context, *args, **kwargs):
    """Jinja2 filter for generating an absolute url to context and include
    a `back` url parameter for redirecting back to the current page.

    This method is not meant to be called directly, but used inside Jinja
    templates.

    .. sourcecode:: html+jinja

        {{ context|y_url_back }}

    :param context: Content type to generate url for
    :type context: :class:`~yoshimi.content.ContentType`
    """
    return _back(url, context, *args, **kwargs)


def path_filter(context, *args, **kwargs):
    """Jinja2 filter for generating a (relative) path to a context

    This method is not meant to be called directly, but used inside Jinja
    templates.

    .. sourcecode:: html+jinja

        {{ context|y_path }}

    :param context: Content type to generate url for
    :type context: :class:`~yoshimi.content.ContentType`
    """
    request = get_current_request()
    return path(request, context, *args, **kwargs)


def path_back_filter(context, *args, **kwargs):
    """Jinja2 filter for generating a relative url to context and include
    a `back` url parameter for redirecting back to the current page.

    This method is not meant to be called directly, but used inside Jinja
    templates.

    .. sourcecode:: html+jinja

        {{ context|y_path_back }}

    :param context: Content type to generate url for
    :type context: :class:`~yoshimi.content.ContentType`
    """
    return _back(path, context, *args, **kwargs)


def _back(url_func, context, *args, **kwargs):
    request = get_current_request()
    kwargs.update({'query': {'back': request.path_qs}})
    return url_func(request, context, *args, **kwargs)
