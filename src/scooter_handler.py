import datetime
from input_validation import InputValidation

class ScooterHandler:
    def __init__(self, db_manager, logger):
        self.db_manager = db_manager
        self.logger = logger

    def add_scooter(self, scooter_info, username):
        print("\nAdding a New Scooter")
        if not self.db_manager:
            print("Error: Database is not connected. Can't add scooter.")
            return

        if not InputValidation.is_valid_serial(scooter_info.get('serial_number', '')):
            print("Invalid serial number format (10-17 alphanumeric characters).")
            self.logger.writelog(username, "Add Scooter Failed", "Invalid serial number format", issuspicious=True)
            return
            
        if not InputValidation.is_valid_location(scooter_info.get('location', '')):
            print("Invalid location format (latitude,longitude with 5 decimal places).")
            self.logger.writelog(username, "Add Scooter Failed", "Invalid location format", issuspicious=True)
            return
            
        if not InputValidation.is_valid_soc(scooter_info.get('state_of_charge', 0)):
            print("Invalid state of charge (0-100%).")
            self.logger.writelog(username, "Add Scooter Failed", "Invalid state of charge", issuspicious=True)
            return

        existing_scooter = self.db_manager.getdata('scooters', {'serial_number': scooter_info['serial_number']})
        if existing_scooter:
            print(f"Error: Scooter with serial number '{scooter_info['serial_number']}' already exists.")
            self.logger.writelog(username, "Add Scooter Failed", 
                               f"Duplicate serial number: {scooter_info['serial_number']}", issuspicious=True)
            return

        scooter_data = {
            'serial_number': scooter_info.get('serial_number', ''),
            'brand': scooter_info.get('brand', ''),
            'model': scooter_info.get('model', ''),
            'top_speed': scooter_info.get('top_speed', 0),
            'battery_capacity': scooter_info.get('battery_capacity', 0),
            'state_of_charge': scooter_info.get('state_of_charge', 0),
            'target_range_soc': scooter_info.get('target_range_soc', 0),
            'location': scooter_info.get('location', ''),
            'out_of_service_status': scooter_info.get('out_of_service_status', 0),
            'mileage': scooter_info.get('mileage', 0.0),
            'last_maintenance_date': scooter_info.get('last_maintenance_date', ''),
            'in_service_date': datetime.date.today().isoformat()
        }

        try:
            self.db_manager.addnewrecord('scooters', scooter_data)
            print(f"Scooter '{scooter_data['brand']} {scooter_data['model']}' (Serial: {scooter_data['serial_number']}) added successfully!")
            self.logger.writelog(username, "Add Scooter", 
                               f"New scooter added: {scooter_data['serial_number']}")
        except Exception as e:
            print(f"Couldn't add scooter. Error: {e}")
            self.logger.writelog(username, "Add Scooter Failed", f"Error: {e}", issuspicious=True)

    def update_scooter(self, serial_number, new_info, username, is_service_engineer=False):
        print(f"\nUpdating Scooter Info for Serial: {serial_number}")
        if not self.db_manager:
            print("Error: Database not connected. Can't update scooter.")
            return

        existing_scooter = self.db_manager.getdata('scooters', {'serial_number': serial_number})
        if not existing_scooter:
            print(f"Error: Scooter with serial number '{serial_number}' not found.")
            self.logger.writelog(username, "Update Scooter Failed", 
                               f"Scooter '{serial_number}' not found", issuspicious=True)
            return

        # Fields that service engineers can't modify
        forbidden_fields = ['serial_number', 'brand', 'model', 'top_speed', 'battery_capacity'] if is_service_engineer else []
        
        cleaned_info = {}
        for key, value in new_info.items():
            if key in forbidden_fields:
                print(f"Service Engineers are not allowed to change '{key}'. Skipping.")
                self.logger.writelog(username, "Update Scooter Warning",
                                   f"Attempt to modify forbidden field '{key}' on scooter '{serial_number}'")
                continue

            cleaned_value = InputValidation.clean_up_input(str(value))
            
            if key == 'location' and not InputValidation.is_valid_location(cleaned_value):
                print(f"Invalid location format '{cleaned_value}'. Update cancelled.")
                self.logger.writelog(username, "Update Scooter Failed",
                                   f"Invalid location for scooter '{serial_number}'", issuspicious=True)
                return
                
            if key == 'state_of_charge' and not InputValidation.is_valid_soc(cleaned_value):
                print(f"Invalid state of charge '{cleaned_value}'. Must be 0-100. Update cancelled.")
                self.logger.writelog(username, "Update Scooter Failed",
                                   f"Invalid SoC for scooter '{serial_number}'", issuspicious=True)
                return
                
            cleaned_info[key] = cleaned_value

        if not cleaned_info:
            print("No valid information provided for update. Nothing changed.")
            return

        try:
            self.db_manager.updateexistingrecord('scooters', 'serial_number', serial_number, cleaned_info)
            print(f"Scooter with serial '{serial_number}' updated successfully!")
            self.logger.writelog(username, "Update Scooter", 
                               f"Updated scooter '{serial_number}'")
        except Exception as e:
            print(f"Couldn't update scooter '{serial_number}'. Error: {e}")
            self.logger.writelog(username, "Update Scooter Failed", f"Error: {e}", issuspicious=True)

    def delete_scooter(self, serial_number, username):
        print(f"\nDeleting Scooter with Serial: {serial_number}")
        if not self.db_manager:
            print("Error: Database is not connected. Can't delete scooter.")
            return

        existing_scooter = self.db_manager.getdata('scooters', {'serial_number': serial_number})
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
            self.db_manager.deleterecord('scooters', 'serial_number', serial_number)
            print(f"Scooter with serial '{serial_number}' successfully deleted.")
            self.logger.writelog(username, "Delete Scooter", 
                               f"Deleted scooter '{serial_number}'")
        except Exception as e:
            print(f"A problem happened while deleting scooter '{serial_number}'. Error: {e}")
            self.logger.writelog(username, "Delete Scooter Failed", f"Error: {e}", issuspicious=True)

    def search_scooter(self, query, username):
        print(f"\nSearching Scooters for: '{query}'")
        if not self.db_manager:
            print("Error: Database is not ready. Can't search scooters.")
            return []

        all_scooters = self.db_manager.getdata('scooters')
        results = []
        clean_query = InputValidation.clean_up_input(query).lower()

        if not clean_query:
            print("No search term provided, showing all scooters.")
            results = all_scooters
        else:
            for scooter in all_scooters:
                if (clean_query in scooter.get('serial_number', '').lower() or
                    clean_query in scooter.get('brand', '').lower() or
                    clean_query in scooter.get('model', '').lower() or
                    clean_query in scooter.get('location', '').lower()):
                    results.append(scooter)

        if results:
            print(f"Found {len(results)} scooter(s):")
            for s in results:
                status = "Out of Service" if s.get('out_of_service_status', 0) == 1 else "Available"
                print(
                    f"  Serial: {s.get('serial_number')}, Brand/Model: {s.get('brand')} {s.get('model')}, "
                    f"SoC: {s.get('state_of_charge')}%, Location: {s.get('location')}, Status: {status}")
            self.logger.writelog(username, "Search Scooter", 
                               f"Searched for '{query}', found {len(results)} results.")
        else:
            print("No scooters found matching your search.")
            self.logger.writelog(username, "Search Scooter", 
                               f"Searched for '{query}', found no results.")
        return results

    def mark_scooter_out_of_service(self, serial_number, username, reason=""):
        print(f"\nMarking Scooter {serial_number} as Out of Service")
        if not self.db_manager:
            print("Error: Database is not connected.")
            return

        existing_scooter = self.db_manager.getdata('scooters', {'serial_number': serial_number})
        if not existing_scooter:
            print(f"Error: Scooter with serial '{serial_number}' not found.")
            self.logger.writelog(username, "Scooter OOS Failed", 
                               f"Scooter '{serial_number}' not found", issuspicious=True)
            return

        try:
            self.db_manager.updateexistingrecord('scooters', 'serial_number', serial_number, {
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
        if not self.db_manager:
            print("Error: Database is not connected.")
            return

        existing_scooter = self.db_manager.getdata('scooters', {'serial_number': serial_number})
        if not existing_scooter:
            print(f"Error: Scooter with serial '{serial_number}' not found.")
            self.logger.writelog(username, "Scooter IS Failed", 
                               f"Scooter '{serial_number}' not found", issuspicious=True)
            return

        try:
            self.db_manager.updateexistingrecord('scooters', 'serial_number', serial_number, {
                'out_of_service_status': 0,
                'last_maintenance_date': datetime.date.today().isoformat()
            })
            print(f"Scooter {serial_number} marked as in service.")
            self.logger.writelog(username, "Scooter IS", 
                               f"Marked scooter '{serial_number}' as in service")
        except Exception as e:
            print(f"Couldn't update scooter status. Error: {e}")
            self.logger.writelog(username, "Scooter IS Failed", f"Error: {e}", issuspicious=True)