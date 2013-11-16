import sqlalchemy
from passlib.apps import custom_app_context
from pyramid.security import remember
from pyramid.security import forget
from pyramid.security import authenticated_userid
from yoshimi.contenttypes import User


def register_auth(config):
    """Registers the y_user property on the request"""
    config.add_request_method(auth_coordinator, name='y_user', property=True)


def auth_coordinator(request):
    """Returns an AuthCoordinator for the request"""
    return AuthCoordinator(request)


class AuthCoordinator(object):
    """Central coordinator for authenticating users

    Responsible for logging users in/out, checking if a user is logged in and
    getting the currently logged in user.
    """
    def __init__(self, request):
        self.req = request
        self._user = None

    @property
    def current(self):
        """Returns the currently logged in user.

        Returns None if no user is logged in.
        """
        logged_in_id = authenticated_userid(self.req)
        if self._user is None and logged_in_id:
            self._user = self.load(logged_in_id)

        return self._user

    @property
    def is_logged_in(self):
        """Returns Trueish if a user is logged in for current request"""
        return authenticated_userid(self.req)

    def login(self, email, password):
        """Logs in a user

        :param string email: The user's email
        :param string password" The user's password
        :return tuple: Tuple of HTTP headers to keep user logged in. False if
                       user could not be logged in.
        """
        user = self.load(email)
        if not user:
            return False

        if custom_app_context.verify(password, user.password_hash):
            return remember(self.req, email)

        return False

    def logout(self):
        """Logs out the current user

        :return tuple: Tuple of HTTP headers than will logged the user out
        """
        self._user = None
        return forget(self.req)

    def load(self, email):
        """Loads a user from the database

        :param string email: The user's email
        :returns: User` or None if user could not be found
        """
        try:
            return User.query.filter_by(email=email).one()
        except sqlalchemy.orm.exc.NoResultFound:
            return None
