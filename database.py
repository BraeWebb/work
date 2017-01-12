import psycopg2

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
