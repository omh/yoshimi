#!/usr/bin/env python
import os
import sys
import nose

os.environ['YOSHIMI_TEST_DB'] = 'sqlite:///:memory:'
with_db = False
argv = sys.argv[:]
argv.append('tests')

if '--with-db' in argv:
    del argv[argv.index('--with-db')]
    with_db = True

def abort_if_unsuccessful(successful):
    [sys.exit(1) for s in successful if s == False]

successful = []
print("Running unit tests...")
successful.append(nose.run(argv=argv))

if with_db:
    argv.insert(1, '-a database')

    os.environ['YOSHIMI_TEST_DB'] = 'mysql+mysqlconnector://root@localhost/yoshimi_test'
    print("\nRunning database tests against MySQL...")
    successful.append(nose.run(argv=argv))

    os.environ['YOSHIMI_TEST_DB'] = 'postgresql+psycopg2://localhost/yoshimi_test'
    print("\nRunning database tests against PostgreSQL...")
    successful.append(nose.run(argv=argv))

abort_if_unsuccessful(successful)
