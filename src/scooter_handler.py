import datetime
from input_validation import InputValidation
from input_handler import InputHandler
from logger import Logger
from db_handler import DBHandler

class ScooterHandler:
    def __init__(self, db_handler: DBHandler = None, logger: Logger = None, input_validation: InputValidation = None, input_handler: InputHandler = None):
        self.db_handler = db_handler
        self.logger = logger
        self.input_validation = input_validation
        self.input_handler = input_handler

    def add_scooter(self, scooter_info, username):
        print("\nAdding a New Scooter")
        if not self.db_handler:
            print("Error: Database is not connected. Can't add scooter.")
            return

        try:
            cleaned_data = self.input_handler.handle_scooter_data(scooter_info)
        except ValueError as e:
            print(f"Validation error while cleaning scooter data: {e}")
            self.logger.writelog(username, "Add Scooter Failed", f"Validation error: {e}", issuspicious=True)
            return

        serial_number = cleaned_data.get('serial_number', '')

        existing_scooter = self.db_handler.getdata('scooters', {'serial_number': serial_number})
        if existing_scooter:
            print(f"Error: Scooter with serial number '{serial_number}' already exists.")
            self.logger.writelog(username, "Add Scooter Failed", f"Duplicate serial number: {serial_number}", issuspicious=True)
            return

        scooter_data = {
            'serial_number': serial_number,
            'brand': cleaned_data.get('brand', ''),
            'model': cleaned_data.get('model', ''),
            'top_speed': cleaned_data.get('top_speed', 0),
            'battery_capacity': cleaned_data.get('battery_capacity', 0),
            'state_of_charge': cleaned_data.get('soc', 0),
            'target_range_soc': cleaned_data.get('target_range_soc', 0),
            'location': cleaned_data.get('location', {}),
            'out_of_service_status': cleaned_data.get('out_of_service', 0),
            'mileage': cleaned_data.get('mileage', 0.0),
            'last_maintenance_date': cleaned_data.get('last_maintenance_date', ''),
            'in_service_date': datetime.date.today().isoformat()
        }

        try:
            self.db_handler.addnewrecord('scooters', scooter_data)
            print(f"Scooter '{scooter_data['brand']} {scooter_data['model']}' (Serial: {serial_number}) added successfully!")
            self.logger.writelog(username, "Add Scooter",
                                f"New scooter added: {serial_number}")
        except Exception as e:
            print(f"Couldn't add scooter. Error: {e}")
            self.logger.writelog(username, "Add Scooter Failed", f"Error: {e}", issuspicious=True)

    def updatescooterlimit(self, serialnumber, newinfo, username):
        print(f"\nUpdating Scooter Info (Limited for Service Engineer) for Serial: {serialnumber}")

        if not self.db_handler:
            print("Error: Database not connected. Can't update scooter.")
            return

        existing_scooter = self.db_handler.getdata('scooters', {'serial_number': serialnumber})
        if not existing_scooter:
            print(f"Error: Scooter with serial number '{serialnumber}' not found.")
            self.logger.writelog(username, "Update Scooter Failed", f"Scooter '{serialnumber}' not found for SE update", is_suspicious=True)
            return

        allowed_fields = ['state_of_charge', 'location', 'out_of_service_status', 'mileage', 'last_maintenance_date']
        updates_for_db = {}
        originalvalues = existing_scooter[0]

        for key, value in newinfo.items():
            if key not in allowed_fields:
                print(f"Service Engineers are not allowed to change '{key}'. Skipping this field.")
                self.logger.writelog(username, "Update Scooter Failed",
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
                self.logger.writelog(username, "Update Scooter Failed", f"Invalid value for '{key}' on scooter '{serialnumber}'", is_suspicious=True)
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
            self.logger.writelog(username, "Update Scooter", f"Limited update by Service Engineer for scooter '{serialnumber}'.")
        except Exception as e:
            print(f"Error while updating scooter '{serialnumber}': {e}")
            self.logger.writelog(username, "Update Scooter Failed", f"Database error: {e}", is_suspicious=True)

    def update_scooter(self, serialnumber, newinfo, username):
        print(f"\nUpdating Scooter Info for Serial: {serialnumber}")

        if not self.db_handler:
            print("Error: Database not connected. Can't update scooter.")
            return

        existing_scooter = self.db_handler.getdata('scooters', {'serial_number': serialnumber})
        if not existing_scooter:
            print(f"Error: Scooter with serial number '{serialnumber}' not found.")
            self.logger.writelog(username, "Update Scooter Failed", f"Scooter '{serialnumber}' not found for update", is_suspicious=True)
            return

        originalvalues = existing_scooter[0]

        try:
            cleaned_data = self.input_handler.handle_scooter_data(newinfo, username)
        except ValueError as ve:
            print(f"Validation error during cleaning: {ve}. Update cancelled.")
            self.logger.writelog(username, "Update Scooter Failed", f"Validation error for scooter '{serialnumber}': {ve}", is_suspicious=True)
            return

        updates_for_db = {}

        for key, cleaned_value in cleaned_data.items():
            if key == 'location':
                old_loc = originalvalues.get('location', {})
                if round(old_loc.get('latitude', 0), 5) != cleaned_value['latitude'] or round(old_loc.get('longitude', 0), 5) != cleaned_value['longitude']:
                    updates_for_db[key] = cleaned_value
                else:
                    print(f"'{key}' is the same. No update needed.")
            else:
                if str(originalvalues.get(key, '')).strip() != str(cleaned_value).strip():
                    updates_for_db[key] = cleaned_value
                else:
                    print(f"'{key}' is the same. No update needed.")

        if not updates_for_db:
            print("No valid or changed information to update.")
            return

        try:
            self.db_handler.updateexistingrecord('scooters', 'serial_number', serialnumber, updates_for_db)
            print(f"Scooter with serial number '{serialnumber}' successfully updated.")
            self.logger.writelog(username, "Update Scooter", f"Full update for scooter '{serialnumber}'.")
        except Exception as e:
            print(f"Error while updating scooter '{serialnumber}': {e}")
            self.logger.writelog(username, "Update Scooter Failed", f"Database error: {e}", is_suspicious=True)


    def delete_scooter(self, serial_number, username):
        print(f"\nDeleting Scooter with Serial: {serial_number}")
        if not self.db_handler:
            print("Error: Database is not connected. Can't delete scooter.")
            return

        existing_scooter = self.db_handler.getdata('scooters', {'serial_number': serial_number})
        if not existing_scooter:
            print(f"Error: Scooter with serial '{serial_number}' not found.")
            self.logger.writelog(username, "Delete Scooter Failed", 
                               f"Scooter '{serial_number}' not found", issuspicious=True)
            return

        confirmation = input(
            f"Are you sure you want to delete scooter '{serial_number}'? This cannot be undone! (type 'yes' to confirm): ").lower()
        if confirmation != 'yes':
            print("Deletion cancelled.")
            self.logger.writelog(username, "Delete Scooter Cancelled", 
                               f"Cancelled deletion of scooter '{serial_number}'")
            return

        try:
            self.db_handler.deleterecord('scooters', 'serial_number', serial_number)
            print(f"Scooter with serial '{serial_number}' successfully deleted.")
            self.logger.writelog(username, "Delete Scooter", 
                               f"Deleted scooter '{serial_number}'")
        except Exception as e:
            print(f"A problem happened while deleting scooter '{serial_number}'. Error: {e}")
            self.logger.writelog(username, "Delete Scooter Failed", f"Error: {e}", issuspicious=True)

    def search_scooter(self, query, username):
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
            query = query.lower()
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

            self.logger.writelog(username, "Search Scooter", f"Searched for '{query}', found {len(results)} results.")
        else:
            print("No scooters found matching your search.")
            self.logger.writelog(username, "Search Scooter", f"Searched for '{query}', scooter not found.")
        return results

    def mark_scooter_out_of_service(self, serial_number, username, reason=""):
        print(f"\nMarking Scooter {serial_number} as Out of Service")
        if not self.db_handler:
            print("Error: Database is not connected.")
            return

        existing_scooter = self.db_handler.getdata('scooters', {'serial_number': serial_number})
        if not existing_scooter:
            print(f"Error: Scooter with serial '{serial_number}' not found.")
            self.logger.writelog(username, "Scooter OOS Failed", 
                               f"Scooter '{serial_number}' not found", issuspicious=True)
            return

        try:
            self.db_handler.updateexistingrecord('scooters', 'serial_number', serial_number, {
                'out_of_service_status': 1,
                'last_maintenance_date': datetime.date.today().isoformat()
            })
            print(f"Scooter {serial_number} marked as out of service.")
            self.logger.writelog(username, "Scooter OOS", 
                               f"Marked scooter '{serial_number}' as out of service. Reason: {reason}")
        except Exception as e:
            print(f"Couldn't update scooter status. Error: {e}")
            self.logger.writelog(username, "Scooter OOS Failed", f"Error: {e}", issuspicious=True)

    def mark_scooter_in_service(self, serial_number, username):
        print(f"\nMarking Scooter {serial_number} as In Service")
        if not self.db_handler:
            print("Error: Database is not connected.")
            return

        existing_scooter = self.db_handler.getdata('scooters', {'serial_number': serial_number})
        if not existing_scooter:
            print(f"Error: Scooter with serial '{serial_number}' not found.")
            self.logger.writelog(username, "Scooter IS Failed", 
                               f"Scooter '{serial_number}' not found", issuspicious=True)
            return

        try:
            self.db_handler.updateexistingrecord('scooters', 'serial_number', serial_number, {
                'out_of_service_status': 0,
                'last_maintenance_date': datetime.date.today().isoformat()
            })
            print(f"Scooter {serial_number} marked as in service.")
            self.logger.writelog(username, "Scooter IS", 
                               f"Marked scooter '{serial_number}' as in service")
        except Exception as e:
            print(f"Couldn't update scooter status. Error: {e}")
            self.logger.writelog(username, "Scooter IS Failed", f"Error: {e}", issuspicious=True)