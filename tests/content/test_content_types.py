from yoshimi import test
from yoshimi.content import Content, Location, Path
from .types import Article, Folder, get_article, get_folder


class TestContent(test.TestCase):
    def test_create_new(self):
        article = get_article(name='testing')
        self.assertEquals(article.name, 'testing')

    def test_has_main_location_attribute(self):
        article = get_article()
        self.assertIsNotNone(article.main_location)

    def test_can_set_main_location_attribute(self):
        article = get_article()
        location = Location()
        article.main_location = location

        self.assertEquals(article.main_location, location)

    def test_has_locations_attribute(self):
        article = get_article()
        self.assertEquals(len(article.locations), 1)

    def test_get_parent(self):
        article1 = get_article()
        article2 = get_article(article1.main_location, name='a2')

        self.assertEquals(article2.parent, article1.main_location)

    def test_get_entity_from_location(self):
        folder = get_folder()
        article = get_article(folder.main_location)

        self.assertEquals(
            article.main_location.parent.content, folder
        )

    def test_slugs(self):
        f1 = get_folder(slug='Folder')
        a1 = get_article(f1.main_location, slug='Article1')
        a2 = get_article(a1.main_location, slug='Article2')
        a2.locations.append(Location(f1.main_location))

        slugs = a2.main_location.slugs

        self.assertEqual('Folder', slugs[0])
        self.assertEqual('Article1', slugs[1])
        self.assertEqual('Article2', slugs[2])


@test.all_databases
class TestContentDatabase(test.DatabaseTestCase):
    def test_get_ancestors(self):
        root = get_folder(name='f1')
        child1 = get_article(root.main_location, name='c1')
        child2 = get_folder(child1.main_location, name='c2')
        self.s.add_all([root, child1, child2])
        self.s.commit()

        ancestors = child2.main_location.lineage

        self.assertEqual(len(ancestors), 3)
        self.assertEqual(ancestors[0], root.main_location)
        self.assertEqual(ancestors[1], child1.main_location)
        self.assertEqual(ancestors[2], child2.main_location)

    #def test_delete_entity_that_have_children(self):
        #root = get_folder(name='f1')
        #root2 = get_folder(name='f2')
        #child1 = get_article(root.main_location, name='c1')
        #child2 = get_folder(child1.main_location, name='c2')
        #self.s.add_all([root, child1, child2, root2])
        #self.s.commit()

        #root.delete()
        #self.s.commit()

        #self.assertEqual(self.s.query(Path).count(), 1)
        #self.assertEqual(self.s.query(Location).count(), 1)
        #self.assertEqual(self.s.query(Content).count(), 1)
        #self.assertEqual(self.s.query(Article).count(), 0)
        #self.assertEqual(self.s.query(Folder).count(), 1)

    def test_delete_location_that_have_children(self):
        root = get_folder(name='f1')
        root.locations.append(Location())
        root2 = get_folder(name='f2')
        child1 = get_article(root.locations[1], name='c1')
        child2 = get_folder(child1.main_location, name='c2')
        self.s.add_all([root, child1, child2, root2])
        self.s.commit()

        root.locations[1].delete()
        self.s.commit()

        # root's main location, root2's location
        self.assertEqual(self.s.query(Path).count(), 2)
        self.assertEqual(self.s.query(Location).count(), 2)
        self.assertEqual(self.s.query(Content).count(), 2)
        self.assertEqual(self.s.query(Article).count(), 0)
        self.assertEqual(self.s.query(Folder).count(), 2)
