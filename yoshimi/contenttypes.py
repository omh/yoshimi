import sqlalchemy as sa
from yoshimi.content import ContentType, Content


class User(ContentType, Content):
    email = sa.Column(sa.String(400), nullable=False)
    password_hash = sa.Column(sa.String(150), nullable=False)

    def __init__(self, *args, **kwargs):
        kwargs['name'] = kwargs.get('name', kwargs.get('username', 'New user'))
        super(User, self).__init__(*args, **kwargs)

sa.Index('email_index', User.email, unique=True, mysql_length=20)
