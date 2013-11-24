from pyramid import testing
from pyramid.httpexceptions import HTTPFound
from webob.multidict import MultiDict
from yoshimi.auth import AuthCoordinator
from yoshimi.forms import BaseForm
from yoshimi.forms import ContentMoveForm
from yoshimi.views import login
from yoshimi.views import logout
from yoshimi.views import move
from yoshimi import test


class TestMoveView(test.TestCase):
    def setUp(self):
        self.request = testing.DummyRequest()
        self.request.POST = MultiDict()
        self.request.method = 'POST'
        ContentMoveForm.csrf_enabled = False

    def test_validation_error_if_no_location_id_in_form(self):
        rv = move(self.request)
        self.assertTrue('form_errors' in rv)

    @test.patch('yoshimi.views.Location')
    @test.patch('yoshimi.views.url')
    def test_moves_location_when_new_parent_id_is_provided(self, url, Location):
        url.return_value = '/move'
        self.request.POST['parent_location_id'] = 123
        self.request.context = test.Mock()

        rv = move(self.request)

        self.assertIsInstance(rv, HTTPFound)
        self.assertTrue(self.request.context.move.called)


class TestLoginView(test.TestCase):
    def setUp(self):
        self.request = testing.DummyRequest()
        self.request.POST = MultiDict(
            {'email': 'testing@example.com',
             'password': '123456'}
        )
        self.request.method = 'POST'
        self.request.y_user = test.Mock(spec_set=AuthCoordinator)

    def test_redirects_on_succesful_login(self):
        self.request.y_user.login.return_value = {'A': 2}
        rv = login(self.request)

        self.assertIsInstance(rv, HTTPFound)

    def test_sets_csrf_in_session_on_successful_login(self):
        self.request.y_user.login.return_value = {'A': 2}
        login(self.request)

        self.assertTrue('_csrft_' in self.request.session)

    def test_returns_form_on_failed_login(self):
        self.request.y_user.login.return_value = False
        rv = login(self.request)

        self.assertIsInstance(rv['form'], BaseForm)


class TestLogoutView(test.TestCase):
    def setUp(self):
        self.request = testing.DummyRequest()
        self.request.session['_csrft_'] = 'some token'
        self.request.y_user = test.Mock(spec_set=AuthCoordinator)
        self.request.y_user.logout.return_value = {}

    def test_returns_redirect(self):
        self.assertIsInstance(logout(self.request), HTTPFound)

    def test_clears_session(self):
        logout(self.request)
        self.assertEqual(len(self.request.session), 0)
