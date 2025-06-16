from superadmin import SuperAdministrator
import re
from input_validation import InputValidation
from db_handler import DBHandler
from logger import Logger
from input_handler import InputHandler

class SystemAdministrator(SuperAdministrator):
    def __init__(self, username, password_hash, role, firstname, lastname, reg_date=None, db_handler: DBHandler = None, logger: Logger = None, input_validation: InputValidation = None, input_handler: InputHandler = None):
        self.username = username
        self.passwordhash = password_hash
        self.role = role
        self.first_name = firstname
        self.last_name = lastname
        self.reg_date = reg_date
        self.db_handler = db_handler
        self.logger = logger
        self.input_validation = input_validation
        self.input_handler = input_handler


    def addserviceengineer(self, username, password, firstname, lastname):
        if self._manage_user_account(username, password, firstname, lastname, "Service Engineer", "Creating a New Service Engineer"):
            if self._create_user_record(username, password, firstname, lastname, "ServiceEngineer"):
                print("Service Engineer was successfully added")
                self.logmyaction("Added Service Engineer", f"New Service Engineer '{username}' created.")

    def updateserviceengineerinfo(self, usernametochange, new_info):
        self._update_user_info(usernametochange, new_info, "ServiceEngineer")

    def deleteserviceengineer(self, usernametodelete):
        self._delete_user(usernametodelete, "ServiceEngineer", "ERROR: System admin cant be deleted using this function.")

    def resetengineerpassword(self, usernamereset, newpassword):
        self._reset_password(usernamereset, newpassword, "ServiceEngineer")


    def handle_menu_choice(self, choice, logger):
        if choice == '3':
            u = input("New Service Engineer Username: ")
            p = input("New Service Engineer Password: ")
            f = input("New Service Engineer First Name: ")
            l = input("New Service Engineer Last Name: ")
            self.addserviceengineer(u, p, f, l)
        elif choice == '4':
            u = input("Username of Service Engineer to update: ")
            new_f = input("New First Name (leave empty to skip): ")
            new_l = input("New Last Name (leave empty to skip): ")
            updatedata = {}
            if new_f: updatedata['first_name'] = new_f
            if new_l: updatedata['last_name'] = new_l
            self.updateserviceengineerinfo(u, updatedata)
        elif choice == '5':
            u = input("Username of Service Engineer to delete: ")
            self.deleteserviceengineer(u)
        elif choice == '6':
            u = input("Username of Service Engineer to reset password: ")
            new_p = input("New password for Service Engineer: ")
            self.resetengineerpassword(u, new_p)
        elif choice == '7':
            tinfo = {
                'first_name': input("Traveller First Name: "),
                'last_name': input("Traveller Last Name: "),
                'birthday': input("Traveller Birthday (YYYY-MM-DD): "),
                'gender': input("Traveller Gender: "),
                'street_name': input("Traveller Street Name: "),
                'house_number': input("Traveller House Number: "),
                'zip_code': input("Traveller Zip Code (DDDDXX): "),
                'city': input(f"Traveller City (choose from {', '.join(self.dutch_cities)}): "),
                'email_address': input("Traveller Email Address: "),
                'mobile_phone': input("Traveller Mobile Phone (8 digits, e.g., 12345678): "),
                'driving_license_number': input("Traveller Driving License Number (XXDDDDDDD or XDDDDDDDD): ")
            }
            if self.input_validation.is_valid_phone(tinfo['mobile_phone']):
                tinfo['mobile_phone'] = "+31-6-" + tinfo['mobile_phone']
            self.addtraveller(tinfo)
        elif choice == '8':
            custid = input("Enter Traveller Customer ID to update: ")
            updatedata = {}
            print("Enter new values (leave empty to skip):")
            new_email = input("New Email: ")
            if new_email: updatedata['email_address'] = new_email
            new_phone = input("New Mobile Phone (8 digits): ")
            if new_phone:
                if self.input_validation.is_valid_phone(new_phone):
                    updatedata['mobile_phone'] = "+31-6-" + new_phone
                else:
                    updatedata['mobile_phone'] = new_phone
            new_zip = input("New Zip Code: ")
            if new_zip: updatedata['zip_code'] = new_zip
            new_city = input(f"New City (choose from {', '.join(self.dutch_cities)}): ")
            if new_city: updatedata['city'] = new_city
            self.updatetraveller(custid, updatedata)
        elif choice == '9':
            custid = input("Enter Traveller Customer ID to delete: ")
            self.deletetraveller(custid)
        elif choice == '10':
            s_query = input("Enter search term for travellers (name, email, ID): ")
            self.searchtraveller(s_query)
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
            self.addscooter(s_info)
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
            self.updatescooter(serial, updatedata, serviceengineer=False)
        elif choice == '13':
            serial = input("Enter Scooter Serial Number to delete: ")
            self.deletescooter(serial)
        elif choice == '14':
            s_query = input("Enter search term for scooters (serial, brand, model): ")
            self.getscooterinfo(s_query)
        elif choice == '15':
            codeforbackup = input("Enter the restore code given by super admin.")
            self.makebackup(codeforbackup)
        elif choice == '16':
            code = input("Enter restore code: ")
            b_id = input("Enter backup ID: ")
            self.restoresystembackup(code, b_id)
        elif choice == '17':
            self.viewlogs()
        elif choice == '18':
            self.viewallusers()
        else:
            print("That's not a valid option. Please try again.")

    def show_menu(self):
        print("\n--- Your Menu ---")
        print("1. Change My Password")
        print("2. Log Out")
        print("System Admin Specific")
        print("3. Add New Service Engineer")
        print("4. Update Service Engineer Info")
        print("5. Delete Service Engineer")
        print("6. Reset Service Engineer Password")
        print("7. Add New Traveller")
        print("8. Update Traveller Info")
        print("9. Delete Traveller")
        print("10. Search Travellers")
        print("11. Add New Scooter")
        print("12. Update Scooter Info")
        print("13. Delete Scooter")
        print("14. Search Scooters")
        print("15. Make System Backup (Needs Super Admin Code)")
        print("16. Restore System Backup (Needs Super Admin Code)")
        print("17. View All System Logs")
        print("18. View All System Users and Roles")
        print("19. Check for Suspicious Activities (Logs)")