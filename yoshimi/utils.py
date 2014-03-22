"""
    yoshimi.utils
    ~~~~~~~~~~~~~

    Implements various small helper functions and classes

    :copyright: (c) 2013 by Ole Morten Halvorsen
    :license: BSD, see LICENSE for more details.
"""
import functools


def page_number(n):
    """Ensures a number is minimum 1, always positive and an integer"""
    return max(int(n), 1)


def cache_func(func):
    """ Caches the output of `func`

    A useful scenario for this function is when you want to provide a function
    to a template that returns some expensive result (e.g a SQL query) and
    allow the user to call the function many times.

    Internally this function simply wraps the provided function in Python's
    :func:`~functools.lru_cache`.

    :param function func: Function to cache return value of.
    :return function: Decorated version of `func`
    """
    return functools.lru_cache(maxsize=1)(func)


class LazyPagination:
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


class Proxy:
    """ Simple proxy class that delegates calls to its proxy """
    def __getattr__(self, name):
        return getattr(self._proxy, name)

    def __str__(self):
        return self._proxy.__str__()
