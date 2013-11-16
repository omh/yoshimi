import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.ext import declarative
from yoshimi.db import (
    BaseQuery,
    DeclarativeBase,
    get_db,
    mark_changed
)


Base = declarative.declarative_base(cls=DeclarativeBase)


def get_query(obj, *args, **kwargs):
    kwargs['session'] = get_db()
    return BaseQuery(*args, **kwargs)


class Path(Base):
    """Represents a node in the content structure.

    A Closure Table is used to maintain the tree structure in the database.
    """
    ancestor = sa.Column(
        sa.Integer,
        sa.ForeignKey('location.id', ondelete='CASCADE'),
        primary_key=True,
    )
    descendant = sa.Column(
        sa.Integer,
        sa.ForeignKey('location.id', ondelete='CASCADE'),
        primary_key=True,
    )
    length = sa.Column(sa.Integer, nullable=False)
    ancestor_location = orm.relationship(
        'Location',
        foreign_keys=[ancestor],
        backref=orm.backref(
            'ancestor_paths',
            lazy='dynamic',
        ),
    )
    descendant_location = orm.relationship(
        'Location',
        foreign_keys=[descendant],
        backref=orm.backref(
            'descendant_paths',
            lazy='dynamic',
        ),
    )


class Location(Base):
    """Represents the location of a Content object in the content tree
    structure.

    Creating a root location::

        >>> content.locations[] = Location()

    Moving a location::

        >>> content.main_location.move(root.main_location)
    """
    id = sa.Column(sa.Integer, primary_key=True)
    is_main = sa.Column(sa.Boolean, default=False, nullable=False)
    content_id = sa.Column(
        sa.Integer,
        sa.ForeignKey('content.id', ondelete='CASCADE'),
    )
    paths = orm.relationship(
        Path,
        foreign_keys=[Path.descendant],
        order_by=Path.length.desc(),
    )

    def __init__(self, parent=None, **kwargs):
        """Creates a new Location

        :param Location parent: The parent for this Location. If set to None
                                then the location will be created as a root
                                location.
        """
        super(Location, self).__init__(**kwargs)

        path = Path(
            ancestor_location=self,
            descendant_location=self,
            length=0
        )
        self.paths.append(path)

        if parent is not None:
            for parent_path in parent.descendant_paths:
                new_path = Path()
                new_path.ancestor_location = parent_path.ancestor_location
                new_path.descendant_location = self
                new_path.length = parent_path.length + 1
                self.paths.append(new_path)

        self._parent = parent

    def __getitem__(self, item):
        if not hasattr(self, '_child'):
            raise KeyError
        if self._child and self._child.__name__ == item:
            return self._child
        else:
            raise KeyError

    @classmethod
    def ancestors_by_id(cls, location_id):
        """Fetches all ancestor locations all the way to the root

        Given a structure of::

            root
            -- child1
            -- -- child2
            -- child3
            -- -- child4

        Calling this method on child4 will return the following list
        of locations::

            [root, child3, child4]
        :returns sqlalchemy.orm.query.Query:
        """
        return cls.query.join(
            Path, Path.ancestor == Location.id
        ).filter(
            Path.descendant == location_id
        ).order_by(
            Path.length.desc()
        ).options(
            orm.joinedload_all('paths.ancestor_location.content'),
            orm.joinedload_all('content'),
        )

    @property
    def parent(self):
        """Fetches the parent location

        If the location is a top-level location (i.e no parent) then None
        is returned.

        :returns Location: A Location or None
        """
        if hasattr(self, '_parent') and getattr(self, '_parent') is not None:
            return self._parent

        try:
            self._parent = self.sorted_paths[-2].ancestor_location
        except IndexError:
            self._parent = None

        return self._parent

    @property
    def lineage(self):
        try:
            return [p.ancestor_location for p in self.sorted_paths]
        except IndexError:
            return None

    @property
    def sorted_paths(self):
        self._sort_paths()
        return self.paths

    @property
    def slug(self):
        return self.content.slug

    @property
    def slugs(self):
        return [p.ancestor_location.slug for p in self.sorted_paths]

    def ancestors(self):
        return self.ancestors_by_id(self.id)

    def children(self, *entities, **options):
        """Fetch a list of children

        :param entities: A list of entities to fetch. If you don't specify
                         any all entities will be fetched. This can cause N+1
                         amount of SQL queries. Always specify the which
                         entities to fetch if you are able to.
        :returns sqlalchemy.orm.query.Query:
        """
        if not 'depth' in options:
            options['depth'] = 1

        if len(entities) >= 2:
            query = get_query(self, orm.with_polymorphic(Content, entities))
        elif len(entities) == 1:
            query = get_query(self, *entities)
        else:
            query = get_query(self, Content)

        return query.join(Location).join(
            Path, Path.descendant == Location.id
        ).filter(
            Path.ancestor == self.id,
            Path.length.between(1, options['depth'])
        ).options(
            orm.joinedload_all('locations.paths')
        )

    def move(self, new_parent):
        """Moves this location to under new location

        This will also recursivly move all children of this location.

        Because this method uses raw queries all objects in the session will
        be expired after calling this method.

        :param Location new_parent: The new parent for this location
        """
        session = get_db()
        self._del_non_interconnected_paths(session)
        self._recreate_paths(session, self.id, new_parent.id)
        self._parent = new_parent

        mark_changed(session)
        session.expire_all()

    def delete(self):
        """Deletes this location and any children of this location. Any content
        entries that become orphant will also be deleted.

        Because this method uses raw queries all objects in the session will
        be expired after calling this method.
        """
        def _del_path_subtree(session):
            if session.bind.dialect.name == "mysql":
                session.execute("""DELETE l2 from location
                    JOIN path ON path.ancestor = location.id
                    JOIN location AS l2 ON path.descendant = l2.id
                    WHERE location.id = :location_id
                """, {'location_id': self.id})
            else:
                subq = session.query(Path.descendant).filter(
                    Path.ancestor == self.id
                ).subquery()
                session.query(Location).filter(
                    Location.id.in_(subq)
                ).delete(synchronize_session=False)

        session = get_db()
        _del_path_subtree(session)

        # Clean up any content that might have been orphaned
        session.query(Content).filter(
            ~Content.locations.any()
        ).delete(synchronize_session=False)

        mark_changed(session)
        session.expire_all()

    def _del_non_interconnected_paths(self, session):
        """Deletes paths that are not interconnected."""
        if session.bind.dialect.name == "mysql":
            r = session.execute("""DELETE P FROM path as p
                JOIN path AS d ON p.descendant = d.descendant
                LEFT JOIN path as X
                    ON x.ancestor = d.ancestor
                    AND x.descendant = p.ancestor
                WHERE
                    d.ancestor = :location_id
                    AND x.ancestor IS NULL
            """, {'location_id': self.id})
            print("RES %s" % r.rowcount)
        else:
            subq = session.query(Path.descendant).filter(
                Path.ancestor == self.id
            ).subquery()
            session.query(Path).filter(
                Path.descendant.in_(subq),
                ~Path.ancestor.in_(subq)
            ).delete(synchronize_session=False)

    def _recreate_paths(self, session, location_id, new_location_id):
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
                supertree.descendant = :new_parent_location
        """, {
            "subtree": location_id,
            "new_parent_location": new_location_id
        })

    def _sort_paths(self):
        self.paths.sort(key=lambda path: path.length, reverse=True)


class Content(Base):
    """Represents a resource in the content/tree structure

    A resource can have multiple locations in the tree and it will always have
    at least one.

    Example usage::

        root = Content(name='Name here', slug='name-here')
        child = Content(root.main_location)
        child.name = "Child name here"
        child.slug = "child-name-here"
    """
    __mapper_args__ = {
        'polymorphic_identity': 'content',
        'polymorphic_on': 'type'
    }
    __name__ = 'Content'
    __editable_fields__ = {'name', 'slug'}

    id = sa.Column(sa.Integer, primary_key=True)
    creator_id = sa.Column(
        sa.Integer,
        sa.ForeignKey('content.id'),
    )
    name = sa.Column(sa.String(1024), nullable=False)
    type = sa.Column(sa.String(50), nullable=False)
    slug = sa.Column(sa.String(250), nullable=False)
    own_content = orm.relationship(
        'Content',
        backref=orm.backref('creator', remote_side=[id])
    )
    locations = orm.relationship(
        'Location',
        lazy='joined',
        backref='content',
    )

    def __init__(self, parent=None, **kwargs):
        """
        :param Location parent: Where in the tree to place the resource.
                                Pass in None if you want to create a new root
                                Content or a location instance to create the
                                resource below that location.
        :param string name: The content's name
        :param string slug: The content's slug
        """
        super(Content, self).__init__(**kwargs)

        if parent is None:
            location = Location()
        else:
            location = parent.__class__(parent)

        self.main_location = location

    @property
    def main_location(self):
        """Fetches the main location

        :throws sqlalchemy.orm.exc.NoResultFound: If no main location is found
        :rtype: Location
        """
        for l in self.locations:
            if l.is_main:
                return l

        raise orm.exc.NoResultFound("No main location found")

    @main_location.setter
    def main_location(self, new_main_location):
        """Sets the main location for this resource

        If the location is not already one of the locations for this resource
        it will be added as a location. The previous main location will be
        changed to a non main location.

        :param new_main_location Location: Location to set as the main
        """
        new_main_location.is_main = True
        self._main_location = new_main_location

        for location in self.locations:
            location.is_main = False

        if not new_main_location in self.locations:
            self.locations.append(new_main_location)

    @property
    def parent(self):
        return self.main_location.parent

    @property
    def slugs(self):
        return self.main_location.slugs

    def children(self, *args, **kwargs):
        return self.main_location.children(*args, **kwargs)

    def ancestors(self, *args, **kwargs):
        return self.main_location.ancestors(*args, **kwargs)

    def location_for_parent(self, parent_location):
        for l in self.locations:
            if l.parent and l.parent.id == parent_location.id:
                return l

    def delete(self):
        """
        Need to fetch all content in a subtree, then delete them.

        Locations will be deleted thanks to cascade deletes.
        Paths will be deleted thanks to cascade deletes.
        """
        def _del_resource_subtree(session):
            if session.bind.dialect.name == "mysql":
                session.execute("""
                    DELETE content FROM content
                        WHERE content.id IN (
                            SELECT l2.content_id
                            FROM location
                            JOIN path ON path.ancestor = location.id
                            JOIN location AS l2 ON path.descendant = l2.id
                            WHERE location.content_id = :content_id
                        );
                """, {'content_id': self.id})
            else:
                L2 = orm.aliased(Location)
                q = session.query(L2.content_id).select_from(Location).join(
                    Path, Path.ancestor == Location.id
                ).join(
                    L2, L2.id == Path.descendant
                ).filter(
                    Location.content_id == self.id
                ).subquery()
                session.query(Content).filter(
                    Content.id.in_(q)
                ).delete(synchronize_session=False)

        session = orm.session.object_session(self)
        _del_resource_subtree(session)


class ContentType(object):
    @declarative.declared_attr
    def __mapper_args__(cls):
        return {'polymorphic_identity': cls.__tablename__}

    @declarative.declared_attr
    def id(cls):
        return sa.Column(
            sa.Integer,
            sa.ForeignKey(
                'content.id',
                ondelete='CASCADE',
            ),
            primary_key=True
        )
