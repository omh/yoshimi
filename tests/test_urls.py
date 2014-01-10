import pytest
from pyramid.testing import DummyRequest
from pyramid.httpexceptions import (
    HTTPFound,
    HTTPMovedPermanently
)
from yoshimi import test


class _PathFunctionBase():
    def setup(self):
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


class TestPath(_PathFunctionBase):
    def setup(self):
        super().setup()
        from yoshimi.url import path
        self.fut = path

    def assert_call(self, *args, **kw):
        self.req.resource_path.assert_called_with(*args, **kw)


class TestUrl(_PathFunctionBase):
    def setup(self):
        super().setup()
        from yoshimi.url import url
        self.fut = url

    def assert_call(self, *args, **kw):
        self.req.resource_url.assert_called_with(*args, **kw)


class TestBackToContextUrl:
    def setup(self):
        from yoshimi.url import back_to_context_url
        self.fut = back_to_context_url

        def y_path(context):
            return '/context'

        self.req = DummyRequest()
        self.req.y_path = y_path

    @test.patch('yoshimi.url.safe_redirect_url', autospec=True)
    def test_with_back_get_param(self, safe_redirect_url):
        self.req.GET['back'] = '/back'
        self.fut(self.req, self.req)
        safe_redirect_url.assert_called_with(self.req, '/back')

    @test.patch('yoshimi.url.safe_redirect_url', autospec=True)
    def test_without_back_get_param(self, safe_redirect_url):
        self.fut(self.req, 'bla')
        safe_redirect_url.assert_called_with(self.req, '/context')


class TestRedirectBackToContext:
    @test.patch('yoshimi.url.back_to_context_url', autospec=True)
    def test_context_redirect_back(self, url_func_mock):
        from yoshimi.url import redirect_back_to_context
        request_mock = test.Mock()
        context_mock = test.Mock()

        redirect_back_to_context(context_mock, request_mock)

        url_func_mock.assert_called_once_with(context_mock, request_mock)


class TestRedirectBack:
    def setup(self):
        from yoshimi.url import redirect_back
        self.fut = redirect_back

        def y_path(context):
            return '/context'

        self.req = DummyRequest()
        self.req.y_path = y_path

    def test_redirect_back(self):
        self.req.GET['back'] = '/testing'
        rv = self.fut(self.req)

        assert isinstance(rv, HTTPFound)
        assert rv.location == '/testing'

    def test_redirect_back_using_fallback(self):
        rv = self.fut(self.req, fallback='/fallback')
        assert rv.location == '/fallback'


class TestRedirectBackToParent:
    def setup(self):
        from yoshimi.url import redirect_back_to_parent
        self.fut = redirect_back_to_parent
        self.req = DummyRequest()

    @test.patch('yoshimi.url.redirect_back_to_context', autospec=True)
    def test_redirects_to_parent(self, redirect_func):
        context = test.Mock()
        context.parent = test.Mock()
        self.fut(self.req, context)

        redirect_func.assert_called_once_with(self.req, context.parent)

    @test.patch('yoshimi.url.redirect_back', autospec=True)
    def test_redirects_to_slash_without_parent(self, redirect_func):
        context = test.Mock()
        context.parent = None
        self.fut(self.req, context)

        redirect_func.assert_called_once_with(self.req)


class TestSafeRedirectUrl:
    def setup(self):
        from yoshimi.url import safe_redirect_url
        self.fut = safe_redirect_url

        self.req = DummyRequest()
        self.req.registry.settings = {}

    def test_redirect_to_same_host_is_ok(self):
        self.req.url = "http://www.example.com/some-page"
        url = "http://www.example.com/testing"
        rv = self.fut(self.req, url)
        assert url == rv

    def test_redirect_to_relative_url_is_ok(self):
        url = "/testing"
        rv = self.fut(self.req, url)
        assert url == rv

    def test_redirect_to_different_host_fails(self):
        url = "http://www.example2.com"
        rv = self.fut(self.req, url, fallback='/error')
        assert rv == '/error'

    def test_redirect_to_whitelisted_host_is_ok(self):
        self.req.registry.settings = {
            'yoshimi.host_whitelist': [
                'www.example.com'
            ]
        }
        url = "http://www.example.com"
        rv = self.fut(self.req, url, fallback='/error')
        assert rv == url

    def test_redirect_to_not_whitelisted_host_fails(self):
        self.req.registry.settings = {
            'yoshimi.host_whitelist': [
                'www.example.com'
            ]
        }
        url = "http://www.example.com:81"
        rv = self.fut(self.req, url, fallback='/error')
        assert rv == '/error'


class TestResourceUrlAdapter:
    def test_populates_location_aware_attributes(self):
        from yoshimi.url import ResourceUrlAdapter

        loc1 = test.MagicMock()
        loc2 = test.MagicMock()
        loc3 = test.MagicMock()
        loc3.lineage = [loc1, loc2, loc3]
        loc3.id = 1
        loc3.slugs = ['a', 'b', 'c']

        request = DummyRequest()
        ResourceUrlAdapter(loc3, request)

        assert loc1.__parent__ is None
        assert loc1.__name__ is not None
        assert loc2.__parent__ is not None
        assert loc2.__name__ is not None
        assert loc3.__parent__ is not None
        assert loc3.__name__ is not None


class TestRootFactory:
    def setup_class(cls):
        from yoshimi.url import RootFactory
        cls.fut = RootFactory

    def setup(self):
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

    def teardown(self):
        test.patch.stopall()

    def test_returns_resource_root(self):
        root = self.fut(self.context_getter)(self.request)
        assert self.loc2 == root['a']['b-1']

    def test_returns_none_without_traverse_match(self):
        self.request.matchdict = None
        root = self.fut(self.context_getter)(self.request)
        assert root is None

    def test_returns_none_without_context(self):
        root = self.fut(lambda id: None)(self.request)
        assert root is None

    def test_raises_redirect_on_url_mismatch(self):
        self.request.matchdict['traverse'] = ("bla-1",)
        with pytest.raises(HTTPMovedPermanently) as cm:
            self.fut(self.context_getter)(self.request)

        assert cm.value.location == '/a/b-1'

    def test_returns_resource_root_with_trailing_view(self):
        self.request.matchdict['traverse'] = ('a', 'b-1', 'view')
        root = self.fut(self.context_getter)(self.request)
        assert self.loc2 == root['a']['b-1']

    def test_returns_none_with_invalid_url_format(self):
        self.request.matchdict['traverse'] = ('a', 'b2')
        self.context_getter = test.Mock()
        self.context_getter.return_value = None

        root = self.fut(self.context_getter)(self.request)

        assert root is None
