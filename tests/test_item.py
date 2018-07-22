import os
import sys
import unittest
import datetime

sys.path.insert(0, os.path.abspath('..'))
from item import Item
from database import database


class TestItem(unittest.TestCase):
    def setUp(self):
        """Setup the test items with some test data used within the tests"""
        with database() as db:
            sql = 'INSERT INTO items (item_code, date, description, charge) VALUES (%s, %s, %s, %s)'
            db.query(sql, 'DPWV', '1990-05-05', 'Test Item A', 23.4)
            db.query(sql, 'SDWF', '1995-05-05', 'Test Item B', 45)

    def tearDown(self):
        """Remove the test data from the database"""
        with database() as db:
            db.query("DELETE FROM items WHERE item_code = 'DPWV' OR item_code = 'SDWF'")

    def test_init(self):
        """Ensure that the item constructor works correctly by

        a) Creating an item with a valid item code and ensuring variables are set correctly
        b) Creating an item with an invalid item code and ensuring the correct error is raised
        """
        item = Item('DPWV')
        self.assertEqual(item.code, 'DPWV')
        self.assertEqual(item.date, datetime.date(1990, 5, 5))
        self.assertEqual(item.description, 'Test Item A')
        self.assertEqual(item.amount, 23.4)

        with self.assertRaises(KeyError):
            Item('DEIG')

    def test_generate(self):
        """Ensure that the generate_code method works by testing properties of the code

        Properties:
        - Of type string
        - Of length 4
        - Consisting of alphanumeric characters
        - All uppercase
        """
        code = Item._generate_code()
        self.assertEqual(len(code), 4)
        self.assertEqual(type(code), type(''))
        self.assertTrue(code.isalnum())
        self.assertTrue(code.isupper())

    def test_create(self):
        """Ensure item creation works by using the create method and checking changes are made to the database"""
        item = Item.create(datetime.date(2000, 5, 5), 'Creation test item', 23)
        with database() as db:
            result = db.query('SELECT * FROM items WHERE item_code = %s', item.code)
            self.assertEqual(result, [(item.code, datetime.date(2000, 5, 5), 'Creation test item', 23)])
            db.query('DELETE FROM items WHERE item_code = %s', item.code)

    def test_delete(self):
        """Ensure item deletion works by using the delete method and checking the information is removed from that
        database"""
        with database() as db:
            self.assertTrue(db.exists('items', item_code = 'DPWV'))
            item = Item('DPWV')
            item.delete()
            self.assertFalse(db.exists('items', item_code = 'DPWV'))

    # TODO: get_all and get_unlogged tests

    def test_lt(self):
        """Ensure that the __lt__ magic method is used by comparing two items"""
        less, more = Item('DPWV'), Item('SDWF')
        self.assertLess(less, more)
        self.assertGreater(more, less)

    # TODO: statistics test

if __name__ == '__main__':
    unittest.main()