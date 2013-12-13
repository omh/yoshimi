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

# @TODO test children query does not trigger extra query when accessing content
# type attributes, e.g article.title


class TestQueryEagerLoading(test.QueryCountTestCase):
    def test_load_path_with_content(self):
        id = self.get_id_from_added_object(get_content())

        with self.count_queries():
            fetched_content = Query(self.s, Content).load_path() \
                .filter_by(id=id).one()
            fetched_content.paths

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
        self.a1 = get_article(parent=self.root, name='a1', title='a1 title')
        self.a2 = get_article(parent=self.root, name='a2')
        self.f1 = get_folder(parent=self.root, name='f1')
        self.f2 = get_folder(parent=self.root, name='f2')
        self.fa1 = get_article(parent=self.f1, name='fa1')
        self.fa2 = get_article(parent=self.f2, name='fa2')

        self.s.add(self.root)
        self.s.commit()

        self.query = Query(self.s, self.root)

    def test_get_children(self):
        children = self.query.children() \
            .order_by(Content.id).all()

        self.assertEquals(len(children), 4)
        self.assertEquals(children[0], self.a1)
        self.assertEquals(children[1], self.a2)
        self.assertEquals(children[2], self.f1)
        self.assertEquals(children[3], self.f2)

    def test_filter_children_by_entity_type(self):
        children = self.query.children(Folder). \
            order_by(Folder.id).all()

        self.assertEquals(len(children), 2)
        self.assertEquals(children[0], self.f1)
        self.assertEquals(children[1], self.f2)

    def test_filter_children_with_two_entity_types(self):
        children = self.query.children(Folder, Article).all()

        self.assertEquals(len(children), 4)

    def test_filter_children_on_attribute(self):
        a1 = self.query.children(Article).filter(
            Article.title == 'a1 title'
        ).one()

        self.assertEqual(a1.title, 'a1 title')

    def test_filter_children_on_content_attribute(self):
        a1 = self.query.children(Article).filter(
            Content.name == 'a1'
        ).one()

        self.assertEqual(a1, self.a1)

    def test_children_with_depth_of_two(self):
        children = self.query.children(Folder, Article).depth(2).all()

        self.assertEqual(len(children), 6)


class TestRepo(test.TestCase):
    def test_move(self):
        repo = Repo(test.Mock())
        subject = test.Mock()
        rv = repo.move(subject)

        self.assertIsInstance(rv, MoveOperation)


@test.all_databases
class TestMoveOperation(test.DatabaseTestCase):
    def test_to(self):
        root = get_folder(name='f1')
        subject = get_article(root, name='a1')
        new_parent = get_folder(root, name='a2')
        self.s.add(root)
        self.s.commit()

        move = MoveOperation(self.s, subject)
        move.to(new_parent)

        self.assertEqual(subject.parent, new_parent)


@test.all_databases
class TestDeleteOperation(test.DatabaseTestCase):
    def setUp(self):
        """
        - root [main, folder]
          - child1 [loc: 1, main, article]
            - child2 [main, folder]
        - root2 [main, folder]
          - child3 [main, article]
            - child4 [main, folder]
        path count: 12
        content count: 6
        article count: 2
        folder count: 4
        """
        super().setUp()

        self.root = get_folder(name='r1')
        self.child1 = get_article(self.root, name='a1')
        self.child2 = get_folder(self.child1, name='a2')

        self.root2 = get_folder(name='r2')
        self.child3 = get_article(self.root2, name='a3')
        self.child4 = get_folder(self.child3, name='a4')

        self.s.add_all([self.root, self.child1, self.child2])
        self.s.add_all([self.root2, self.child3, self.child4])
        self.s.commit()

        self.path_count = 12
        self.content_count = 6
        self.article_count = 2
        self.folder_count = 4

        self.fut = DeleteOperation(self.s)

    def test_delete_single_object(self):
        self.fut.delete(self.child4)
        self.assertSubtree(
            path_count=self.path_count - 3,
            content_count=self.content_count - 1,
            article_count=self.article_count,
            folder_count=self.folder_count - 1,
        )

    def test_delete_subtree(self):
        self.fut.delete(self.root)
        self.assertSubtree(
            path_count=self.path_count - 6,
            content_count=self.content_count - 3,
            article_count=self.article_count - 1,
            folder_count=self.folder_count - 2,
        )

    def assertSubtree(
            self,
            path_count=0,
            content_count=0,
            article_count=0,
            folder_count=0,
    ):
        self.assertEqual(self.s.query(Path).count(), path_count)
        self.assertEqual(self.s.query(Content).count(), content_count)
        self.assertEqual(self.s.query(Article).count(), article_count)
        self.assertEqual(self.s.query(Folder).count(), folder_count)
