from flask import Flask, render_template, request, redirect, jsonify, abort

from invoice import Invoice, Item, Person
from datetime import date

app = Flask(__name__)


@app.route('/invoices', defaults={'page': 1})
@app.route('/invoices/page/<int:page>')
def invoices(page):
    invoices_per_page = 5
    invoice_count =Invoice.get_invoice_count()
    page_count = invoice_count // invoices_per_page + int(invoice_count % invoices_per_page > 0)

    start = max(invoice_count - (page*invoices_per_page), 0)
    end = max(invoice_count - ((page-1)*invoices_per_page), 0)

    return render_template('invoices.html', invoices=list(reversed(Invoice.get_all(start=start, end=end))),
                           page_count=page_count, page=page)

@app.route('/api/item', methods=['POST'])
def api_log_item():
    item = Item.create(request.form.get('date'), request.form.get('description'), request.form.get('charge'))
    return jsonify(**item.dict()), 201

@app.route('/api/item', methods=['GET'])
def api_view_items():
    return jsonify([item.dict() for item in Item.get_all()])

@app.route('/api/item/<item>', methods=['GET'])
def api_view_item(item):
    try:
        item = Item(item)
    except KeyError:
        abort(404)
    return jsonify(**item.dict())

@app.route('/api/item/<item>', methods=['PUT'])
def api_edit_item(item):
    try:
        item = Item(item)
    except KeyError:
        abort(404)
    item.update(date=request.form.get('date'), description=request.form.get('description'), charge=request.form.get('charge'))
    return jsonify(**item.dict())

@app.route('/api/item/<item>', methods=['DELETE'])
def api_delete_item(item):
    try:
        item = Item(item)
    except KeyError:
        abort(404)
    item.delete()
    return jsonify(error=False, item=item.dict())

@app.route('/api/log/invoice', methods=['POST'])
def api_log_invoice():
    invoice = Invoice.create(request.form.get('date'), request.form.get('payer'),
                             request.form.get('payee'), request.form.getlist('items'))
    return redirect('/invoice/{}'.format(invoice.id))

@app.route('/api/invoice/<invoice>/delete')
def api_delete_invoice(invoice):
    Invoice(invoice).delete()
    return 'Deleted'

@app.route('/people', defaults={'page': 1})
@app.route('/people/page/<int:page>')
def people(page):
    people_per_page = 10
    people = Person.get_all()
    people_count = len(people)

    page_count = len(people) // people_per_page + int(len(people) % people_per_page > 0)

    start = max(people_count - (page*people_per_page), 0)
    end = max(people_count - ((page-1)*people_per_page), 0)

    return render_template('people.html', people=list(people),
                           page_count=page_count, page=page)

@app.route('/api/person', methods=['POST'])
def api_add_contact():
    person = Person.create(request.form.get('name'), request.form.get('email'),
                           request.form.get('address'))
    return person.name

@app.route('/api/person/<person>/delete')
def api_delete_person(person):
    Person(person).delete()
    return 'Deleted'

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
app.add_url_rule('/people/add', 'add_contact', lambda: render_template('people/add.html',))
app.add_url_rule('/api/email/invoice/<invoice>', 'send_email_invoice', lambda invoice: Invoice(invoice).email(request.form.get('body')), methods=['POST'])

if __name__ == '__main__':
    app.run(debug=True)
