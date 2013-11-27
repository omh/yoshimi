from pyramid.httpexceptions import HTTPFound
from pyramid import testing
from yoshimi import test
from yoshimi.utils import LazyPagination
from yoshimi.utils import page_number
from yoshimi.utils import redirect_back
from yoshimi.utils import context_redirect_back_url
from yoshimi.utils import safe_redirect


class TestContextRedirectBackUrl(test.TestCase):
    def setUp(self):
        def y_path(context):
            return '/context'

        self.req = testing.DummyRequest()
        self.req.y_path = y_path

    @test.patch('yoshimi.utils.safe_redirect')
    def test_with_back_get_param(self, safe_redirect):
        self.req.GET['back'] = '/back'
        context_redirect_back_url(self.req, 'bla')
        safe_redirect.assert_called_with(self.req, '/back')

    @test.patch('yoshimi.utils.safe_redirect')
    def test_without_back_get_param(self, safe_redirect):
        context_redirect_back_url(self.req, 'bla')
        safe_redirect.assert_called_with(self.req, '/context')


class TestRedirectBack(test.TestCase):
    def setUp(self):
        def y_path(context):
            return '/context'

        self.req = testing.DummyRequest()
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
        self.req = testing.DummyRequest()
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


class TestPageNumber(test.TestCase):
    def test_returns_one_for_negative_number(self):
        self.assertEquals(page_number(-1), 1)

    def test_returns_one_for_zero(self):
        self.assertEquals(page_number(0), 1)

    def test_returns_casts_to_int(self):
        self.assertEquals(page_number('2'), 2)

    def test_return_number(self):
        self.assertEquals(page_number(5), 5)


class TestLazyPaginator(test.TestCase):
    def test_calls_paginate_and_forwards_property(self):
        query = test.Mock()
        query.configure_mock(**{'paginate.return_value.total': 30})

        total = LazyPagination(query, 4).total

        query.paginate.assert_called_with(4)
        self.assertEqual(total, 30)
