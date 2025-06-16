import datetime
import hashlib
import secrets
from input_validation import InputValidation

class User:
    def __init__(self, username, passwordhash, firstname, lastname):
        self.username = username
        self.passwordhash = passwordhash
        self.firstname = firstname
        self.lastname = lastname
        self.registrationdate = datetime.date.today().isoformat()
        self.isloggedin = False

    def getmyusername(self):
        return self.username

    def amiloggedin(self):
        return self.isloggedin

    def is_valid_password(self, enteredpassword):
        hashedenteredpassword = self.makepasswordhash(enteredpassword)
        return hashedenteredpassword == self.passwordhash

    def login(self, enteredpassword):
        if self.is_valid_password(enteredpassword):
            self.isloggedin = True
            print(f"Hello, {self.username}. You've been logged in.")
            return True
        else:
            print("Login failed: wrong credentials. Please try again.")
            return False

    def logout(self):
        self.isloggedin = False
        print("User logged out.")

    def changemypassword(self, newpassword):
        currentpasswordinput = input("type your current password to confirm")
        if self.is_valid_password(currentpasswordinput):
            if InputValidation.is_valid_password(newpassword):
                self.passwordhash = self.makepasswordhash(newpassword)
                print("Password successfully changed")
                return True
            else:
                print("password doesnt meet criteria")
                return False
        else:
            print("Incorrect current password. Password change failed.")
            return False

    @staticmethod
    def makepasswordhash(password):
        hasher = hashlib.sha256()
        hasher.update(password.encode('utf-8'))
        return hasher.hexdigest()

    def show_common_menu(self) -> None:
        print("\n--- Your Menu ---")
        print("1. Change My Password")
        print("2. Log Out")