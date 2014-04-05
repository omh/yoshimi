"""
    yoshimi.repo
    ~~~~~~~~~~~~

    Implements the content repository which is the main method of interacting
    with the CMS's content.

    :copyright: (c) 2013 by Ole Morten Halvorsen
    :license: BSD, see LICENSE for more details.
"""
from functools import partial

from pyramid.httpexceptions import HTTPNotFound
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound
from zope.sqlalchemy import mark_changed
from zope.interface import implementer

from yoshimi.content import Content
from yoshimi.content import Path
from yoshimi.interfaces import IQueryExtensions
from yoshimi.utils import Proxy
from yoshimi.services import Trash


class Repo(Proxy):
    """Content repository for interacting with the CMS content.

        Normally you wouldn't instantiate this class directly but rather use it
        through the request object like so::

            request.y_repo.query(Article).get(1)

        The Repo class conveniently wraps SQLAlchemy's
        :class:`~sqlalchemy.orm.session.Session` allowing you to use most of
        the session methods. Some methods such as `.query` is overloaded to
        provide convenience methods for dealing with Yoshimi content.
    """
    def __init__(self, registry, session):
        """
        :param session: SQLAlchemy session
        :type session: :class:`~sqlalchemy.orm.session.Session`
        """
        self._proxy = session
        self._registry = registry

    def move(self, subject):
        return MoveOperation(self._proxy, subject)

    def delete(self, subject):
        op = DeleteOperation(self._proxy)
        op.delete(subject)

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

            request.y_repo.query(article).limit(1).children().all()

        Example of how to fetch 10 articles sorted by the article's title::

            request.y_repo.query(article).children().limit(10). \\
             ordery_by(Article.title).all()

        Example of how to fetch 10 articles sorted by the article's title and
        also eagerly load in all article contents and what is required to
        generate URLs to the articles. This ensures everything is fetched in 1
        query and will prevent the all too common `N+1` number of queries
        problem::

            request.y_repo.query(Article).children() \\
            .load_path().limit(10).ordery_by(Article.title).all()

        :param list entities: Entities to query
        :returns: New query instance for `entities`.
        :rtype: :class:`.Query`
        """
        exts = self._registry.queryUtility(
            IQueryExtensions, default=_QueryExtensions()
        )
        return Query(self._proxy, entities, exts.methods)

    @property
    def trash(self):
        return Trash(self._proxy)


class Query(Proxy):
    def __init__(self, session, entities, exts=None):
        self.session = session
        self._entities = entities
        self._entities_list = self._to_list(entities)
        self._proxy = None
        self.exts = exts if exts else {}
        self._ops = {}
        self._destructive_op = {}

    def __getattr__(self, name):
        if name in self.exts:
            return self._apply_extension(name)

        # Skip pre checks if we're using query.get() as it throws an exception
        # if there's existing filters
        enable_pre_checks = False if name == 'get' else True

        self._compile(enable_pre_checks)

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

    def status(self, status_id):
        self._add_op('status', partial(status, lambda: self._proxy, status_id))

        return self

    def get_query(self):
        self._compile()
        return self._proxy

    def _apply_extension(self, name):
        def inner(*args, **kwargs):
            self._add_op(
                name,
                partial(
                    self.exts[name], lambda: self._proxy, *args, **kwargs
                )
            )
            return self
        return inner

    def _compile(self, enable_pre_checks=True):
        for _, op_func in self._destructive_op.items():
            self._proxy = op_func()
            break

        if self._proxy is None:
            self._proxy = self._default_query()

        if enable_pre_checks:
            self._pre_checks()

        for _, op_func in self._ops.items():
            self._proxy = op_func()

    def _default_query(self):
        return self.session.query(self._entities)

    def _pre_checks(self):
        if 'children' in self._destructive_op and 'depth' not in self._ops:
            self.depth(1)

        if 'status' not in self._ops:
            self.status(Content.status.AVAILABLE)

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
    jl = joinedload('paths', innerjoin=True)

    return query.options(jl)


def depth(query_getter, levels):
    return query_getter().filter(Path.length.between(1, levels))


def status(query_getter, status_id):
    return query_getter().filter(Content.status_id == status_id)


def children(query_maker, parent, *content_types):
    """Fetches a list of children returning a query that can be filtered
    further if needed.

    :param tuple content_types: Content Types to fetch. If you don't
     specify any all content types will be fetched.
    :rtype: :class:`sqlalchemy.orm.query.Query`
    :return: Once query is triggered it will return a list of
     :class:`.Content` objects.
    """
    q = query_maker(Content).with_polymorphic(
        content_types
    ).join(
        Path, Path.descendant == Content.id
    ).filter(
        Path.ancestor == parent.id,
    )
    if content_types:
        q = q.filter(Content.type.in_(
            [t.__mapper_args__['polymorphic_identity'] for t in content_types]
        ))

    return q


def content_getter(repo, id):
    """
    Responsible for taking a unique id to a content object and fetching it from
    the database.

    Raises a :class:`~pyarmid.httpexceptions.HTTPNotFound` exception if no
    object is found.

    We avoid the use of get() as SQLAlchemy does not allow get() to be used
    with filters.

    :param repo: Repository
    :type repo: :class:`~.Repo`
    :param id: Unique identifier id of a content object
    """
    try:
        return repo.query(Content).load_path().filter_by(id=id).one()
    except NoResultFound:
        raise HTTPNotFound


class MoveOperation:
    def __init__(self, session, subject):
        self._session = session
        self._subject = subject

    def to(self, new_parent):
        """Moves a content object to a new location

        This will also recursivly move all children of this below the content
        object.

        Because this method uses raw queries all objects in the session will
        be expired after calling this method.

        :param new_parent: The new parent/destination for the move
        :type new_parent: `yoshimi.content.Content`
        """
        self._del_non_interconnected_paths(self._session, self._subject.id)
        self._recreate_paths(self._session, self._subject.id, new_parent.id)

        mark_changed(self._session)
        self._session.expire_all()

    def _del_non_interconnected_paths(self, session, subject_id):
        """Deletes paths that are not interconnected."""
        if session.bind.dialect.name == "mysql":
            session.execute("""DELETE p FROM path as p
                JOIN path AS d ON p.descendant = d.descendant
                LEFT JOIN path as x
                    ON x.ancestor = d.ancestor
                    AND x.descendant = p.ancestor
                WHERE
                    d.ancestor = :content_id
                    AND x.ancestor IS NULL
            """, {'content_id': subject_id})
        else:
            subq = session.query(Path.descendant).filter(
                Path.ancestor == subject_id
            ).subquery()
            session.query(Path).filter(
                Path.descendant.in_(subq),
                ~Path.ancestor.in_(subq)
            ).delete(synchronize_session=False)

    def _recreate_paths(self, session, subject_id, new_parent_id):
        session.execute("""INSERT INTO
                path (ancestor, descendant, length)
            SELECT
                supertree.ancestor,
                subtree.descendant,
                supertree.length + subtree.length + 1
            FROM
                path as supertree
            JOIN
                path as subtree ON subtree.ancestor = :subtree
            WHERE
                supertree.descendant = :new_parent_id
        """, {
            "subtree": subject_id,
            "new_parent_id": new_parent_id
        })


class DeleteOperation:
    def __init__(self, session):
        self._session = session

    def delete(self, target):
        """
        Need to fetch all content in a subtree, then delete them.

        Paths will be deleted thanks to cascading deletes.
        """
        if self._session.bind.dialect.name == "mysql":
            self._session.execute("""
                DELETE content from content
                JOIN path ON path.descendant = content.id
                WHERE
                    path.ancestor = :content_id
                """, {'content_id': target.id}
            )
        else:
            q = self._session.query(Content).filter(
                Content.id.in_(
                    self._session.query(Path.descendant).select_from(
                        Path
                    ).filter(
                        Path.ancestor == target.id
                    )
                )
            )
            q.delete(synchronize_session=False)


@implementer(IQueryExtensions)
class _QueryExtensions:
    methods = {}
