from pyramid.httpexceptions import HTTPMovedPermanently
from pyramid.interfaces import IResourceURL
from pyramid.traversal import ResourceURL
from zope.interface import implementer


def url(request, location, *elements, route=None, **kw):
    """Generates a URL for a given location and route name

    Normally you would invoke this function via the request object as
    ``y_url``::

        request.y_url(location)

    This function is just a light wrapper around
    :meth:`pyramid.request.Request.resource_path`.

    :param request: A request object
    :type request: :class:`pyramid.request.Request`
    :param location: Location to generate URL for
    :type location: :class:`~yoshimi.content.Location`
    :param str route: Route to use when generating the URL. If not provided the
     :attr:`pyramid.request.Request.matched_route.name` will be used.
    :param dict kw: Dict of keywords which are passed onto
     :meth:`pyramid.request.Request.resource_url`
    :return str: URL to location
    """
    route = request.matched_route.name if route is None else route
    return request.resource_path(
        location, *elements, route_name=route, **kw
    )


@implementer(IResourceURL)
class ResourceUrlAdapter(ResourceURL):
    """URL adapter used by Pyramid\'s
    :meth:`~pyramid.request.Request.resource_url` and
    :meth:`~pyramid.request.Request.resource_path` methods to generate
    URLs/paths for :class:`~yoshimi.content.Location` objects. This class is
    not meant to be used directly.

    This is a thin wrapper around the default
    :class:`pyramid.traversal.ResourceURL` class in Pyramid. This class ensures
    that the :class:`~yoshimi.content.Location` is made *Location Aware* (i.e
    it has __name__ and __parent__ attributes).
    """
    def __init__(self, location, request):
        """
        :param location: Location to generate URL for
        :type location: :class:`~yoshimi.content.Location`
        :param request: Current request
        :type request: :class:`~pyramid.request.Request`
        """
        self._make_location_aware(self._slug_tuple(location), location.lineage)
        super().__init__(location, request)

    def _make_location_aware(self, path_elements, locations):
        """Generates ``__parent__`` and ``__name__`` attributes for a list
        representing a :class:`~yoshimi.content.Location` lineage. This makes
        the list location aware.

        :param tuple path_elements: Tuple of each element in the path
        :param list locations: Lineage of a location. Root should be the first
         item.
        """
        prev = None
        for path, location in zip(path_elements, locations):
            location.__parent__ = prev
            location.__name__ = path
            prev = location

    def _slug_tuple(self, resource):
        slugs = resource.slugs
        slugs[-1] += "-%s" % resource.id

        return slugs


class RootFactory():
    """Generates a traversal root factory for Pyramid to use when looking up
    URLs.

    This class is responsible for taking a URL and generating a Traversal root
    object that Pyramid then uses match a URL to the
    :class:`~yoshimi.content.Location` object. The URL is parsed looking for
    a numeric :class:`~yoshimi.content.Location`. The last numeric value that
    is separated by a `-` (dash) is assumed to be the id of the context. E.g::

        /news/sports/this-is-an-article-123

    If there is something trailing the numeric ID it will be taken as the name
    of a view and be used when Pyramid does it view matching. E.g this will
    match an ``edit`` view::

        /news/sports/this-is-an-article-123/edit

    Only the ID is needed to lookup a :class:`~yoshimi.content.Location`. The
    rest of the URL is there to make it human and robot (SEO) readable. The
    human readable part of the URL is matched against the actual human readable
    part of the Location and if it doesn't match a 301 Permanent redirect is
    issued. This allows the human readable URL to change without having to do
    any database queries or keeping track of past URLs.
    """
    def __init__(self, context_getter):
        """
        :param callable context_getter: A callable that takes one argument, an
         unique id, and returns a context object for that id.
        """
        self.context_getter = context_getter

    def __call__(self, request):
        """Performs the URL lookup and returns a Traversal root object or None
        if no context for the current URL could be found. If a context object
        is found but the human readable part of the URL doesn't match an
        HTTPMovedPermanently expection is raied is issued.

        :param request: Current request
        :type request: `pyramid.request.Request`
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
        context = self._get_context(id)
        if not context:
            return None

        context_url = request.resource_path(context)
        if not self._validate_url(requested_url_parts, context_url):
            raise HTTPMovedPermanently(location=request.y_url(context))

        return self._get_root(requested_url_parts, context.lineage)

    def _get_context(self, context_id):
        try:
            return self.context_getter(context_id)
        except:
            return None

    def _validate_url(self, requested_url_parts, context_url):
        requested_slug = "/".join(requested_url_parts)
        return requested_slug.lstrip('/') == context_url.lstrip('/')

    def _get_root(self, path_elements, contexts):
        if len(path_elements) < 1:
            return None

        root = None
        for path, location in zip(reversed(path_elements), reversed(contexts)):
            root = {path: dict(root)} if root else {path: location}

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
