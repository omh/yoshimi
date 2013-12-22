from zope.interface import (
    Attribute,
    Interface,
)


class IQueryExtensions(Interface):
    """ Interface for storing query extensions (methods) which will be added to
    the query object.
    """
    methods = Attribute(
        """A list of methods to be added to a query object."""
    )
