from database import database

class Item(object):
    def __init__(self, item_code):
        self.item_code = item_code
        with database() as db:
            if db.exists('items', item_code = self.item_code):
                self.date, self.description, self.charge = \
                    db.query('SELECT date, description, charge FROM items WHERE item_code = %s', self.item_code)[0]

    @classmethod
    def create(cls, date, description, charge):
        import random, string
        with database() as db:
            id = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(4))
            db.commit('INSERT INTO items (item_code, date, description, charge) VALUES (%s, %s, %s, %s)',
                      id, date, description, charge)
        return Item(id)

    @staticmethod
    def get_unlogged():
        with database() as db:
            return [Item(item[0]) for item in db.query('SELECT item_code FROM items WHERE item_code NOT IN (SELECT item_code FROM invoice_items)')]

    def get_id(self):
        return self.item_code

    def get_date(self):
        return self.date

    def get_amount(self):
        return self.charge

    def get_description(self):
        return self.description

    def __lt__(self, other):
        return self.get_date() < other.get_date()