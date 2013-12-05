"""
    yoshimi.repo
    ~~~~~~~~~~~~

    Implements the content repository which is the main method of interacting
    with the CMS's content.

    :copyright: (c) 2013 by Ole Morten Halvorsen
    :license: BSD, see LICENSE for more details.
"""
from functools import partial
from sqlalchemy.orm import (
    joinedload,
    with_polymorphic,
)
from yoshimi.content import Location
from yoshimi.content import Content
from yoshimi.content import Path
from yoshimi.utils import Proxy


class Repo(Proxy):
    """Content repository to easily interact with the CMS content.

        Normally you wouldn't instantiate this class directly but rather use it
        through the request object like so::

            request.y_repo.query(Article).get(1)

        The Repo class conveniently wraps SQLAlchemy's
        :class:`~sqlalchemy.orm.session.Session` allowing you to use most of
        the session methods. Some methods such as `.query` is overloaded to
        provide convenience methods for dealing with Yoshimi content.
    """
    def __init__(self, session):
        """
        :param session: SQLAlchemy session
        :type session: :class:`~sqlalchemy.orm.session.Session`
        """
        self._proxy = session

    # @TODO: entities should be *entities to match SQLA Query api
    def query(self, entities):
        """
        Wrapper around SQLAlchemy's :class:`~sqlalchemy.orm.query.Query` class
        to provide an easy way to perform commonly used queries such as
        fetching the children of a specific type or specify eager load
        behaviour.

        Note that you cannot mix and match Yoshimi's query methods with
        SQLAlchemy. Specify your Yoshimi query methods first, then SQLAlchemy.
        This is due to the fact that as soon as a SQLAlchemy is called
        SQLAlchemy will return it's query class and not Yoshimi's. E.g this
        works::

            request.y_repo.query(article).children().limit(1).all()

        But this will not as limit(10) is a SQLAlchemy method::

            request.y_repo.query(article).limit(1).children()..all()

        Example of how to fetch 10 articles sorted by the article's title::

            request.y_repo.query(article).children().limit(10). \\
             ordery_by(Article.title).all()

        Example of how to fetch 10 articles sorted by the article's title and
        also eagerly load in all article contents and what is required to
        generate URLs to the articles. This ensure everything is fetched in 1
        query and will prevent N+1 queries::

            request.y_repo.query(article).children() \\
            .load_content().load_path() \\
            .limit(10).ordery_by(Article.title).all()

        :param list entities: Entities to query
        :returns: New query instance for `entities`.
        :rtype: :class:`.Query`
        """
        return Query(self._proxy, entities)


class Query():
    def __init__(self, session, entities):
        self.session = session
        self._entities = entities
        self._entities_list = self._to_list(entities)
        self._proxy = None
        self._ops = {}
        self._destructive_op = {}

    def __getattr__(self, name):
        self._compile()
        return getattr(self._proxy, name)

    def children(self, *content_types):
        """Fetches a list of children returning a query that can be filtered
        further if needed.

        :param tuple content_types: Content Types to fetch. If you don't
         specify any all content types will be fetched.
        """
        self._set_destructive_op(
            'children', partial(
                children,
                self.session.query,
                self._entities_list[0],
                *content_types
            )
        )

        return self

    def depth(self, levels):
        self._add_op('depth', partial(depth, lambda: self._proxy, levels))
        return self

    def load_path(self):
        self._add_op('load_path', partial(
            load_path, lambda: self._proxy, self._entities_list[0])
        )
        return self

    def load_content(self):
        self._add_op('load_content', partial(
            load_content, lambda: self._proxy, self._entities_list[0])
        )
        return self

    def load_locations(self):
        self._add_op('load_locations', partial(
            load_locations, lambda: self._proxy, self._entities_list[0])
        )
        return self

    def get_query(self):
        self._compile()
        return self._proxy

    def _compile(self):
        for op_name, op_func in self._destructive_op.items():
            self._proxy = op_func()
            break

        if self._proxy is None:
            self._proxy = self._default_query()

        self._pre_checks()
        for op_name, op_func in self._ops.items():
            self._proxy = op_func()

    def _default_query(self):
        return self.session.query(self._entities)

    def _pre_checks(self):
        if 'children' in self._destructive_op and not 'depth' in self._ops:
            self.depth(1)

    def _add_op(self, op_name, op_func):
        self._ops[op_name] = op_func

    def _set_destructive_op(self, op_name, op_func):
        self._destructive_op = {op_name: op_func}

    def _to_list(self, x):
        if not isinstance(x, (list, tuple)):
            return [x]
        else:
            return x


def load_path(query_getter, subject):
    query = query_getter()
    if hasattr(subject, 'paths'):
        jl = joinedload('paths')
    else:
        jl = joinedload('locations', innerjoin=True) \
            .joinedload('paths')

    jl = jl.joinedload('ancestor_location', innerjoin=True) \
           .joinedload('content', innerjoin=True)

    return query.options(jl)


def load_content(query_getter, subject):
    query = query_getter()
    if not hasattr(subject, 'content'):
        return query

    return query.options(joinedload('content', innerjoin=True))


def load_locations(query_getter, subject):
    query = query_getter()
    if not hasattr(subject, 'locations'):
        return query

    return query.options(joinedload('locations', innerjoin=True))


def depth(query_getter, levels):
    return query_getter().filter(Path.length.between(1, levels))


def children(query_maker, parent, *content_types):
    """Fetches a list of children returning a query that can be filtered
    further if needed.

    :param tuple content_types: Content Types to fetch. If you don't
     specify any all content types will be fetched.
    :rtype: :class:`sqlalchemy.orm.query.Query`
    :return: Once query is triggered it will return a list of
     :class:`.Location` objects.
    """
    q = query_maker(Location).join(
        Path, Path.descendant == Location.id
    ).join(
        Content, Content.id == Location.content_id
    ).join(
        Location.content.of_type(
            with_polymorphic(Content, content_types, flat=True)
        )
    ).filter(
        Path.ancestor == parent.id,
    )

    if len(content_types) == 1:
        for type in content_types:
            q = q.filter(type.id == Content.id)

    types = [t.type for t in content_types]
    if types:
        q = q.filter(Content.type.in_(types))

    return q
