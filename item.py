import pylab

from database import database


class Item(object):
    """An Item identified by the item code and stored within the database

    An Item is a billable item with attributes of the date of logging this item, a item description and the charge for
    the item.

    This class provides an interface to the item model stored in the database
    """

    def __init__(self, item_code):
        """Initialize the class variables including the item code provided in the constructor and the date, description
        and amount retrieved from the database
        """
        self.code = item_code
        with database() as db:
            if db.exists('items', item_code=self.code):
                sql = 'SELECT date, description, charge FROM items WHERE item_code = %s'
                self.date, self.description, self.amount = db.query(sql, self.code, limit=1)[0]
            else:
                raise KeyError('No item with item code of {} exists within the database'.format(self.code))

    @staticmethod
    def _generate_code():
        import random, string
        return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(4))

    @classmethod
    def create(cls, date, description, charge):
        """Create a new item with the given information

        Generate a random item code and associate it with the information provided in the database"""
        with database() as db:
            # Generate a new item code until one is generated which is not already in use
            id = cls._generate_code()
            while db.exists('items', item_code=id):
                id = cls._generate_code()

            # Insert the new item into the database
            sql = 'INSERT INTO items (item_code, date, description, charge) VALUES (%s, %s, %s, %s)'
            db.query(sql, id, date, description, charge)
        return cls(id)

    def delete(self):
        """Delete an item from the database"""
        with database() as db:
            sql = 'DELETE FROM items WHERE item_code = %s'
            db.query(sql, self.code)

    @staticmethod
    def get_all():
        """Retrieve an instance of all items that are currently stored in the database"""
        with database() as db:
            return [Item(item[0]) for item in db.query('SELECT item_code FROM items')]

    @staticmethod
    def get_unlogged():
        """Retrieve an instance of all items which have not been added to an invoice currently in the database"""
        with database() as db:
            sql = 'SELECT item_code FROM items WHERE item_code NOT IN (SELECT item_code FROM invoice_items)'
            return [Item(item[0]) for item in db.query(sql)]

    def update(self, date=None, description=None, charge=None):
        """Update the values of the attributes which are not empty or None"""
        with database() as db:
            if date:
                db.query('UPDATE items SET date = %s where item_code = %s', date, self.code)
                self.date = date
            if description:
                db.query('UPDATE items SET description = %s where item_code = %s', description, self.code)
                self.description = description
            if charge:
                db.query('UPDATE items SET charge = %s where item_code = %s', charge, self.code)
                self.amount = charge

    def __lt__(self, other):
        """The __lt__ magic method allows items to be sorted according to their date"""
        return self.date < other.date

    def dict(self):
        """Return the dictionary representation of the item"""
        return {
            'code': self.code,
            'date': self.date,
            'description': self.description,
            'amount': self.amount,
        }

    @staticmethod
    def statistics():
        """Generate a pylab figure demonstrating the amount charged for each item over time"""
        dates = []
        costs = []
        pylab.figure()
        for item in sorted(Item.get_all()):
            dates.append(item.date)
            costs.append(item.amount)
        pylab.legend(('Item Charges',))
        pylab.plot(dates, costs)
        return pylab
