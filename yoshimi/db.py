from math import ceil
from pyramid.httpexceptions import HTTPNotFound
from sqlite3 import Connection as SQLite3Connection
from sqlalchemy import engine_from_config
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.ext import declarative
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.query import Query
from zope.sqlalchemy import ZopeTransactionExtension


class Pagination(object):
    """Internal helper class returned by :meth:`BaseQuery.paginate`.  You
    can also construct it from any other SQLAlchemy query object if you are
    working with other libraries.  Additionally it is possible to pass `None`
    as query object in which case the :meth:`prev` and :meth:`next` will
    no longer work.
    """

    def __init__(self, query, page, per_page, total, items):
        #: the unlimited query object that was used to create this
        #: pagination object.
        self.query = query
        #: the current page number (1 indexed)
        self.page = page
        #: the number of items to be displayed on a page.
        self.per_page = per_page
        #: the total number of items matching the query
        self.total = total
        #: the items for the current page
        self.items = items

    @property
    def pages(self):
        """The total number of pages"""
        if self.per_page == 0:
            pages = 0
        else:
            pages = int(ceil(self.total / float(self.per_page)))
        return pages

    def prev(self, error_out=False):
        """Returns a :class:`Pagination` object for the previous page."""
        assert self.query is not None, 'a query object is required ' \
                                       'for this method to work'
        return self.query.paginate(self.page - 1, self.per_page, error_out)

    @property
    def prev_num(self):
        """Number of the previous page."""
        return self.page - 1

    @property
    def has_prev(self):
        """True if a previous page exists"""
        return self.page > 1

    def next(self, error_out=False):
        """Returns a :class:`Pagination` object for the next page."""
        assert self.query is not None, 'a query object is required ' \
                                       'for this method to work'
        return self.query.paginate(self.page + 1, self.per_page, error_out)

    @property
    def has_next(self):
        """True if a next page exists."""
        return self.page < self.pages

    @property
    def next_num(self):
        """Number of the next page"""
        return self.page + 1

    def iter_pages(self, left_edge=2, left_current=2,
                   right_current=3, right_edge=2):
        """Iterates over the page numbers in the pagination.  The four
        parameters control the thresholds how many numbers should be produced
        from the sides.  Skipped page numbers are represented as `None`.
        This is how you could render such a pagination in the templates:

        .. sourcecode:: html+jinja

            {% macro render_pagination(pagination, endpoint) %}
              <div class=pagination>
              {%- for page in pagination.iter_pages() %}
                {% if page %}
                  {% if page != pagination.page %}
                    <a href="{{ url_for(endpoint, page=page) }}">{{ page }}</a>
                  {% else %}
                    <strong>{{ page }}</strong>
                  {% endif %}
                {% else %}
                  <span class=ellipsis>...</span>
                {% endif %}
              {%- endfor %}
              </div>
            {% endmacro %}
        """
        last = 0
        for num in range(1, self.pages + 1):
            if num <= left_edge or \
               (num > self.page - left_current - 1 and
                num < self.page + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num


class BaseQuery(Query):
    def paginate(self, page, per_page=30, error_out=True):
            """Returns `per_page` items from page `page`.  By default it will
            abort with 404 if no items were found and the page was larger than
            1.  This behavor can be disabled by setting `error_out` to `False`.

            Returns an :class:`Pagination` object.
            """
            if error_out and page < 1:
                raise HTTPNotFound(404)
            items = self.limit(per_page).offset((page - 1) * per_page).all()
            if not items and page != 1 and error_out:
                raise HTTPNotFound(404)

            # No need to count if we're on the first page and there are fewer
            # items than we expected.
            if page == 1 and len(items) < per_page:
                total = len(items)
            else:
                total = self.order_by(None).count()

            return Pagination(self, page, per_page, total, items)


class DeclarativeBase(object):
    query_class = BaseQuery
    query = None

    @declarative.declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }


Session = None
engine = None


def setup_db(settings, extension=ZopeTransactionExtension):
    from yoshimi.entities import Base

    global engine
    engine = engine_from_config(settings, 'sqlalchemy.')

    session_options = {'query_cls': BaseQuery}
    if extension is not None:
        session_options['extension'] = extension()
    global Session
    Session = scoped_session(sessionmaker(**session_options))
    Session.configure(bind=engine)

    DeclarativeBase.query = Session.query_property()
    Base.metadata.bind = engine

    setup_listeners()

    return engine


def setup_listeners():
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        if isinstance(dbapi_connection, SQLite3Connection):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()


def get_db(request=None):
    return Session()
