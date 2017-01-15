from database import database

class Person(object):
    """An interface to the person database model

    Contains information regarding the persons name, address and email address
    """
    def __init__(self, name):
        """Initialize the class by retrieving the person data from the database based on the name"""
        self.name = name
        with database() as db:
            if(db.exists('persons', person_name = self.name)):
                self.address, self.email = db.query('SELECT address, email FROM persons WHERE person_name = %s', self.name)[0]
            else:
                raise KeyError('No person with the name {} exists within the database'.format(self.name))

    @classmethod
    def create(cls, name, address, email):
        """Add a new person to the database if the name is not already in use"""
        with database() as db:
            if not db.exists('persons', person_name = name):
                sql = 'INSERT INTO persons (person_name, address, email) VALUES (%s, %s, %s)'
                db.query(sql, name, address, email)
            else:
                raise KeyError('A person with the name {} already exists within the database'.format(name))
        return cls(name)

    def delete(self):
        """Remove the person data from the database"""
        with database() as db:
            db.query('DELETE FROM persons WHERE person_name = %s', self.name)

    @staticmethod
    def get_all():
        """Retrieve all persons stored in the database"""
        with database() as db:
            return [Person(person[0]) for person in db.query('SELECT person_name FROM persons')]