from pyramid import testing
from pyramid.httpexceptions import HTTPFound
from webob.multidict import MultiDict
from yoshimi.auth import AuthCoordinator
from yoshimi.forms import BaseForm
from yoshimi.forms import ContentMoveForm
from yoshimi.views import login
from yoshimi.views import logout
from yoshimi.views import move
from tests.yoshimi import Mock


class TestDeleteView:
    def setup(self):
        from yoshimi.views import delete
        self.fut = delete

        self.req = test.Mock()
        self.context = test.Mock()

    @test.patch('yoshimi.views.redirect_back_to_parent', autospec=True)
    def test_delete(self, redirect_func):
        self.fut(self.context, self.req)

        self.req.y_repo.trash.insert.assert_called_once_with(self.context)
        redirect_func.assert_called_once_with(self.req, self.context)
        assert self.req.session.flash.call_count == 1


class TestMoveView:
    def setup(self):
        self.request = testing.DummyRequest()
        self.request.POST = MultiDict()
        self.request.method = 'POST'
        self.request.y_path = Mock()
        self.request.y_repo = Mock()
        ContentMoveForm.csrf_enabled = False

    def test_validation_error_if_no_content_id_in_form(self):
        rv = move(None, self.request)
        assert 'form_errors' in rv

    def test_moves_content_when_new_parent_id_is_provided(self):
        self.request.y_path.return_value = '/move'
        self.request.POST['parent_id'] = 123
        self.request.context = Mock()

        rv = move(self.request.context, self.request)

        assert isinstance(rv, HTTPFound)
        assert self.request.y_repo.move.called is True


class TestLoginView:
    def setup(self):
        self.request = testing.DummyRequest()
        self.request.POST = MultiDict(
            {'email': 'testing@example.com',
             'password': '123456'}
        )
        self.request.method = 'POST'
        self.request.y_user = Mock(spec_set=AuthCoordinator)

    def test_redirects_on_succesful_login(self):
        self.request.y_user.login.return_value = {'A': 2}
        rv = login(self.request)

        assert isinstance(rv, HTTPFound)

    def test_sets_csrf_in_session_on_successful_login(self):
        self.request.y_user.login.return_value = {'A': 2}
        login(self.request)

        assert '_csrft_' in self.request.session

    def test_returns_form_on_failed_login(self):
        self.request.y_user.login.return_value = False
        rv = login(self.request)

        assert isinstance(rv['form'], BaseForm)


class TestLogoutView:
    def setup(self):
        self.request = testing.DummyRequest()
        self.request.session['_csrft_'] = 'some token'
        self.request.y_user = Mock(spec_set=AuthCoordinator)
        self.request.y_user.logout.return_value = {}

    def test_returns_redirect(self):
        assert isinstance(logout(self.request), HTTPFound)

    def test_clears_session(self):
        logout(self.request)
        assert len(self.request.session) == 0


class TestWrapView:
    def setup(self):
        from yoshimi.views import wrap_view

        def view1():
            return {'view1': 1}

        def view2():
            return {'view2': 1}

        @wrap_view(view1, view2)
        def view3():
            return {'view3': 1}

        self.fut = view3

    def test_no_wrap_when_not_activated_by_venusian_scan(self):
        rv = self.fut()

        assert 'view1' not in rv
        assert 'view2' not in rv
        assert 'view3' in rv

    def test_wraps_when_activated_by_venusian_scan(self):
        self.fut.__wrapped__.__yoshimi_should_wrap_view__ = True
        rv = self.fut()

        assert 'view1' in rv
        assert 'view2' in rv
        assert 'view3' in rv
