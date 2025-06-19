import shutil
import sqlite3
import datetime
import hashlib
from cryptography.fernet import Fernet
import secrets
import re
import os
from db_handler import DBHandler
from logger import Logger
from user import User
from input_handler import InputHandler
from input_validation import InputValidation
from superadmin import SuperAdministrator
from systemadmin import SystemAdministrator
from serviceengineer import ServiceEngineer
from traveller_handler import TravellerHandler
from scooter_handler import ScooterHandler

try:
    with open("encryption.key", "rb") as key_file:
        ENCRYPTION_KEY = key_file.read()
except FileNotFoundError:
    ENCRYPTION_KEY = Fernet.generate_key()
    with open("encryption.key", "wb") as key_file:
        key_file.write(ENCRYPTION_KEY)
    print("Created new key and saved it in 'encryption.key'.")
else:
    print("Loaded the key from 'encryption.key'.")


class UmMembers:
    def __init__(self, db_name="src/data/urban_mobility.db",
                 encryption_key=ENCRYPTION_KEY,
                 valid_roles = ['SuperAdministrator', 'SystemAdministrator', 'ServiceEngineer'],
                 valid_cities = ["Amsterdam", "Rotterdam", "Utrecht", "The Hague", "Eindhoven", "Groningen", "Maastricht", "Leiden", "Haarlem", "Delft"]):
        self.db_handler = DBHandler(db_name, encryption_key)
        self.logger = Logger(self.db_handler)
        self.input_validation = InputValidation(valid_roles, valid_cities)
        self.input_handler = InputHandler(self.input_validation, valid_cities)
        self.traveller_handler = TravellerHandler(self.db_handler, self.logger, self.input_validation, self.input_handler)
        self.scooter_handler = ScooterHandler(self.db_handler, self.logger, self.input_validation, self.input_handler)
        self.valid_cities = valid_cities
        self.loggedinuser = None

    def setupapp(self):
        self.db_handler.connect_to_db()
        self.superadmincreate()

    def shutdown_app(self):
        self.db_handler.disconnect_from_db()
        print("Urban Mobility Backend System is shutting down.")

    def superadmincreate(self):
        superadminusername = "super_admin"
        superadminpassword = "Admin_123?"
        passwordhash = User.makepasswordhash(superadminpassword)

        all_users = self.db_handler.getdata('users')
        existsuperadmin = False
        for user in all_users:
            decrypted_username = user['username']
            if decrypted_username == superadminusername:
                existsuperadmin = True
                break

        if not existsuperadmin:
            self.db_handler.addnewrecord(
                'users',
                {
                    'username': superadminusername,
                    'password_hash': passwordhash,
                    'role': 'SuperAdministrator',
                    "first_name": None,
                    "last_name": None,
                    'registration_date': datetime.date.today().isoformat()
                }
            )
            self.logger.writelog(
                "SYSTEM",
                f"Default Super Administrator '{superadminusername}' created.",
                issuspicious=False
            )


    def run(self):
        self.setupapp()

        while True:
            print("\nUrban Mobility Backend System Login")
            usernameinput = input("Enter username (or 'quit' to exit): ")
            if usernameinput.lower() == 'quit':
                self.shutdown_app()
                break

            password_input = input("Enter password: ")

            all_users = self.db_handler.getdata('users')
            userlog = []

            for user in all_users:
                if user['username'].lower() == usernameinput.lower():
                    userlog = [user]
                    break

            if not userlog:
                print("No user found. Try again")
                self.logger.writelog("LOGIN_ATTEMPT", f"Failed login for unknown user: '{usernameinput}'", issuspicious=True)
                continue

            loggedinuser = userlog[0]
            if loggedinuser['role'] == 'SuperAdministrator':
                current_user = SuperAdministrator(self.valid_cities, loggedinuser['username'], loggedinuser['password_hash'], loggedinuser['role'], None, None, loggedinuser['registration_date'], self.db_handler, self.logger, self.input_validation, self.input_handler, self.traveller_handler, self.scooter_handler)
            elif loggedinuser['role'] == 'SystemAdministrator':
                current_user = SystemAdministrator(self.valid_cities, loggedinuser['username'], loggedinuser['password_hash'], loggedinuser['role'], loggedinuser['first_name'], loggedinuser['last_name'], loggedinuser['registration_date'], self.db_handler, self.logger, self.input_validation, self.input_handler, self.traveller_handler, self.scooter_handler)
            elif loggedinuser['role'] == 'ServiceEngineer':
                current_user = ServiceEngineer(self.valid_cities, loggedinuser['username'], loggedinuser['password_hash'], loggedinuser['role'], loggedinuser['first_name'], loggedinuser['last_name'], loggedinuser['registration_date'], self.db_handler, self.logger, self.input_validation, self.input_handler, self.traveller_handler, self.scooter_handler)
            else:
                print(f"Error: role '{loggedinuser['role']}' is not recognized. Contact an administrator.")
                self.logger.writelog("LOGIN_ATTEMPT", f"Blocked login for user '{usernameinput}' with unknown role '{loggedinuser['role']}'", issuspicious=True)
                continue
            if current_user.login(password_input):
                self.loggedinuser = current_user
                self.logger.writelog(self.loggedinuser.getmyusername(), "User logged in successfully.", issuspicious=False)
                self.runsession()
            else:
                self.logger.writelog(usernameinput, "Failed login attempt (wrong password).", issuspicious=True)
            self.loggedinuser = None

    def runsession(self):
        role = self.loggedinuser.__class__.__name__
        while self.loggedinuser.amiloggedin():
            print(f"\nLogged in as: {self.loggedinuser.getmyusername()} ({role})")
            self.loggedinuser.show_menu()
            choice = input("Choose an option: ")
            self.clear_console()
            if choice == '1':
                if role == 'SuperAdministrator':
                    print("SuperAdministrator cannot change their password.")
                else:
                    new_pw = input("Enter new password: ")
                    self.loggedinuser.changemypassword(new_pw)
                    self.logger.writelog(self.loggedinuser.getmyusername(), "Attempted password change.")
            elif choice == '2':
                self.loggedinuser.logout()
                self.logger.writelog(self.loggedinuser.getmyusername(), "User logged out.", issuspicious=False)
                break
            else:
                self.loggedinuser.handle_menu_choice(choice)

    def clear_console(self):
        os.system('cls' if os.name == 'nt' else 'clear')

if __name__ == "__main__":
    app = UmMembers()
    app.run()