from flask import Flask

app = Flask(__name__)


@app.route('/invoices')
def invoices():
    return 'A list of invoices with preview data such as amount, date, etc. Includes a log item and log invoice button'


@app.route('/invoice/<invoice>')
def invoice(invoice):
    return 'Display a HTML version of the invoice - includes a download, email, edit and pdf button'


@app.route('/invoice/<invoice>.pdf')
def invoice_pdf(invoice):
    return open('{}.pdf'.format(invoice), 'rb').read(), 200, {'Content-Type': 'application/pdf',
                                                              'Content-Disposition': 'inline; filename="{}.pdf"'
                                                                  .format(invoice)}


@app.route('/invoice/<invoice>/download')
def invoice_download(invoice):
    return open('{}.pdf'.format(invoice), 'rb').read(), 200, {'Content-Type': 'application/pdf',
                                                              'Content-Disposition': 'attachment; filename="{}.pdf"'
                                                                  .format(invoice)}


@app.route('/invoice/<invoice>/edit')
def edit_invoice(invoice):
    return 'Edit the invoice information'


@app.route('/log/invoice')
def log_invoice():
    return 'A form for logging a new invoice'


if __name__ == '__main__':
    app.run()
