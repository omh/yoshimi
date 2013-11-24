from yoshimi import test
from yoshimi.content import Content, Location
from .types import get_content


class TestContent(test.TestCase):
    def test_create_root(self):
        root = Content()

        self.assertEquals(len(root.locations), 1)

    def test_add_location(self):
        root = Content()
        root.locations.append(Location())

        self.assertEquals(len(root.locations), 2)

    def test_main_location_set_on_init(self):
        resource = Content()
        self.assertTrue(resource.locations[0].is_main)

    def test_get_main_location(self):
        resource = Content()
        self.assertIsNotNone(resource.main_location)

    def test_set_main_location(self):
        main_location = Location()
        resource = Content()
        resource.main_location = main_location

        self.assertTrue(resource.main_location == main_location)

    def test_main_location_added_as_location_if_not_already(self):
        resource = Content()
        resource.main_location = Location()

        self.assertTrue(len(resource.locations) == 2)

    def test_only_one_main_location(self):
        resource = Content()
        resource.locations.append(Location())
        resource.main_location = Location()

        self.assertFalse(resource.locations[0].is_main)
        self.assertFalse(resource.locations[1].is_main)

    def test_main_location_throws_exception_when_not_set(self):
        import sqlalchemy
        resource = Content()
        resource.main_location.is_main = False

        with self.assertRaises(sqlalchemy.orm.exc.NoResultFound):
            resource.main_location

    def test_content_has_creator(self):
        user = Content()
        resource = Content(creator=user)

        self.assertEqual(user, resource.creator)

    def test_creator_has_list_of_own_content(self):
        user = Content()
        Content(creator=user)
        Content(creator=user)

        self.assertEqual(len(user.own_content), 2)


class TestContentDatabase(test.DatabaseTestCase):
    def test_main_location_is_persisted(self):
        resource = get_content()
        resource.locations.append(Location())
        self.s.add(resource)
        self.s.commit()

        self.assertTrue(resource.locations[0].is_main)
        self.assertFalse(resource.locations[1].is_main)
