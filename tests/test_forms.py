from pyramid import testing
from pyramid.httpexceptions import HTTPUnauthorized
from webob.multidict import MultiDict
from wtforms.fields import TextField
from yoshimi.forms import ConflictPreventionForm
from yoshimi.forms import ContentMoveForm
from yoshimi.forms import CsrfForm
from yoshimi import test


class Dummy:
    """Mock's aren't pickle'able, so manually creating a dummy object
    instead."""
    a = "testing"


class DummyForm(ConflictPreventionForm):
    a = TextField()


class TestCsrfForm(test.TestCase):
    def setUp(self):
        self.request = testing.DummyRequest()
        self.request.POST = MultiDict()
        self.request.session.get_csrf_token = lambda: None

    def test_raises_401_when_csrf_empty(self):
        with self.assertRaises(HTTPUnauthorized):
            form = CsrfForm(formdata=None, csrf_context=self.request.session)
            form.validate()

    def test_raises_401_when_csrf_mismatch(self):
        self.request.POST['csrf_token'] = 'abc'
        with self.assertRaises(HTTPUnauthorized):
            form = CsrfForm(self.request.POST, csrf_context=self.request.session)
            form.validate()

    def test_form_validates_when_csrf_matches(self):
        self.request.POST['csrf_token'] = 'abc'
        self.request.session.get_csrf_token = lambda: 'abc'
        form = CsrfForm(self.request.POST, csrf_context=self.request.session)
        self.assertTrue(form.validate())

    def test_no_csrf_check_when_disabled(self):
        form = CsrfForm(self.request.POST, csrf_enabled=False)
        self.assertTrue(form.validate())


class TestConflictPreventionForm(test.TestCase):
    def setUp(self):
        self.dummy = Dummy()

    def test_form_when_no_changes(self):
        form = DummyForm(
            formdata=None,
            obj=self.dummy,
            csrf_enabled=False
        )

        form = DummyForm(
            formdata=MultiDict({'cp_token': form.cp_token.data}),
            obj=self.dummy,
            csrf_enabled=False
        )

        self.assertTrue(form.validate())

    def test_validation_fails_when_data_is_outdated(self):
        form = DummyForm(
            formdata=None,
            obj=self.dummy,
            csrf_enabled=False
        )

        self.dummy.a = "data changed"

        form = DummyForm(
            formdata=MultiDict({'cp_token': form.cp_token.data}),
            obj=self.dummy,
            csrf_enabled=False
        )

        self.assertFalse(form.validate())


class TestContentMoveForm(test.TestCase):
    def test_location_id_is_required(self):
        form = ContentMoveForm(csrf_enabled=False)
        self.assertFalse(form.validate())

    def test_validates(self):
        form = ContentMoveForm(
            formdata=MultiDict({'parent_location_id': 123}),
            csrf_enabled=False
        )
        self.assertTrue(form.validate())
