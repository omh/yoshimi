from yoshimi import test
from yoshimi.content import Location
from .types import get_content


class TestLocation(test.TestCase):
    def test_get_parent(self):
        root = Location()
        child = Location(root)

        self.assertEquals(root, child.parent)


class TestLocationDatabase(test.DatabaseTestCase):
    def test_create_paths_to_root_created(self):
        root = Location()
        child = Location(root)
        self.s.add(root)
        self.s.commit()

        self.assertEquals(len(child.paths), 2)

        # Ensure path lenght is set correctly
        self.assertEquals(child.paths[0].length, 1)
        self.assertEquals(child.paths[1].length, 0)

    def test_get_parent_no_session(self):
        root = Location()
        self.s.add(root)

        self.assertIsNone(root.parent)

    def test_get_parent(self):
        root = Location()
        child = Location(root)
        self.s.add(root)
        self.s.commit()

        self.assertEquals(
            child.parent, root
        )

    def test_parents_multiple_levels(self):
        root = get_content()
        child = get_content(root.locations[0])
        child2 = get_content(child.locations[0])
        self.s.add(root)
        self.s.commit()

        self.assertEquals(
            child2.main_location.parent.parent, root.main_location
        )

    def test_move(self):
        root = Location()
        root2 = Location()
        child = Location(root)
        self.s.add(root)
        self.s.add(root2)
        self.s.add(child)
        self.s.commit()

        child.move(root2)
        self.assertEquals(root2, child.parent)
