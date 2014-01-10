import os
from contextlib import contextmanager
from sqlalchemy import event
from yoshimi import db
from yoshimi.entities import Base

dbs = []


def setup_test_db(dsn):
    global dbs
    if not dsn in dbs:
        db.setup_db({'sqlalchemy.url': dsn}, extension=None)
        dbs.append(dsn)
        Base.metadata.drop_all()
        Base.metadata.create_all()


class DatabaseTestCase:
    def setup(self):
        setup_test_db(os.environ.get('YOSHIMI_TEST_DB'))
        db.Session.remove()
        self.connection = db.engine.connect()
        self.s = db.Session(bind=self.connection)
        self.trans = self.connection.begin()

    def teardown(self):
        self.trans.rollback()
        self.s.close()
        self.connection.close()


class QueryCountTestCase(DatabaseTestCase):
    @contextmanager
    def count_queries(self):
        self.statements = []

        def catch_queries(conn, cursor, statement, *args):
            self.statements.append(statement)

        event.listen(self.connection, 'before_cursor_execute', catch_queries)
        yield
        event.remove(self.connection, 'before_cursor_execute', catch_queries)

    def assert_query_count_is(self, expected_count):
        if expected_count != len(self.statements):
            queries = "\n\n".join([q for q in self.statements])
            raise AssertionError(
                "%s queries dit not match != expected %s. \n\nQueries:\n%s" % (
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
