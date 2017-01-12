import os
import sys
import unittest
from psycopg2 import InterfaceError

sys.path.insert(0, os.path.abspath('..'))
import config
from database import database


class TestDatabase(unittest.TestCase):
    def setUp(self):
        """Create/Wipe a table called test_data where tests will be run"""
        with database() as db:
            db.query('DROP TABLE IF EXISTS test_data')
            db.query('CREATE TABLE test_data (variable INTEGER)')

    def tearDown(self):
        """Drop the test_data table used to perform tests"""
        with database() as db:
            db.query('DROP TABLE test_data')

    def test_repr(self):
        """Ensure that the database object is returning the proper representation"""
        with database() as db:
            repr_str = 'Database(database={}, user={})'.format(config.postgres_database, config.postgres_user)
            self.assertEqual(repr(db), repr_str)

    def test_commit(self):
        """Ensure that the database commit method retains the data

        Accomplished by inserting a new row into the table and committing
        Then in a new database object check that the result matches the expected outcome if committed properly
        """
        db = database()
        db.query('INSERT INTO test_data (variable) VALUES (1)')
        db.commit()
        del db

        db = database()
        result = db.query('SELECT * FROM test_data')
        self.assertEqual(result, [(1,)])
        del db

    def test_rollback(self):
        """Ensure that the database rollback method removes changes to the data

        Accomplished by inserting a new row into the table, and rolling back
        Then in a new database object check that the result matches the data if the previous code was never run
        """
        db = database()
        db.query('INSERT INTO test_data (variable) VALUES (1)')
        db.rollback()
        del db

        db = database()
        result = db.query('SELECT * FROM test_data')
        self.assertEqual(result, [])
        del db

    def test_close(self):
        """Ensure that the close method closes the database connection

        Checks the expected error is raised when a query is made on a closed database,
        thus confirming there is no connection
        """
        with self.assertRaises(InterfaceError):
            db = database()
            db.close()
            db.query('SELECT * FROM test_data')

    def test_with_commit(self):
        """Ensure that an error free with statement commits when exiting

        Performs an error free with block and ensures the data remains
        """
        with database() as db:
            db.query('INSERT INTO test_data (variable) VALUES (1)')
        db = database()
        result = db.query('SELECT * FROM test_data')
        self.assertEqual(result, [(1,)])

    def test_with_rollback(self):
        """Ensure that an error occurring in a database with context forces the database to rollback

        Raises an error in the with context and ensures that modifications were removed
        """
        try:
            with database() as db:
                db.query('INSERT INTO test_data (variable) VALUES (1)')
                raise Exception
        except:
            pass
        db = database()
        result = db.query('SELECT * FROM test_data')
        self.assertEqual(result, [])

    def test_limit(self):
        """Ensure that the limit keyword of the query method works as expected

        Performs several queries with varying limits and compares the results to the expected results
        """
        with database() as db:
            db.query('INSERT INTO test_data (variable) VALUES (1), (2), (3), (4), (5)')
            result = db.query('SELECT * FROM test_data', limit=1)
            self.assertEqual(result, [(1,)])
            result = db.query('SELECT * FROM test_data', limit=3)
            self.assertEqual(result, [(1,), (2,), (3,)])
            result = db.query('SELECT * FROM test_data')
            self.assertEqual(result, [(1,), (2,), (3,), (4,), (5,)])

    def test_exists(self):
        """Ensure that the exists method accurately reports the existence of rows in the database"""
        with database() as db:
            db.query('INSERT INTO test_data (variable) VALUES (1), (2), (3), (4), (5)')
            self.assertTrue(db.exists('test_data'))
            self.assertTrue(db.exists('test_data', variable=3))
            self.assertFalse(db.exists('test_data', variable=6))

    def test_bool(self):
        """Ensure that the database returns the correct boolean value based on whether it is open or closed"""
        db = database()
        self.assertTrue(db)
        db.close()
        self.assertFalse(db)

    def test_del(self):
        """Ensure that the __del__ magic method works in the same way the close works"""
        with self.assertRaises(InterfaceError):
            db = database()
            db.__del__()
            db.query('SELECT * FROM test_data')


if __name__ == '__main__':
    unittest.main()
