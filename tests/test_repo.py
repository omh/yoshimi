from yoshimi import test
from yoshimi.repo import (
    Repo,
    Proxy,
    Query,
    MoveOperation,
    DeleteOperation,
)
from yoshimi.content import (
    Path,
    Location,
    Content,
)
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
        class TestObject:
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


class TestRepo(test.TestCase):
    def test_move(self):
        repo = Repo(test.Mock())
        subject = test.Mock()
        rv = repo.move(subject)

        self.assertIsInstance(rv, MoveOperation)

    @test.patch('yoshimi.repo.DeleteOperation')
    def test_delete_location(self, delete):
        session = test.Mock()
        repo = Repo(session)
        subject = Location()
        repo.delete(subject)

        delete.assert_called_once_with(session)
        delete.return_value.delete_location.assert_called_once_with(subject)


@test.all_databases
class TestMoveOperation(test.DatabaseTestCase):
    def test_to(self):
        root = get_folder(name='f1')
        subject = get_article(root.main_location, name='a1')
        new_parent = get_folder(root.main_location, name='a2')
        self.s.add(root)
        self.s.commit()

        move = MoveOperation(self.s, subject.main_location)
        move.to(new_parent.main_location)

        self.assertEqual(subject.parent, new_parent.main_location)

# Alternatives for dealing with main location:
# - Remove the concept of main location
# - Introduce more queries to find content with locations but no main location
# and assign a main location
# - Allow only one location and make up the rest with tags?
#
# Another issue:
# - Web frowns upon multiple urls for same content, bad for SEO.
# - can be mitigated with rel='canonical'

# Tags that drive urls and hence structure? e.g define which tags drive the
# structure


@test.all_databases
class TestDeleteOperation(test.DatabaseTestCase):
    def setUp(self):
        """
        - root [main, folder]
          - child1 [loc: 1, main, article]
            - child2 [main, folder]
        - child1 [loc: 2, article]
        - root2 [main, folder]
          - child3 [main, article]
            - child4 [main, folder]
       path count: 13
       loc count: 7
       content count: 6
       article count: 2
       folder count: 4
       """
        super().setUp()

        self.root = get_folder(name='r1')
        self.child1 = get_article(self.root.main_location, name='a1')
        self.child1.locations.append(Location())
        self.child2 = get_folder(self.child1.main_location, name='a2')

        self.root2 = get_folder(name='r2')
        self.child3 = get_article(self.root2.main_location, name='a3')
        self.child4 = get_folder(self.child3.main_location, name='a4')

        self.s.add_all([self.root, self.child1, self.child2])
        self.s.add_all([self.root2, self.child3, self.child4])
        self.s.commit()

        self.path_count = 13
        self.location_count = 7
        self.content_count = 6
        self.article_count = 2
        self.folder_count = 4

    # @TODO assert that content was removed
    def test_delete_main_location(self):
        delete = DeleteOperation(self.s)
        delete.delete_location(self.root.main_location)

        self.assertSubtree(
            path_count=7,
            location_count=3,
            content_count=3,
            article_count=1,
            folder_count=2,
        )

    def test_delete_location_on_content_with_multiple_locations(self):
        delete = DeleteOperation(self.s)
        delete.delete_location(self.child1.locations[1])

        self.assertSubtree(
            path_count=self.path_count - 1,
            location_count=self.location_count - 1,
            content_count=self.content_count,
            article_count=self.article_count,
            folder_count=self.folder_count,
        )

    def assertSubtree(
            self,
            path_count=0,
            location_count=0,
            content_count=0,
            article_count=0,
            folder_count=0,
    ):
        self.assertEqual(self.s.query(Path).count(), path_count)
        self.assertEqual(self.s.query(Location).count(), location_count)
        self.assertEqual(self.s.query(Content).count(), content_count)
        self.assertEqual(self.s.query(Article).count(), article_count)
        self.assertEqual(self.s.query(Folder).count(), folder_count)
