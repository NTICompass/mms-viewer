import sqlite3

class PhoneBook:
    def __init__(self, database='phonebook.db'):
        self.db_conn = sqlite3.connect(database)

    def __del__(self):
        self.db_conn.close()

    def get_name(self, number):
        sql = self.db_conn.cursor()
        sql.execute('SELECT first_name, last_name FROM phone_numbers WHERE phone_num=?', (number,))
        return sql.fetchone()

    def get_names(self, numbers):
        sql = self.db_conn.cursor()
        
        values = ','.join(['?'] * len(numbers))
        result = sql.execute('SELECT phone_num, first_name, last_name FROM phone_numbers WHERE phone_num IN ({0})'.format(values), numbers)

        # Convert this to an object of tuples
        return {row[0]:(row[1],row[2]) for row in result}
