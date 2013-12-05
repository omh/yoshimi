from yoshimi import test
from yoshimi.repo import (
    Proxy,
    Query,
)
from yoshimi.content import Location
from yoshimi.content import Content
from .content.types import (
    Article,
    Folder,
    get_article,
    get_folder,
    get_content,
)


class TestProxy(test.TestCase):
    def test_calls_original_method(self):
        self.assertEqual(self._get_proxy().test(), 'test')

    def test_doesnt_calls_original_method(self):
        self.assertEqual(self._get_proxy().no_proxy(), 'proxy')

    def test_call_undefined_method(self):
        with self.assertRaises(AttributeError):
            self.assertEqual(self._get_proxy().undefined(), 'proxy')

    def _get_proxy(self):
        class TestObject():
            def test(self):
                return 'test'

        class Cut(Proxy):
            def __init__(self):
                self._proxy = TestObject()

            def no_proxy(self):
                return 'proxy'

        return Cut()


class TestQueryEagerLoading(test.QueryCountTestCase):
    def test_load_path_with_location(self):
        id = self.get_id_from_added_object(Location())

        with self.count_queries():
            fetched_loc = Query(self.s, Location).load_path() \
                .filter_by(id=id).one()
            fetched_loc.paths

        self.assertQueryCount(1)

    def test_load_path_with_content(self):
        id = self.get_id_from_added_object(get_content())

        with self.count_queries():
            fetched_content = Query(self.s, Content).load_path() \
                .filter_by(id=id).one()
            fetched_content.main_location.paths

        self.assertQueryCount(1)

    def test_load_content_with_location(self):
        id = self.get_id_from_added_object(get_article())

        with self.count_queries():
            fetched_loc = Query(self.s, Location).load_content() \
                .filter_by(id=id).one()
            fetched_loc.content.id

        self.assertQueryCount(1)

    def test_load_locations_with_article(self):
        id = self.get_id_from_added_object(get_article())

        with self.count_queries():
            fetched_loc = Query(self.s, Article).load_locations() \
                .filter_by(id=id).one()
            fetched_loc.main_location

        self.assertQueryCount(1)


class TestQueryChildren(test.DatabaseTestCase):
    def setUp(self):
        super().setUp()
        # - root
            # - - article 1
            # - - article 2
            # - - folder 1
                # - - article 3
            # - - folder 2
                # - - article 4
        self.root = get_folder(name='root')
        self.a1 = get_article(
            self.root.main_location, name='a1', title='a1 title'
        )
        self.a2 = get_article(self.root.main_location, name='a2')
        self.f1 = get_folder(self.root.main_location, name='f1')
        self.f2 = get_folder(self.root.main_location, name='f2')
        self.fa1 = get_article(self.f1.main_location, name='fa1')
        self.fa2 = get_article(self.f2.main_location, name='fa2')

        self.s.add(self.root)
        self.s.commit()

        self.query = Query(self.s, self.root)

    def test_get_children(self):

        children = self.query.children() \
            .order_by(Location.id).all()

        self.assertEquals(len(children), 4)
        self.assertEquals(children[0], self.a1.main_location)
        self.assertEquals(children[1], self.a2.main_location)
        self.assertEquals(children[2], self.f1.main_location)
        self.assertEquals(children[3], self.f2.main_location)

    def test_filter_children_by_entity_type(self):
        children = self.query.children(Folder). \
            order_by(Location.id).all()

        self.assertEquals(len(children), 2)
        self.assertEquals(children[0], self.f1.main_location)
        self.assertEquals(children[1], self.f2.main_location)

    def test_filter_children_with_two_entity_types(self):
        children = self.query.children(Folder, Article).all()

        self.assertEquals(len(children), 4)

    def test_filter_children_on_attribute(self):
        a1 = self.query.children(Article).filter(
            Article.title == 'a1 title'
        ).one()

        self.assertEqual(a1.content.title, 'a1 title')

    def test_filter_children_on_content_attribute(self):
        a1 = self.query.children(Article).filter(
            Content.name == 'a1'
        ).one()

        self.assertEqual(a1, self.a1.main_location)

    def test_children_with_depth_of_two(self):
        children = self.query.children(Folder, Article).depth(2).all()

        self.assertEqual(len(children), 6)
