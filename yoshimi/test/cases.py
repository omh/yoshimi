from contextlib import contextmanager
import os
import unittest
from sqlalchemy import event
from yoshimi import db
from yoshimi.entities import Base


class TestCase(unittest.TestCase):
    def setup(self):
        pass

    def setUp(self):
        self.setup()

    def teardown(self):
        pass

    def tearDown(self):
        self.teardown()


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


class DatabaseTestCase(TestCase):
    def setUp(self):
        setup_test_db(os.environ.get('YOSHIMI_TEST_DB'))

        db.Session.remove()

        self.connection = db.engine.connect()
        self.s = db.Session(bind=self.connection)
        self.trans = self.connection.begin()
        super().setUp()

    def tearDown(self):
        self.trans.rollback()
        self.s.close()
        self.connection.close()
        super().tearDown()


class QueryCountTestCase(DatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.enable_count = False

    @contextmanager
    def count_queries(self):
        self.statements = []

        #@event.listens_for(self.connection, 'before_cursor_execute')
        def catch_queries(conn, cursor, statement, *args):
            self.statements.append(statement)

        event.listen(self.connection, 'before_cursor_execute', catch_queries)
        yield
        event.remove(self.connection, 'before_cursor_execute', catch_queries)

    def assertQueryCount(self, expected_count):
        if expected_count != len(self.statements):
            queries = "\n".join(["- %s" % q for q in self.statements])
            raise AssertionError(
                "%s queries != expected %s. Queries:\n%s" % (
                    len(self.statements),
                    expected_count,
                    queries
                )
            )

    def add_object(self, obj, commit=True):
        self.s.add(obj)
        if commit:
            self.s.commit()

        return obj

    def get_id_from_added_object(self, obj):
        self.add_object(obj, commit=True)
        id = obj.id
        self.s.expire(obj)
        return id
