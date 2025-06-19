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

    def add_scooter(self, username):
        print("\n--- Add New Scooter ---")

        if not self.db_handler:
            print("Error: Database is not connected. Can't add scooter.")
            return

        serial_number = input("Scooter Serial Number (10-17 alphanumeric): ")
        brand = input("Scooter Brand: ")
        model = input("Scooter Model: ")

        # Validate top speed
        while True:
            top_speed = input("Top Speed (km/h): ")
            try:
                float(top_speed)
                break
            except ValueError:
                print("Please enter a valid number for top speed (e.g. 75).")

        # Validate battery capacity
        while True:
            battery_capacity = input("Battery Capacity (Wh): ")
            try:
                float(battery_capacity)
                break
            except ValueError:
                print("Please enter a valid number for battery capacity (e.g. 200).")

        # Validate state of charge
        while True:
            state_of_charge = input("State of Charge (%): ")
            try:
                float(state_of_charge)
                break
            except ValueError:
                print("Please enter a valid number for state of charge (e.g. 80).")

        # Validate target_range_input
        while True:
            target_range_input = input("Target Range SoC (min,max %) (e.g. 50,80): ")
            parts = [p.strip() for p in target_range_input.split(',')]
            if len(parts) == 2 and all(p.isdigit() for p in parts):
                target_min_soc, target_max_soc = parts
                break
            else:
                print("Please enter two numbers separated by a comma, e.g. 50,80.")

        # Validate location_input
        while True:
            location_input = input("Location (lat, long (5 dec)): ")
            parts = [p.strip() for p in location_input.split(',')]
            if len(parts) == 2:
                lat_str, long_str = parts
                try:
                    float(lat_str)
                    float(long_str)
                    break
                except ValueError:
                    print("Latitude and longitude must be valid numbers (e.g. 51.9225, 4.47917).")
            else:
                print("Please enter latitude and longitude separated by a comma (e.g. 51.9225, 4.47917).")

        # Validate out_of_service_status
        while True:
            out_of_service_status = input("Out of Service (0/1): ")
            if out_of_service_status in ("0", "1"):
                break
            else:
                print("Please enter 0 (in service) or 1 (out of service).")

        # Validate mileage
        while True:
            mileage = input("Mileage (km): ")
            try:
                float(mileage)
                break
            except ValueError:
                print("Please enter a valid number for mileage (e.g. 8000).")

        last_maintenance_date = input("Last Maintenance (YYYY-MM-DD): ")

        scooter_info = {
            'serial_number': serial_number,
            'brand': brand,
            'model': model,
            'top_speed': top_speed,
            'battery_capacity': battery_capacity,
            'soc': state_of_charge,
            'soc_range': {'target_min_soc': target_min_soc, 'target_max_soc': target_max_soc},
            'location': {'latitude': lat_str, 'longitude': long_str},
            'out_of_service': out_of_service_status,
            'mileage': mileage,
            'last_maintenance': last_maintenance_date
        }

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
            'soc': cleaned_data.get('soc', 0),
            'soc_range': cleaned_data.get('soc_range', 0),
            'location': cleaned_data.get('location', {}),
            'out_of_service': cleaned_data.get('out_of_service', 0),
            'mileage': cleaned_data.get('mileage', 0.0),
            'last_maintenance': cleaned_data.get('last_maintenance', ''),
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

    def updatescooterlimit(self, username):
        all_scooters = self.db_handler.getdata('scooters')

        if not all_scooters:
            print("No scooters found.")
            return

        print("\n--- List of Scooters ---")
        for idx, scooter in enumerate(all_scooters, start=1):
            print(f"{idx}. Serial: {scooter['serial_number']} | {scooter['brand']} {scooter['model']} | Top Speed: {scooter['top_speed']} km/h | SoC: {scooter['soc']}%")

        while True:
            try:
                choice = int(input("Select a scooter by number: "))
                if 1 <= choice <= len(all_scooters):
                    selected_scooter = all_scooters[choice - 1]
                    serialnumber = selected_scooter['serial_number']
                    break
                else:
                    print(f"Please enter a number between 1 and {len(all_scooters)}.")
            except ValueError:
                print("Invalid input. Please enter a number.")

        print(f"\n--- Updating Scooter (Service Engineer Mode): {serialnumber} ---")
        state_of_charge = input("State of Charge (%): ")
        target_range_input = input("Target Range SoC (min,max (%)): ")
        location_input = input("Location (lat,long) (5 decimals): ")
        out_of_service_status = input("Out of Service (0/1): ")
        mileage = input("Mileage (km): ")
        last_maintenance_date = input("Last Maintenance (YYYY-MM-DD): ")

        lat_str, long_str = location_input.split(',')
        target_min_soc, target_max_soc = target_range_input.split(',')

        newinfo = {
            'serial_number': serialnumber,
            'soc': state_of_charge,
            'soc_range': {
                'target_min_soc': target_min_soc,
                'target_max_soc': target_max_soc
            },
            'location': {
                'latitude': lat_str,
                'longitude': long_str
            },
            'out_of_service': out_of_service_status,
            'mileage': mileage,
            'last_maintenance': last_maintenance_date
        }

        try:
            cleaned_data = self.input_handler.handle_scooter_data_limit(newinfo, username)
        except ValueError as ve:
            print(f"Validation error during cleaning: {ve}. Update cancelled.")
            self.logger.writelog(username, "Update Scooter Failed", f"Validation error for scooter '{serialnumber}': {ve}", is_suspicious=True)
            return

        existing_scooter = self.db_handler.getdata('scooters', {'serial_number': serialnumber})
        if not existing_scooter:
            print(f"Error: Scooter with serial number '{serialnumber}' not found.")
            self.logger.writelog(username, "Update Scooter Failed", f"Scooter '{serialnumber}' not found for SE update", is_suspicious=True)
            return

        originalvalues = existing_scooter[0]
        updates_for_db = {}

        for key in cleaned_data:
            if key == 'location':
                old_loc_str = originalvalues.get('location', '')
                try:
                    old_lat, old_lon = map(lambda x: round(float(x), 5), old_loc_str.split(','))
                    new_lat, new_lon = map(lambda x: round(float(x), 5), cleaned_data[key].split(','))

                    if old_lat != new_lat or old_lon != new_lon:
                        updates_for_db[key] = cleaned_data[key]
                    else:
                        print(f"'{key}' is the same. No update needed.")
                except Exception as e:
                    print(f"Error comparing location: {e}")

            elif key == 'soc_range':
                old_range_str = originalvalues.get('soc_range', '')
                try:
                    old_min, old_max = map(int, old_range_str.split('-'))
                    new_min, new_max = map(int, cleaned_data[key].split('-'))

                    if old_min != new_min or old_max != new_max:
                        updates_for_db[key] = cleaned_data[key]
                    else:
                        print(f"'{key}' is the same. No update needed.")
                except Exception as e:
                    print(f"Error comparing soc_range: {e}")

            else:
                old_value = str(originalvalues.get(key, '')).strip()
                new_value = str(cleaned_data[key]).strip()
                if old_value != new_value:
                    updates_for_db[key] = cleaned_data[key]
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


    def update_scooter(self, username):
        all_scooters = self.db_handler.getdata('scooters')

        if not all_scooters:
            print("No scooters found.")
            return

        print("\n--- List of Scooters ---")
        for idx, scooter in enumerate(all_scooters, start=1):
            print(f"{idx}. Serial: {scooter['serial_number']} | {scooter['brand']} {scooter['model']} | Top Speed: {scooter['top_speed']} km/h | SoC: {scooter['soc']}%")

        while True:
            try:
                choice = int(input("Select a scooter by number: "))
                if 1 <= choice <= len(all_scooters):
                    selected_scooter = all_scooters[choice - 1]
                    serialnumber = selected_scooter['serial_number']
                    break
                else:
                    print(f"Please enter a number between 1 and {len(all_scooters)}.")
            except ValueError:
                print("Invalid input. Please enter a number.")

        print(f"\n--- Updating Scooter: {serialnumber} ---")
        brand = input("Scooter Brand: ")
        model = input("Scooter Model: ")
        serial_number = input("Serial Number: ")
        top_speed = input("Top Speed (km/h): ")
        battery_capacity = input("Battery Capacity (Wh): ")
        state_of_charge = input("State of Charge (%): ")
        target_range_input = input("Target Range SoC (min,max %) (e.g. 50,80): ")
        location_input = input("Location (lat,long) (5 decimals): ")
        out_of_service_status = input("Out of Service (0/1): ")
        mileage = input("Mileage (km): ")
        last_maintenance_date = input("Last Maintenance (YYYY-MM-DD): ")

        lat_str, long_str = location_input.split(',')
        target_min_soc, target_max_soc = target_range_input.split(',')

        newinfo = {
            'serial_number': serial_number,
            'brand': brand,
            'model': model,
            'top_speed': top_speed,
            'battery_capacity': battery_capacity,
            'soc': state_of_charge,
            'soc_range': {
                'target_min_soc': target_min_soc,
                'target_max_soc': target_max_soc
            },
            'location': {
                'latitude': lat_str,
                'longitude': long_str
            },
            'out_of_service': out_of_service_status,
            'mileage': mileage,
            'last_maintenance': last_maintenance_date
        }

        try:
            cleaned_data = self.input_handler.handle_scooter_data(newinfo)
        except ValueError as ve:
            print(f"Validation error during cleaning: {ve}. Update cancelled.")
            self.logger.writelog(username, "Update Scooter Failed", f"Validation error for scooter '{serialnumber}': {ve}", is_suspicious=True)
            return

        existing_scooter = self.db_handler.getdata('scooters', {'serial_number': serialnumber})
        if not existing_scooter:
            print(f"Error: Scooter with serial number '{serialnumber}' not found.")
            self.logger.writelog(username, "Update Scooter Failed", f"Scooter '{serialnumber}' not found for update", is_suspicious=True)
            return

        originalvalues = existing_scooter[0]
        updates_for_db = {}

        for key in cleaned_data:
            if key == 'location':
                old_loc_str = originalvalues.get('location', '')
                try:
                    old_lat, old_lon = map(lambda x: round(float(x), 5), old_loc_str.split(','))
                    new_lat, new_lon = map(lambda x: round(float(x), 5), cleaned_data[key].split(','))

                    if old_lat != new_lat or old_lon != new_lon:
                        updates_for_db[key] = cleaned_data[key]
                    else:
                        print(f"'{key}' is the same. No update needed.")
                except Exception as e:
                    print(f"Error comparing location: {e}")

            elif key == 'soc_range':
                old_range_str = originalvalues.get('soc_range', '')
                try:
                    old_min, old_max = map(int, old_range_str.split('-'))
                    new_min, new_max = map(int, cleaned_data[key].split('-'))

                    if old_min != new_min or old_max != new_max:
                        updates_for_db[key] = cleaned_data[key]
                    else:
                        print(f"'{key}' is the same. No update needed.")
                except Exception as e:
                    print(f"Error comparing soc_range: {e}")

            else:
                old_value = str(originalvalues.get(key, '')).strip()
                new_value = str(cleaned_data[key]).strip()
                if old_value != new_value:
                    updates_for_db[key] = cleaned_data[key]
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

    def delete_scooter(self, username):
        all_scooters = self.db_handler.getdata('scooters')

        if not all_scooters:
            print("No scooters found.")
            return

        print("\n--- List of Scooters ---")
        for idx, scooter in enumerate(all_scooters, start=1):
            print(f"{idx}. Serial: {scooter['serial_number']} | {scooter['brand']} {scooter['model']} | SoC: {scooter['soc']}%")

        while True:
            try:
                choice = int(input("Select a scooter to delete by number: "))
                if 1 <= choice <= len(all_scooters):
                    selected_scooter = all_scooters[choice - 1]
                    serialnumber = selected_scooter['serial_number']
                    break
                else:
                    print(f"Please enter a number between 1 and {len(all_scooters)}.")
            except ValueError:
                print("Invalid input. Please enter a number.")

        confirm = input(f"Are you sure you want to delete scooter '{serialnumber}'? This cannot be undone (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("Deletion cancelled.")
            self.logger.writelog(username, "Delete Scooter Cancelled", f"Cancelled deletion of scooter '{serialnumber}'.")
            return

        try:
            self.db_handler.deleterecord('scooters', 'serial_number', serialnumber)
            print(f"Scooter with serial number '{serialnumber}' has been deleted.")
            self.logger.writelog(username, "Delete Scooter", f"Scooter '{serialnumber}' deleted from database.")
        except Exception as e:
            print(f"Error while deleting scooter '{serialnumber}': {e}")
            self.logger.writelog(username, "Delete Scooter Failed", f"Database error while deleting scooter '{serialnumber}': {e}", is_suspicious=True)

    def search_scooter(self, username):
        query = input("Enter search query for scooters (leave empty to list all): ")

        print(f"\nSearching Scooters for: '{query}'")

        if not self.db_handler:
            print("Error: Database not connected. Can't search scooters.")
            return []

        SEARCH_FIELDS = {
            'serial_number': 'Serial Number',
            'brand': 'Brand',
            'model': 'Model',
            'top_speed': 'Top Speed',
            'battery_capacity': 'Battery Capacity',
            'soc': 'State of Charge',
            'out_of_service': 'Out of Service'
        }

        all_scooters = self.db_handler.getdata('scooters') or []
        results = []

        if not query:
            print("No search term provided, showing all scooters.")
            results = [{'scooter': s, 'matched_field': 'N/A', 'matched_value': 'N/A'} for s in all_scooters]
        else:
            query = query.lower()
            for scooter in all_scooters:
                matched_field = None
                matched_value = None
                for field, display_name in SEARCH_FIELDS.items():
                    field_value = str(scooter.get(field, '')).lower()
                    if query in field_value:
                        matched_field = display_name
                        matched_value = scooter.get(field)
                        break

                if matched_field:
                    results.append({
                        'scooter': scooter,
                        'matched_field': matched_field,
                        'matched_value': matched_value
                    })

        if results:
            print(f"Found {len(results)} scooter(s):")
            for result in results:
                s = result['scooter']
                print(
                    f"  Serial: {s.get('serial_number')}, Brand: {s.get('brand')}, Model: {s.get('model')}, "
                    f"Top Speed: {s.get('top_speed')} km/h, SoC: {s.get('soc')}%, Out of Service: {s.get('out_of_service')}")
                print(f"    (Matched on {result['matched_field']}: {result['matched_value']})")

            self.logger.writelog(username, "Search Scooter",
                                f"Searched for '{query}', found {len(results)} results.")
        else:
            print("No scooters found matching your search.")
            self.logger.writelog(username, "Search Scooter",
                                f"Searched for '{query}', scooter not found.")

        return results


    # def search_scooter(self, query, username):
    #     print(f"\nSearching Scooters for: '{query}'")

    #     if not self.db_handler:
    #         print("Error: Database not connected. Can't search scooters.")
    #         return []

    #     SEARCH_FIELDS = {
    #         'serial_number': 'Serial Number',
    #         'brand': 'Brand',
    #         'mo ': 'Model',
    #     }

    #     all_scooters = self.db_handler.getdata('scooters')
    #     results = []

    #     if not query:
    #         print("No search term provided, showing all scooters.")
    #         results = all_scooters
    #     else:
    #         query = query.lower()
    #         for scooter in all_scooters:
    #             matched_field = None
    #             for field, display_name in SEARCH_FIELDS.items():
    #                 field_value = str(scooter.get(field, '')).lower()
    #                 if query in field_value:
    #                     matched_field = display_name
    #                     break

    #             if matched_field:
    #                 results.append({
    #                     'scooter': scooter,
    #                     'matched_field': matched_field,
    #                     'matched_value': scooter.get(field)
    #                 })

    #     if results:
    #         print(f"Found {len(results)} scooter(s):")
    #         for result in results:
    #             s = result['scooter']
    #             print(
    #                 f"  Serial: {s.get('serial_number')}, Brand: {s.get('brand')}, Model: {s.get('model')}, "
    #                 f"SoC: {s.get('soc')}%, Location: {s.get('location')}")
    #             print(f"    (Matched on {result['matched_field']}: {result['matched_value']})")

    #         self.logger.writelog(username, "Search Scooter", f"Searched for '{query}', found {len(results)} results.")
    #     else:
    #         print("No scooters found matching your search.")
    #         self.logger.writelog(username, "Search Scooter", f"Searched for '{query}', scooter not found.")
    #     return results

    # def mark_scooter_out_of_service(self, serial_number, username, reason=""):
    #     print(f"\nMarking Scooter {serial_number} as Out of Service")
    #     if not self.db_handler:
    #         print("Error: Database is not connected.")
    #         return

    #     existing_scooter = self.db_handler.getdata('scooters', {'serial_number': serial_number})
    #     if not existing_scooter:
    #         print(f"Error: Scooter with serial '{serial_number}' not found.")
    #         self.logger.writelog(username, "Scooter OOS Failed", 
    #                            f"Scooter '{serial_number}' not found", issuspicious=True)
    #         return

    #     try:
    #         self.db_handler.updateexistingrecord('scooters', 'serial_number', serial_number, {
    #             'out_of_service': 1,
    #             'last_maintenance': datetime.date.today().isoformat()
    #         })
    #         print(f"Scooter {serial_number} marked as out of service.")
    #         self.logger.writelog(username, "Scooter OOS", 
    #                            f"Marked scooter '{serial_number}' as out of service. Reason: {reason}")
    #     except Exception as e:
    #         print(f"Couldn't update scooter status. Error: {e}")
    #         self.logger.writelog(username, "Scooter OOS Failed", f"Error: {e}", issuspicious=True)

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
                'out_of_service': 0,
                'last_maintenance': datetime.date.today().isoformat()
            })
            print(f"Scooter {serial_number} marked as in service.")
            self.logger.writelog(username, "Scooter IS", 
                               f"Marked scooter '{serial_number}' as in service")
        except Exception as e:
            print(f"Couldn't update scooter status. Error: {e}")
            self.logger.writelog(username, "Scooter IS Failed", f"Error: {e}", issuspicious=True)