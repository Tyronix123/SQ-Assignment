import datetime
import secrets
from input_validation import InputValidation

class TravellerHandler:
    def __init__(self, db_manager, logger, dutch_cities):
        self.db_manager = db_manager
        self.logger = logger
        self.dutch_cities = dutch_cities

    def add_traveller(self, traveller_info, username):
        print("\nAdding a New Traveller")
        if not self.db_manager:
            print("Error: Database is not connected. Can't add traveller.")
            return

        if not InputValidation.is_valid_email(traveller_info.get('email_address', '')):
            print("Wrong email address format.")
            self.logger.writelog(username, "Add Traveller Failed", f"Invalid email for new traveller", issuspicious=True)
            return
        if not InputValidation.is_valid_phone(traveller_info.get('mobile_phone', '')):
            print("Wrong mobile phone format. Use +31-6-DDDDDDDD or just 8 digits.")
            self.logger.writelog(username, "Add Traveller Failed", f"Invalid mobile phone for new traveller", issuspicious=True)
            return
        if not InputValidation.is_valid_zip(traveller_info.get('zip_code', '')):
            print("Wrong Dutch zip code format. Use DDDDXX (e.g., 1234AB).")
            self.logger.writelog(username, "Add Traveller Failed", f"Invalid zip code for new traveller", issuspicious=True)
            return
        if not InputValidation.is_valid_license(traveller_info.get('driving_license_number', '')):
            print("Wrong driving license format. Use XXDDDDDDD or XDDDDDDDD.")
            self.logger.writelog(username, "Add Traveller Failed", f"Invalid driving license for new traveller", issuspicious=True)
            return

        if traveller_info.get('city') not in self.dutch_cities:
            print(f"Invalid city. Please choose from: {', '.join(self.dutch_cities)}")
            self.logger.writelog(username, "Add Traveller Failed", f"Invalid city '{traveller_info.get('city')}'", issuspicious=True)
            return

        customer_id = "CUST-" + secrets.token_hex(8)
        reg_date = datetime.date.today().isoformat()

        data_to_insert = {
            'customer_id': customer_id,
            'first_name': traveller_info.get('first_name', ''),
            'last_name': traveller_info.get('last_name', ''),
            'birthday': traveller_info.get('birthday', ''),
            'gender': traveller_info.get('gender', ''),
            'street_name': traveller_info.get('street_name', ''),
            'house_number': traveller_info.get('house_number', ''),
            'zip_code': traveller_info.get('zip_code', ''),
            'city': traveller_info.get('city', ''),
            'email_address': traveller_info.get('email_address', ''),
            'mobile_phone': traveller_info.get('mobile_phone', ''),
            'driving_license_number': traveller_info.get('driving_license_number', ''),
            'registration_date': reg_date
        }
        try:
            self.db_manager.addnewrecord('travellers', data_to_insert)
            print(f"Traveller '{data_to_insert['first_name']} {data_to_insert['last_name']}' added with ID: {customer_id}")
            self.logger.writelog(username, "Add Traveller", f"New traveller '{customer_id}' added.")
        except Exception as e:
            print(f"Couldn't add traveller. Error: {e}")
            self.logger.writelog(username, "Add Traveller Failed", f"Error: {e}", issuspicious=True)

    def update_traveller(self, customer_id, new_info, username):
        print(f"\nUpdating Traveller Info for ID: {customer_id}")
        if not self.db_manager:
            print("Error: Database not connected. Can't update traveller.")
            return

        existing_traveller = self.db_manager.getdata('travellers', {'customer_id': customer_id})
        if not existing_traveller:
            print(f"Error: Traveller with ID '{customer_id}' not found.")
            self.logger.writelog(username, "Update Traveller Failed", f"Traveller '{customer_id}' not found", issuspicious=True)
            return

        cleaned_info = {}
        for key, value in new_info.items():
            cleaned_value = InputValidation.clean_up_input(str(value))
            if key == 'email_address' and not InputValidation.checkemail(cleaned_value):
                print(f"Invalid email address '{cleaned_value}'. Update cancelled.")
                self.logger.writelog(username, "Update Traveller Failed", f"Invalid email for '{customer_id}'", issuspicious=True)
                return
            if key == 'mobile_phone' and not InputValidation.checkphonenum(cleaned_value):
                print(f"Invalid mobile phone '{cleaned_value}'. Update cancelled.")
                self.logger.writelog(username, "Update Traveller Failed", f"Invalid mobile phone for '{customer_id}'",
                                    issuspicious=True)
                return
            if key == 'zip_code' and not InputValidation.checkzipcode(cleaned_value):
                print(f"Invalid zip code '{cleaned_value}'. Update cancelled.")
                self.logger.writelog(username, "Update Traveller Failed", f"Invalid zip code for '{customer_id}'", issuspicious=True)
                return
            if key == 'driving_license_number' and not InputValidation.checklicense(cleaned_value):
                print(f"Invalid driving license '{cleaned_value}'. Update cancelled.")
                self.logger.writelog(username, "Update Traveller Failed", f"Invalid driving license for '{customer_id}'",
                                    issuspicious=True)
                return
            if key == 'city' and cleaned_value not in self.dutch_cities:
                print(f"Invalid city '{cleaned_value}'. Choose from: {', '.join(self.dutch_cities)}. Update cancelled.")
                self.logger.writelog(username, "Update Traveller Failed", f"Invalid city for '{customer_id}'", issuspicious=True)
                return
            cleaned_info[key] = cleaned_value

        if not cleaned_info:
            print("No valid information provided for update. Nothing changed.")
            return

        try:
            self.db_manager.updateexistingrecord('travellers', 'customer_id', customer_id, cleaned_info)
            print(f"Traveller with ID '{customer_id}' information updated successfully!")
            self.logger.writelog(username, "Update Traveller", f"Info for traveller '{customer_id}' updated.")
        except Exception as e:
            print(f"Couldn't update traveller '{customer_id}'. Error: {e}")
            self.logger.writelog(username, "Update Traveller Failed", f"Error: {e}", issuspicious=True)

    def delete_traveller(self, customer_id, username):
        print(f"\nDeleting Traveller with ID: {customer_id}")
        if not self.db_manager:
            print("Error: Database is not connected. Can't delete traveller.")
            return

        existing_traveller = self.db_manager.getdata('travellers', {'customer_id': customer_id})
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
            self.db_manager.deleterecord('travellers', 'customer_id', customer_id)
            print(f"Traveller with ID '{customer_id}' successfully deleted.")
            self.logger.writelog(username, "Delete Traveller", f"Traveller '{customer_id}' deleted.")
        except Exception as e:
            print(f"A problem happened while deleting traveller '{customer_id}'. Error: {e}")
            self.logger.writelog(username, "Delete Traveller Failed", f"Error: {e}", issuspicious=True)

    def search_traveller(self, query, username):
        print(f"\nSearching Travellers for: '{query}'")
        if not self.db_manager:
            print("Error: Database is not ready. Can't search travellers.")
            return []

        all_travellers = self.db_manager.getdata('travellers')
        results = []
        clean_query = InputValidation.clean_up_input(query).lower()

        if not clean_query:
            print("No search term provided, showing all travellers.")
            results = all_travellers
        else:
            for traveller in all_travellers:
                if (clean_query in traveller.get('first_name', '').lower() or
                        clean_query in traveller.get('last_name', '').lower() or
                        clean_query in traveller.get('email_address', '').lower() or
                        clean_query in traveller.get('customer_id', '').lower()):
                    results.append(traveller)

        if results:
            print(f"Found {len(results)} traveller(s):")
            for t in results:
                print(
                    f"  ID: {t.get('customer_id')}, Name: {t.get('first_name')} {t.get('last_name')}, Email: {t.get('email_address')}, Phone: {t.get('mobile_phone')}")
            self.logger.writelog(username, "Search Traveller", f"Searched for '{query}', found {len(results)} results.")
        else:
            print("No travellers found matching your search.")
            self.logger.writelog(username, "Search Traveller", f"Searched for '{query}', found no results.")
        return results