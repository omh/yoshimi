from datetime import datetime

from zope.sqlalchemy import mark_changed
from sqlalchemy import insert
from sqlalchemy.sql.expression import literal

from yoshimi.entities import TrashContent
from yoshimi.content import (
    Content,
    Path
)


class Trash:
    def __init__(self, session):
        self._session = session

    def insert(self, target, soft=True):
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

    def empty(self):
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
        self._session.query(Content).filter_by(
            status_id=Content.status.PENDING_DELETION
        ).delete(
            synchronize_session=False
        )

        mark_changed(self._session)
        self._session.expire_all()

    def restore(self, target, with_children=True):
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
