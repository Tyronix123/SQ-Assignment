import datetime
import hashlib
import secrets
import re
from db_handler import DBHandler
from logger import Logger

from input_validation import InputValidation
from input_handler import InputHandler
from traveller_handler import TravellerHandler
from user import User


class ServiceEngineer(User):
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
        self.dutch_cities = ["Amsterdam", "Rotterdam", "Utrecht", "The Hague", "Eindhoven",
                             "Groningen", "Maastricht", "Leiden", "Haarlem", "Delft"]
        self.traveller_handler = TravellerHandler(db_handler, logger, self.dutch_cities)

    def addtraveller(self, travellerinfo):
        self.traveller_handler.add_traveller(travellerinfo, self.username)

    def updatetraveller(self, customerid, newinfo):
        self.traveller_handler.update_traveller(customerid, newinfo, self.username)

    def deletetraveller(self, customerid):
        self.traveller_handler.delete_traveller(customerid, self.username)

    def searchtraveller(self, query):
        return self.traveller_handler.search_traveller(query, self.username)

    def updatescooterlimit(self, serialnumber, newinfo):
        print(f"\nUpdating Scooter Info (Limited for Service Engineer) for Serial: {serialnumber}")
        
        if not self.db_handler:
            print("Error: Database not connected. Can't update scooter.")
            return

        existing_scooter = self.db_handler.getdata('scooters', {'serial_number': serialnumber})
        if not existing_scooter:
            print(f"Error: Scooter with serial number '{serialnumber}' not found.")
            self.logger.writelog(self.username, "Update Scooter Failed", f"Scooter '{serialnumber}' not found for SE update", is_suspicious=True)
            return

        allowed_fields = ['state_of_charge', 'location', 'out_of_service_status', 'mileage', 'last_maintenance_date']
        updates_for_db = {}
        originalvalues = existing_scooter[0]

        for key, value in newinfo.items():
            if key not in allowed_fields:
                print(f"Service Engineers are not allowed to change '{key}'. Skipping this field.")
                self.logger.writelog(self.username, "Update Scooter Failed",
                                f"SE tried to change forbidden field '{key}' on '{serialnumber}'", is_suspicious=True)
                continue

            try:
                if key == 'state_of_charge':
                    cleaned = self.input_handler.clean_soc(value)
                elif key == 'location':
                    lat = value.get("latitude", 0.0)
                    lon = value.get("longitude", 0.0)
                    cleaned = self.input_handler.clean_location(lat, lon)
                elif key == 'out_of_service_status':
                    cleaned = self.input_handler.clean_out_of_service(value)
                elif key == 'mileage':
                    cleaned = self.input_handler.clean_mileage(value)
                elif key == 'last_maintenance_date':
                    cleaned = self.input_handler.clean_last_maintenance_date(value)
                else:
                    cleaned = value

            except ValueError as ve:
                print(f"Validation error for '{key}': {ve}. Update cancelled.")
                self.logger.writelog(self.username, "Update Scooter Failed", f"Invalid value for '{key}' on scooter '{serialnumber}'", is_suspicious=True)
                continue

            if key == 'location':
                old_loc = originalvalues.get('location', {})
                if round(old_loc.get('latitude', 0), 5) != cleaned['latitude'] or round(old_loc.get('longitude', 0), 5) != cleaned['longitude']:
                    updates_for_db[key] = cleaned
                else:
                    print(f"'{key}' is the same. No update needed.")
            elif str(originalvalues.get(key, '')).strip() != str(cleaned).strip():
                updates_for_db[key] = cleaned
            else:
                print(f"'{key}' is the same. No update needed.")

        if not updates_for_db:
            print("No valid or changed information to update.")
            return

        try:
            self.db_handler.updateexistingrecord('scooters', 'serial_number', serialnumber, updates_for_db)
            print(f"Scooter with serial number '{serialnumber}' successfully updated.")
            self.logger.writelog(self.username, "Update Scooter", f"Limited update by Service Engineer for scooter '{serialnumber}'.")
        except Exception as e:
            print(f"Error while updating scooter '{serialnumber}': {e}")
            self.logger.writelog(self.username, "Update Scooter Failed", f"Database error: {e}", is_suspicious=True)


    def searchscooter(self, query):
        print(f"\nSearching Scooters for: '{query}'")
        
        if not self.db_handler:
            print("Error: Database not connected. Can't search scooters.")
            return []

        SEARCH_FIELDS = {
            'serial_number': 'Serial Number',
            'brand': 'Brand',
            'model': 'Model',
        }

        all_scooters = self.db_handler.getdata('scooters')
        results = []

        if not query:
            print("No search term provided, showing all scooters.")
            results = all_scooters
        else:
            for scooter in all_scooters:
                matched_field = None
                for field, display_name in SEARCH_FIELDS.items():
                    field_value = str(scooter.get(field, '')).lower()
                    if query in field_value:
                        matched_field = display_name
                        break
                
                if matched_field:
                    results.append({
                        'scooter': scooter,
                        'matched_field': matched_field,
                        'matched_value': scooter.get(field)
                    })

        if results:
            print(f"Found {len(results)} scooter(s):")
            for result in results:
                s = result['scooter']
                print(
                    f"  Serial: {s.get('serial_number')}, Brand: {s.get('brand')}, Model: {s.get('model')}, "
                    f"SoC: {s.get('soc')}%, Location: {s.get('location')}")
                print(f"    (Matched on {result['matched_field']}: {result['matched_value']})")
            
            self.logger.writelog(self.username, "Search Scooter", f"Searched for '{query}', found {len(results)} results.")
        else:
            print("No scooters found matching your search.")
            self.logger.writelog(self.username, "Search Scooter", f"Searched for '{query}', scooter not found.")
        return results

    def handle_menu_choice(self, choice):
        if choice == '3':
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
        elif choice == '4':
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
        elif choice == '5':
            custid = input("Enter Traveller Customer ID to delete: ")
            self.deletetraveller(custid)
        elif choice == '6':
            s_query = input("Enter search term for travellers (name, email, ID): ")
            self.searchtraveller(s_query)
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
            self.updatescooterlimit(serial, updatedata)
        elif choice == '8':
            s_query = input("Enter search term for scooters (serial, brand, model): ")
            self.searchscooter(s_query)
        else:
            print("That's not a valid option. Please try again.")




    def show_menu(self):
        print("\n--- Your Menu ---")
        print("1. Change My Password")
        print("2. Log Out")
        print("Service Engineer Specific")
        print("3. Add New Traveller")
        print("4. Update Traveller Info")
        print("5. Delete Traveller")
        print("6. Search Travellers")
        print("7. Update Scooter Info")
        print("8. Search Scooters")