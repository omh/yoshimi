from pyramid import testing
from pyramid.httpexceptions import HTTPMovedPermanently
from yoshimi import test
from yoshimi import url


class _PathFunctionTests(test.TestCase):
    def setUp(self):
        self.req = test.Mock()
        self.req.matched_route.name = 'route_name'
        self.content = test.Mock()
        self.fut = None

    def assert_call(self, *args, **kw):
        pass

    def test_url_with_default_route(self):
        self.fut(self.req, self.content)
        self.assert_call(
            self.content, route_name='route_name',
        )

    def test_url_with_route(self):
        self.fut(self.req, self.content, route='testroute')
        self.assert_call(
            self.content, route_name='testroute',
        )

    def test_url_with_elements(self):
        self.fut(self.req, self.content, 'edit')
        self.assert_call(
            self.content, ('edit'), route_name='route_name',
        )

    def test_url_with_query_params(self):
        self.fut(self.req, self.content, query={'q1': 'testing'})
        self.assert_call(
            self.content, route_name='route_name', query={'q1': 'testing'}
        )


class TestPath(_PathFunctionTests):
    def setUp(self):
        super().setUp()
        self.fut = url.path

    def assert_call(self, *args, **kw):
        self.req.resource_path.assert_called_with(*args, **kw)


class TestUrl(_PathFunctionTests):
    def setUp(self):
        super().setUp()
        self.fut = url.url

    def assert_call(self, *args, **kw):
        self.req.resource_url.assert_called_with(*args, **kw)


class TestResourceUrlAdapter(test.TestCase):
    def test_populates_location_aware_attributes(self):
        loc1 = test.MagicMock()
        loc2 = test.MagicMock()
        loc3 = test.MagicMock()
        loc3.lineage = [loc1, loc2, loc3]
        loc3.id = 1
        loc3.slugs = ['a', 'b', 'c']

        request = testing.DummyRequest()
        url.ResourceUrlAdapter(loc3, request)

        self.assertIsNone(loc1.__parent__)
        self.assertIsNotNone(loc1.__name__)
        self.assertIsNotNone(loc2.__parent__)
        self.assertIsNotNone(loc2.__name__)
        self.assertIsNotNone(loc3.__parent__)
        self.assertIsNotNone(loc3.__name__)


class TestRootFactory(test.TestCase):
    def setUp(self):
        self.request = testing.DummyRequest()
        self.request.matchdict['traverse'] = ("a", "b-1")
        self.request.resource_path = test.Mock()
        self.request.resource_path.return_value = '/a/b-1'
        self.request.y_path = test.Mock()
        self.request.y_path.return_value = '/a/b-1'

        self.loc1 = test.Mock()
        self.loc2 = test.Mock()
        self.loc2.lineage = [self.loc1, self.loc2]
        self.context_getter = lambda id: self.loc2

        self.patched_url = test.patch('yoshimi.url.path').start()
        self.patched_url.return_value = '/a/b-1'
        self.addCleanup(test.patch.stopall)

    def test_returns_resource_root(self):
        root = url.RootFactory(self.context_getter)(self.request)
        self.assertEqual(self.loc2, root['a']['b-1'])

    def test_returns_none_without_traverse_match(self):
        self.request.matchdict = None
        root = url.RootFactory(self.context_getter)(self.request)
        self.assertIsNone(root)

    def test_returns_none_without_context(self):
        root = url.RootFactory(lambda id: None)(self.request)
        self.assertIsNone(root)

    def test_raises_redirect_on_url_mismatch(self):
        self.request.matchdict['traverse'] = ("bla-1",)
        with self.assertRaises(HTTPMovedPermanently) as cm:
            url.RootFactory(self.context_getter)(self.request)

        self.assertEqual(cm.exception.location, '/a/b-1')

    def test_returns_resource_root_with_trailing_view(self):
        self.request.matchdict['traverse'] = ('a', 'b-1', 'view')
        root = url.RootFactory(self.context_getter)(self.request)
        self.assertEqual(self.loc2, root['a']['b-1'])

    def test_returns_none_with_invalid_url_format(self):
        self.request.matchdict['traverse'] = ('a', 'b2')
        self.context_getter = test.Mock()
        self.context_getter.return_value = None

        root = url.RootFactory(self.context_getter)(self.request)

        self.assertIsNone(root)
