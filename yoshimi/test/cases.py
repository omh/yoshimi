import os
import unittest
from yoshimi import db
from yoshimi.content import Base


class TestCase(unittest.TestCase):
    pass


dbs = []


def setup_test_db(dsn):
    global dbs
    if not dsn in dbs:
        db.setup_db(
            {'sqlalchemy.url': dsn},
            extension=None,
        )
        dbs.append(dsn)

        Base.metadata.drop_all()
        Base.metadata.create_all()


class DatabaseTestCase(unittest.TestCase):
    def setUp(self):
        setup_test_db(os.environ.get('YOSHIMI_TEST_DB'))

        db.Session.remove()

        self.connection = db.engine.connect()
        self.s = db.Session(bind=self.connection)
        self.trans = self.connection.begin()

    def tearDown(self):
        self.trans.rollback()
        self.s.close()
        self.connection.close()
