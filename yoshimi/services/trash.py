"""
    yoshimi.services.trash
    ~~~~~~~~~~~~~~~~~~~~~~

    Implements the concept of a Trash for content.

    :copyright: (c) 2013 by Ole Morten Halvorsen
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime

from zope.sqlalchemy import mark_changed
from sqlalchemy import insert
from sqlalchemy.sql.expression import literal
from sqlalchemy.orm import contains_eager
from yoshimi.entities import TrashContent
from yoshimi.content import (
    Content,
    Path
)


class Trash:
    """ Implements a soft delete for content.

    Content added to the trash will remain available and can be restored. The
    trash supports two ways of deleting content, 1) a "soft" delete and 2)
    a "hard" delete. A "soft" delete means content will be added to the trash
    and can be restored later. A "hard" delete means the content is marked as
    pending deletion and will be deleted by a background job.

    When the trash is emptied the content is not deleted right away as
    that is a deferred process that will be done in a background job. This is
    due to the potentially slow process of deleting content and all the data
    associated with it (e.g files and images that might exists on external
    system such as CDNs, etc) It's recommended that the trash is used when
    deleting content.

    Normally the trash is used via the repo object.

    Example usage::

        request.y_repo.trash.insert(article) # Can be restored by user
        # Restore the article and any children it had
        request.y_repo.trash.restore(article)

        request.y_repo.trash.insert(article)
        # Empty trash - article can no longer be restored
        request.y_repo.trash.empty()
    """
    def __init__(self, session):
        """
        :param session: SQLAlchemy session
        :type session: :class:`~sqlalchemy.orm.session.Session`
        """
        self._session = session

    def insert(self, target, soft=True):
        """ Inserts a content type into the trash.

        Any children of `target` will also be inserted into the trash
        recursively.

        A record (:class:`~yoshimi.entities.TrashContent`) will be inserted
        with meta data such as when the content type was deleted.

        By default this performs a `soft` insert which allows user to restore
        `target` if needed. Set `soft=True` if you want `target` to be deleted
        right away.

        Note that this method will expire all objects in the current session.

        :param target: Content type to insert into the trash
        :type target: :class:`~yoshimi.content.ContentType`
        :param bool soft: Soft or hard insert
        """
        if soft:
            status_id = Content.status.TRASHED
            self._insert_trash_entities(target, status_id)
            self._set_content_status(
                target,
                Content.status.AVAILABLE,
                Content.status.TRASHED,
            )
        else:
            status_id = Content.status.PENDING_DELETION
            self._set_content_status(
                target,
                Content.status.AVAILABLE,
                Content.status.PENDING_DELETION,
            )

        mark_changed(self._session)
        self._session.expire_all()

    def count(self):
        """ Returns the number of entries in the trash

        Only items marked as "trashed" will be counted. Anything pending
        deletion will not be counted.

        :return int: Number of items in the trash
        """
        return self._session.query(TrashContent).join(
            Content
        ).filter_by(
            status_id=Content.status.TRASHED
        ).count()

    def items(self):
        """ Returns query that fetches items in the Trash

        The items returned by the query will be
        :class:`~yoshimi.entities.TrashContent`. To get the
        :class:`~yoshimi.content.Content` use the `.content` property.

        :rtype: :class:`~sqlalchemy.orm.query.Query`
        """
        return self._session.query(TrashContent).join(
            Content
        ).filter(
            Content.status_id == Content.status.TRASHED
        ).order_by(
            TrashContent.created_at.desc()
        ).options(
            contains_eager(TrashContent.content)
            .joinedload(Content.paths, innerjoin=True),
        )

    def empty(self):
        """ Empties the trash

        The contents of the trash won't be deleted from the database right away
        as that is a deferred process done via a background job.

        Note that this method will expire all objects in the current session.
        """
        self._session.query(Content).filter_by(
            status_id=Content.status.TRASHED
        ).update(
            {Content.status_id: Content.status.PENDING_DELETION},
            synchronize_session=False
        )
        self._session.query(TrashContent).delete(synchronize_session=False)

        mark_changed(self._session)
        self._session.expire_all()

    def permanently_empty(self):
        """ Permanently removed items in the trash

        Physically deletes items that were marked "pending deletion".
        """
        self._session.query(Content).filter_by(
            status_id=Content.status.PENDING_DELETION
        ).delete(
            synchronize_session=False
        )

        mark_changed(self._session)
        self._session.expire_all()

    def restore(self, target, with_children=True):
        """ Restores `target` from the trash

        By default `target` and all its children will be restored. Specify
        `with_children=False` if you want to only restore `target` and not its
        children.

        Note that this method will expire all objects in the current session.

        :param target: Content type to restore from the trash
        :type target: :class:`~yoshimi.content.ContentType`
        :param bool with_children: Whether to include children
        """
        if with_children:
            self._delete_trash_entries(target)
            self._set_content_status(
                target,
                Content.status.TRASHED,
                Content.status.AVAILABLE,
            )
            mark_changed(self._session)
            self._session.expire_all()
        else:
            self._session.delete(target.trash_info)
            target.status_id = target.status.AVAILABLE
            self._session.add(target)

    def _set_content_status(self, target, old_status, new_status):
        self._children_query(target).filter_by(
            status_id=old_status
        ).update(
            {Content.status_id: new_status},
            synchronize_session=False
        )

    def _insert_trash_entities(self, target, status_id):
        insert_columns = (
            TrashContent.content_id,
            TrashContent.created_at,
        )
        select_columns = (
            Content.id,
            literal(datetime.utcnow()).label("created_at"),
        )
        children_query = self._children_query(
            target, select_columns
        ).filter_by(
            status_id=Content.status.AVAILABLE
        )

        self._session.execute(
            insert(TrashContent).from_select(
                insert_columns, children_query
            )
        )

    def _delete_trash_entries(self, target):
        self._session.query(TrashContent).filter(
            (TrashContent.content_id.in_(
                self._session.query(Path.descendant).select_from(
                    Path
                ).filter(
                    Path.ancestor == target.id
                )
            )) | (TrashContent.content_id == target.id)
        ).delete(synchronize_session=False)

    def _children_query(self, target, columns=None):
        if not columns:
            columns = (Content,)

        return self._session.query(*columns).filter(
            (Content.id.in_(
                self._session.query(Path.descendant).select_from(
                    Path
                ).filter(
                    Path.ancestor == target.id
                )
            )) | (Content.id == target.id)
        )
