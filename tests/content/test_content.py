from yoshimi import test
from yoshimi.content import Content
from .types import get_content


class TestContent(test.TestCase):
    def test_content_has_creator(self):
        user = Content()
        resource = Content(creator=user)

        self.assertEqual(user, resource.creator)

    def test_creator_has_list_of_own_content(self):
        user = Content()
        Content(creator=user)
        Content(creator=user)

        self.assertEqual(len(user.own_content), 2)

    def test_parent(self):
        c1 = get_content()
        c2 = get_content(parent=c1, name='c2')

        self.assertEquals(c2.parent, c1)

    def test_slugs(self):
        f1 = get_content(slug='Folder')
        a1 = get_content(parent=f1, slug='Article1')
        a2 = get_content(parent=a1, slug='Article2')

        slugs = a2.slugs

        self.assertEqual('Folder', slugs[0])
        self.assertEqual('Article1', slugs[1])
        self.assertEqual('Article2', slugs[2])

    def test_lineage(self):
        root = get_content(name='f1')
        child1 = get_content(parent=root, name='c1')
        child2 = get_content(parent=child1, name='c2')

        ancestors = child2.lineage

        self.assertEqual(len(ancestors), 3)
        self.assertEqual(ancestors[0], root)
        self.assertEqual(ancestors[1], child1)
        self.assertEqual(ancestors[2], child2)

    def test_paths_to_root_are_created(self):
        root = Content()
        child = Content(root)

        self.assertEquals(len(child.paths), 2)
        self.assertEquals(child._sorted_paths()[0].length, 1)
        self.assertEquals(child._sorted_paths()[1].length, 0)
