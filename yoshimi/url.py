from pyramid.httpexceptions import HTTPNotFound
from pyramid.httpexceptions import HTTPMovedPermanently
from pyramid.interfaces import IResourceURL
from pyramid.traversal import ResourceURL
from zope.interface import implementer
from yoshimi.content import Location


def extract_slug_from(url_parts, separator='-'):
    """Extracts content id and slug from a tuple of URL parts

    This function assumes the identifier is a numeric at the end of a URL part
    and that it is separated by the value in the `separator` parameter.
    E.g: `/some/url-49`. This function will use the last numeric value it can
    find.

    :param tuple url_parts: URL to extract id from
    :param str separated: Character to use to separate URL from the id
    :return tuple: (id, slug) or (None, None)
    """
    mutable_url_parts = list(url_parts[:])
    for url in url_parts:
        part = mutable_url_parts.pop()
        try:
            id = int(part.split(separator)[-1])
            if id > 0:
                mutable_url_parts.append(part)
                return (id, "/".join(mutable_url_parts))
        except (KeyError, ValueError):
            continue

    return None, None


def generate_slug(obj):
    """Generates the slug for :class:`~yoshimi.content.Content` or
    :class:`~yoshimi.content.Location`. If `obj` is of type
    :class:`~yoshimi.content.Content` the main location will be used.

    :param obj: Content or location to generate the slug for
    :type obj: :class:`~yoshimi.content.Content` or
     :class:`~yoshimi.content.Location`
    :return string: Generated slug
    """
    if hasattr(obj, 'main_location'):
        obj = obj.main_location

    return "/".join(_generate_slug_tuple(obj))


def _generate_slug_tuple(obj):
    slugs = obj.slugs
    slugs[-1] += "-%s" % obj.id

    return slugs


def url(request, location, *elements, route=None, **kw):
    """Generates a URL for a given location and route name

    This function is just a light wrapper around
    :meth:`pyramid.request.Request.resource_path`

    :param request: A request object
    :type request: :class:`pyramid.request.Request`
    :param location: Location to generate URL for
    :type location: :class:`~yoshimi.content.Location`
    :param str route: If not provided the
     :attr:`pyramid.request.Request.matched_route.name` will be used.
    :param dict query: Dict of URL query parameters
    :return str: URL to location
    """
    route = request.matched_route.name if route is None else route
    return request.resource_path(
        location, *elements, route_name=route, **kw
    )


def locations_for_id(id):
    """@TODO: This is a repo method"""
    return Location.ancestors_by_id(id).all()


def redirect_if_slug_mismatch(request, slug, generated_slug):
    """Raises a redirect exception (HTTPMovedPermanently) if the two slugs
    don't match.

    :param request: A request object
    :type request: :class:`pyramid.request.Request`
    :param slug: Slug for the current URL
    :param generated_slug: Generated slug from the Content object
    """
    if not generated_slug == slug:
        raise HTTPMovedPermanently(location=request.route_path(
            request.matched_route.name, traverse=generated_slug
        ))


def lineage_for_request(request):
    """Fetches the location and all ancestors for a given request.

    If the id of the current location in the URL can not be found then a 404
    HTTPException is raised. If the location doesn't exist a 404 HTTPException
    is also thrown. If the slug in the URL doens't match the actual slug
    a redirect (301) HTTPException is raised.

    :param request: A request object
    :type request: :class:`pyramid.request.Request`
    :param options: Additional options that will be passed on to slug()
    :returns list: List of locations. The last one in the list being the
                   current location.
    """
    id, slug = extract_slug_from(request.matchdict.get('traverse', []))
    if not id:
        raise HTTPNotFound

    locations = locations_for_id(id)
    if not locations:
        raise HTTPNotFound

    redirect_if_slug_mismatch(request, slug, generate_slug(locations[-1]))

    return locations


def get_root(request):
    """Returns a root for use in traversal."""
    return make_tree(lineage_for_request(request))


def make_tree(locations):
    """Generates a traversal compatible tree of objects from a fetched list of
    locations in the current path.

    :param list locations: List of all locations until the root.
    :rtype: :class:`~yoshimi.content.Location`
    :return: Root location with the appropriate traversal attrbutes
     (__name__ and __parent__) set.
    """
    if len(locations) < 1:
        return None

    root = None
    path_elements = _generate_slug_tuple(locations[-1])
    for path, location in zip(reversed(path_elements), reversed(locations)):
        root = {path: dict(root)} if root else {path: location}

    return root


def make_location_aware(locations):
    """Generates ``__parent__`` and ``__name__`` attributes for a list
    representing a :class:`~yoshimi.content.Location` lineage. This makes the
    list location aware.

    :param list locations: Lineage of a location. Root should be the first item.
    """
    prev = None
    path_elements = _generate_slug_tuple(locations[-1])
    for path, location in zip(path_elements, locations):
        location.__parent__ = prev
        location.__name__ = path
        prev = location


@implementer(IResourceURL)
class ResourceUrlAdapter(ResourceURL):
    def __init__(self, resource, request):
        make_location_aware(resource.lineage)
        super().__init__(resource, request)
