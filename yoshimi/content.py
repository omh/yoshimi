from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import (
    backref,
    relationship,
)
from sqlalchemy.ext import declarative

from yoshimi.db import DeclarativeBase


Base = declarative.declarative_base(cls=DeclarativeBase)


class Path(Base):
    """Represents a node in the content structure.

    A Closure Table is used to maintain the tree structure in the database.
    """
    ancestor = Column(
        Integer,
        ForeignKey('content.id', ondelete='CASCADE'),
        primary_key=True,
    )
    descendant = Column(
        Integer,
        ForeignKey('content.id', ondelete='CASCADE'),
        primary_key=True,
    )
    length = Column(Integer, nullable=False)
    ancestor_content = relationship(
        'Content',
        foreign_keys=[ancestor],
        backref=backref(
            'ancestor_paths',
        ),
    )
    descendant_content = relationship(
        'Content',
        foreign_keys=[descendant],
        backref=backref(
            'descendant_paths',
        ),
    )


class Content(Base):
    """Represents a resource in the content/tree structure

    Example usage:

    .. code-block:: python

        root = Content(name='Name here', slug='name-here')
        child = Content(parent=root, name='Child name', slug='child name')
    """
    __mapper_args__ = {
        'polymorphic_identity': 'content',
        'polymorphic_on': 'type'
    }
    __name__ = 'Content'
    __editable_fields__ = {'name', 'slug'}

    id = Column(Integer, primary_key=True)
    creator_id = Column(Integer, ForeignKey('content.id'))
    name = Column(String(1024), nullable=False)
    # @TODO index on type, used by children query.
    type = Column(String(50), nullable=False)
    slug = Column(String(250), nullable=False)
    own_content = relationship(
        'Content',
        backref=backref('creator', remote_side=[id])
    )
    paths = relationship(Path, foreign_keys=[Path.descendant])

    def __init__(self, parent=None, **kwargs):
        """
        :param string name: The content's name
        :param string slug: The content's slug
        :param Content parent: Where in the tree to place the resource. Pass
         in None if you want to create a new root.
        """
        super(Content, self).__init__(**kwargs)

        self.paths.append(
            Path(
                ancestor_content=self,
                descendant_content=self,
                length=0
            )
        )

        if parent is not None:
            for parent_path in parent.descendant_paths:
                self.paths.append(
                    Path(
                        ancestor_content=parent_path.ancestor_content,
                        descendant_content=self,
                        length=parent_path.length + 1,
                    )
                )

    @property
    def slugs(self):
        return [p.ancestor_content.slug for p in self._sorted_paths()]

    @property
    def parent(self):
        """Returns the parent object

        If this object is on the top-level (i.e no parent) then None
        is returned.

        :rtype: A :class:`.Content` or None
        """
        try:
            return self._sorted_paths()[-2].ancestor_content
        except IndexError:
            return None

    @property
    def lineage(self):
        try:
            return [p.ancestor_content for p in self._sorted_paths()]
        except IndexError:
            return None

    def _sorted_paths(self):
        self._sort_paths()
        return self.paths

    def _sort_paths(self):
        self.paths.sort(key=lambda path: path.length, reverse=True)

    #def delete(self):
        #"""
        #Need to fetch all content in a subtree, then delete them.

        #Locations will be deleted thanks to cascade deletes.
        #Paths will be deleted thanks to cascade deletes.
        #"""
        #def _del_resource_subtree(session):
            #if session.bind.dialect.name == "mysql":
                #session.execute("""
                    #DELETE content FROM content
                        #WHERE content.id IN (
                            #SELECT l2.content_id
                            #FROM location
                            #JOIN path ON path.ancestor = location.id
                            #JOIN location AS l2 ON path.descendant = l2.id
                            #WHERE location.content_id = :content_id
                        #);
                #""", {'content_id': self.id})
            #else:
                #L2 = aliased(Location)
                #q = session.query(L2.content_id).select_from(Location).join(
                    #Path, Path.ancestor == Location.id
                #).join(
                    #L2, L2.id == Path.descendant
                #).filter(
                    #Location.content_id == self.id
                #).subquery()
                #session.query(Content).filter(
                    #Content.id.in_(q)
                #).delete(synchronize_session=False)

        #session = session.object_session(self)
        #_del_resource_subtree(session)


class ContentType:
    @declarative.declared_attr
    def __mapper_args__(cls):
        return {'polymorphic_identity': cls.__tablename__}

    @declarative.declared_attr
    def id(cls):
        return Column(
            Integer,
            ForeignKey(
                'content.id',
                ondelete='CASCADE',
            ),
            primary_key=True
        )
