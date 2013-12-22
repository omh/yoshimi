import sqlalchemy
from yoshimi import test
from yoshimi.entities import TrashContent
from yoshimi.services import Trash
from .content.types import get_content


class TestTrashContent(test.TestCase):
    def test_relationship_with_content(self):
        c1 = get_content()
        entity = TrashContent(content=c1)

        self.assertEqual(entity.content, c1)
        self.assertEqual(c1.trash_info, entity)


class TestTrash(test.DatabaseTestCase):
    def setup(self):
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
        self.assertIsNotNone(trash_entry)
        self.assertIsNotNone(trash_entry.created_at)
        self.assertTrue(self.c3.is_trashed)
        self.assertFalse(self.c1.is_trashed)

    def test_insert_single_not_soft(self):
        self.trash.insert(self.c3, soft=False)

        self.assertTrue(self.c3.is_pending_deletion)

    def test_insert_subtree(self):
        self.trash.insert(self.root)

        self.assertTrue(self.root.is_trashed)
        self.assertTrue(self.c1.is_trashed)
        self.assertTrue(self.c2.is_trashed)
        self.assertTrue(self.c3.is_trashed)

    def test_empty(self):
        self.trash.insert(self.c3)

        self.trash.empty()

        self.assertTrue(self.c3.is_pending_deletion)
        self.assertEqual(self._trash_count(), 0)

    def test_permanently_empty(self):
        self.trash.insert(self.c3)

        self.trash.empty()
        self.trash.permanently_empty()

        with self.assertRaises(sqlalchemy.orm.exc.ObjectDeletedError):
            self.c3.id

    def test_restore_without_children(self):
        self.trash.insert(self.root)

        self.trash.restore(self.root, with_children=False)

        self.assertTrue(self.root.is_available)
        self.assertTrue(self.c1.is_trashed)
        self.assertEqual(self._trash_count(), 3)

    def test_restore_with_children(self):
        self.trash.insert(self.root)

        self.trash.restore(self.root, with_children=True)

        self.assertTrue(self.root.is_available)
        self.assertTrue(self.c1.is_available)
        self.assertEqual(self._trash_count(), 0)

    def _trash_count(self):
        return self.s.query(TrashContent).count()

    def _get_trash_entity(self, id):
        return self.s.query(TrashContent).filter_by(
            content_id=id
        ).one()
