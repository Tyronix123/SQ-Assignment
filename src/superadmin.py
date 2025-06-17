import datetime
import hashlib
import secrets
import os
import shutil
from input_validation import InputValidation
from input_handler import InputHandler
from traveller_handler import TravellerHandler
from scooter_handler import ScooterHandler
from user import User
from logger import Logger
from db_handler import DBHandler

class SuperAdministrator(User):
    def __init__(self, username, password_hash, role, firstname, lastname, regdate=None, db_handler: DBHandler = None, logger: Logger = None, input_validation: InputValidation = None, input_handler: InputHandler = None):
        self.username = username
        self.passwordhash = password_hash
        self.role = role
        self.first_name = firstname
        self.last_name = lastname
        self.reg_date = regdate
        self.db_handler = db_handler
        self.logger = logger
        self.dutch_cities = ["Amsterdam", "Rotterdam", "Utrecht", "The Hague", "Eindhoven",
                            "Groningen", "Maastricht", "Leiden", "Haarlem", "Delft"]
        self.traveller_handler = TravellerHandler(db_handler, logger, self.dutch_cities)
        self.scooter_handler = ScooterHandler(db_handler, logger)
        self.input_validation = input_validation
        self.input_handler = input_handler

    def _manage_user_account(self, username, password, firstname, lastname, role, action_details):
        print(f"\n{action_details}")
        if not self.db_handler:
            print("Error: Database not connected.")
            return False

        user_data = {
            "username":  username,
            "password":  password,
            "firstname": firstname,
            "lastname":  lastname,
            "role":      role,
        }

        validated_user_data = self.input_handler.handle_user_data(user_data)
        if validated_user_data is None:
            print("Failed to validate user data. Please try again.")
            self.logger.writelog(self.username, f"{role} creation Failed", f"Invalid user data for '{username}'", issuspicious=True)
            return False

        existing_user = self.db_handler.getdata('users', {'username': username})
        if existing_user:
            print(f"Username: '{username}' is already taken. Please pick a different one.")
            self.logger.writelog(self.username, f"{role} creation Failed", f"Username '{username}' already in use", issuspicious=True)
            return False

        return True

    def _create_user_record(self, username, password, firstname, lastname, role):

        raw_user_data = {
            "username":  username,
            "password":  password,
            "firstname": firstname,
            "lastname":  lastname,
            "role":      role,
        }
    
        try:
            cleaned = self.input_handler.handle_user_data(raw_user_data)

            cleaned["password_hash"] = self.makepasswordhash(cleaned.pop("password"))
            cleaned["registration_date"] = datetime.date.today().isoformat()
            self.db_handler.addnewrecord("users", cleaned)
            return True

        except ValueError as ve:
            print(f"User data invalid: {ve}")
            self.logger.writelog(self.username, f"Add {role} Failed", str(ve), issuspicious=True)
            return False

        except Exception as e:
            print(f"Something went wrong while adding the {role}: {e}")
            self.logger.writelog(self.username, f"Add {role} Failed", f"Error: {e}", issuspicious=True)
            return False
        
    def _update_user_info(self, usernametochange, newinfo: dict, role):
        print(f"\n-- Changing {role} Details for: {usernametochange} --")
        if not self.db_handler:
            print("Error: Database not connected. Can't update admin.")
            return False

        adminrecords = self.db_handler.getdata('users', {'username': usernametochange})
        if not adminrecords or adminrecords[0].get('role') != role:
            print(f"Error: {role} '{usernametochange}' not found or isn't a {role}.")
            self.logger.writelog(self.username, f"Update {role} Failed",
                        f"Target '{usernametochange}' not found or wrong role", issuspicious=True)
            return False

        cleanedinfo = self.input_handler.handle_user_data(newinfo.items())

        if 'role' in cleanedinfo:
            print("Security Alert! Tried to change user role. That's not allowed here.")
            del cleanedinfo['role']
            self.logger.writelog(self.username, f"Update {role} Failed", f"Attempted role change for '{usernametochange}'",
                        issuspicious=True)

        if not cleanedinfo:
            print("No new information was provided to update. Nothing changed.")
            return False

        try:
            self.db_handler.updateexistingrecord('users', 'username', usernametochange, cleanedinfo)
            print(f"{role} '{usernametochange}' updated successfully!")
            self.logger.writelog(self.username, f"Update {role}", f"Details for '{usernametochange}' updated.")
            return True
        except Exception as e:
            print(f"Couldn't update {role} '{usernametochange}'. Error: {e}")
            self.logger.writelog(self.username, f"Update {role} Failed", f"Error updating '{usernametochange}': {e}",
                        issuspicious=True)
            return False

    def _delete_user(self, username_to_delete, role, self_deletion_message):
        print(f"\n--- Deleting {role}: {username_to_delete} ---")
        if not self.db_handler:
            print("Error: Database not connected.")
            return False

        if username_to_delete == self.username:
            print(self_deletion_message)
            self.logger.writelog(self.username, f"Delete {role} Failed", f"Tried to delete self ({username_to_delete})",
                           issuspicious=True)
            return False

        target_admin_records = self.db_handler.getdata('users', {'username': username_to_delete})
        if not target_admin_records or target_admin_records[0].get('role') != role:
            print(f"Error: {role} '{username_to_delete}' not found or isn't a {role}.")
            self.logger.writelog(self.username, f"Delete {role} Failed",
                           f"Target '{username_to_delete}' not found or wrong role", issuspicious=True)
            return False

        confirmation = input(
            f"Are you certain you want to delete {role} '{username_to_delete}'? This cannot be undone. (type 'yes' to confirm): ").lower()
        if confirmation != 'yes':
            print("Deleting cancelled.")
            self.logger.writelog(self.username, f"Deletion {role} Cancelled", f"Cancelled deletion of '{username_to_delete}'")
            return False

        try:
            self.db_handler.deleterecord('users', 'username', username_to_delete)
            print(f"{role} '{username_to_delete}' has been deleted.")
            self.logger.writelog(self.username, f"Delete {role}", f"{role} '{username_to_delete}' deleted.")
            return True
        except Exception as e:
            print(f"Problem occurred. Couldn't delete: '{username_to_delete}'. Error: {e}")
            self.logger.writelog(self.username, f"Delete {role} Failed", f"Error deleting '{username_to_delete}': {e}",
                           issuspicious=True)
            return False

    def _reset_password(self, username_reset, newpassword, role):
        print(f"\n-- {role} password reset: {username_reset} --")
        if not self.db_handler:
            print("Error: Database is not available.")
            return False

        target_admin_records = self.db_handler.getdata('users', {'username': username_reset})
        if not target_admin_records or target_admin_records[0].get('role') != role:
            print(f"Error: {role} '{username_reset}' not found.")
            self.logger.writelog(self.username, f"Reset {role} Password Failed",
                           f"Target '{username_reset}' not found or wrong role", issuspicious=True)
            return False

        if not self.input_validation.is_valid_password(newpassword):
            print("The new password isn't strong enough.")
            self.logger.writelog(self.username, f"Reset {role} Password Failed", f"Bad new password for '{username_reset}'",
                           issuspicious=True)
            return False

        hashed_password = self.makepasswordhash(newpassword)
        try:
            self.db_handler.updateexistingrecord('users', 'username', username_reset, {'password_hash': hashed_password})
            print(f"Password for {role} '{username_reset}' has been successfully reset!")
            self.logger.writelog(self.username, f"Reset {role} Password",
                           f"Password for '{username_reset}' reset.")
            return True
        except Exception as e:
            print(f"A problem happened while resetting password for '{username_reset}'. Error: {e}")
            self.logger.writelog(self.username, f"Reset {role} Password Failed",
                           f"Error resetting password for '{username_reset}': {e}", issuspicious=True)
            return False

    def addsystemadmin(self, username, password, firstname, lastname):
        if self._manage_user_account(username, password, firstname, lastname, "SystemAdministrator", "Creating a New System Administrator"):
            if self._create_user_record(username, password, firstname, lastname, "SystemAdministrator"):
                print("System Administrator was successfully added")
                self.logger.writelog(self.username, "Add System Admin", f"New System Admin '{username}' created.")

    def changesystemadmininfo(self, usernametochange, newinfo):
        self._update_user_info(usernametochange, newinfo, "SystemAdministrator")

    def deletesystemadmin(self, sysadmin_to_delete):
        self._delete_user(sysadmin_to_delete, "SystemAdministrator", "Can't delete Super Administrator account")

    def resetpasswordsysadmin(self, usernamereset, newpassword):
        self._reset_password(usernamereset, newpassword, "SystemAdministrator")

    def createrestorecode(self, sysadminusername):
        print(f"\nGenerating Restore Code for System Administrator: {sysadminusername}")
        if not self.db_handler:
            print("Error: Database is not ready. Can't generate restore code.")
            return "ERROR"
        
        if sysadminusername != 'superadmin':
            target_admin_records = self.db_handler.getdata('users', {'username': sysadminusername})
            if not target_admin_records or target_admin_records[0].get('role') != 'SystemAdministrator':
                print(f"Error: System Administrator '{sysadminusername}' not found or isn't a System Administrator. Cannot generate restore code.")
                self.logger.writelog(self.username, "Generate Restore Code Failed",
                               f"Target '{sysadminusername}' not found/wrong role", issuspicious=True)
                return "ERROR"

        restore_code = secrets.token_urlsafe(16)
        backup_id = secrets.token_hex(8)
        expiry_date = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()

        try:
            self.db_handler.addnewrecord(
                'restore_codes',
                {
                    'code': restore_code,
                    'backup_id': backup_id,
                    'backup_file_name': None,
                    'created_by_admin': self.username,
                    'system_admin_username': sysadminusername,
                    'expiry_date': expiry_date,
                    'is_revoked': 0
                }
            )
            print(f"Successfully generated a restore code for '{sysadminusername}'.")
            print(f"IMPORTANT! Restore Code: {restore_code}. This code is valid until: {expiry_date}.Backup ID (for this code): {backup_id}")
            print("Give this code is a one time use only.")
            self.logger.writelog(self.username, "Generate Restore Code",
                           f"Generated code for '{sysadminusername}', backup ID: {backup_id}")
            return restore_code
        except Exception as e:
            print(f"Couldn't generate restore code. Error: {e}")
            self.logger.writelog(self.username, "Generate Restore Code Failed", f"Error: {e}", issuspicious=True)
            return "ERROR"

    def revokerestorecode(self, code_to_revoke: str) -> bool:
        """Mark a restore code as revoked so it can no longer be used."""
        print(f"\nRevoking restore code: {code_to_revoke}")

        if not self.db_handler:
            print("Error: Database not connected. Cannot revoke code.")
            self.logger.writelog(self.username, "Revoke Code Failed", "DB not connected", issuspicious=True)
            return False

        records = self.db_handler.getdata('restore_codes', {'code': code_to_revoke})
        if not records:
            print("No such restore code in the system.")
            self.logger.writelog(self.username, "Revoke Code Failed",
                            f"Code '{code_to_revoke}' not found", issuspicious=True)
            return False

        record = records[0]
        if record.get('is_revoked') == 1:
            print("This restore code is already revoked.")
            return False

        try:
            self.db_handler.updateexistingrecord('restore_codes',
                                                'code',
                                                code_to_revoke,
                                                {'is_revoked': 1})
            print("Restore code successfully revoked.")
            self.logger.writelog(self.username, "Revoke Code", f"Code '{code_to_revoke}' revoked.")
            return True
        except Exception as e:
            print(f"Could not revoke code. Error: {e}")
            self.logger.writelog(self.username, "Revoke Code Failed", str(e), issuspicious=True)
            return False



    # Backup and restore methods
    def makebackup(self, restorecode):
        print("\nInitiating System Backup")
        dbpath = self.db_handler.db_name
        backupdir = "backup"

        existingtraveller = self.db_handler.getdata('restore_codes', {'code': restorecode})
        if not existingtraveller:
            print("No such restore code in system.")
            self.logger.writelog(self.username, "Attempted restore code usage.", f"Restore code '{restorecode}' not found",
                            issuspicious=True)
            return False
        currentcode = existingtraveller[0]
        if currentcode.get('is_revoked') == 1:
            print("Code is already revoked in system.")
            self.logger.writelog(self.username, "Attempted revoked code usage.", f"Attempted use revoked code '{restorecode}'",
                            issuspicious=True)
            return False

        if not os.path.exists(backupdir):
            try:
                os.makedirs(backupdir)
                print(f"Created backup directory: '{backupdir}'")
            except OSError as e:
                print(f"Error creating backup directory '{backupdir}': {e}")
                self.logger.writelog(self.username, "System Backup", f"Failed: Error creating directory - {e}")
                return False

        if not os.path.exists(dbpath):
            print(f"Error: Database file not found at '{dbpath}'. Backup failed.")
            self.logger.writelog(self.username, "System Backup", f"Failed: Database file '{dbpath}' not found.")
            return False

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        originaldbfile = os.path.basename(dbpath)
        backup_filename = f"{os.path.splitext(originaldbfile)[0]}_{timestamp}.sqlite_bak"
        backup_full_path = os.path.join(backupdir, backup_filename)

        try:
            shutil.copy2(dbpath, backup_full_path)
            self.db_handler.updateexistingrecord('restore_codes', 'code', restorecode,
                                               {'backup_file_name': backup_filename})
            print(f"Successfully backed up database '{originaldbfile}' to '{backup_full_path}' using code {restorecode}.")
            self.logger.writelog(self.username, "System Backup", f"Successful backup to '{backup_full_path}'.")
            return True
        except IOError as e:
            print(f"Error during backup: {e}")
            self.logger.writelog(self.username, "System Backup", f"Failed: IOError - {e}")
            return False
        except Exception as e:
            print(f"An unexpected error occurred during backup: {e}")
            self.logger.writelog(self.username, "System Backup", f"Failed: Unexpected error - {e}")
            return False
        
    def restoresystembackup(self, restore_code, backup_id):
        print(f"\nRestoring System Backup")
        if not self.db_handler:
            print("Error: Database not connected. Can't restore backup.")
            self.logger.writelog(self.username, "Restore Backup Failed", "Database not connected.")
            return False

        code_records = self.db_handler.getdata('restore_codes', {'code': restore_code, 'backup_id': backup_id})
        if not code_records:
            print("Invalid restore code or backup identifier.")
            self.logger.writelog(self.username, "Restore Backup Failed", f"Invalid code '{restore_code}' or identifier '{backup_id}'.",
                            issuspicious=True)
            return False

        code_record = code_records[0]
        savedbackupfilename = code_record.get('backup_file_name')
        if not savedbackupfilename:
            print(f"Error: Restore record for backup identifier '{backup_id}' does not contain the actual backup filename. Restore failed.")
            self.logger.writelog(self.username, "Restore Backup Failed",
                            f"Missing 'backup_file_name' in record for identifier '{backup_id}'.")
            return False

        if code_record.get('is_revoked') == 1:
            print("This restore code has already been used.")
            self.logger.writelog(self.username, "Restore Backup Failed", f"Used/revoked code '{restore_code}'.", issuspicious=True)
            return False

        expirydate = code_record.get('expiry_date')
        if expirydate:
            expiry_date = datetime.date.fromisoformat(expirydate)
            if datetime.date.today() > expiry_date:
                print("This code has expired.")
                self.logger.writelog(self.username, "Restore Backup Failed", f"Expired code '{restore_code}'.", issuspicious=True)
                return False

        self.db_handler.updateexistingrecord('restore_codes', 'code', restore_code, {'is_revoked': 1})
        print("Restore code is valid. Proceeding with database restore...")

        backupdir = "backup"
        backup_file_to_restore_path = os.path.join(backupdir, savedbackupfilename)
        currentdbpath = self.db_handler.db_name
        originaldbname = os.path.basename(currentdbpath)

        if not os.path.exists(backup_file_to_restore_path):
            print(f"Error: Backup file not found at '{backup_file_to_restore_path}'. Restore failed.")
            self.logger.writelog(self.username, "Restore Backup Failed",
                            f"Backup file '{savedbackupfilename}' not found for identifier '{backup_id}'.")
            return False

        pre_restore_backup_filename = f"{os.path.splitext(originaldbname)[0]}_pre_restore_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.sqlite_bak"
        pre_restore_backup_path = os.path.join(backupdir, pre_restore_backup_filename)

        try:
            if os.path.exists(currentdbpath):
                print(f"Creating pre-restore backup of current database to '{pre_restore_backup_path}'...")
                shutil.copy2(currentdbpath, pre_restore_backup_path)
                print("Pre-restore backup created successfully.")
            else:
                print(f"Current database file '{currentdbpath}' does not exist. Skipping pre-restore backup.")

            print(f"Restoring database from '{backup_file_to_restore_path}' to '{currentdbpath}'...")
            shutil.copy2(backup_file_to_restore_path, currentdbpath)
            print("Database restore completed successfully.")
            self.logger.writelog(self.username, "System Backup Restore",
                            f"Successfully restored system using code '{restore_code}' for identifier '{backup_id}'. "
                            f"Current database replaced with '{savedbackupfilename}'. "
                            f"Pre-restore backup of original database saved to '{pre_restore_backup_path}'.")
            return True
        except IOError as e:
            print(f"Error during database restore: {e}")
            self.logger.writelog(self.username, "System Backup Restore Failed", f"IOError during restore: {e}")
            print("Restore failed due to IOError. Manual intervention might be required.")
            return False
        except Exception as e:
            print(f"An unexpected error occurred during database restore: {e}")
            self.logger.writelog(self.username, "System Backup Restore Failed", f"Unexpected error during restore: {e}")
            print("Restore failed due to unexpected error. Manual intervention might be required.")
            return False

    def addtraveller(self, travellerinfo):
        self.traveller_handler.add_traveller(travellerinfo, self.username)

    def updatetraveller(self, customerid, newinfo):
        self.traveller_handler.update_traveller(customerid, newinfo, self.username)

    def deletetraveller(self, customerid):
        self.traveller_handler.delete_traveller(customerid, self.username)

    def searchtraveller(self, query):
        return self.traveller_handler.search_traveller(query, self.username)

    def addscooter(self, scooterinfo):
        self.scooter_handler.add_scooter(scooterinfo, self.username)

    def updatescooter(self, serialnumber, newinfo, serviceengineer=False):
        self.scooter_handler.update_scooter(serialnumber, newinfo, self.username)

    def deletescooter(self, serialnumber):
        self.scooter_handler.delete_scooter(serialnumber, self.username)

    def getscooterinfo(self, query):
        return self.scooter_handler.search_scooter(query, self.username)

    def mark_scooter_out_of_service(self, serial_number, reason=""):
        self.scooter_handler.mark_scooter_out_of_service(serial_number, self.username, reason)

    def mark_scooter_in_service(self, serial_number):
        self.scooter_handler.mark_scooter_in_service(serial_number, self.username)

    def viewlogs(self):
        if self.logger:
            self.logger.show_logs_to_admin()
        else:
            print("Logger not available to view logs.")
            self.logger.writelog(self.username, "View Logs Failed", "Logger unavailable.")

    def viewallusers(self):
        print("\nAll System Users and Their Roles")
        if not self.db_handler:
            print("Error: Database not connected. Can't view users.")
            return

        users = self.db_handler.getdata('users')
        if not users:
            print("No users found in the system.")
            return

        for user in users:
            print(f"Username: {user.get('username')}, Role: {user.get('role')}")
        self.logger.writelog(self.username, "View Users", "Viewed all system users and roles.")

    def handle_menu_choice(self, choice, logger):
        if choice == '3':
            u = input("New System Admin Username: ")
            p = input("New System Admin Password: ")
            f = input("New System Admin First Name: ")
            l = input("New System Admin Last Name: ")
            self.addsystemadmin(u, p, f, l)
        elif choice == '4':
            u = input("Username of System Admin to update: ")
            new_f = input("New First Name (leave empty to skip): ")
            new_l = input("New Last Name (leave empty to skip): ")
            updatedata = {}
            if new_f: updatedata['first_name'] = new_f
            if new_l: updatedata['last_name'] = new_l
            self.changesystemadmininfo(u, updatedata)
        elif choice == '5':
            u = input("Username of System Admin to delete: ")
            self.deletesystemadmin(u)
        elif choice == '6':
            u = input("Username of System Admin to reset password: ")
            new_p = input("New password for System Admin: ")
            self.resetpasswordsysadmin(u, new_p)
        elif choice == '7':
            sa_user = input("Enter System Administrator username for restore code: ")
            self.createrestorecode(sa_user)
        elif choice == '8':
            code_to_revoke = input("Enter restore code to revoke: ")
            self.revokerestorecode(code_to_revoke)
        elif choice == '9':
            self.viewlogs()
        elif choice == '10':
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
        elif choice == '11':
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
        elif choice == '12':
            custid = input("Enter Traveller Customer ID to delete: ")
            self.deletetraveller(custid)
        elif choice == '13':
            s_info = {
                'serial_number': input("Scooter Serial Number (10-17 alphanumeric): "),
                'brand': input("Scooter Brand: "),
                'model': input("Scooter Model: "),
                'top_speed': float(input("Scooter Top Speed (km/h): ")),
                'battery_capacity': float(input("Scooter Battery Capacity (Wh): ")),
                'state_of_charge': float(input("Scooter State of Charge (%): ")),
                'target_range_soc': float(input("Scooter Target Range SoC (%): ")),
                'location': input("Scooter Location (latitude,longitude with 5 decimals, e.g., 51.92250,4.47917): "),
                'out_of_service_status': int(input("Scooter Out of Service (0 for No, 1 for Yes): ")),
                'mileage': float(input("Scooter Mileage (km): ")),
                'last_maintenance_date': input("Scooter Last Maintenance Date (YYYY-MM-DD): ")
            }
            self.addscooter(s_info)
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
            self.updatescooter(serial, updatedata, serviceengineer=False)
        elif choice == '15':
            serial = input("Enter Scooter Serial Number to delete: ")
            self.deletescooter(serial)
        elif choice == '16':
            code = self.createrestorecode('superadmin')
            self.makebackup(code)
        elif choice == '17':
            code = input("Enter restore code: ")
            b_id = input("Enter backup ID: ")
            self.restoresystembackup(code,b_id)
        else:
            print("That's not a valid option. Please try again.")

    def show_menu(self):
        print("1. Change My Password") #works
        print("2. Log Out")
        print("3. Add New System Administrator")
        print("4. Update System Administrator Info")
        print("5. Delete System Administrator")
        print("6. Reset System Administrator Password")
        print("7. Generate Restore Code for System Admin Backup")
        print("8. Revoke Restore Code")
        print("9. View All System Logs")
        print("10. Add New Traveller (Like System Admin)")
        print("11. Update Traveller Info (Like System Admin)")
        print("12. Delete Traveller (Like System Admin)")
        print("13. Add New Scooter (Like System Admin)")
        print("14. Update Scooter Info (Like System Admin)")
        print("15. Delete Scooter (Like System Admin)")
        print("16. Make backup")
        print("17. Restore backup from backup")