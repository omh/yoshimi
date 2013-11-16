from passlib.context import CryptContext
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid import testing
from yoshimi import auth
from yoshimi import test
from yoshimi.contenttypes import User

# Override passlibs custom_app_context to speed up password verification for
# while testing.
auth.custom_app_context = CryptContext(
    schemes=['sha256_crypt'],
    sha256_crypt__default_rounds=1
)

def mock_load_user(user):
    a = auth.AuthCoordinator(testing.DummyRequest())
    a.load = test.Mock(return_value=user)

    return a


class TestAuthCoordinator(test.TestCase):
    def setUp(self):
        self.user = User(
            name="Test user",
            slug="/test-user",
            email="test@test.com",
            password_hash=auth.custom_app_context.encrypt("testpass")
        )
        self.config = testing.setUp()
        self.auth = mock_load_user(self.user)
        self.config.testing_securitypolicy(
            remember_result=[('Set-Cookie', 'yoshimi_auth="bla"')]
        )

    def tearDown(self):
        testing.tearDown()

    def test_login_user_successful(self):
        rv = self.auth.login("test@test.com", "testpass")
        self.assertNotEqual(rv, False)

    def test_login_user_incorrect_pass(self):
        rv = self.auth.login("test@test.com", "incorrect pass")
        self.assertFalse(rv)

    def test_logout_current(self):
        self.config.testing_securitypolicy(forget_result=[])
        self.assertEqual(self.auth.logout(), [])

    def test_is_logged_in(self):
        self.config.testing_securitypolicy(userid="123")
        self.assertEqual(self.auth.is_logged_in, "123")

    def test_current(self):
        self.config.testing_securitypolicy(userid="123")
        self.assertEqual(self.auth.current, self.user)
