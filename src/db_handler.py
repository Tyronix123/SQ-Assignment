import sqlite3
from cryptography.fernet import Fernet

class DBHandler:
    def __init__(self, db_name, encryption_key):
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        self.cipher = Fernet(encryption_key)

    def connect_to_db(self):
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            print(f"Couldn't connect to the database! Error: {e}")

    def disconnect_from_db(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None

    def create_database(self):
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()

        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT,
            role TEXT,
            registration_date DATETIME
        )
        ''')

        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS travellers (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT,
            last_name TEXT,
            birthday DATE,
            gender TEXT,
            street_name TEXT,
            house_number TEXT,
            zip_code TEXT,
            city TEXT,
            email TEXT,
            mobile_phone TEXT,
            driving_license TEXT,
            registration_date DATETIME
        )
        ''')

        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS scooters (
            scooter_id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT,
            model TEXT,
            serial_number TEXT,
            top_speed REAL,
            battery_capacity REAL,
            soc INTEGER,
            soc_range TEXT,
            location TEXT,
            out_of_service TEXT,
            mileage REAL,
            last_maintenance DATE,
            in_service_date DATETIME
        )
        ''')

        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE,
            time TIME,
            username TEXT,
            activity TEXT,
            details TEXT,
            suspicious TEXT,
            FOREIGN KEY(username) REFERENCES users(username)
        )
        ''')

        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS restore_codes (
            code TEXT PRIMARY KEY,
            created_by TEXT,
            for_user TEXT,
            used TEXT,
            FOREIGN KEY(created_by) REFERENCES users(username),
            FOREIGN KEY(for_user) REFERENCES users(username)
        )
        ''')

        self.conn.commit()
        self.conn.close()
        print(self.getdata('restore_codes'))

    def encryptdata(self, data):
        return self.cipher.encrypt(data.encode('utf-8'))

    def decryptdata(self, encrypted_data):
        return self.cipher.decrypt(encrypted_data).decode('utf-8')

    def runquery(self, query, params=(), get_one=False, get_all=False):
        if not self.conn:
            print("Can't run query, database connection not found")
            return None
        try:
            self.cursor.execute(query, params)
            self.conn.commit()
            if get_all:
                return self.cursor.fetchall()
            elif get_one:
                return self.cursor.fetchone()
            return None
        except sqlite3.Error as e:
            print(f"a database error happened when running: {e}")
            return None

    def addnewrecord(self, table_name, data_info):
        if not self.conn:
            print("can't add record, no database connection.")
            return

        columns = []
        values = []
        question_marks = []

        for col, val in data_info.items():
            columns.append(col)
            if table_name == 'travellers' and col == 'mobile_phone':
                values.append(self.encryptdata(str(val)))
            elif table_name == 'scooters' and col == 'location':
                values.append(self.encryptdata(str(val)))
            elif table_name == 'logs' and (col == 'description' or col == 'additional_info'):
                values.append(self.encryptdata(str(val)))
            else:
                values.append(val)
            question_marks.append('?')

        query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(question_marks)})"
        self.runquery(query, tuple(values))

    def getdata(self, tablename, filters=None):
        if not self.conn:
            print("Can't get data, no database connection")
            return []
        query = f"SELECT * FROM {tablename}"
        params = []
        if filters:
            where_parts = []
            for col, val in filters.items():
                where_parts.append(f"{col} = ?")
                params.append(val)
            query += " WHERE " + " AND ".join(where_parts)
        rows = self.runquery(query, tuple(params), get_all=True)
        if not rows:
            return []
        column_names = [description[0] for description in self.cursor.description]
        results = []
        for rowdata in rows:
            recorddict = {}
            for i, colname in enumerate(column_names):
                value = rowdata[i]
                if tablename == 'travellers' and colname == 'mobile_phone' and value is not None:
                    recorddict[colname] = self.decryptdata(value)
                elif tablename == 'scooters' and colname == 'location' and value is not None:
                    recorddict[colname] = self.decryptdata(value)
                elif tablename == 'logs' and (colname == 'description' or colname == 'additional_info') and value is not None:
                    recorddict[colname] = self.decryptdata(value)
                else:
                    recorddict[colname] = value
            results.append(recorddict)
        return results

    def updateexistingrecord(self, tablename, idcolumn, id_value, new_info):
        if not self.conn:
            print("Can't update, no database connection")
            return

        set_parts = []
        values = []
        for col, val in new_info.items():
            set_parts.append(f"{col} = ?")
            if tablename == 'travellers' and col == 'mobile_phone':
                values.append(self.encryptdata(str(val)))
            elif tablename == 'scooters' and col == 'location':
                values.append(self.encryptdata(str(val)))
            elif tablename == 'logs' and (col == 'description' or col == 'additional_info'):
                values.append(self.encryptdata(str(val)))
            else:
                values.append(val)

        values.append(id_value)
        query = f"UPDATE {tablename} SET {', '.join(set_parts)} WHERE {idcolumn} = ?"
        self.runquery(query, tuple(values))

    def deleterecord(self, table_name, id_column, id_value):
        if not self.conn:
            print("Can't delete record, no database connection active.")
            return
        query = f"DELETE FROM {table_name} WHERE {id_column} = ?"
        self.runquery(query, (id_value,))