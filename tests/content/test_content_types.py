from yoshimi import test
from .types import get_article, get_folder


class TestContent(test.TestCase):
    def test_create_new(self):
        article = get_article(name='testing')
        self.assertEquals(article.name, 'testing')

    def test_parent(self):
        article1 = get_article()
        article2 = get_article(parent=article1, name='a2')

        self.assertEquals(article2.parent, article1)

    def test_slugs(self):
        f1 = get_folder(slug='Folder')
        a1 = get_article(parent=f1, slug='Article1')
        a2 = get_article(parent=a1, slug='Article2')

        slugs = a2.slugs

        self.assertEqual('Folder', slugs[0])
        self.assertEqual('Article1', slugs[1])
        self.assertEqual('Article2', slugs[2])

    def test_lineage(self):
        root = get_folder(name='f1')
        child1 = get_article(parent=root, name='c1')
        child2 = get_folder(parent=child1, name='c2')

        ancestors = child2.lineage

        self.assertEqual(len(ancestors), 3)
        self.assertEqual(ancestors[0], root)
        self.assertEqual(ancestors[1], child1)
        self.assertEqual(ancestors[2], child2)


class TestContentDatabase(test.DatabaseTestCase):
    def test_lineage(self):
        root = get_folder(name='f1')
        child1 = get_article(parent=root, name='c1')
        child2 = get_folder(parent=child1, name='c2')
        self.s.add_all([root, child1, child2])
        self.s.commit()

        ancestors = child2.lineage

        self.assertEqual(len(ancestors), 3)
        self.assertEqual(ancestors[0], root)
        self.assertEqual(ancestors[1], child1)
        self.assertEqual(ancestors[2], child2)
