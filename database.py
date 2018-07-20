import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

import config


class database:
    def __init__(self):
        """Establish a connection to the database and initialize the class"""
        self.db = psycopg2.connect(host=config.postgres_host,
                                   user=config.postgres_user,
                                   password=config.postgres_password,
                                   database=config.postgres_database)
        self.cursor = self.db.cursor()

    def commit(self):
        """Commit the queries previously run on the database"""
        self.db.commit()

    def rollback(self):
        """Rollback the queries previously run on the database"""
        self.db.rollback()

    def close(self):
        """Close the cursor object and the connection to the database

        Used when closing the context manager or deleting the object
        """
        self.cursor.close()
        self.db.close()

    def __enter__(self):
        """Allows for the database to have context management"""
        return self

    def __exit__(self, exception_type, exception_val, trace):
        """Allows for the database to have context management

        If an error occurred rollback the database, otherwise, commits
        """
        if not exception_type:
            self.commit()
        else:
            self.rollback()
        self.close()

    def __repr__(self):
        """Represent the database object as a string"""
        data = [s.split(' ') for s in self.db.dsn.split('=')]
        return 'Database(database={}, user={})'.format(data[1][0], data[2][0])

    def query(self, query, *variables, limit=None):
        """Execute a SQL query and return the results

        query: a string SQL statement to execute on the database
        *variables: the items to place in the query in the place of %s
        limit: the maximum amount of rows to return
        """
        self.cursor.execute(query, variables)
        try:
            if limit:
                return self.cursor.fetchmany(limit)
            else:
                return self.cursor.fetchall()
        except psycopg2.ProgrammingError:
            return None

    def exists(self, table, **where):
        """Check if rows exist in a table satisfying the given where clauses

        table: the database table to check
        **where: key value pairs of where conditions for locating the rows
        """
        # Format the list of where statements
        wheres = ' AND '.join([str(attr) + '=\'' + str(val) + '\'' for attr, val in where.items()])

        if where:
            query = 'SELECT COUNT(*) FROM {} WHERE {}'.format(table, wheres)
        else:
            query = 'SELECT COUNT(*) FROM {}'.format(table, wheres)
        self.cursor.execute(query)

        return bool(self.cursor.fetchone()[0])

    def __bool__(self):
        """Return true if the database has an open connection, false otherwise"""
        return not bool(self.db.closed)

    def __del__(self):
        """Closes all connections to the database when the object is deleted"""
        self.close()


def create_invoice_items(connection):
    connection.query("""CREATE TABLE invoice_items (item_code text NOT NULL,
                        invoice_number integer NOT NULL);""")


def create_invoices(connection):
    connection.query("""CREATE TABLE invoices (invoice_number integer NOT NULL,
                        date date NOT NULL, 
                        payer text NOT NULL, 
                        payee text NOT NULL);""")


def create_items(connection):
    connection.query("""CREATE TABLE items (
                        item_code text NOT NULL,
                        date date NOT NULL,
                        description text NOT NULL,
                        charge double precision NOT NULL);""")


def create_persons(connection):
    connection.query("""CREATE TABLE persons (
                        person_name text NOT NULL,
                        address text NOT NULL,
                        email text NOT NULL);""")


def create_tables(connection):
    create_invoice_items(connection)
    create_invoices(connection)
    create_items(connection)
    create_persons(connection)


def create_database(connection):
    connection.query("CREATE DATABASE work")
    create_tables(connection)


def tables_exist(connection):
    for table in ("invoice_items", "invoices", "items", "persons"):
        try:
            connection.exists(table)
        except psycopg2.ProgrammingError:
            return False
    return True


def database_exists():
    try:
        test_connection_db = database()
        test_connection_db.close()
        return True
    except psycopg2.OperationalError:
        return False


if __name__ == "__main__":
    if not database_exists():
        tmp = config.postgres_database
        config.postgres_database = 'postgres'
        with database() as connection:
            connection.db.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            create_database(connection)
        config.postgres_database = tmp

    test_connection = database()
    if not tables_exist(test_connection):
        with database() as connection:
            create_tables(connection)
    test_connection.close()
