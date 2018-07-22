import os
import sys
import unittest

sys.path.insert(0, os.path.abspath('..'))
from person import Person
from database import database


class TestItem(unittest.TestCase):
    def setUp(self):
        """Populate the data with some test person data"""
        with database() as db:
            sql = 'INSERT INTO persons (person_name, address, email) VALUES (%s, %s, %s)'
            db.query(sql, 'test_person_a', '123 Fake Street', 'test@example.com')
            db.query(sql, 'test_person_b', '124 Fake Street', 'boss@example.com')

    def tearDown(self):
        """Remove the test data from the database"""
        with database() as db:
            db.query("DELETE FROM persons WHERE person_name = 'test_person_a' OR person_name = 'test_person_b'")

    def test_init(self):
        """Ensure that the class constructor properly assigns variables from the database and correctly raises an
        error when provided an invalid name
        """
        person = Person('test_person_a')
        self.assertEqual(person.name, 'test_person_a')
        self.assertEqual(person.address, '123 Fake Street')
        self.assertEqual(person.email, 'test@example.com')

        with self.assertRaises(KeyError):
            error_person = Person('fake_person')

    def test_create(self):
        """Ensure that the create method correctly modifies the database with the new data"""
        person = Person.create('created_person', 'create@example.com', '125 Fake Street')
        with database() as db:
            results = db.query("SELECT * FROM persons WHERE person_name = 'created_person'")
            self.assertEqual(results, [('created_person', '125 Fake Street', 'create@example.com')])
            db.query("DELETE FROM persons WHERE person_name = 'created_person'")

    def test_delete(self):
        """Ensure that the delete method correctly removes data associated to the person from the database"""
        person = Person('test_person_b')
        person.delete()
        with database() as db:
            results = db.query("SELECT * FROM persons WHERE person_name = 'test_person_b'")
            self.assertEqual(results, [])

    # TODO: test get_all

if __name__ == '__main__':
    unittest.main()