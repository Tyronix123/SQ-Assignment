import datetime
import hashlib
import secrets
from input_validation import InputValidation
import bcrypt
from db_handler import DBHandler
from logger import Logger

#Soort van abstract class voor SuperAdmin, SystemAdmin en ServiceEngineer
class User:
    def __init__(self, username, passwordhash, role, firstname, lastname, input_validation: InputValidation, db_handler: DBHandler, logger: Logger):
        self.username = username
        self.passwordhash = passwordhash
        self.role = role
        self.first_name = firstname
        self.last_name = lastname
        self.registrationdate = datetime.date.today().isoformat()
        self.isloggedin = False
        self.input_validation = input_validation
        self.db_handler = db_handler
        self.logger = logger
        
    def getmyusername(self):
        return self.username

    def amiloggedin(self):
        return self.isloggedin

    def is_valid_password(self, enteredpassword):
        return bcrypt.checkpw(enteredpassword.encode('utf-8'), self.passwordhash.encode('utf-8'))

    def login(self, enteredpassword):
        if self.is_valid_password(enteredpassword):
            self.isloggedin = True
            print(f"Hello, {self.getmyusername()}. You've been logged in.")
            return True
        else:
            print("Login failed: wrong credentials. Please try again.")
            return False

    def logout(self):
        self.isloggedin = False
        print("User logged out.")

    def changemypassword(self, newpassword):
        if self.role == 'SuperAdministrator':
            print("SuperAdministrators cannot change their password.")

        raw_users = self.db_handler.getrawdata('users')
        target_user_raw = None

        # Find user by decrypting usernames and matching role
        for raw_user in raw_users:
            decrypted_username = self.db_handler.decryptdata(raw_user['username'])
            if decrypted_username.lower() == self.username.lower() and raw_user['role'] == self.role:
                target_user_raw = raw_user
                break

        currentpasswordinput = input("Type your current password to confirm: ")
        if self.is_valid_password(currentpasswordinput):
            if not self.input_validation.is_valid_password(newpassword):
                print("The new password isn't strong enough.")
                self.logger.writelog(
                    self.username,
                    f"Change {self.role} Password Failed",
                    f"Bad new password for '{self.username}'",
                    issuspicious=True
                )
                return False

            hashed_password = self.makepasswordhash(newpassword)

            try:
                self.db_handler.updateexistingrecord(
                    'users',
                    'username',
                    target_user_raw['username'],
                    {'password_hash': hashed_password}
                )
                print(f"Password for {self.role} '{self.username}' has been successfully changed!")
                self.logger.writelog(
                    self.username,
                    f"Change {self.role} Password",
                    f"Password for '{self.username}' changed."
                )
                return True
            except Exception as e:
                print(f"A problem happened while changing password for '{self.username}'. Error: {e}")
                self.logger.writelog(
                    self.username,
                    f"Changing {self.role} Password Failed",
                    f"Error changing password for '{self.username}': {e}",
                    issuspicious=True
                )
                return False

    @staticmethod
    def makepasswordhash(password):
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
