import psycopg2
import config

class database:

    def __init__(self):
        '''
        Establish a connection to the database and return the cursor

        __init__() -> Cursor
        '''
        self.db = psycopg2.connect(host=config.postgres_host,
                                   user=config.postgres_user,
                                   password=config.postgres_password,
                                   database=config.postgres_database)
        self.cur = self.db.cursor()

    def commit(self, query, *variables):
        '''
        Execute SQL statements to be commited as changes to the database

        commit(str, str, str, ..., str) -> Cursor
        '''
        self.cur.execute(query, variables)
        self.db.commit()
        return self.cur

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_val, trace):
        self.close()

    def close(self):
        '''
        Close the connection to the database

        close() -> None
        '''
        self.cur.close()
        self.db.close()

    def iterate(self, query, callback):
        '''
        Execute SQL query and call the callback function for each row with row
        as a parameter

        iterate(str, function) -> None
        '''
        self.cur.execute(query)
        numrows = int(self.cur.rowcount)
        for x in range(numrows):
            row=self.cur.fetchone()
            callback(row)
        self.db.commit()
        self.cur.close()

    def query(self, query, *variables):
        '''
        Execute a SQL query and return all rows as an array

        query(str, str, str, ..., str) -> tuple<tuple<obj>>
        '''
        self.cur.execute(query, variables)
        return self.cur.fetchall()

    def exists(self, table, **where):
        '''
        Check if rows exist in a table satifying the given where clauses

        exists(str, attr=str, attr=str, ..., attr=str) -> bool
        '''
        wheres = [str(attr)+'=\''+str(val)+'\'' for attr, val in where.items()]
        self.cur.execute('SELECT COUNT(*) FROM {} WHERE {}'
                         .format(table,' AND '.join(wheres)))
        return self.cur.fetchone()[0]
