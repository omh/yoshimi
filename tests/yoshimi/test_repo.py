import pytest
from tests.yoshimi import (
    DatabaseTestCase,
    QueryCountTestCase,
    Mock,
    patch,
    all_databases,
)
from tests.yoshimi.contenttypes import (
    Article,
    Folder,
    get_article,
    get_folder,
    get_content,
)
from yoshimi.repo import (
    Repo,
    Query,
    MoveOperation,
    DeleteOperation,
    _QueryExtensions,
)
from yoshimi.content import (
    Path,
    Content,
)
from yoshimi.trash import Trash

# @TODO test children query does not trigger extra query when accessing content
# type attributes, e.g article.title


class TestRepo:
    @patch('yoshimi.repo.MoveOperation', autospec=MoveOperation)
    def test_move(self, move_class):
        session = Mock()
        repo = get_repo_mock(session=session)
        subject = Mock()

        rv = repo.move(subject)

        assert isinstance(rv, MoveOperation)
        move_class.assert_called_once_with(session, subject)

    @patch('yoshimi.repo.DeleteOperation', autospec=DeleteOperation)
    def test_delete(self, delete_class):
        session = Mock()
        repo = get_repo_mock(session=session)
        subject = Mock()

        repo.delete(subject)

        delete_class.assert_called_once_with(session)
        delete_class.return_value.delete.assert_called_once_with(subject)

    @patch('yoshimi.repo.Query', autospec=Query)
    def test_query(self, query_class):
        session = Mock()
        registry = Mock()
        query_extension = Mock(autospec=_QueryExtensions)
        query_extension.methods = {}
        registry.queryUtility.return_value = query_extension
        repo = Repo(registry, session)
        subject = Mock()

        rv = repo.query(subject)

        assert isinstance(rv, Query)
        query_class.assert_called_once_with(session, subject, {})

    @patch('yoshimi.repo.Trash', autospec=True)
    def test_trash(self, trash_class):
        session = Mock()
        repo = get_repo_mock(session=session)

        rv = repo.trash

        assert isinstance(rv, Trash)
        trash_class.assert_called_once_with(session)


class TestQueryEagerLoading(QueryCountTestCase):
    def test_load_path_with_content(self):
        id = self.get_id_from_added_object(get_content())

        with self.count_queries():
            fetched_content = Query(self.s, Content) \
                .load_path().filter_by(id=id).one()
            fetched_content.paths

        self.assert_query_count_is(1)


class TestQuery:
    def test_extension(self):
        # callable(query, *args, **kwargs)
        session = Mock()
        callable = Mock()
        query = Query(session, None, {'test_func': callable})
        query.test_func('a').get_query()

        # Unable to assert that callable was called with a lambda so simply
        # asserting that it was called
        assert callable.call_count == 1


class TestQueryChildren(DatabaseTestCase):
    def setup(self):
        super().setup()
        # - root
        # - - article 1
        # - - article 2
        # - - folder 1
        # - - - article 3
        # - folder 2
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

        assert len(children) == 4
        assert children[0] == self.a1
        assert children[1] == self.a2
        assert children[2] == self.f1
        assert children[3] == self.f2

    def test_filter_children_by_entity_type(self):
        children = self.query.children(Folder). \
            order_by(Folder.id).all()

        assert len(children) == 2
        assert children[0] == self.f1
        assert children[1] == self.f2

    def test_filter_children_with_two_entity_types(self):
        children = self.query.children(Folder, Article).all()

        assert len(children) == 4

    def test_filter_children_on_attribute(self):
        a1 = self.query.children(Article).filter(
            Article.title == 'a1 title'
        ).one()

        assert a1.title == 'a1 title'

    def test_filter_children_on_content_attribute(self):
        a1 = self.query.children(Article).filter(
            Content.name == 'a1'
        ).one()

        assert a1 == self.a1

    def test_children_with_depth_of_two(self):
        children = self.query.children(Folder, Article).depth(2).all()

        assert len(children) == 6


class TestQueryStatus(DatabaseTestCase):
    def setup(self):
        super().setup()
        self.a1 = get_article(name='a1')
        self.a1.status_id = self.a1.status.TRASHED
        self.a2 = get_article(name='a2')

        self.s.add_all((self.a1, self.a2))
        self.s.flush()

        self.query = Query(self.s, self.a1.__class__)

    def test_defaults_to_available_only(self):
        rv = self.query.all()

        assert len(rv) == 1
        assert rv[0] == self.a2


class TestContentGetter(DatabaseTestCase):
    def setup(self):
        super().setup()
        from yoshimi.repo import content_getter
        self.fut = content_getter

        self.a1 = get_content(name='a1')
        self.s.add(self.a1)
        self.s.flush()

        self.repo = get_repo_mock(session=self.s)

    def test_returns_content_when_found(self):
        rv = self.fut(self.repo, self.a1.id)
        assert rv == self.a1

    def test_raises_404_if_not_found(self):
        from pyramid.httpexceptions import HTTPNotFound
        with pytest.raises(HTTPNotFound):
            self.fut(self.repo, 999)


@all_databases
class TestMoveOperation(DatabaseTestCase):
    def test_to(self):
        root = get_folder(name='f1')
        subject = get_article(root, name='a1')
        new_parent = get_folder(root, name='a2')
        self.s.add(root)
        self.s.commit()

        move = MoveOperation(self.s, subject)
        move.to(new_parent)

        assert subject.parent == new_parent


@all_databases
class TestDeleteOperation(DatabaseTestCase):
    def setup(self):
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
        super().setup()

        self.root = get_folder(name='r1')
        self.child1 = get_article(self.root, name='a1')
        self.child2 = get_folder(self.child1, name='a2')

        self.root2 = get_folder(name='r2')
        self.child3 = get_article(self.root2, name='a3')
        self.child4 = get_folder(self.child3, name='a4')

        self.s.add_all([self.root, self.child1, self.child2])
        self.s.add_all([self.root2, self.child3, self.child4])
        self.s.commit()

        self.path_count = self.s.query(Path).count()
        self.content_count = self.s.query(Content).count()
        self.article_count = self.s.query(Article).count()
        self.folder_count = self.s.query(Folder).count()

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
        assert self.s.query(Path).count() == path_count
        assert self.s.query(Content).count() == content_count
        assert self.s.query(Article).count() == article_count
        assert self.s.query(Folder).count() == folder_count


def get_repo_mock(registry=None, session=None, query_extensions=None):
    if not session:
        session = Mock()
    if not registry:
        registry = Mock()
    if not query_extensions:
        query_extensions = {}

    query_extension = Mock(autospec=_QueryExtensions)
    query_extension.methods = query_extensions
    registry.queryUtility.return_value = query_extension
    repo = Repo(registry, session)

    return repo
