"""
    yoshimi.utils
    ~~~~~~~~~

    Implements various small helper functions and classes

    :copyright: (c) 2013 by Ole Morten Halvorsen
    :license: BSD, see LICENSE for more details.
"""
from urllib.parse import urlparse
from pyramid.httpexceptions import HTTPFound


def context_redirect_back_url(request, context):
    """Helper to redirect to a url specified as a GET param and fall back to a context's URL if no 'back' GET parameter is specified.

    :param request pyramid.request.Request: Request object
    :param context: Context to redirect to if 'back' url parameter is not
    specified.
    :return string: Redirect url
    """
    return safe_redirect(
        request, request.GET.get('back', request.y_url(context))
    )

def redirect_back(request, fallback='/', **options):
    """Helper to redirect to a url specified as a GET param

    :param request pyramid.request.Request: Request object
    :param fallback: Url to use if 'back' url parameter is not specified
    :param **options: Options that are passed to HTTPFound
    :return HTTPFound:
    """
    back_url = safe_redirect(request, request.GET.get('back', fallback))
    return HTTPFound(location=back_url, **options)


def safe_redirect(request, url, fallback='/'):
    """Checks and returns a url if it is safe to redirect to

    To prevent an potential attacking user from redirecting off to a malicous
    site we only redirect to urls that is:
        1. Relative (has no host/domain in them) OR
        2. Absolute urls that match current request's host OR
        3. Absolute urls who's host is in the `yoshimi.host_whitelist`
           whitelist setting.
    :param pyramid.request.Request request: Request object
    :param string url: URL to check
    :param string fallback: URL to return if the passed in `url` is not deemed safe
    """
    test_url = urlparse(url)

    # Relative url - it's fine
    if test_url.netloc == '':
        return url

    # Host/port matches - it's fine
    ref_url = urlparse(request.url)
    if test_url.netloc == ref_url.netloc:
        return url

    whitelist = request.registry.settings.get('yoshimi.host_whitelist', [])
    if test_url.netloc in whitelist:
        return url

    return fallback


def page_number(n):
    """Ensures a number is minimum 1, always positive and an integer"""
    return max(int(n), 1)


class LazyPagination(object):
    """Makes a lazy paginator - nothing is fetched until it's used

    This class is useful if you want to send a paginator to the template, but
    you don't want it to trigger any queries until variable is actually
    accessed.

    Example::

        list = LazyPagination(article.children(), 3)
        list.total #=> Triggers the query
        3

    :param string query: A query
    """
    def __init__(self, query, page):
        self.query = query
        self.page = page
        self.paginator = None

    def __getattr__(self, name):
        if not self.paginator:
            self.paginator = self.query.paginate(self.page)

        return getattr(self.paginator, name)
