from tests.yoshimi import DatabaseTestCase
from tests.yoshimi.contenttypes import (
    get_folder,
    get_article,
)


class TestContent:
    def test_create_new(self):
        article = get_article(name='testing')
        assert article.name == 'testing'

    def test_parent(self):
        article1 = get_article()
        article2 = get_article(parent=article1, name='a2')

        assert article2.parent == article1

    def test_slugs(self):
        f1 = get_folder(slug='Folder')
        a1 = get_article(parent=f1, slug='Article1')
        a2 = get_article(parent=a1, slug='Article2')

        slugs = a2.slugs

        assert 'Folder' == slugs[0]
        assert 'Article1' == slugs[1]
        assert 'Article2' == slugs[2]

    def test_lineage(self):
        root = get_folder(name='f1')
        child1 = get_article(parent=root, name='c1')
        child2 = get_folder(parent=child1, name='c2')

        ancestors = child2.lineage

        assert len(ancestors) == 3
        assert ancestors[0] == root
        assert ancestors[1] == child1
        assert ancestors[2] == child2


class TestContentDatabase(DatabaseTestCase):
    def test_lineage(self):
        root = get_folder(name='f1')
        child1 = get_article(parent=root, name='c1')
        child2 = get_folder(parent=child1, name='c2')
        self.s.add_all([root, child1, child2])
        self.s.commit()

        ancestors = child2.lineage

        assert len(ancestors) == 3
        assert ancestors[0] == root
        assert ancestors[1] == child1
        assert ancestors[2] == child2
