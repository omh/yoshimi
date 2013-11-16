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

        slugs = a2.slugs

        self.assertEqual('Folder', slugs[0])
        self.assertEqual('Article1', slugs[1])
        self.assertEqual('Article2', slugs[2])


@test.all_databases
class TestContentDatabase(test.DatabaseTestCase):
    def test_get_children(self):
        root = get_folder(name='f1')
        child1 = get_article(root.main_location, name='c1')
        child2 = get_article(root.main_location, name='c2')
        self.s.add(root)
        self.s.commit()

        children = root.children().order_by(Content.id).all()

        self.assertEquals(len(children), 2)
        self.assertEquals(children[0], child1)
        self.assertEquals(children[1], child2)

    def test_filter_children_by_entity_type(self):
        root = get_folder(name='f1')
        get_article(root.main_location, name='c1')
        child2 = get_folder(root.main_location, name='c2')
        self.s.add(root)
        self.s.commit()

        children = root.children(Folder).order_by(Content.id).all()

        self.assertEquals(len(children), 1)
        self.assertEquals(children[0], child2)

    def test_filter_children_with_two_entity_types(self):
        root = get_folder(name='f1')
        get_article(root.main_location, name='c1')
        get_folder(root.main_location, name='c2')
        self.s.add(root)
        self.s.commit()

        children = root.children(Folder, Article).all()

        self.assertEquals(len(children), 2)

    def test_children_with_depth_of_two(self):
        root = get_folder(name='f1')
        child1 = get_article(root.main_location, name='c1')
        self.s.add(root)
        self.s.commit()
        # Commit child2 separately to guarantee it will be inserted after
        # child1 so that we can order on the id to compare the order
        child2 = get_folder(child1.main_location, name='c2')
        self.s.add(child2)
        self.s.commit()

        children = root.children(Article, Folder, depth=2)
        children = children.order_by(Content.id.asc()).all()

        self.assertEqual(len(children), 2)
        self.assertEqual(children[0], child1)
        self.assertEqual(children[1], child2)

    def test_get_ancestors(self):
        root = get_folder(name='f1')
        child1 = get_article(root.main_location, name='c1')
        child2 = get_folder(child1.main_location, name='c2')
        self.s.add_all([root, child1, child2])
        self.s.commit()

        ancestors = child2.ancestors().all()

        self.assertEqual(len(ancestors), 3)
        self.assertEqual(ancestors[0], root.main_location)
        self.assertEqual(ancestors[1], child1.main_location)
        self.assertEqual(ancestors[2], child2.main_location)

    def test_delete_entity_that_have_children(self):
        root = get_folder(name='f1')
        root2 = get_folder(name='f2')
        child1 = get_article(root.main_location, name='c1')
        child2 = get_folder(child1.main_location, name='c2')
        self.s.add_all([root, child1, child2, root2])
        self.s.commit()

        root.delete()
        self.s.commit()

        self.assertEqual(self.s.query(Path).count(), 1)
        self.assertEqual(self.s.query(Location).count(), 1)
        self.assertEqual(self.s.query(Content).count(), 1)
        self.assertEqual(self.s.query(Article).count(), 0)
        self.assertEqual(self.s.query(Folder).count(), 1)

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

    def test_find_child_location_of_parent(self):
        root = get_folder(name='r1')
        root2 = get_folder(name='r2')
        root3 = get_folder(name='r3')
        article = get_article(root.main_location, name='a1')
        l2 = Location(root2.main_location)
        l3 = Location(root3.main_location)
        article.locations.append(l2)
        article.locations.append(l3)
        self.s.add_all([root, root2, root3, article])
        self.s.commit()

        l2_fetched = article.location_for_parent(root2.main_location)
        l3_fetched = article.location_for_parent(root3.main_location)
        self.assertEqual(l2_fetched, l2)
        self.assertEqual(l3_fetched, l3)
