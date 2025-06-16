import datetime
import hashlib
import secrets
from input_validation import InputValidation
from traveller_handler import TravellerHandler

class ServiceEngineer(User):
    def __init__(self, username, password_hash, firstname, lastname, reg_date=None, db_manager=None, logger=None):
        super().__init__(username, password_hash, firstname, lastname)
        self.db_manager = db_manager
        self.logger = logger
        self.traveller_handler = TravellerHandler(db_manager, logger, self.dutch_cities)
        self.dutch_cities = ["Amsterdam", "Rotterdam", "Utrecht", "The Hague", "Eindhoven",
                             "Groningen", "Maastricht", "Leiden", "Haarlem", "Delft"]

    def logmyaction(self, description, additional_info="", is_suspicious=False):
        if self.logger:
            self.logger.writelog(self.username, description, additional_info, is_suspicious)
        else:
            print(f"LOG (no logger connected): {description} - {additional_info}")

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
        if not self.db_manager:
            print("Error: Database not connected. Can't update scooter.")
            return
        existing_scooter = self.db_manager.getdata('scooters', {'serial_number': serialnumber})
        if not existing_scooter:
            print(f"Error: Scooter with serial number '{serialnumber}' not found.")
            self.logmyaction("Update Scooter Failed", f"Scooter '{serialnumber}' not found for SE update",
                             is_suspicious=True)
            return

        allowed_fields = ['state_of_charge', 'location', 'out_of_service_status', 'mileage', 'last_maintenance_date']
        updates_for_db = {}
        originalvalues = existing_scooter[0]

        for key, value in newinfo.items():
            if key not in allowed_fields:
                print(f"Service Engineers are not allowed to change '{key}'. Skipping this field.")
                self.logmyaction("Update Scooter Failed",
                                 f"SE tried to change forbidden field '{key}' on '{serialnumber}'", is_suspicious=True)
                continue

            cleaned_value = InputValidation.clean_up_input(str(value))

            if key == 'location' and not InputValidation.is_valid_location(cleaned_value):
                print(f"Invalid location format for '{key}': '{cleaned_value}'. Update cancelled.")
                self.logmyaction("Update Scooter Failed", f"Invalid location for '{serialnumber}' for SE update",
                                 is_suspicious=True)
                return

            if str(originalvalues.get(key, '')).strip() != cleaned_value.strip():
                updates_for_db[key] = value
            else:
                print(f"'{key}' value is the same. No change needed.")

        if not updates_for_db:
            print("No valid or different information provided for update. Nothing changed.")
            return

        try:
            self.db_manager.updateexistingrecord('scooters', 'serial_number', serialnumber, updates_for_db)
            print(f"Scooter with serial number '{serialnumber}' information updated.")
            self.logmyaction("Update Scooter",
                             f"Info for scooter '{serialnumber}' updated by Service Engineer (limited).")
        except Exception as e:
            print(f"Couldn't update scooter '{serialnumber}'. Error: {e}")
            self.logmyaction("Update Scooter Failed", f"Error: {e}", is_suspicious=True)

    def searchscooter(self, query):
        print(f"\nSearching Scooters for: '{query}'")
        if not self.db_manager:
            print("Error: Database not connected. Can't search scooters.")
            return []

        all_scooters = self.db_manager.getdata('scooters')
        results = []
        cleanedquery = InputValidation.clean_up_input(query).lower()

        if not cleanedquery:
            print("No search term provided, showing all scooters.")
            results = all_scooters
        else:
            for scooter in all_scooters:
                if (cleanedquery in scooter.get('serial_number', '').lower() or
                        cleanedquery in scooter.get('brand', '').lower() or
                        cleanedquery in scooter.get('model', '').lower()):
                    results.append(scooter)

        if results:
            print(f"Found {len(results)} scooter(s):")
            for s in results:
                print(
                    f"  Serial: {s.get('serial_number')}, Brand: {s.get('brand')}, Model: {s.get('model')}, SoC: {s.get('state_of_charge')}%, Location: {s.get('location')}")
            self.logmyaction("Search Scooter", f"Searched for '{query}', found {len(results)} results.")
        else:
            print("No scooters found matching your search.")
            self.logmyaction("Search Scooter", f"Searched for '{query}', scooter not found.")
        return results

    def show_service_engineer_menu(self):
        self.show_common_menu()
        print("Service Engineer Specific")
        print("3. Add New Traveller")
        print("4. Update Traveller Info")
        print("5. Delete Traveller")
        print("6. Search Travellers")
        print("7. Update Scooter Info")
        print("8. Search Scooters")