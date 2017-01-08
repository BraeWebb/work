from database import database

class Person(object):
    def __init__(self, name):
        self.name = name
        with database() as db:
            self.address, self.email = db.query('SELECT address, email FROM persons WHERE person_name = %s', self.name)[0]

    @staticmethod
    def get_all():
        with database() as db:
            return [Person(person[0]) for person in db.query('SELECT person_name FROM persons')]

    def get_name(self):
        return self.name

    def get_address(self):
        return self.address

    def get_email(self):
        return self.email

    def __str__(self):
        return self.name