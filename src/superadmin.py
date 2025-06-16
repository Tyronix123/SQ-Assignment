import datetime
import hashlib
import secrets
import os
import shutil
from input_validation import InputValidation
from traveller_handler import TravellerHandler
from scooter_handler import ScooterHandler

class SuperAdministrator(User):
    def __init__(self, username, password_hash, firstname, lastname, regdate=None, db_manager=None, logger=None):
        super().__init__(username, password_hash, firstname, lastname)
        self.db_manager = db_manager
        self.logger = logger
        self.traveller_handler = TravellerHandler(db_manager, logger, self.dutch_cities)
        self.scooter_handler = ScooterHandler(db_manager, logger)
        self.dutch_cities = ["Amsterdam", "Rotterdam", "Utrecht", "The Hague", "Eindhoven",
                            "Groningen", "Maastricht", "Leiden", "Haarlem", "Delft"]

    def logmyaction(self, description, additionalinfo="", issuspicious=False):
        if self.logger:
            self.logger.writelog(self.username, description, additionalinfo, issuspicious)
        else:
            print(f"ERROR: no logger connected: {description} - {additionalinfo}")

    # Common user management methods
    def _manage_user_account(self, username, password, firstname, lastname, role, action_description):
        print(f"\n{action_description}")
        if not self.db_manager:
            print("Error: Database not connected.")
            return False

        if not InputValidation.is_valid_username(username):
            print("Username is not valid. Please use only letters and numbers (3-20 characters long).")
            self.logmyaction(f"{role} creation Failed", f"username format for '{username}' is incorrect",
                           issuspicious=True)
            return False

        if password and not InputValidation.is_valid_password(password):
            print("Password has to meet criteria. Please try again")
            self.logmyaction(f"{role} creation Failed", f"Weak password for '{username}'", issuspicious=True)
            return False

        existing_user = self.db_manager.getdata('users', {'username': username})
        if existing_user:
            print(f"Username: '{username}' is already taken. Please pick a different one.")
            self.logmyaction(f"{role} creation Failed", f"Username '{username}' already in use",
                           issuspicious=True)
            return False

        return True

    def _create_user_record(self, username, password, firstname, lastname, role):
        hashedpassword = self.makepasswordhash(password) if password else None
        try:
            user_data = {
                'username': username,
                'first_name': InputValidation.clean_up_input(firstname),
                'last_name': InputValidation.clean_up_input(lastname),
                'user_role': role,
                'registration_date': datetime.date.today().isoformat()
            }
            if hashedpassword:
                user_data['password_hash'] = hashedpassword
            
            self.db_manager.addnewrecord('users', user_data)
            return True
        except Exception as e:
            print(f"something went wrong while adding the {role}: {e}")
            self.logmyaction(f"Add {role} Failed", f"Error: {e}", issuspicious=True)
            return False

    def _update_user_info(self, usernametochange, newinfo, role):
        print(f"\n-- Changing {role} Details for: {usernametochange} --")
        if not self.db_manager:
            print("Error: Database not connected. Can't update admin.")
            return False

        adminrecords = self.db_manager.getdata('users', {'username': usernametochange})
        if not adminrecords or adminrecords[0].get('user_role') != role:
            print(f"Error: {role} '{usernametochange}' not found or isn't a {role}.")
            self.logmyaction(f"Update {role} Failed",
                           f"Target '{usernametochange}' not found or wrong role", issuspicious=True)
            return False

        cleanedinfo = {k: InputValidation.clean_up_input(str(v)) for k, v in newinfo.items()}

        if 'user_role' in cleanedinfo:
            print("Security Alert! Tried to change user role. That's not allowed here.")
            del cleanedinfo['user_role']
            self.logmyaction(f"Update {role} Failed", f"Attempted role change for '{usernametochange}'",
                           issuspicious=True)

        if not cleanedinfo:
            print("No new information was provided to update. Nothing changed.")
            return False

        try:
            self.db_manager.updateexistingrecord('users', 'username', usernametochange, cleanedinfo)
            print(f"{role} '{usernametochange}' updated successfully!")
            self.logmyaction(f"Update {role}", f"Details for '{usernametochange}' updated.")
            return True
        except Exception as e:
            print(f"Couldn't update {role} '{usernametochange}'. Error: {e}")
            self.logmyaction(f"Update {role} Failed", f"Error updating '{usernametochange}': {e}",
                           issuspicious=True)
            return False

    def _delete_user(self, username_to_delete, role, self_deletion_message):
        print(f"\n--- Deleting {role}: {username_to_delete} ---")
        if not self.db_manager:
            print("Error: Database not connected.")
            return False

        if username_to_delete == self.username:
            print(self_deletion_message)
            self.logmyaction(f"Delete {role} Failed", f"Tried to delete self ({username_to_delete})",
                           issuspicious=True)
            return False

        target_admin_records = self.db_manager.getdata('users', {'username': username_to_delete})
        if not target_admin_records or target_admin_records[0].get('user_role') != role:
            print(f"Error: {role} '{username_to_delete}' not found or isn't a {role}.")
            self.logmyaction(f"Delete {role} Failed",
                           f"Target '{username_to_delete}' not found or wrong role", issuspicious=True)
            return False

        confirmation = input(
            f"Are you certain you want to delete {role} '{username_to_delete}'? This cannot be undone. (type 'yes' to confirm): ").lower()
        if confirmation != 'yes':
            print("Deleting cancelled.")
            self.logmyaction(f"Deletion {role} Cancelled", f"Cancelled deletion of '{username_to_delete}'")
            return False

        try:
            self.db_manager.deleterecord('users', 'username', username_to_delete)
            print(f"{role} '{username_to_delete}' has been deleted.")
            self.logmyaction(f"Delete {role}", f"{role} '{username_to_delete}' deleted.")
            return True
        except Exception as e:
            print(f"Problem occurred. Couldn't delete: '{username_to_delete}'. Error: {e}")
            self.logmyaction(f"Delete {role} Failed", f"Error deleting '{username_to_delete}': {e}",
                           issuspicious=True)
            return False

    def _reset_password(self, username_reset, newpassword, role):
        print(f"\n-- {role} password reset: {username_reset} --")
        if not self.db_manager:
            print("Error: Database is not available.")
            return False

        target_admin_records = self.db_manager.getdata('users', {'username': username_reset})
        if not target_admin_records or target_admin_records[0].get('user_role') != role:
            print(f"Error: {role} '{username_reset}' not found.")
            self.logmyaction(f"Reset {role} Password Failed",
                           f"Target '{username_reset}' not found or wrong role", issuspicious=True)
            return False

        if not InputValidation.is_valid_password(newpassword):
            print("The new password isn't strong enough.")
            self.logmyaction(f"Reset {role} Password Failed", f"Bad new password for '{username_reset}'",
                           issuspicious=True)
            return False

        hashed_password = self.makepasswordhash(newpassword)
        try:
            self.db_manager.updateexistingrecord('users', 'username', username_reset, {'password_hash': hashed_password})
            print(f"Password for {role} '{username_reset}' has been successfully reset!")
            self.logmyaction(f"Reset {role} Password",
                           f"Password for '{username_reset}' reset.")
            return True
        except Exception as e:
            print(f"A problem happened while resetting password for '{username_reset}'. Error: {e}")
            self.logmyaction(f"Reset {role} Password Failed",
                           f"Error resetting password for '{username_reset}': {e}", issuspicious=True)
            return False

    # Super Admin specific methods
    def addsystemadmin(self, username, password, firstname, lastname):
        if self._manage_user_account(username, password, firstname, lastname, "System Administrator", "Creating a New System Administrator"):
            if self._create_user_record(username, password, firstname, lastname, "SystemAdministrator"):
                print("System Administrator was successfully added")
                self.logmyaction("Add System Admin", f"New System Admin '{username}' created.")

    def changesystemadmininfo(self, usernametochange, newinfo):
        self._update_user_info(usernametochange, newinfo, "SystemAdministrator")

    def deletesystemadmin(self, sysadmin_to_delete):
        self._delete_user(sysadmin_to_delete, "SystemAdministrator", "Can't delete Super Administrator account")

    def resetpasswordsysadmin(self, usernamereset, newpassword):
        self._reset_password(usernamereset, newpassword, "SystemAdministrator")

    def createrestorecode(self, sysadminusername):
        print(f"\nGenerating Restore Code for System Administrator: {sysadminusername}")
        if not self.db_manager:
            print("Error: Database is not ready. Can't generate restore code.")
            return "ERROR"
        
        if sysadminusername != 'superadmin':
            target_admin_records = self.db_manager.getdata('users', {'username': sysadminusername})
            if not target_admin_records or target_admin_records[0].get('user_role') != 'SystemAdministrator':
                print(f"Error: System Administrator '{sysadminusername}' not found or isn't a System Administrator. Cannot generate restore code.")
                self.logmyaction("Generate Restore Code Failed",
                               f"Target '{sysadminusername}' not found/wrong role", issuspicious=True)
                return "ERROR"

        restore_code = secrets.token_urlsafe(16)
        backup_id = secrets.token_hex(8)
        expiry_date = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()

        try:
            self.db_manager.addnewrecord(
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
            self.logmyaction("Generate Restore Code",
                           f"Generated code for '{sysadminusername}', backup ID: {backup_id}")
            return restore_code
        except Exception as e:
            print(f"Couldn't generate restore code. Error: {e}")
            self.logmyaction("Generate Restore Code Failed", f"Error: {e}", issuspicious=True)
            return "ERROR"

    # Backup and restore methods
    def makebackup(self, restorecode):
        print("\nInitiating System Backup")
        dbpath = self.db_manager.db_name
        backupdir = "backup"

        existingtraveller = self.db_manager.getdata('restore_codes', {'code': restorecode})
        if not existingtraveller:
            print("No such restore code in system.")
            self.logmyaction("Attempted restore code usage.", f"Restore code '{restorecode}' not found",
                            issuspicious=True)
            return False
        currentcode = existingtraveller[0]
        if currentcode.get('is_revoked') == 1:
            print("Code is already revoked in system.")
            self.logmyaction("Attempted revoked code usage.", f"Attempted use revoked code '{restorecode}'",
                            issuspicious=True)
            return False

        if not os.path.exists(backupdir):
            try:
                os.makedirs(backupdir)
                print(f"Created backup directory: '{backupdir}'")
            except OSError as e:
                print(f"Error creating backup directory '{backupdir}': {e}")
                self.logmyaction("System Backup", f"Failed: Error creating directory - {e}")
                return False

        if not os.path.exists(dbpath):
            print(f"Error: Database file not found at '{dbpath}'. Backup failed.")
            self.logmyaction("System Backup", f"Failed: Database file '{dbpath}' not found.")
            return False

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        originaldbfile = os.path.basename(dbpath)
        backup_filename = f"{os.path.splitext(originaldbfile)[0]}_{timestamp}.sqlite_bak"
        backup_full_path = os.path.join(backupdir, backup_filename)

        try:
            shutil.copy2(dbpath, backup_full_path)
            self.db_manager.updateexistingrecord('restore_codes', 'code', restorecode,
                                               {'backup_file_name': backup_filename})
            print(f"Successfully backed up database '{originaldbfile}' to '{backup_full_path}' using code {restorecode}.")
            self.logmyaction("System Backup", f"Successful backup to '{backup_full_path}'.")
            return True
        except IOError as e:
            print(f"Error during backup: {e}")
            self.logmyaction("System Backup", f"Failed: IOError - {e}")
            return False
        except Exception as e:
            print(f"An unexpected error occurred during backup: {e}")
            self.logmyaction("System Backup", f"Failed: Unexpected error - {e}")
            return False

    def restoresystembackup(self, restore_code, backup_id):
        print(f"\nRestoring System Backup")
        if not self.db_manager:
            print("Error: Database not connected. Can't restore backup.")
            self.logmyaction("Restore Backup Failed", "Database not connected.")
            return False

        code_records = self.db_manager.getdata('restore_codes', {'code': restore_code, 'backup_id': backup_id})
        if not code_records:
            print("Invalid restore code or backup identifier.")
            self.logmyaction("Restore Backup Failed", f"Invalid code '{restore_code}' or identifier '{backup_id}'.",
                            issuspicious=True)
            return False

        code_record = code_records[0]
        savedbackupfilename = code_record.get('backup_file_name')
        if not savedbackupfilename:
            print(f"Error: Restore record for backup identifier '{backup_id}' does not contain the actual backup filename. Restore failed.")
            self.logmyaction("Restore Backup Failed",
                            f"Missing 'backup_file_name' in record for identifier '{backup_id}'.")
            return False

        if code_record.get('is_revoked') == 1:
            print("This restore code has already been used.")
            self.logmyaction("Restore Backup Failed", f"Used/revoked code '{restore_code}'.", issuspicious=True)
            return False

        expirydate = code_record.get('expiry_date')
        if expirydate:
            expiry_date = datetime.date.fromisoformat(expirydate)
            if datetime.date.today() > expiry_date:
                print("This code has expired.")
                self.logmyaction("Restore Backup Failed", f"Expired code '{restore_code}'.", issuspicious=True)
                return False

        self.db_manager.updateexistingrecord('restore_codes', 'code', restore_code, {'is_revoked': 1})
        print("Restore code is valid. Proceeding with database restore...")

        backupdir = "backup"
        backup_file_to_restore_path = os.path.join(backupdir, savedbackupfilename)
        currentdbpath = self.db_manager.db_name
        originaldbname = os.path.basename(currentdbpath)

        if not os.path.exists(backup_file_to_restore_path):
            print(f"Error: Backup file not found at '{backup_file_to_restore_path}'. Restore failed.")
            self.logmyaction("Restore Backup Failed",
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
            self.logmyaction("System Backup Restore",
                            f"Successfully restored system using code '{restore_code}' for identifier '{backup_id}'. "
                            f"Current database replaced with '{savedbackupfilename}'. "
                            f"Pre-restore backup of original database saved to '{pre_restore_backup_path}'.")
            return True
        except IOError as e:
            print(f"Error during database restore: {e}")
            self.logmyaction("System Backup Restore Failed", f"IOError during restore: {e}")
            print("Restore failed due to IOError. Manual intervention might be required.")
            return False
        except Exception as e:
            print(f"An unexpected error occurred during database restore: {e}")
            self.logmyaction("System Backup Restore Failed", f"Unexpected error during restore: {e}")
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
        self.scooter_handler.update_scooter(serialnumber, newinfo, self.username, serviceengineer)

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
            self.logmyaction("View Logs Failed", "Logger unavailable.")

    def viewallusers(self):
        print("\nAll System Users and Their Roles")
        if not self.db_manager:
            print("Error: Database not connected. Can't view users.")
            return

        users = self.db_manager.getdata('users')
        if not users:
            print("No users found in the system.")
            return

        for user in users:
            print(
                f"Username: {user.get('username')}, Role: {user.get('user_role')}, Name: {user.get('first_name')} {user.get('last_name')}")
        self.logmyaction("View Users", "Viewed all system users and roles.")

    def superadminmenu(self):
        self.show_common_menu()
        print("--- Super Admin Only ---")
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