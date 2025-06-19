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

    def add_traveller(self, username):
        print("\nAdding a New Traveller")
        if not self.db_handler:
            print("Error: Database is not connected. Can't add traveller.")
            return
        
        traveller_info = {
            'first_name': input("Traveller First Name: "),
            'last_name':  input("Traveller Last Name: "),
            'birthday':   input("Traveller Birthday (YYYY-MM-DD): "),
            'gender':     input("Traveller Gender (Male/Female): "),
            'street_name':input("Traveller Street Name: "),
            'house_number':input("Traveller House Number: "),
            'zip_code':   input("Traveller Zip Code (DDDDXX): "),
            'city':       input(f"Traveller City (choose from {', '.join(self.dutch_cities)}): "),
            'email':      input("Traveller Email Address: "),
            'mobile_phone': input("Traveller Mobile Phone (8 digits): "),
            'driving_license': input("Driving License Number (XXDDDDDDD or XDDDDDDDD): ")
        }

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

    def update_traveller(self, username):
        all_travellers = self.db_handler.getdata('travellers')

        if not all_travellers:
            print("No travellers found.")
            return

        print("\n--- List of Travellers ---")
        for idx, traveller in enumerate(all_travellers, start=1):
            print(f"{idx}. ID: {traveller['customer_id']} | Name: {traveller['first_name']} {traveller['last_name']} | Email: {traveller['email']}")

        try:
            choice = int(input("\nSelect a traveller by number to update: ")) - 1
            if choice < 0 or choice >= len(all_travellers):
                print("Invalid selection.")
                return
        except ValueError:
            print("Invalid input.")
            return

        selected_traveller = all_travellers[choice]
        cid = selected_traveller['customer_id']

        data = {}
        print("\nEnter new values (leave empty to skip):")
        em = input("New Email: ")
        if em:
            data['email'] = em

        ph = input("New Mobile Phone (8 digits): ")
        if ph:
            if self.input_validation.is_valid_phone(ph):
                data['mobile_phone'] = "+31-6-" + ph
            else:
                print("Invalid phone format. Skipping update for phone.")

        zp = input("New Zip Code: ")
        if zp:
            data['zip_code'] = zp

        ct = input(f"New City (choose from {', '.join(self.dutch_cities)}): ")
        if ct:
            data['city'] = ct

        if not data:
            print("No updates provided.")
            return

        self.db_handler.updateexistingrecord('travellers', 'customer_id', cid, data)
        print("Traveller information updated successfully.")

        self.logger.writelog(
            username,
            "Update Traveller",
            f"Updated traveller ID '{cid}' with new data: {data}"
        )


    def delete_traveller(self, username):
        if not self.db_handler:
            print("Error: Database is not connected. Can't delete traveller.")
            return

        travellers = self.db_handler.getdata('travellers')
        if not travellers:
            print("No travellers found in the system.")
            return

        print("\n--- Travellers ---")
        for idx, t in enumerate(travellers, start=1):
            print(f"{idx}. ID: {t['customer_id']} | "
                f"{t['first_name']} {t['last_name']} | "
                f"{t['email']}")

        try:
            choice = int(input("\nSelect traveller number to delete: ")) - 1
            if choice < 0 or choice >= len(travellers):
                print("Invalid selection.")
                return
        except ValueError:
            print("Invalid input.")
            return

        target = travellers[choice]
        customer_id = target['customer_id']

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

    def search_traveller(self, username):
        query = input("Enter search query for travellers (leave empty to list all): ")

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

        all_travellers = self.db_handler.getdata('travellers') or []
        results = []

        if not query:
            print("No search term provided, showing all travellers.")
            results = [{'traveller': t, 'matched_field': 'N/A', 'matched_value': 'N/A'} for t in all_travellers]
        else:
            query = query.lower()
            for traveller in all_travellers:
                matched_field = None
                matched_value = None
                for field, display_name in SEARCH_FIELDS.items():
                    field_value = str(traveller.get(field, '')).lower()
                    if query in field_value:
                        matched_field = display_name
                        matched_value = traveller.get(field)
                        break

                if matched_field:
                    results.append({
                        'traveller': traveller,
                        'matched_field': matched_field,
                        'matched_value': matched_value
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
