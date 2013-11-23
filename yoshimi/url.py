from pyramid.httpexceptions import HTTPNotFound
from pyramid.httpexceptions import HTTPMovedPermanently
from yoshimi.content import Location


def extract_slug_from(url_parts, separator='-'):
    """Extracts content id and slug from a tuple of url parts

    This function assumes the identifier is a numeric at the end of a url part
    and that it is separated by the value in the `separator` parameter.
    E.g: `/some/url-49`. This function will use the last numeric value it can
    find.

    :param tuple url_parts: Url to extract id from
    :param str separated: Character to use to separate url from the id
    :return tuple: Tuple of id, slug or None, None
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


def generate_slug(obj, parent=None):
    """Generates the slug for a content type or :class:`yoshimi.content.Location`.

    If you pass in a content type the main location will be used unless you
    also pass in a :class:`yoshimi.content.Location` as the `parent` parameter.
    If `parent` parameter is set the location on `obj` which is the child
    location of the `parent` will be used as the starting point for generating
    the slug. This is useful when when you want to generate a slug for
    a specifc location but you only have the
    :class:`yoshimi.content.ContentType`. E.g:

    .. code-block:: python

        children = folder.main_location.children()
        for c in children:
            print generate_slug(c, parent=folder.main_location)

    :param obj:
    :type obj: :class:`yoshimi.content.ContentType` or
               :class:`yoshimi.content.Location`
    :return string: Generated slug
    """
    if not hasattr(obj, 'paths'):
        if parent:
            obj = obj.location_for_parent(parent)
        else:
            obj = obj.main_location

    return "%s-%s" % ("/".join(obj.slugs), obj.id)


def url(request, location, *elements, route='.', parent=None, **query):
    """Generates a url for a given location and route name

    This function is just a light wrapper around
    :meth:`pyramid.request.Request.route_path`

    :param yoshimi.content.Location location: A location
    :param str route: If not provided the
                      :attr:`pyramid.request.Request.matched_route.name` will
                      be used.
    :param dict query: Dict of url query parameters
    :return str: Url to location
    """
    if route == '.':
        route = request.matched_route.name

    traverse = generate_slug(location, parent=parent)
    if elements:
        traverse = tuple(traverse.split("/")) + elements

    return request.route_path(
        route, traverse=traverse, _query = query
    )


def locations_for_id(id):
    return Location.ancestors_by_id(id).all()


def redirect_if_slug_mismatch(request, slug, generated_slug):
    """Raises a redirect exception (HTTPMovedPermanently) if the two slugs
    don't match.

    :param request: pyramid.request object
    :param slug: Slug from current url
    :param generated_slug: Generated slug from the Content object
    """
    if not generated_slug == slug:
        raise HTTPMovedPermanently(location=request.route_path(
            request.matched_route.name, traverse=generated_slug
        ))


def lineage_for_request(request):
    """Fetches the location and all ancestors for a given request

    If the id of the current location in the url can not be found then a 404
    HTTPException is raised. If the location doesn't exist a 404 HTTPException
    is also thrown. If the slug in the url doens't match the actual slug
    a redirect (301) HTTPException is raised.

    :param request: pyramid.request object
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
    """Returns a root for use in traversal"""
    return make_tree(lineage_for_request(request))


def make_tree(locations):
    """Generates a traversal compatible tree of objects from a fetched list of
    locations in the current path

    :param list locations: List of all locations until the root
    :return Location: Root location with the appropriate traversal attrbutes
                      (__name__ and __parent__) set
    """
    if len(locations) < 1:
        return None

    root = Location()
    previous_loc = root
    for l in locations:
        previous_loc._child = l
        l.__name__ = l.slug
        l.__parent__ = previous_loc
        previous_loc = l

    last_loc = locations[-1]
    last_loc.__name__ = "%s-%s" % (last_loc.slug, last_loc.id)

    return root
