import os
import sys
import unittest
import datetime
from flask import Flask

sys.path.insert(0, os.path.abspath('..'))
from invoice import Invoice
from person import Person
from item import Item
from database import database

class TestInvoice(unittest.TestCase):
    def setUp(self):
        """Setup the invoice unit test by creating fake data to test and setting up the directory and flask app"""
        with database() as db:
            db.query("INSERT INTO persons (person_name, address, email) VALUES ('test_payer', '123 Fake Street', 'test@braewebb.com'), ('test_payee', '124 Fake Street', 'test@braewebb.com')")
            db.query("INSERT INTO invoices (invoice_number, date, payer, payee) VALUES (424, '1990-02-05', 'test_payer', 'test_payee')")
            db.query("INSERT INTO items (item_code, date, description, charge) VALUES ('XDSA', '1990-02-04', 'Test Item', 30), ('SDWF', '1990-02-03', 'Test Item 2', 10.7)")
            db.query("INSERT INTO invoice_items (item_code, invoice_number) VALUES ('XDSA', 424), ('SDWF', 424)")
        os.chdir('..')
        self.app = Flask('test_app')

    def tearDown(self):
        """Deleted the fake data created as well as the flask app, additionally changes directory"""
        with database() as db:
            db.query("DELETE FROM persons WHERE person_name = 'test_payer' OR person_name = 'test_payee'")
            db.query("DELETE FROM invoice_items WHERE item_code = 'XDSA' OR item_code = 'SDWF'")
            db.query("DELETE FROM invoices WHERE invoice_number=424")
            db.query("DELETE FROM items WHERE item_code = 'XDSA' OR item_code = 'SDWF'")
        os.chdir('tests')
        del self.app


    def test_init(self):
        """Ensure that the invoice acquires the correct attributes from the __init__ method

        Also ensure an error is raised if an invalid ID is used"""
        invoice = Invoice(424)
        self.assertEqual(invoice.pdf_file, 'pdfs/424.pdf')
        self.assertEqual(invoice.date, datetime.date(1990, 2, 5))
        # TODO: After implementation of __eq__ in Person
        # self.assertEqual(invoice.payer, Person('test_payer'))
        # self.assertEqual(invoice.payee, Person('test_payee'))
        self.assertEqual(invoice.amount, 40.7)
        self.assertEqual(invoice.name, '0424')
        with self.assertRaises(KeyError):
            Invoice(9895)

    #TODO: test_get_all

    def test_create(self):
        """Ensures the create method works by creating an invoice and checking the database matches"""
        invoice = Invoice.create(datetime.date(1999, 1, 1), 'test_payer', 'test_payee', ['XDSA', 'SDWF'])
        id = invoice.id
        with database() as db:
            results = db.query('SELECT * FROM invoices WHERE invoice_number = %s', id)
            self.assertEqual(results, [(id, datetime.date(1999, 1, 1), 'test_payer', 'test_payee')])
            results = db.query('SELECT * FROM invoice_items WHERE invoice_number = %s', id)
            self.assertEqual(results, [('XDSA', id), ('SDWF', id)])
        invoice.delete()

    def test_delete(self):
        """Ensures that the delete method works by checking the data is removed from the database"""
        Invoice(424).delete()
        with database() as db:
            results = db.query('SELECT * FROM invoices WHERE invoice_number = %s', 424)
            self.assertEqual(results, [])
            results = db.query('SELECT * FROM invoice_items WHERE invoice_number = %s', 424)
            self.assertEqual(results, [])

    # def test_items(self):
    #     """Ensures the correct items are in the items attribute"""
    #     items = Invoice(424).items
    #     # TODO: After implementation of __eq__ in Item
    #     # self.assertEqual(items, [Item('XDSA'), Item('SDWF')])

    def test_build(self):
        """Builds a PDF and ensures it was properly created"""
        invoice = Invoice(424)
        invoice.pdf_file = 'tests/invoices/build_test.pdf'
        with self.app.app_context():
            invoice.build_pdf()
        self.assertTrue(os.path.isfile('tests/invoices/build_test.pdf'))
        invoice.delete_pdf()

    def test_delete_pdf(self):
        """Ensure that a PDF was deleted by checking the file path"""
        invoice = Invoice(424)
        invoice.pdf_file = 'tests/invoices/delete_test.pdf'
        with self.app.app_context():
            invoice.build_pdf()
        invoice.delete_pdf()
        self.assertFalse(os.path.isfile('tests/invoices/build_test.pdf'))

    def test_pdf(self):
        """Ensure the pdf method returns the file correctly"""
        invoice = Invoice(424)
        invoice.pdf_file = 'tests/invoices/pdf_test.pdf'
        with self.app.app_context():
            response = invoice.pdf()
        with open('tests/invoices/pdf_test.pdf', 'rb') as f:
            self.assertEqual(f.read(), response[0])
        invoice.delete_pdf()

    def test_download(self):
        """Ensure the download method returns the file correctly"""
        invoice = Invoice(424)
        invoice.pdf_file = 'tests/invoices/download_test.pdf'
        with self.app.app_context():
            response = invoice.download()
        with open('tests/invoices/download_test.pdf', 'rb') as f:
            self.assertEqual(f.read(), response[0])
        invoice.delete_pdf()

    # TODO: test_email



if __name__ == '__main__':
    unittest.main()