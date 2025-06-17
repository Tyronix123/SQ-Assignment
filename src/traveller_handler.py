import datetime
import secrets
from db_handler import DBHandler
from input_handler import InputHandler
from input_validation import InputValidation
from logger import Logger

class TravellerHandler:
    def __init__(self, db_handler: DBHandler = None, logger: Logger = None, input_validation: InputValidation = None, input_handler: InputHandler = None):
        self.db_handler = db_handler
        self.logger = logger
        self.input_validation = input_validation
        self.input_handler = input_handler
        self.dutch_cities = ["Amsterdam", "Rotterdam", "Utrecht", "The Hague", "Eindhoven",
                            "Groningen", "Maastricht", "Leiden", "Haarlem", "Delft"]

    def add_traveller(self, traveller_info, username):
        print("\nAdding a New Traveller")
        if not self.db_handler:
            print("Error: Database is not connected. Can't add traveller.")
            return

        try:
            cleaned_data = self.input_handler.handle_traveller_data(traveller_info)
        except ValueError as e:
            print(f"Validation error while cleaning traveller data: {e}")
            self.logger.writelog(username, "Add Traveller Failed", f"Validation error: {e}", issuspicious=True)
            return

        if cleaned_data.get('city') not in self.dutch_cities:
            print(f"Invalid city. Please choose from: {', '.join(self.dutch_cities)}")
            self.logger.writelog(username, "Add Traveller Failed", f"Invalid city '{cleaned_data.get('city')}'", issuspicious=True)
            return
        
        existing_traveller = self.db_handler.getdata('travellers', {'email': cleaned_data.get('email', '')})
        if existing_traveller:
            print(f"Error: Traveller with email address '{cleaned_data.get('email', '')}' already exists.")
            self.logger.writelog(username, "Add Traveller Failed", f"Duplicate email address: {cleaned_data.get('email', '')}", issuspicious=True)
            return

        reg_date = datetime.date.today().isoformat()

        data_to_insert = {
            'first_name': cleaned_data.get('first_name', ''),
            'last_name': cleaned_data.get('last_name', ''),
            'birthday': cleaned_data.get('birthday', ''),
            'gender': cleaned_data.get('gender', ''),
            'street_name': cleaned_data.get('street_name', ''),
            'house_number': cleaned_data.get('house_number', ''),
            'zip_code': cleaned_data.get('zip_code', ''),
            'city': cleaned_data.get('city', ''),
            'email': cleaned_data.get('email', ''),
            'mobile_phone': cleaned_data.get('mobile_phone', ''),
            'driving_license': cleaned_data.get('driving_license', ''),
            'registration_date': reg_date
        }

        try:
            self.db_handler.addnewrecord('travellers', data_to_insert)
            print(f"Traveller '{data_to_insert['first_name']} {data_to_insert['last_name']}' added")
            self.logger.writelog(username, "Add Traveller", f"New traveller '{data_to_insert['first_name']} {data_to_insert['last_name']}'added.")
        except Exception as e:
            print(f"Couldn't add traveller. Error: {e}")
            self.logger.writelog(username, "Add Traveller Failed", f"Error: {e}", issuspicious=True)

    def update_traveller(self, customer_id, new_info, username):
        print(f"\nUpdating Traveller Info for ID: {customer_id}")
        
        if not self.db_handler:
            print("Error: Database not connected. Can't update traveller.")
            return

        existing_traveller = self.db_handler.getdata('travellers', {'customer_id': customer_id})
        if not existing_traveller:
            print(f"Error: Traveller with ID '{customer_id}' not found.")
            self.logger.writelog(username, "Update Traveller Failed", 
                            f"Traveller '{customer_id}' not found", issuspicious=True)
            return

        original_values = existing_traveller[0]

        try:
            cleaned_data = self.input_handler.handle_traveller_data(new_info)
        except ValueError as ve:
            print(f"Validation error: {ve}. Update cancelled.")
            self.logger.writelog(username, "Update Traveller Failed",
                            f"Validation error for traveller '{customer_id}': {ve}", issuspicious=True)
            return

        updates_for_db = {}
        for key, cleaned_value in cleaned_data.items():
            original_value = original_values.get(key, '')
            
            if self.input_validation.is_valid_phone(cleaned_value):
                cleaned_value = "+31-6-" + cleaned_value
                
            if str(original_value).strip() != str(cleaned_value).strip():
                updates_for_db[key] = cleaned_value
            else:
                print(f"'{key}' is the same. No update needed.")

        if not updates_for_db:
            print("No valid or changed information to update.")
            return

        try:
            self.db_handler.updateexistingrecord('travellers', 'customer_id', customer_id, updates_for_db)
            print(f"Traveller with ID '{customer_id}' successfully updated.")
            self.logger.writelog(username, "Update Traveller",
                            f"Updated fields for traveller '{customer_id}': {', '.join(updates_for_db.keys())}")
        except Exception as e:
            print(f"Error while updating traveller '{customer_id}': {e}")
            self.logger.writelog(username, "Update Traveller Failed",
                            f"Database error for traveller '{customer_id}': {e}", issuspicious=True)

    def delete_traveller(self, customer_id, username):
        print(f"\nDeleting Traveller with ID: {customer_id}")
        if not self.db_handler:
            print("Error: Database is not connected. Can't delete traveller.")
            return

        existing_traveller = self.db_handler.getdata('travellers', {'customer_id': customer_id})
        if not existing_traveller:
            print(f"Error: Traveller with ID '{customer_id}' not found.")
            self.logger.writelog(username, "Delete Traveller Failed", f"Traveller '{customer_id}' not found", issuspicious=True)
            return

        confirmation = input(
            f"Are you sure you want to delete traveller '{customer_id}'? This cannot be undone! (type 'yes' to confirm): ").lower()
        if confirmation != 'yes':
            print("Deletion cancelled.")
            self.logger.writelog(username, "Delete Traveller Cancelled", f"Cancelled deletion of '{customer_id}'")
            return

        try:
            self.db_handler.deleterecord('travellers', 'customer_id', customer_id)
            print(f"Traveller with ID '{customer_id}' successfully deleted.")
            self.logger.writelog(username, "Delete Traveller", f"Traveller '{customer_id}' deleted.")
        except Exception as e:
            print(f"A problem happened while deleting traveller '{customer_id}'. Error: {e}")
            self.logger.writelog(username, "Delete Traveller Failed", f"Error: {e}", issuspicious=True)

    def search_traveller(self, query, username):
        print(f"\nSearching Travellers for: '{query}'")

        if not self.db_handler:
            print("Error: Database not connected. Can't search travellers.")
            return []

        SEARCH_FIELDS = {
            'customer_id': 'Customer ID',
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'email': 'Email',
            'mobile_phone': 'Phone'
        }

        all_travellers = self.db_handler.getdata('travellers')
        results = []

        if not query:
            print("No search term provided, showing all travellers.")
            results = all_travellers
        else:
            query = query.lower()
            for traveller in all_travellers:
                matched_field = None
                for field, display_name in SEARCH_FIELDS.items():
                    field_value = str(traveller.get(field, '')).lower()
                    if query in field_value:
                        matched_field = display_name
                        break

                if matched_field:
                    results.append({
                        'traveller': traveller,
                        'matched_field': matched_field,
                        'matched_value': traveller.get(field)
                    })

        if results:
            print(f"Found {len(results)} traveller(s):")
            for result in results:
                t = result['traveller']
                print(
                    f"  ID: {t.get('customer_id')}, Name: {t.get('first_name')} {t.get('last_name')}, "
                    f"Email: {t.get('email')}, Phone: {t.get('mobile_phone')}")
                print(f"    (Matched on {result['matched_field']}: {result['matched_value']})")

            self.logger.writelog(username, "Search Traveller", 
                            f"Searched for '{query}', found {len(results)} results.")
        else:
            print("No travellers found matching your search.")
            self.logger.writelog(username, "Search Traveller", 
                            f"Searched for '{query}', traveller not found.")
        
        return results