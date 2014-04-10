import pytest
import sqlalchemy
from tests.yoshimi import DatabaseTestCase
from tests.yoshimi.contenttypes import get_content
from yoshimi.entities import TrashContent
from yoshimi.trash import Trash


class TestTrashContent:
    def test_relationship_with_content(self):
        c1 = get_content()
        entity = TrashContent(content=c1)

        assert entity.content == c1
        assert c1.trash_info == entity


class TestTrash(DatabaseTestCase):
    def setup(self):
        super().setup()
        self.root = get_content()
        self.c1 = get_content(parent=self.root)
        self.c2 = get_content(parent=self.c1)
        self.c3 = get_content(parent=self.c2)
        self.s.add(self.root)
        self.s.flush()
        self.trash = Trash(self.s)
        self.trash_count = self._trash_count()

    def test_insert_single_soft(self):
        self.trash.insert(self.c3)

        trash_entry = self._get_trash_entity(self.c3.id)
        assert trash_entry is not None
        assert trash_entry.created_at is not None
        assert self.c3.is_trashed is True
        assert self.c1.is_trashed is False

    def test_insert_single_not_soft(self):
        self.trash.insert(self.c3, soft=False)

        assert self.c3.is_pending_deletion is True

    def test_insert_subtree(self):
        self.trash.insert(self.root)

        assert self.root.is_trashed is True
        assert self.c1.is_trashed is True
        assert self.c2.is_trashed is True
        assert self.c3.is_trashed is True

    def test_count(self):
        self.trash.insert(self.c3)
        assert self.trash.count() == 1

    def test_items(self):
        self.trash.insert(self.c2)
        assert len(self.trash.items().all()) == 2

    def test_empty(self):
        self.trash.insert(self.c3)

        self.trash.empty()

        assert self.c3.is_pending_deletion is True
        assert self._trash_count() == 0

    def test_permanently_empty(self):
        self.trash.insert(self.c3)

        self.trash.empty()
        self.trash.permanently_empty()

        with pytest.raises(sqlalchemy.orm.exc.ObjectDeletedError):
            self.c3.id

    def test_restore_without_children(self):
        self.trash.insert(self.root)

        self.trash.restore(self.root, with_children=False)

        assert self.root.is_available is True
        assert self.c1.is_trashed is True
        assert self._trash_count() is 3

    def test_restore_with_children(self):
        self.trash.insert(self.root)

        self.trash.restore(self.root, with_children=True)

        assert self.root.is_available is True
        assert self.c1.is_available is True
        assert self._trash_count() == 0

    def _trash_count(self):
        return self.s.query(TrashContent).count()

    def _get_trash_entity(self, id):
        return self.s.query(TrashContent).filter_by(
            content_id=id
        ).one()
