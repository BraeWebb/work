from os import remove as os_remove

import pylab
from flask import render_template
from xhtml2pdf.pisa import CreatePDF

import config
from database import database
from emailer import Email
from item import Item
from person import Person


class Invoice(object):
    """An Invoice identified by the invoice id and stored within the database

    An Invoice contains information of the date of creation, payer, payee and a list of items included in each invoice

    This class provides an interface to the invoice model stored in the database
    """

    def __init__(self, invoice_id):
        """Initializes an Invoice based on the given invoice_id

        invoice_id: The numeric identifier of the invoice
        """
        self.id = int(invoice_id)
        # The location where the pdf copy of this invoice will be stored if generated
        self.pdf_file = 'pdfs/{}.pdf'.format(self.id)

        with database() as db:
            if db.exists('invoices', invoice_number=self.id):
                sql = 'SELECT date, payer, payee FROM invoices WHERE invoice_number = %s'
                self.date, self.payer, self.payee = db.query(sql, self.id, limit=1)[0]

                sql = 'SELECT SUM(charge) FROM items WHERE item_code IN (SELECT item_code FROM invoice_items WHERE invoice_number = %s)'
                self.amount = db.query(sql, self.id, limit=1)[0][0]
            else:
                raise KeyError('No invoice with invoice id of {} exists within the database'.format(self.id))
        self.payer, self.payee = Person(self.payer), Person(self.payee)
        self.name = '{:04d}'.format(self.id)

    @staticmethod
    def get_invoice_count():
        """Returns the total amount of invoices in the database"""
        with database() as db:
            return db.query('SELECT COUNT(*) FROM invoices')[0][0]

    @staticmethod
    def get_last_invoice():
        """Returns the last lodged invoice"""
        with database() as db:
            if db.exists('invoices'):
                return Invoice(db.query("SELECT MAX(invoice_number) FROM invoices")[0][0])

    @staticmethod
    def get_all(start=1, end=None):
        """Retrieve all the invoices that are stored in the database
        If start and end are specified it will only retrieve that range of invoices from the database

        Returns a list of Invoice instances
        """
        if end is None:
            end = Invoice.get_invoice_count()
        with database() as db:
            return [Invoice(inv_id) for inv_id in range(start + 1, end + 1)]

    @classmethod
    def create(cls, date, payer, payee, items):
        """Insert a new invoice into the database and return the instance"""
        with database() as db:
            # Calculate the next invoice id
            max = db.query('SELECT MAX(invoice_number) FROM invoices')[0][0]
            id = int(max) + 1 if max is not None else 1

            sql = 'INSERT INTO invoices (invoice_number, date, payer, payee) VALUES (%s, %s, %s, %s)'
            db.query(sql, id, date, payer, payee)

            for item in items:
                if db.exists('items', item_code=item):
                    sql = 'INSERT INTO invoice_items (item_code, invoice_number) VALUES (%s, %s)'
                    db.query(sql, item, id)
                else:
                    raise KeyError('No item with id of {} exists, thus invoice creation canceled'.format(item))
        return Invoice(id)

    def delete(self):
        """Remove the invoice from the database and it's links to items"""
        with database() as db:
            items = db.query('SELECT item_code FROM invoice_items WHERE invoice_number = %s', self.id)
            db.query('DELETE FROM invoice_items WHERE invoice_number = %s', self.id)
            db.query('DELETE FROM invoices WHERE invoice_number = %s', self.id)
            for item in items:
                db.query('DELETE FROM items WHERE item_code = %s', item[0])
        self.delete_pdf()

    @property
    def payment_details(self):
        return config.payment_details

    @property
    def abn(self):
        return config.abn

    @property
    def items(self):
        """Get all the items included in the invoice

        Returns a list of Item instances
        """
        with database() as db:
            return [Item(item[0])
                    for item in db.query('SELECT item_code FROM invoice_items WHERE invoice_number = %s', self.id)]

    def build_pdf(self):
        """Creates and exports a PDF version of the invoice"""
        with open(self.pdf_file, 'wb+') as output:
            CreatePDF(self.html(), dest=output)

    def delete_pdf(self):
        """Deletes the pdf copy of the invoice"""
        try:
            os_remove(self.pdf_file)
        except OSError:
            pass

    def pdf(self):
        """Builds and opens the PDF file of the invoice and returns it's bytes in a http inline format"""
        self.build_pdf()
        with open(self.pdf_file, 'rb') as pdf:
            return pdf.read(), 200, {'Content-Type': 'application/pdf',
                                     'Content-Disposition': 'inline; filename="Invoice #{}.pdf"'.format(self.name)}

    def download(self):
        """Builds and opens the PDF file of the invoice and returns it's bytes in a http attachment format"""
        self.build_pdf()
        with open(self.pdf_file, 'rb') as pdf:
            return pdf.read(), 200, {'Content-Type': 'application/pdf',
                                     'Content-Disposition': 'attachment; filename="Invoice #{}.pdf"'.format(self.name)}

    def html(self):
        """Renders the invoice html template providing the details of the invoice"""
        return render_template('invoices/invoice.html', invoice=self)

    def email(self, body):
        """Builds a PDF of this invoice and attaches it to an invoice

        Email:
        - From: Payee
        - To: Payer
        - Subject: Invoice {invoicename}
        - Body: the body parameter provided
        """
        self.build_pdf()
        with Email(self.payer.email, self.payee.email, 'Invoice {}'.format(self.name)) as email:
            email.attach_pdf(self.pdf_file, 'Invoice #{}'.format(self.name))
            email.set_body(body)
            email.send()
        return 'Email Sent!'

    @staticmethod
    def statistics():
        """Builds a pylab plot with information about all invoices in the database"""
        dates = []
        costs = []
        pylab.xkcd()
        pylab.figure()
        for invoice in Invoice.get_all():
            dates.append(invoice.id)
            costs.append(invoice.amount)
        pylab.legend(('Invoice Amounts',))
        pylab.plot(dates, costs, marker='o', label='Charge')
        pylab.xlabel('Invoice Number')
        pylab.ylabel('Money')
        pylab.legend(loc=2)
        ax = pylab.axes()
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.tick_params(axis=u'both', which=u'both', length=0)
        return pylab
