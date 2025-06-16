import shutil
import sqlite3
import datetime
import hashlib
from cryptography.fernet import Fernet
import secrets
import re
import os
from input_validation import InputValidation
from db_handler import DBHandler
from logger import Logger
from user import User
from superadmin import SuperAdministrator
from systemadmin import SystemAdministrator
from serviceengineer import ServiceEngineer

try:
    with open("encryption.key", "rb") as key_file:
        ENCRYPTION_KEY = key_file.read()
except FileNotFoundError:
    ENCRYPTION_KEY = Fernet.generate_key()
    with open("encryption.key", "wb") as key_file:
        key_file.write(ENCRYPTION_KEY)
    print("Hey! Just made a brand new secret key and saved it in 'encryption.key'.")
else:
    print("Cool! Loaded the secret key from 'encryption.key'.")

class UmMembers:
    def __init__(self, db_name="um.db", encryption_key=ENCRYPTION_KEY):
        self.db_manager = DBHandler(db_name, encryption_key)
        self.logger = Logger(self.db_manager)
        self.loggedinuser = None

    def setupapp(self):
        self.db_manager.connect_to_db()
        self.db_manager.create_database()
        self.superadmincreate()

    def shutdown_app(self):
        self.db_manager.disconnect_from_db()
        print("Urban Mobility Backend System is shutting down. Goodbye!")

    def superadmincreate(self):
        superadminusername = "super_admin"
        superadminpassword = "Admin_123?"
        passwordhash = User.makepasswordhash(superadminpassword)

        existsuperadmin = self.db_manager.getdata('users', {'username': superadminusername})
        if not existsuperadmin:
            self.db_manager.addnewrecord(
                'users',
                {
                    'username': superadminusername,
                    'password_hash': passwordhash,
                    'first_name': 'Default',
                    'last_name': 'SuperAdmin',
                    'user_role': 'SuperAdministrator',
                    'registration_date': datetime.date.today().isoformat()
                }
            )
            self.logger.writelog("SYSTEM", f"Default Super Administrator '{superadminusername}' created.",
                                 issuspicious=False)

    def run(self):
        self.setupapp()

        while True:
            print("\nUrban Mobility Backend System Login")
            usernameinput = input("Enter username (or 'quit' to exit): ").strip()
            if usernameinput.lower() == 'quit':
                self.shutdown_app()
                break

            password_input = input("Enter password: ").strip()

            userlog = self.db_manager.getdata('users', {'username': usernameinput})
            if not userlog:
                print("No user found. Try again")
                self.logger.writelog("LOGIN_ATTEMPT", f"Failed login for unknown user: '{usernameinput}'",
                                     issuspicious=True)
                continue

            loggedinuser = userlog[0]
            if loggedinuser['user_role'] == 'SuperAdministrator':
                current_user = SuperAdministrator(loggedinuser['username'], loggedinuser['password_hash'],
                                                  loggedinuser['first_name'], loggedinuser['last_name'],
                                                  loggedinuser['registration_date'], self.db_manager, self.logger)
            elif loggedinuser['user_role'] == 'SystemAdministrator':
                current_user = SystemAdministrator(loggedinuser['username'], loggedinuser['password_hash'],
                                                   loggedinuser['first_name'], loggedinuser['last_name'],
                                                   loggedinuser['registration_date'], self.db_manager, self.logger)
            elif loggedinuser['user_role'] == 'ServiceEngineer':
                current_user = ServiceEngineer(loggedinuser['username'], loggedinuser['password_hash'],
                                               loggedinuser['first_name'], loggedinuser['last_name'],
                                               loggedinuser['registration_date'], self.db_manager, self.logger)
            else:
                current_user = User(loggedinuser['username'], loggedinuser['password_hash'],
                                    loggedinuser['first_name'], loggedinuser['last_name'])

            if current_user.login(password_input):
                self.loggedinuser = current_user
                self.logger.writelog(self.loggedinuser.getmyusername(), "User logged in successfully.",
                                     issuspicious=False)
                self.runsession()
            else:
                self.logger.writelog(usernameinput, "Failed login attempt (wrong password).", issuspicious=True)
            self.loggedinuser = None

    def runsession(self):
        user_role = self.loggedinuser.__class__.__name__

        while self.loggedinuser.amiloggedin():
            print(f"\nLogged in as: {self.loggedinuser.getmyusername()} ({user_role})")

            if user_role == 'SuperAdministrator':
                self.loggedinuser.superadminmenu()
            elif user_role == 'SystemAdministrator':
                self.loggedinuser.systemadminmenu()
            elif user_role == 'ServiceEngineer':
                self.loggedinuser.show_service_engineer_menu()

            choice = input("Choose an option: ").strip()

            if choice == '1':
                new_pw = input("Enter new password: ")
                self.loggedinuser.changemypassword(new_pw)
                self.logger.writelog(self.loggedinuser.getmyusername(), "Attempted password change.")
            elif choice == '2':
                self.loggedinuser.logout()
                self.logger.writelog(self.loggedinuser.getmyusername(), "User logged out.", issuspicious=False)
                break

            elif user_role == 'SuperAdministrator':
                if choice == '3':
                    u = input("New System Admin Username: ")
                    p = input("New System Admin Password: ")
                    f = input("New System Admin First Name: ")
                    l = input("New System Admin Last Name: ")
                    self.loggedinuser.addsystemadmin(u, p, f, l)
                elif choice == '4':
                    u = input("Username of System Admin to update: ")
                    new_f = input("New First Name (leave empty to skip): ")
                    new_l = input("New Last Name (leave empty to skip): ")
                    updatedata = {}
                    if new_f: updatedata['first_name'] = new_f
                    if new_l: updatedata['last_name'] = new_l
                    self.loggedinuser.changesystemadmininfo(u, updatedata)
                elif choice == '5':
                    u = input("Username of System Admin to delete: ")
                    self.loggedinuser.deletesystemadmin(u)
                elif choice == '6':
                    u = input("Username of System Admin to reset password: ")
                    new_p = input("New password for System Admin: ")
                    self.loggedinuser.resetpasswordsysadmin(u, new_p)
                elif choice == '7':
                    sa_user = input("Enter System Administrator username for restore code: ")
                    self.loggedinuser.createrestorecode(sa_user)
                elif choice == '8':
                    code_to_revoke = input("Enter restore code to revoke: ")
                    self.loggedinuser.revokecode(code_to_revoke)
                elif choice == '9':
                    self.loggedinuser.viewlogs()
                elif choice == '10':
                    tinfo = {
                        'first_name': input("Traveller First Name: "),
                        'last_name': input("Traveller Last Name: "),
                        'birthday': input("Traveller Birthday (YYYY-MM-DD): "),
                        'gender': input("Traveller Gender: "),
                        'street_name': input("Traveller Street Name: "),
                        'house_number': input("Traveller House Number: "),
                        'zip_code': input("Traveller Zip Code (DDDDXX): "),
                        'city': input(f"Traveller City (choose from {', '.join(self.loggedinuser.dutch_cities)}): "),
                        'email_address': input("Traveller Email Address: "),
                        'mobile_phone': input("Traveller Mobile Phone (8 digits, e.g., 12345678): "),
                        'driving_license_number': input("Traveller Driving License Number (XXDDDDDDD or XDDDDDDDD): ")
                    }
                    if re.match(r"^\d{8}$", tinfo['mobile_phone']):
                        tinfo['mobile_phone'] = "+31-6-" + tinfo['mobile_phone']

                    self.loggedinuser.addtraveller(tinfo)
                elif choice == '11':
                    custid = input("Enter Traveller Customer ID to update: ")
                    updatedata = {}
                    print("Enter new values (leave empty to skip):")
                    new_email = input("New Email: ")
                    if new_email: updatedata['email_address'] = new_email
                    new_phone = input("New Mobile Phone (8 digits): ")
                    if new_phone:
                        if re.match(r"^\d{8}$", new_phone):
                            updatedata['mobile_phone'] = "+31-6-" + new_phone
                        else:
                            updatedata['mobile_phone'] = new_phone
                    new_zip = input("New Zip Code: ")
                    if new_zip: updatedata['zip_code'] = new_zip
                    new_city = input(f"New City (choose from {', '.join(self.loggedinuser.dutch_cities)}): ")
                    if new_city: updatedata['city'] = new_city
                    self.loggedinuser.updatetraveller(custid, updatedata)
                elif choice == '12':
                    custid = input("Enter Traveller Customer ID to delete: ")
                    self.loggedinuser.deletetraveller(custid)
                elif choice == '13':
                    s_info = {
                        'serial_number': input("Scooter Serial Number (10-17 alphanumeric): "),
                        'brand': input("Scooter Brand: "),
                        'model': input("Scooter Model: "),
                        'top_speed': float(input("Scooter Top Speed (km/h): ")),
                        'battery_capacity': float(input("Scooter Battery Capacity (Wh): ")),
                        'state_of_charge': float(input("Scooter State of Charge (%): ")),
                        'target_range_soc': float(input("Scooter Target Range SoC (%): ")),
                        'location': input(
                            "Scooter Location (latitude,longitude with 5 decimals, e.g., 51.92250,4.47917): "),
                        'out_of_service_status': int(input("Scooter Out of Service (0 for No, 1 for Yes): ")),
                        'mileage': float(input("Scooter Mileage (km): ")),
                        'last_maintenance_date': input("Scooter Last Maintenance Date (YYYY-MM-DD): ")
                    }
                    self.loggedinuser.addscooter(s_info)
                elif choice == '14':
                    serial = input("Enter Scooter Serial Number to update: ")
                    updatedata = {}
                    print("Enter new values (leave empty to skip):")
                    new_soc = input("New State of Charge (%): ")
                    if new_soc: updatedata['state_of_charge'] = float(new_soc)
                    new_loc = input("New Location (latitude,longitude): ")
                    if new_loc: updatedata['location'] = new_loc
                    new_oos = input("New Out of Service Status (0/1): ")
                    if new_oos: updatedata['out_of_service_status'] = int(new_oos)
                    new_mileage = input("New Mileage (km): ")
                    if new_mileage: updatedata['mileage'] = float(new_mileage)
                    new_maint_date = input("New Last Maintenance Date (YYYY-MM-DD): ")
                    if new_maint_date: updatedata['last_maintenance_date'] = new_maint_date
                    self.loggedinuser.updatescooter(serial, updatedata, serviceengineer=False)
                elif choice == '15':
                    serial = input("Enter Scooter Serial Number to delete: ")
                    self.loggedinuser.deletescooter(serial)
                elif choice == '16':
                    code = self.loggedinuser.createrestorecode('superadmin')
                    self.loggedinuser.makebackup(code)
                elif choice == '17':
                    code = input("Enter restore code: ")
                    b_id = input("Enter backup ID: ")
                    self.loggedinuser.restoresystembackup(code,b_id)
                else:
                    print("That's not a valid option. Please try again.")

            elif user_role == 'SystemAdministrator':
                if choice == '3':
                    u = input("New Service Engineer Username: ")
                    p = input("New Service Engineer Password: ")
                    f = input("New Service Engineer First Name: ")
                    l = input("New Service Engineer Last Name: ")
                    self.loggedinuser.addserviceengineer(u, p, f, l)
                elif choice == '4':
                    u = input("Username of Service Engineer to update: ")
                    new_f = input("New First Name (leave empty to skip): ")
                    new_l = input("New Last Name (leave empty to skip): ")
                    updatedata = {}
                    if new_f: updatedata['first_name'] = new_f
                    if new_l: updatedata['last_name'] = new_l
                    self.loggedinuser.updateserviceengineerinfo(u, updatedata)
                elif choice == '5':
                    u = input("Username of Service Engineer to delete: ")
                    self.loggedinuser.deleteserviceengineer(u)
                elif choice == '6':
                    u = input("Username of Service Engineer to reset password: ")
                    new_p = input("New password for Service Engineer: ")
                    self.loggedinuser.resetengineerpassword(u, new_p)
                elif choice == '7':
                    tinfo = {
                        'first_name': input("Traveller First Name: "),
                        'last_name': input("Traveller Last Name: "),
                        'birthday': input("Traveller Birthday (YYYY-MM-DD): "),
                        'gender': input("Traveller Gender: "),
                        'street_name': input("Traveller Street Name: "),
                        'house_number': input("Traveller House Number: "),
                        'zip_code': input("Traveller Zip Code (DDDDXX): "),
                        'city': input(f"Traveller City (choose from {', '.join(self.loggedinuser.dutch_cities)}): "),
                        'email_address': input("Traveller Email Address: "),
                        'mobile_phone': input("Traveller Mobile Phone (8 digits, e.g., 12345678): "),
                        'driving_license_number': input("Traveller Driving License Number (XXDDDDDDD or XDDDDDDDD): ")
                    }
                    if re.match(r"^\d{8}$", tinfo['mobile_phone']):
                        tinfo['mobile_phone'] = "+31-6-" + tinfo['mobile_phone']
                    self.loggedinuser.addtraveller(tinfo)
                elif choice == '8':
                    custid = input("Enter Traveller Customer ID to update: ")
                    updatedata = {}
                    print("Enter new values (leave empty to skip):")
                    new_email = input("New Email: ")
                    if new_email: updatedata['email_address'] = new_email
                    new_phone = input("New Mobile Phone (8 digits): ")
                    if new_phone:
                        if re.match(r"^\d{8}$", new_phone):
                            updatedata['mobile_phone'] = "+31-6-" + new_phone
                        else:
                            updatedata['mobile_phone'] = new_phone
                    new_zip = input("New Zip Code: ")
                    if new_zip: updatedata['zip_code'] = new_zip
                    new_city = input(f"New City (choose from {', '.join(self.loggedinuser.dutch_cities)}): ")
                    if new_city: updatedata['city'] = new_city
                    self.loggedinuser.updatetraveller(custid, updatedata)
                elif choice == '9':
                    custid = input("Enter Traveller Customer ID to delete: ")
                    self.loggedinuser.deletetraveller(custid)
                elif choice == '10':
                    s_query = input("Enter search term for travellers (name, email, ID): ")
                    self.loggedinuser.searchtraveller(s_query)
                elif choice == '11':
                    s_info = {
                        'serial_number': input("Scooter Serial Number (10-17 alphanumeric): "),
                        'brand': input("Scooter Brand: "),
                        'model': input("Scooter Model: "),
                        'top_speed': float(input("Scooter Top Speed (km/h): ")),
                        'battery_capacity': float(input("Scooter Battery Capacity (Wh): ")),
                        'state_of_charge': float(input("Scooter State of Charge (%): ")),
                        'target_range_soc': float(input("Scooter Target Range SoC (%): ")),
                        'location': input("Scooter Location (latitude,longitude): "),
                        'out_of_service_status': int(input("Scooter Out of Service (0 for No, 1 for Yes): ")),
                        'mileage': float(input("Scooter Mileage (km): ")),
                        'last_maintenance_date': input("Scooter Last Maintenance Date (YYYY-MM-DD): ")
                    }
                    self.loggedinuser.addscooter(s_info)
                elif choice == '12':
                    serial = input("Enter Scooter Serial Number to update: ")
                    updatedata = {}
                    print("Enter new values (leave empty to skip):")
                    new_soc = input("New State of Charge (%): ")
                    if new_soc: updatedata['state_of_charge'] = float(new_soc)
                    new_loc = input("New Location (latitude,longitude): ")
                    if new_loc: updatedata['location'] = new_loc
                    new_oos = input("New Out of Service Status (0/1): ")
                    if new_oos: updatedata['out_of_service_status'] = int(new_oos)
                    new_mileage = input("New Mileage (km): ")
                    if new_mileage: updatedata['mileage'] = float(new_mileage)
                    new_maint_date = input("New Last Maintenance Date (YYYY-MM-DD): ")
                    if new_maint_date: updatedata['last_maintenance_date'] = new_maint_date
                    self.loggedinuser.updatescooter(serial, updatedata, serviceengineer=False)
                elif choice == '13':
                    serial = input("Enter Scooter Serial Number to delete: ")
                    self.loggedinuser.deletescooter(serial)
                elif choice == '14':
                    s_query = input("Enter search term for scooters (serial, brand, model): ")
                    self.loggedinuser.getscooterinfo(s_query)
                elif choice == '15':
                    codeforbackup = input("Enter the restore code given by super admin.")
                    self.loggedinuser.makebackup(codeforbackup)
                elif choice == '16':
                    code = input("Enter restore code: ")
                    b_id = input("Enter backup ID: ")
                    self.loggedinuser.restoresystembackup(code, b_id)
                elif choice == '17':
                    self.loggedinuser.viewlogs()
                elif choice == '18':
                    self.loggedinuser.viewallusers()
                else:
                    print("Oops! That's not a valid option. Please try again.")

            elif user_role == 'ServiceEngineer':
                if choice == '3':
                    tinfo = {
                        'first_name': input("Traveller First Name: "),
                        'last_name': input("Traveller Last Name: "),
                        'birthday': input("Traveller Birthday (YYYY-MM-DD): "),
                        'gender': input("Traveller Gender: "),
                        'street_name': input("Traveller Street Name: "),
                        'house_number': input("Traveller House Number: "),
                        'zip_code': input("Traveller Zip Code (DDDDXX): "),
                        'city': input(f"Traveller City (choose from {', '.join(self.loggedinuser.dutch_cities)}): "),
                        'email_address': input("Traveller Email Address: "),
                        'mobile_phone': input("Traveller Mobile Phone (8 digits, e.g., 12345678): "),
                        'driving_license_number': input("Traveller Driving License Number (XXDDDDDDD or XDDDDDDDD): ")
                    }
                    if re.match(r"^\d{8}$", tinfo['mobile_phone']):
                        tinfo['mobile_phone'] = "+31-6-" + tinfo['mobile_phone']
                    self.loggedinuser.addtraveller(tinfo)
                elif choice == '4':
                    custid = input("Enter Traveller Customer ID to update: ")
                    updatedata = {}
                    print("Enter new values (leave empty to skip):")
                    new_email = input("New Email: ")
                    if new_email: updatedata['email_address'] = new_email
                    new_phone = input("New Mobile Phone (8 digits): ")
                    if new_phone:
                        if re.match(r"^\d{8}$", new_phone):
                            updatedata['mobile_phone'] = "+31-6-" + new_phone
                        else:
                            updatedata['mobile_phone'] = new_phone
                    new_zip = input("New Zip Code: ")
                    if new_zip: updatedata['zip_code'] = new_zip
                    new_city = input(f"New City (choose from {', '.join(self.loggedinuser.dutch_cities)}): ")
                    if new_city: updatedata['city'] = new_city
                    self.loggedinuser.updatetraveller(custid, updatedata)
                elif choice == '5':
                    custid = input("Enter Traveller Customer ID to delete: ")
                    self.loggedinuser.deletetraveller(custid)
                elif choice == '6':
                    s_query = input("Enter search term for travellers (name, email, ID): ")
                    self.loggedinuser.searchtraveller(s_query)
                elif choice == '7':
                    serial = input("Enter Scooter Serial Number to update: ")
                    updatedata = {}
                    print("Enter new values (leave empty to skip):")
                    new_soc = input("New State of Charge (%): ")
                    if new_soc: updatedata['state_of_charge'] = float(new_soc)
                    new_loc = input("New Location (latitude,longitude): ")
                    if new_loc: updatedata['location'] = new_loc
                    new_oos = input("New Out of Service Status (0/1): ")
                    if new_oos: updatedata['out_of_service_status'] = int(new_oos)
                    new_mileage = input("New Mileage (km): ")
                    if new_mileage: updatedata['mileage'] = float(new_mileage)
                    new_maint_date = input("New Last Maintenance Date (YYYY-MM-DD): ")
                    if new_maint_date: updatedata['last_maintenance_date'] = new_maint_date
                    self.loggedinuser.updatescooterlimit(serial, updatedata)
                elif choice == '8':
                    s_query = input("Enter search term for scooters (serial, brand, model): ")
                    self.loggedinuser.getscooterinfo(s_query)
                else:
                    print("That's not a valid option. Please try again.")

            else:
                print("Invalid choice or role specific action not found. Please try again.")

if __name__ == "__main__":
    app = UmMembers()
    app.run()