"""
    yoshimi.utils
    ~~~~~~~~~~~~~

    Implements various small helper functions and classes

    :copyright: (c) 2013 by Ole Morten Halvorsen
    :license: BSD, see LICENSE for more details.
"""


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


class Proxy():
    """ Simple proxy class that delegates calls to its proxy """
    def __getattr__(self, name):
        return getattr(self._proxy, name)

    def __str__(self):
        return self._proxy.__str__()
