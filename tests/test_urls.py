from pyramid.testing import DummyRequest
from pyramid.httpexceptions import (
    HTTPFound,
    HTTPMovedPermanently
)
from yoshimi import test
from yoshimi.url import (
    url,
    path,
    redirect_back,
    context_redirect_back,
    context_redirect_back_url,
    safe_redirect,
    ResourceUrlAdapter,
    RootFactory
)


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
        self.fut = path

    def assert_call(self, *args, **kw):
        self.req.resource_path.assert_called_with(*args, **kw)


class TestUrl(_PathFunctionTests):
    def setUp(self):
        super().setUp()
        self.fut = url

    def assert_call(self, *args, **kw):
        self.req.resource_url.assert_called_with(*args, **kw)


class TestContextRedirectBackUrl(test.TestCase):
    def setUp(self):
        def y_path(context):
            return '/context'

        self.req = DummyRequest()
        self.req.y_path = y_path

    @test.patch('yoshimi.url.safe_redirect')
    def test_with_back_get_param(self, safe_redirect):
        self.req.GET['back'] = '/back'
        context_redirect_back_url(self.req, 'bla')
        safe_redirect.assert_called_with(self.req, '/back')

    @test.patch('yoshimi.url.safe_redirect')
    def test_without_back_get_param(self, safe_redirect):
        context_redirect_back_url(self.req, 'bla')
        safe_redirect.assert_called_with(self.req, '/context')


class TestContextRedirectBack(test.TestCase):
    @test.patch('yoshimi.url.context_redirect_back_url', autospec=True)
    def test_context_redirect_back(self, url_func_mock):
        request_mock = test.Mock()
        context_mock = test.Mock()

        context_redirect_back(request_mock, context_mock)

        url_func_mock.assert_called_once_with(request_mock, context_mock)


class TestRedirectBack(test.TestCase):
    def setUp(self):
        def y_path(context):
            return '/context'

        self.req = DummyRequest()
        self.req.y_path = y_path

    def test_redirect_back(self):
        self.req.GET['back'] = '/testing'
        rv = redirect_back(self.req)

        self.assertIsInstance(rv, HTTPFound)
        self.assertEqual(rv.location, '/testing')

    def test_redirect_back_using_fallback(self):
        rv = redirect_back(self.req, fallback='/fallback')
        self.assertEqual(rv.location, '/fallback')


class TestSafeRedirect(test.TestCase):
    def setUp(self):
        self.req = DummyRequest()
        self.req.registry.settings = {}

    def test_redirect_to_same_host_is_ok(self):
        self.req.url = "http://www.example.com/some-page"
        url = "http://www.example.com/testing"
        rv = safe_redirect(self.req, url)
        self.assertEquals(url, rv)

    def test_redirect_to_relative_url_is_ok(self):
        url = "/testing"
        rv = safe_redirect(self.req, url)
        self.assertEquals(url, rv)

    def test_redirect_to_different_host_fails(self):
        url = "http://www.example2.com"
        rv = safe_redirect(self.req, url, fallback='/error')
        self.assertEquals(rv, '/error')

    def test_redirect_to_whitelisted_host_is_ok(self):
        self.req.registry.settings = {
            'yoshimi.host_whitelist': [
                'www.example.com'
            ]
        }
        url = "http://www.example.com"
        rv = safe_redirect(self.req, url, fallback='/error')
        self.assertEquals(rv, url)

    def test_redirect_to_not_whitelisted_host_fails(self):
        self.req.registry.settings = {
            'yoshimi.host_whitelist': [
                'www.example.com'
            ]
        }
        url = "http://www.example.com:81"
        rv = safe_redirect(self.req, url, fallback='/error')
        self.assertEquals(rv, '/error')


class TestResourceUrlAdapter(test.TestCase):
    def test_populates_location_aware_attributes(self):
        loc1 = test.MagicMock()
        loc2 = test.MagicMock()
        loc3 = test.MagicMock()
        loc3.lineage = [loc1, loc2, loc3]
        loc3.id = 1
        loc3.slugs = ['a', 'b', 'c']

        request = DummyRequest()
        ResourceUrlAdapter(loc3, request)

        self.assertIsNone(loc1.__parent__)
        self.assertIsNotNone(loc1.__name__)
        self.assertIsNotNone(loc2.__parent__)
        self.assertIsNotNone(loc2.__name__)
        self.assertIsNotNone(loc3.__parent__)
        self.assertIsNotNone(loc3.__name__)


class TestRootFactory(test.TestCase):
    def setUp(self):
        self.request = DummyRequest()
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
        root = RootFactory(self.context_getter)(self.request)
        self.assertEqual(self.loc2, root['a']['b-1'])

    def test_returns_none_without_traverse_match(self):
        self.request.matchdict = None
        root = RootFactory(self.context_getter)(self.request)
        self.assertIsNone(root)

    def test_returns_none_without_context(self):
        root = RootFactory(lambda id: None)(self.request)
        self.assertIsNone(root)

    def test_raises_redirect_on_url_mismatch(self):
        self.request.matchdict['traverse'] = ("bla-1",)
        with self.assertRaises(HTTPMovedPermanently) as cm:
            RootFactory(self.context_getter)(self.request)

        self.assertEqual(cm.exception.location, '/a/b-1')

    def test_returns_resource_root_with_trailing_view(self):
        self.request.matchdict['traverse'] = ('a', 'b-1', 'view')
        root = RootFactory(self.context_getter)(self.request)
        self.assertEqual(self.loc2, root['a']['b-1'])

    def test_returns_none_with_invalid_url_format(self):
        self.request.matchdict['traverse'] = ('a', 'b2')
        self.context_getter = test.Mock()
        self.context_getter.return_value = None

        root = RootFactory(self.context_getter)(self.request)

        self.assertIsNone(root)
