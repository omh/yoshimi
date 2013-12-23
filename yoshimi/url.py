"""
    yoshimi.url
    ~~~~~~~~~~~

    URL, redirect and traversal related functions and classes

    :copyright: (c) 2013 by Ole Morten Halvorsen
    :license: BSD, see LICENSE for more details.
"""
from urllib.parse import urlparse
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPMovedPermanently
from pyramid.interfaces import IResourceURL
from pyramid.traversal import ResourceURL
from zope.interface import implementer


def path(request, content, *elements, route=None, **kw):
    """ Generates an absolute URL for a content object and route name

    Normally you would invoke this function via the request object as
    ``y_path``::

        request.y_path(context)

    This function is just a light wrapper around
    :meth:`~pyramid.request.Request.resource_path`.

    :param request: A request object
    :type request: :class:`~pyramid.request.Request`
    :param content: Content to generate URL for
    :type content: :class:`~yoshimi.content.Content`
    :param str route: Route to use when generating the URL. If not provided the
     :attr:`~pyramid.request.Request.matched_route.name` will be used.
    :param dict kw: Dict of keywords which are passed onto
     :meth:`~pyramid.request.Request.resource_path`
    :return str: Relative URL to content
    """
    route = request.matched_route.name if route is None else route
    return request.resource_path(
        content, *elements, route_name=route, **kw
    )


def url(request, content, *elements, route=None, **kw):
    """ Generates a absolute URL for a given content and route name

    Normally you would invoke this function via the request object as
    ``y_url``::

        request.y_url(context)

    This function is just a light wrapper around
    :meth:`~pyramid.request.Request.resource_url`.

    :param request: A request object
    :type request: :class:`~pyramid.request.Request`
    :param content: Content to generate URL for
    :type content: :class:`~yoshimi.content.Content`
    :param str route: Route to use when generating the URL. If not provided the
     :attr:`~pyramid.request.Request.matched_route.name` will be used.
    :param dict kw: Dict of keywords which are passed onto
     :meth:`~pyramid.request.Request.resource_url`
    :return str: Absolute URL to content
    """
    route = request.matched_route.name if route is None else route
    return request.resource_url(
        content, *elements, route_name=route, **kw
    )


def context_redirect_back(request, context):
    """ Helper to create a HTTPFound redirect to a URL specified as a GET
    parameter and fall back to a context's URL if no 'back' GET parameter is
    specified.

    :param request: Request object
    :type request: :class:`~pyramid.request.Request`
    :param context: Context to redirect to if 'back' URL parameter is not
     specified.
    :rtype: :class:`~pyramid.httpexceptions.HTTPFound`
    """
    return HTTPFound(context_redirect_back_url(request, context))


def context_redirect_back_url(request, context):
    """ Helper to generate a redirect URL specified as a GET parameter and fall
    back to a context's URL if no 'back' GET parameter is specified.

    :param request: Request object
    :type request: :class:`~pyramid.request.Request`
    :param context: Context to redirect to if 'back' URL parameter is not
     specified.
    :return string: Redirect URL
    """
    return safe_redirect(
        request, request.GET.get('back', request.y_path(context))
    )


def redirect_back(request, fallback='/', **options):
    """ Helper to redirect to a URL specified as a GET parameter

    :param request: Request object
    :type request: :class:`~pyramid.request.Request`
    :param str fallback: Url to use if 'back' URL parameter is not specified
    :param dict options: Options that are passed to HTTPFound
    :return HTTPFound:
    """
    back_url = safe_redirect(request, request.GET.get('back', fallback))
    return HTTPFound(location=back_url, **options)


def safe_redirect(request, url, fallback='/'):
    """ Checks and returns a URL if it is safe to redirect to

    To prevent an potential malicious user from redirecting off to a malicious
    site we only redirect to URLs that is:

        1. Relative (has no host/domain in them) OR
        2. Absolute URLs that match current request's host OR
        3. Absolute URLs who's host is in the `yoshimi.host_whitelist`
           white list setting.

    :param: Request object
    :type request: :class:`~pyramid.request.Request`
    :param str url: URL to check
    :param str fallback: URL to return if the passed in `url` is not deemed
     safe
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


@implementer(IResourceURL)
class ResourceUrlAdapter(ResourceURL):
    """ URL adapter used by Pyramid\'s
    :meth:`~pyramid.request.Request.resource_url` and
    :meth:`~pyramid.request.Request.resource_path` methods to generate
    URLs/paths for :class:`~yoshimi.content.Content` objects. This class is
    not meant to be used directly.

    This is a thin wrapper around the default
    :class:`pyramid.traversal.ResourceURL` class in Pyramid. This class ensures
    that the :class:`~yoshimi.content.Content` is made *Location Aware* (i.e
    it has __name__ and __parent__ attributes).
    """
    def __init__(self, content, request):
        """
        :param content: Content to generate URL for
        :type content: :class:`~yoshimi.content.Content`
        :param request: Current request
        :type request: :class:`~pyramid.request.Request`
        """
        self._make_location_aware(self._slug_tuple(content), content.lineage)
        super().__init__(content, request)

    def _make_location_aware(self, path_elements, content_list):
        """Generates ``__parent__`` and ``__name__`` attributes for a list
        representing a :class:`~yoshimi.content.Content` lineage. This makes
        the list content aware.

        :param tuple path_elements: Tuple of each element in the path
        :param list content: Lineage of a content object. Root should be the
         first item.
        """
        prev = None
        for path, content in zip(path_elements, content_list):
            content.__parent__ = prev
            content.__name__ = path
            prev = content

    def _slug_tuple(self, resource):
        slugs = resource.slugs
        slugs[-1] += "-%s" % resource.id

        return slugs


class RootFactory:
    """ Generates a traversal root factory for Pyramid to use when looking up
    URLs.

    This class is responsible for taking a URL and generating a Traversal root
    object that Pyramid then uses match a URL to the
    :class:`~yoshimi.content.Content` object. The URL is parsed looking for
    a numeric :class:`~yoshimi.content.Content`. The last numeric value that
    is separated by a `-` (dash) is assumed to be the id of the context. E.g::

        /news/sports/this-is-an-article-123

    If there is something trailing the numeric ID it will be taken as the name
    of a view and be used when Pyramid does it view matching. E.g this will
    match an ``edit`` view::

        /news/sports/this-is-an-article-123/edit

    Only the ID is needed to lookup a :class:`~yoshimi.content.Content` object.
    The rest of the URL is there to make it human and robot (SEO) readable. The
    human readable part of the URL is matched against the actual human readable
    part of the Content and if it doesn't match a 301 Permanent redirect is
    issued. This allows the human readable URL to change without having to do
    any database queries or keeping track of past URLs.
    """
    def __init__(self, context_getter):
        """
        :param callable context_getter: A callable that takes one argument, \
         an unique id, and returns a context object for that id.

        """
        self.context_getter = context_getter

    def __call__(self, request):
        """ Performs the URL lookup and returns a Traversal root object or None
        if no context for the current URL could be found. If a context object
        is found but the human readable part of the URL doesn't match an
        HTTPMovedPermanently exception is raised.

        :param request: Current request
        :type request: :class:`~pyramid.request.Request`
        :raises pyramid.httpexceptions.HTTPMovedPermanently: If the request
         human readable URL didn't match
        :return: None or a dict like object
        """
        if not request.matchdict:
            return None

        path_elements = request.matchdict.get('traverse', [])

        id, requested_url_parts = self._context_id(
            path_elements, separator='-'
        )
        if not id:
            return None

        context = self._get_context(id)
        if not context:
            return None

        context_url = request.resource_path(context)
        if not self._validate_url(requested_url_parts, context_url):
            raise HTTPMovedPermanently(location=request.y_path(context))

        return self._get_root(requested_url_parts, context.lineage)

    def _get_context(self, context_id):
        return self.context_getter(context_id)

    def _validate_url(self, requested_url_parts, context_url):
        requested_slug = "/".join(requested_url_parts)
        return requested_slug.strip('/') == context_url.strip('/')

    def _get_root(self, path_elements, contexts):
        if len(path_elements) < 1:
            return None

        root = None
        for path, content in zip(reversed(path_elements), reversed(contexts)):
            root = {path: dict(root)} if root else {path: content}

        return root

    def _context_id(self, path_elements, separator='-'):
        """Extracts id and slug from a tuple of URL parts

        :param tuple url_parts: URL to extract id from
        :param str separator: Character to use to separate URL from the id
        :return tuple: (int id, tuple url_parts) or (None, None)
        """
        mutable_url_parts = list(path_elements[:])
        for url in path_elements:
            part = mutable_url_parts.pop()
            try:
                id = int(part.split(separator)[-1])
                if id > 0:
                    mutable_url_parts.append(part)
                    return (id, mutable_url_parts)
            except (KeyError, ValueError):
                continue

        return None, None
