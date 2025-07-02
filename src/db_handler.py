import sqlite3
import re
import bcrypt
from cryptography.fernet import Fernet
import os
import base64

class DBHandler:
    def __init__(self, db_name, encryption_key):
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        self.cipher = Fernet(encryption_key)

        db_dir = os.path.dirname(self.db_name)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
        self.connect_to_db()

    def _sanitize_identifier(self, identifier: str) -> str:
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', identifier):
            raise ValueError(f"Invalid identifier: {identifier}")
        return identifier

    def _validate_table_name(self, table_name: str) -> bool:
        valid_tables = {'users', 'travellers', 'scooters', 'logs', 'restore_codes'}
        return table_name in valid_tables

    def _is_query_safe(self, query: str) -> bool:
        dangerous_patterns = [
            r";\s*--", r";\s*#",
            r"\b(?:DROP|TRUNCATE|ALTER|CREATE|REPLACE)\b",
            r"\b(?:UNION|HAVING)\b",
            r"\b(?:EXEC|EXECUTE|DECLARE)\b",
            r"\b(?:XP_|SP_)\w+",
        ]
        
        query_upper = query.upper()
        for pattern in dangerous_patterns:
            if re.search(pattern, query_upper, re.IGNORECASE):
                return False
        return True
    
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
            first_name TEXT,
            last_name TEXT,
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
            brand TEXT,
            model TEXT,
            serial_number TEXT PRIMARY KEY,
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
            backup_id TEXT, 
            backup_file_name TEXT,
            created_by TEXT,
            for_user TEXT, 
            `expiry_date` DATE,
            used INTEGER,
            FOREIGN KEY(created_by) REFERENCES users(username),
            FOREIGN KEY(for_user) REFERENCES users(username)
        )
        ''')

        self.conn.commit()
        self.conn.close()
        print(self.getdata('restore_codes'))

    def encryptdata(self, data: str) -> str:
        encrypted_bytes = self.cipher.encrypt(data.encode('utf-8'))
        return base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')

    def decryptdata(self, encrypted_data: str) -> str:
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
        decrypted_bytes = self.cipher.decrypt(encrypted_bytes)
        return decrypted_bytes.decode('utf-8')


    def runquery(self, query, params=(), get_one=False, get_all=False):
        if not self.conn:
            print("Can't run query, database connection not found")
            return None
        try:
            if not self._is_query_safe(query):
                raise ValueError("Potentially unsafe query detected")
            
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

    def addnewrecord(self, tablename, record: dict):
        if not self.conn:
            print("Can't add record, no database connection")
            return

        columns = []
        placeholders = []
        values = []

        for col, val in record.items():
            col = self._sanitize_identifier(col)
            columns.append(col)
            placeholders.append("?")

            if tablename == 'travellers' and col in [
                'first_name', 'last_name', 'birthday', 'gender',
                'street_name', 'house_number', 'zip_code', 'city',
                'email', 'mobile_phone', 'driving_license'
            ]:
                values.append(self.encryptdata(str(val)))

            elif tablename == 'users' and col in ['username', 'first_name', 'last_name']:
                values.append(self.encryptdata(str(val)))

            elif tablename == 'scooters' and col == 'location':
                values.append(self.encryptdata(str(val)))

            elif tablename == 'logs' and col in ['username', 'activity', 'details']:
                values.append(self.encryptdata(str(val)))

            else:
                values.append(val)

        query = f"INSERT INTO {tablename} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        self.runquery(query, tuple(values))

    def getdata(self, tablename, filters=None):
        if not self.conn:
            print("Can't get data, no database connection")
            return []
        
        if not self._validate_table_name(tablename):
            raise ValueError(f"Invalid table name: {tablename}")

        query = f"SELECT * FROM {tablename}"
        params = []

        if filters:
            where_parts = []
            for col, val in filters.items():
                col = self._sanitize_identifier(col)
                where_parts.append(f"{col} = ?")
                params.append(val)
            query += " WHERE " + " AND ".join(where_parts)

        rows = self.runquery(query, tuple(params), get_all=True)

        if not rows:
            return []

        column_names = [desc[0] for desc in self.cursor.description]
        results = []

        for rowdata in rows:
            recorddict = {}

            for i, colname in enumerate(column_names):
                value = rowdata[i]

                if tablename == 'travellers' and colname in [
                    'first_name', 'last_name', 'birthday', 'gender',
                    'street_name', 'house_number', 'zip_code', 'city',
                    'email', 'mobile_phone', 'driving_license'
                ] and value is not None:
                    recorddict[colname] = self.decryptdata(value)

                elif tablename == 'users' and colname in ['username', 'first_name', 'last_name'] and value is not None:
                    recorddict[colname] = self.decryptdata(value)

                elif tablename == 'scooters' and colname == 'location' and value is not None:
                    recorddict[colname] = self.decryptdata(value)

                elif tablename == 'logs' and colname in ['username', 'activity', 'details'] and value is not None:
                    recorddict[colname] = self.decryptdata(value)

                else:
                    recorddict[colname] = value

            results.append(recorddict)

        return results
    

    def getrawdata(self, table_name, filters=None):
        if not self.conn:
            raise RuntimeError("Database connection not established")
            
        if not self._validate_table_name(table_name):
            raise ValueError(f"Invalid table name: {table_name}")        
        
        try:
            query = f"SELECT * FROM {table_name}"
            params = []

            if filters:
                conditions = []
                for key, value in filters.items():
                    key = self._sanitize_identifier(key)
                    conditions.append(f"{key} = ?")
                    params.append(value)
                query += " WHERE " + " AND ".join(conditions)

            rows = self.runquery(query, tuple(params), get_all=True)
            if not rows:
                return []

            column_names = [desc[0] for desc in self.cursor.description]
            results = []
            
            for row in rows:
                results.append(dict(zip(column_names, row)))
                
            return results

        except Exception as e:
            print(f"Error retrieving raw data from {table_name}: {e}")
            return []

    
    @staticmethod
    def makepasswordhash(password: str) -> str:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    def updateexistingrecord(self, tablename, idcolumn, id_value, new_info):
        if not self.conn:
            print("Can't update, no database connection")
            return
        
        if not self._validate_table_name(tablename):
            raise ValueError(f"Invalid table name: {tablename}")


        try:
            idcolumn = self._sanitize_identifier(idcolumn)
            set_parts = []
            values = []

            for col, val in new_info.items():
                col = self._sanitize_identifier(col)
                set_parts.append(f"{col} = ?")

                if tablename == 'travellers' and col in [
                    'first_name', 'last_name', 'birthday', 'gender',
                    'street_name', 'house_number', 'zip_code', 'city',
                    'email', 'mobile_phone', 'driving_license'
                ]:
                    values.append(self.encryptdata(str(val)))

                elif tablename == 'users' and col in ['username', 'first_name', 'last_name']:
                    values.append(self.encryptdata(str(val)))

                elif tablename == 'scooters' and col == 'location':
                    values.append(self.encryptdata(str(val)))

                elif tablename == 'logs' and col in ['username', 'activity', 'details']:
                    values.append(self.encryptdata(str(val)))

                else:
                    values.append(val)

            values.append(id_value)
            query = f"UPDATE {tablename} SET {', '.join(set_parts)} WHERE {idcolumn} = ?"
            self.runquery(query, tuple(values))
        except Exception as e:
            print(f"Error updating record: {e}")
            raise


    def deleterecord(self, table_name, id_column, id_value):
        if not self.conn:
            print("Can't delete record, no database connection active.")
            return
        
        if not self._validate_table_name(table_name):
            raise ValueError(f"Invalid table name: {table_name}")
                
        try:
            id_column = self._sanitize_identifier(id_column)
            query = f"DELETE FROM {table_name} WHERE {id_column} = ?"
            self.runquery(query, (id_value,))
        except Exception as e:
            print(f"Error deleting record: {e}")
            raise

    def get_users_by_role(self, role):
        if not self.conn:
            print("Can't get data, no database connection")
            return []

        try:
            query = "SELECT username, first_name, last_name, role FROM users WHERE role = ?"
            rows = self.runquery(query, (role,), get_all=True)

            if not rows:
                print(f"No users found with role: {role}")
                return []

            decrypted_users = []
            for row in rows:
                decrypted_user = {
                    'username': self.decryptdata(row[0]),
                    'first_name': self.decryptdata(row[1]),
                    'last_name': self.decryptdata(row[2]),
                    'role': row[3]
                }
                decrypted_users.append(decrypted_user)

            return decrypted_users

        except Exception as e:
            print(f"Error retrieving users by role: {e}")
            return []