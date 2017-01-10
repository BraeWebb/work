from flask import render_template
from xhtml2pdf import pisa
import pylab

import config
from database import database
from emailer import Email

from item import Item
from person import Person

class Invoice(object):
    def __init__(self, invoice_id):
        self.invoice_id = int(invoice_id)
        self.pdf_file = 'invoices/{}.pdf'.format(self.invoice_id)
        with database() as db:
            if db.exists('invoices', invoice_number = self.invoice_id):
                self.date, self.payer, self.payee = \
                    db.query('SELECT date, payer, payee FROM invoices WHERE invoice_number = %s', self.invoice_id)[0]
                self.amount = db.query('SELECT SUM(charge) FROM items WHERE item_code IN (SELECT item_code FROM invoice_items WHERE invoice_number = %s)', self.invoice_id)[0][0]

    @staticmethod
    def get_all():
        with database() as db:
            return [Invoice(inv[0]) for inv in db.query('SELECT invoice_number FROM invoices')]

    @classmethod
    def create(cls, date, payer, payee, items):
        with database() as db:
            id = int(db.query('SELECT MAX(invoice_number) FROM invoices')[0][0]) + 1
            db.commit('INSERT INTO invoices (invoice_number, date, payer, payee) VALUES (%s, %s, %s, %s)',
                      id, date, payer, payee)
            for item in items:
                if db.exists('items', item_code=item):
                    db.commit('INSERT INTO invoice_items (item_code, invoice_number) VALUES (%s, %s)', item, id)
        return Invoice(id)

    def get_id(self):
        return self.invoice_id

    def get_name(self):
        return '{:04d}'.format(self.invoice_id)

    def get_date(self):
        return self.date

    def get_payer(self):
        return Person(self.payer)

    def get_payee(self):
        return Person(self.payee)

    def get_amount(self):
        return self.amount

    def get_biller_details(self):
        return config.biller_details

    def get_items(self):
        with database() as db:
            return [Item(item[0]) for item in db.query('SELECT item_code FROM invoice_items WHERE invoice_number = %s', self.invoice_id)]

    def build_pdf(self):
        with open(self.pdf_file, 'wb+') as output:
            pisa.CreatePDF(self.html(), dest=output)

    def pdf(self):
        self.build_pdf()
        with open(self.pdf_file, 'rb') as pdf:
            return pdf.read(), 200, {'Content-Type': 'application/pdf',
                                     'Content-Disposition': 'inline; filename="{}.pdf"'.format(self.get_name())}

    def download(self):
        self.build_pdf()
        with open(self.pdf_file, 'rb') as pdf:
            return pdf.read(), 200, {'Content-Type': 'application/pdf',
                                     'Content-Disposition': 'attachment; filename="{}.pdf"'.format(self.get_name())}

    def html(self):
        return render_template('invoices/invoice.html', invoice=self)

    def email(self, body):
        self.build_pdf()
        with Email(self.get_payer().get_email(), self.get_payee().get_email(), 'Invoice {}'.format(self.get_name())) as email:
            email.attach_pdf(self.pdf_file, 'Invoice #{}'.format(self.get_name()))
            email.set_body(body)
            email.send()
        return 'Email Sent!'

    @staticmethod
    def statistics():
        dates = []
        costs = []
        pylab.figure()
        for invoice in Invoice.get_all():
            dates.append(invoice.get_date())
            costs.append(invoice.get_amount())
        pylab.legend(('Invoice Amounts', ))
        pylab.plot(dates, costs)
        return pylab