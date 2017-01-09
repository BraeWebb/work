from flask import Flask, render_template, request, redirect, url_for

from invoice import Invoice, Item, Person
from datetime import date

app = Flask(__name__)


@app.route('/invoices')
def invoices():
    return render_template('invoices.html', invoices=reversed(Invoice.get_all()))

@app.route('/api/log/item', methods=['POST'])
def api_log_item():
    item = Item.create(request.form.get('date'), request.form.get('description'), request.form.get('charge'))
    return redirect(url_for('log_invoice'))


@app.route('/api/log/invoice', methods=['POST'])
def api_log_invoice():
    invoice = Invoice.create(request.form.get('date'), request.form.get('payer'),
                             request.form.get('payee'), request.form.getlist('items'))
    return redirect('/invoice/{}'.format(invoice.get_id()))

@app.route('/statistics')
def invoice_stats():
    return render_template('statistics.html')

@app.route('/statistics/invoices.svg')
def generate_statistics_invoices():
    canvas = Invoice.statistics()
    canvas.savefig('invoices.svg')
    with open('invoices.svg', 'rb') as img:
        return img.read(), 200, {'Content-Type': 'image/svg+xml',
                                 'Content-Disposition': 'attachment; filename="invoices.svg"'}

@app.route('/statistics/items.svg')
def generate_statistics_items():
    canvas = Item.statistics()
    canvas.savefig('items.svg')
    with open('items.svg', 'rb') as img:
        return img.read(), 200, {'Content-Type': 'image/svg+xml',
                                 'Content-Disposition': 'attachment; filename="items.svg"'}

def render(url, **funcs):
    def inner_render(**args):
        for key, arg in args.items():
            if(funcs[key]):
                args[key] = funcs[key](arg)
        return render_template(url, **args)
    return inner_render

app.add_url_rule('/invoice/<invoice>', 'view_invoice', lambda invoice: Invoice(invoice).html())
app.add_url_rule('/invoice/<invoice>.pdf', 'view_invoice_pdf', lambda invoice: Invoice(invoice).pdf())
app.add_url_rule('/invoice/<invoice>/download', 'download_invoice_pdf', lambda invoice: Invoice(invoice).download())
app.add_url_rule('/invoice/<invoice>/email', 'email_invoice', render('invoices/email.html', invoice=Invoice))
app.add_url_rule('/item/log', 'log_item', lambda: render_template('items/log.html', date=date.today()))
app.add_url_rule('/invoice/log', 'log_invoice', lambda: render_template('invoices/log.html', date=date.today(), people=Person.get_all(), items=Item.get_unlogged()))
app.add_url_rule('/api/email/invoice/<invoice>', 'send_email_invoice', lambda invoice: Invoice(invoice).email(request.form.get('body')))

if __name__ == '__main__':
    app.run(debug=True)
