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
    def __init__(self, dutch_cities, username, password_hash, role, firstname, lastname, reg_date=None, 
                 db_handler: DBHandler = None, logger: Logger = None, input_validation: InputValidation = None, input_handler: InputHandler = None,
                 traveller_handler: TravellerHandler = None, scooter_handler: ScooterHandler = None):
        self.dutch_cities = dutch_cities
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
        self.traveller_handler = traveller_handler
        self.scooter_handler = scooter_handler

    def _manage_user_account(self, username, password, firstname, lastname, role, action_details):
        print(f"\n{action_details}")
        
        if not self.db_handler:
            print("Error: Database not connected.")
            return False

        while True:
            user_data = {
                "username":  username,
                "password":  password,
                "firstname": firstname,
                "lastname":  lastname,
                "role":      role,
            }

            try:
                validated_user_data = self.input_handler.handle_user_data(user_data)
                break
            except ValueError as e:
                print(f"Fout: {e}")
                print("Voer de gegevens opnieuw in.\n")
                username = input("Gebruikersnaam: ")
                password = input("Wachtwoord: ")
                firstname = input("Voornaam: ")
                lastname = input("Achternaam: ")

        username = validated_user_data["username"]
        password = validated_user_data["password"]
        firstname = validated_user_data["first_name"]
        lastname = validated_user_data["last_name"]
        role = validated_user_data["role"]

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

    def _update_user_info(self, usernametochange: str, newinfo: dict, role: str) -> bool:
        print(f"\n-- Changing {role} Details for: {usernametochange} --")

        if not self.db_handler:
            print("Error: Database not connected. Can't update user.")
            return False

        all_users_raw = self.db_handler.getrawdata('users')
        target_user = None

        for user in all_users_raw:
            try:
                decrypted_username = self.db_handler.decryptdata(user['username'])
            except Exception:
                continue
            if decrypted_username == usernametochange and user['role'] == role:
                target_user = user
                break

        if not target_user:
            print(f"Error: {role} '{usernametochange}' not found or wrong role.")
            self.logger.writelog(self.getmyusername(), f"Update {role} Failed", f"Target '{usernametochange}' not found or wrong role", issuspicious=True)
            return False

        cleaned = {}
        try:
            if 'first_name' in newinfo:
                cleaned['first_name'] = self.input_handler.clean_first_name(newinfo['first_name'])
            if 'last_name' in newinfo:
                cleaned['last_name'] = self.input_handler.clean_last_name(newinfo['last_name'])
            if 'username' in newinfo:
                new_username = self.input_handler.clean_username(newinfo['username'])

                all_users = self.db_handler.getdata('users')
                if any(u['username'] == new_username for u in all_users):
                    print(f"Error: Username '{new_username}' already exists.")
                    self.logger.writelog(self.getmyusername(), f"Update {role} Failed",
                                        f"Duplicate username '{new_username}'", issuspicious=True)
                    return False

                cleaned['username'] = new_username

        except ValueError as ve:
            print(f"Validation error: {ve}. Update cancelled.")
            self.logger.writelog(self.getmyusername(), f"Update {role} Failed",
                                f"Validation error for '{usernametochange}': {ve}", issuspicious=True)
            return False

        if not cleaned:
            print("No valid info provided to update. Nothing changed.")
            return False

        try:
            encrypted_old_username = target_user['username']

            self.db_handler.updateexistingrecord('users', 'username', encrypted_old_username, cleaned)
            print(f"{role} '{usernametochange}' updated successfully!")
            self.logger.writelog(self.getmyusername(), f"Update {role}",
                                f"Details updated for '{usernametochange}'")
            return True
        except Exception as e:
            print(f"Couldn't update {role} '{usernametochange}'. Error: {e}")
            self.logger.writelog(self.getmyusername(), f"Update {role} Failed",
                                f"Error updating '{usernametochange}': {e}", issuspicious=True)
            return False

    def _delete_user(self, username_to_delete, role, self_deletion_message):
        print(f"\n--- Deleting {role}: {username_to_delete} ---")
        if not self.db_handler:
            print("Error: Database not connected.")
            return False

        if username_to_delete == self.username:
            print(self_deletion_message)
            self.logger.writelog(self.username, f"Delete {role} Failed", f"Tried to delete self ({username_to_delete})", issuspicious=True)
            return False

        all_users_raw = self.db_handler.getrawdata('users')
        target_user = None

        for user in all_users_raw:
            try:
                decrypted_username = self.db_handler.decryptdata(user['username'])
                if decrypted_username == username_to_delete and user.get('role') == role:
                    target_user = user
                    break
            except Exception:
                continue

        if not target_user:
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
            encrypted_username = target_user['username']
            self.db_handler.deleterecord('users', 'username', encrypted_username)
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

        all_users = self.db_handler.getdata('users')
        target_user = None

        for user in all_users:
            if user['username'] == username_reset and user['role'] == role:
                target_user = user
                break

        if not target_user:
            print(f"Error: {role} '{username_reset}' not found.")
            self.logger.writelog(
                self.username,
                f"Reset {role} Password Failed",
                f"Target '{username_reset}' not found or wrong role",
                issuspicious=True
            )
            return False

        if not self.input_validation.is_valid_password(newpassword):
            print("The new password isn't strong enough.")
            self.logger.writelog(
                self.username,
                f"Reset {role} Password Failed",
                f"Bad new password for '{username_reset}'",
                issuspicious=True
            )
            return False

        hashed_password = self.makepasswordhash(newpassword)

        try:
            encrypted_username = self.db_handler.encryptdata(username_reset)
            self.db_handler.updateexistingrecord(
                'users',
                'username',
                encrypted_username,
                {'password_hash': hashed_password}
            )
            print(f"Password for {role} '{username_reset}' has been successfully reset!")
            self.logger.writelog(
                self.username,
                f"Reset {role} Password",
                f"Password for '{username_reset}' reset."
            )
            return True
        except Exception as e:
            print(f"A problem happened while resetting password for '{username_reset}'. Error: {e}")
            self.logger.writelog(
                self.username,
                f"Reset {role} Password Failed",
                f"Error resetting password for '{username_reset}': {e}",
                issuspicious=True
            )
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

    def createrestorecode(self, sysadminusername: str):
        print(f"\nGenerating Restore Code for System Administrator: {sysadminusername}")

        if not self.db_handler:
            print("Error: Database not connected. Can't generate restore code.")
            return "ERROR"

        all_users_raw = self.db_handler.getrawdata('users')
        target_user_raw = None
        creator_user_raw = None

        
        for user in all_users_raw:
            try:
                uname = self.db_handler.decryptdata(user['username'])
                if uname == self.username:
                    creator_user_raw = user
                    break
            except Exception:
                continue


        for user in all_users_raw:
            try:
                uname = self.db_handler.decryptdata(user['username'])
                if uname == sysadminusername and user.get('role') == 'SystemAdministrator':
                    target_user_raw = user
                    break
            except Exception:
                continue

        if not target_user_raw:
            print(f"Error: System Administrator '{sysadminusername}' not found or wrong role.")
            self.logger.writelog(self.getmyusername(),
                                "Generate Restore Code Failed",
                                f"Target '{sysadminusername}' not found / wrong role",
                                issuspicious=True)
            return "ERROR"

        restore_code  = secrets.token_urlsafe(16)
        backup_id     = secrets.token_hex(8)
        expiry_date   = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()

        try:
            self.db_handler.addnewrecord(
                'restore_codes',
                {
                    'code'           : restore_code,
                    'backup_id'      : backup_id,
                    'backup_file_name': None,
                    'created_by'     : creator_user_raw['username'], 
                    'for_user'       : target_user_raw['username'],
                    'expiry_date'    : expiry_date,
                    'used'           : 0
                }
            )
            print(f"Restore code for '{sysadminusername}' created.\n"
                f"Code : {restore_code}\n"
                f"Valid : until {expiry_date}\n"
                f"Backup ID : {backup_id}\n"
                "(one‑time use only)")
            self.logger.writelog(self.getmyusername(),
                                "Generate Restore Code",
                                f"Code generated for '{sysadminusername}', backup ID {backup_id}")
            return restore_code

        except Exception as e:
            print(f"Could not generate restore code. Error: {e}")
            self.logger.writelog(self.getmyusername(),
                                "Generate Restore Code Failed",
                                str(e), issuspicious=True)
            return "ERROR"


    def revokerestorecode(self, code_to_revoke: str | None = None) -> bool:
        if not self.db_handler:
            print("Error: Database not connected. Cannot revoke code.")
            self.logger.writelog(self.username, "Revoke Code Failed", "DB not connected", issuspicious=True)
            return False

        if not code_to_revoke:
            today = datetime.date.today().isoformat()
            restore_codes = self.db_handler.getdata(
                "restore_codes",
                {"used": 0}
            )
            restore_codes = [rc for rc in restore_codes if rc["expiry_date"] >= today]

            if not restore_codes:
                print("No active (unused & unexpired) restore codes found.")
                return False

            print("\nActive Restore Codes:")
            for idx, rc in enumerate(restore_codes, start=1):
                print(
                    f"{idx}. Code: {rc['code']} | For: {self.db_handler.decryptdata(rc['for_user'])} | "
                    f"Created By: {self.db_handler.decryptdata(rc['created_by'])} | Expiry: {rc['expiry_date']}"
                )

            try:
                sel = int(input("\nSelect a code to revoke (number): ")) - 1
                if 0 <= sel < len(restore_codes):
                    code_to_revoke = restore_codes[sel]["code"]
                else:
                    print("Invalid selection.")
                    return False
            except ValueError:
                print("Invalid input.")
                return False

        print(f"\nRevoking restore code: {code_to_revoke}")
        records = self.db_handler.getdata("restore_codes", {"code": code_to_revoke})

        if not records:
            print("No such restore code in the system.")
            self.logger.writelog(
                self.username, "Revoke Code Failed", f"Code '{code_to_revoke}' not found", issuspicious=True
            )
            return False

        record = records[0]
        if record.get("used") == 1:
            print("This restore code is already revoked.")
            return False

        try:
            self.db_handler.updateexistingrecord(
                "restore_codes", "code", code_to_revoke, {"used": 1}
            )
            print("Restore code successfully revoked.")
            self.logger.writelog(
                self.username, "Revoke Code", f"Code '{code_to_revoke}' revoked."
            )
            return True
        except Exception as e:
            print(f"Could not revoke code. Error: {e}")
            self.logger.writelog(self.username, "Revoke Code Failed", str(e), issuspicious=True)
            return False

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

    def addserviceengineer(self, username, password, firstname, lastname):
        if self._manage_user_account(username, password, firstname, lastname, "ServiceEngineer", "Creating a New Service Engineer"):
            if self._create_user_record(username, password, firstname, lastname, "ServiceEngineer"):
                print("Service Engineer was successfully added")
                self.logger.writelog(self.username, "Added Service Engineer", f"New Service Engineer '{username}' created.")

    def updateserviceengineerinfo(self, usernametochange, new_info):
        self._update_user_info(usernametochange, new_info, "ServiceEngineer")

    def deleteserviceengineer(self, usernametodelete):
        self._delete_user(usernametodelete, "ServiceEngineer", "ERROR: System admin cant be deleted using this function.")

    def resetengineerpassword(self, usernamereset, newpassword):
        self._reset_password(usernamereset, newpassword, "ServiceEngineer")

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

    def handle_menu_choice(self, choice):
        if choice == '3':
            u = input("New System Admin Username: ")
            p = input("New System Admin Password: ")
            f = input("New System Admin First Name: ")
            l = input("New System Admin Last Name: ")
            self.addsystemadmin(u, p, f, l)

        elif choice == '4':
            u = input("Username of System Admin to update: ")
            new_u = input("New Username (leave empty to skip): ")
            new_f = input("New First Name (leave empty to skip): ")
            new_l = input("New Last Name (leave empty to skip): ")
            
            data = {}
            if new_u: data['username'] = new_u
            if new_f: data['first_name'] = new_f
            if new_l: data['last_name'] = new_l

            self.changesystemadmininfo(u, data)

        elif choice == '5':
            u = input("Username of System Admin to delete: ")
            self.deletesystemadmin(u)

        elif choice == '6':
            u = input("Username of System Admin to reset password: ")
            new_p = input("New password for System Admin: ")
            self.resetpasswordsysadmin(u, new_p)

        elif choice == '7':
            sa = input("Enter System Admin username for restore code: ")
            self.createrestorecode(sa)

        elif choice == '8':
            self.revokerestorecode()

        elif choice == '9':
            u = input("New Service Engineer Username: ")
            p = input("New Service Engineer Password: ")
            f = input("New Service Engineer First Name: ")
            l = input("New Service Engineer Last Name: ")
            self.addserviceengineer(u, p, f, l)

        elif choice == '10':
            u = input("Username of Service Engineer to update: ")
            nf = input("New First Name (leave empty to skip): ")
            nl = input("New Last Name (leave empty to skip): ")
            nu = input("New Username (leave empty to skip): ")
            data = {}
            if nf: data['first_name'] = nf
            if nl: data['last_name'] = nl
            if nu: data['username'] = nu
            self.updateserviceengineerinfo(u, data)

        elif choice == '11':
            u = input("Username of Service Engineer to delete: ")
            self.deleteserviceengineer(u)

        elif choice == '12':
            u = input("Username of Service Engineer to reset password: ")
            np = input("New password for Service Engineer: ")
            self.resetengineerpassword(u, np)

        elif choice == '13':
            self.viewlogs()

        elif choice == '14':
            code = self.createrestorecode('superadmin')
            self.makebackup(code)

        elif choice == '15':
            rc = input("Enter restore code: ")
            bid = input("Enter backup ID: ")
            self.restoresystembackup(rc, bid)

        elif choice == '16':
            tinfo = {
                'first_name': input("Traveller First Name: "),
                'last_name':  input("Traveller Last Name: "),
                'birthday':   input("Traveller Birthday (YYYY-MM-DD): "),
                'gender':     input("Traveller Gender: "),
                'street_name':input("Traveller Street Name: "),
                'house_number':input("Traveller House Number: "),
                'zip_code':   input("Traveller Zip Code (DDDDXX): "),
                'city':       input(f"Traveller City (choose from {', '.join(self.dutch_cities)}): "),
                'email':      input("Traveller Email Address: "),
                'mobile_phone': input("Traveller Mobile Phone (8 digits): "),
                'driving_license': input("Driving License Number (XXDDDDDDD or XDDDDDDDD): ")
            }
            self.addtraveller(tinfo)

        elif choice == '17':
            cid = input("Traveller ID to update: ")
            data = {}
            print("Enter new values (leave empty to skip):")
            em = input("New Email: ")
            if em: data['email'] = em
            ph = input("New Mobile Phone (8 digits): ")
            if ph:
                data['mobile_phone'] = "+31-6-" + ph if self.input_validation.is_valid_phone(ph) else ph
            zp = input("New Zip Code: ")
            if zp: data['zip_code'] = zp
            ct = input(f"New City (choose from {', '.join(self.dutch_cities)}): ")
            if ct: data['city'] = ct
            self.updatetraveller(cid, data)

        elif choice == '18':
            cid = input("Traveller ID to delete: ")
            self.deletetraveller(cid)

        elif choice == '19':
            sinfo = {
                'serial_number': input("Scooter Serial Number (10-17 alphanumeric): "),
                'brand': input("Scooter Brand: "),
                'model': input("Scooter Model: "),
                'top_speed': float(input("Top Speed (km/h): ")),
                'battery_capacity': float(input("Battery Capacity (Wh): ")),
                'state_of_charge': float(input("State of Charge (%): ")),
                'target_range_soc': float(input("Target Range SoC (%): ")),
                'location': input("Location (lat,long 5 dec): "),
                'out_of_service_status': int(input("Out of Service (0/1): ")),
                'mileage': float(input("Mileage (km): ")),
                'last_maintenance_date': input("Last Maintenance (YYYY-MM-DD): ")
            }
            self.addscooter(sinfo)

        elif choice == '20':
            sn = input("Scooter Serial Number to update: ")
            data = {}
            print("Enter new values (leave empty to skip):")
            soc = input("New SoC (%): ")
            if soc: data['state_of_charge'] = float(soc)
            loc = input("New Location (lat,long): ")
            if loc: data['location'] = loc
            oos = input("Out of Service (0/1): ")
            if oos: data['out_of_service_status'] = int(oos)
            mil = input("New Mileage (km): ")
            if mil: data['mileage'] = float(mil)
            lmd = input("New Last Maintenance Date (YYYY-MM-DD): ")
            if lmd: data['last_maintenance_date'] = lmd
            self.updatescooter(sn, data, serviceengineer=False)

        elif choice == '21':
            sn = input("Scooter Serial Number to delete: ")
            self.deletescooter(sn)
        else:
            print("That's not a valid option. Please try again.")


    def show_menu(self):
        print("1. Change My Password")
        print("2. Log Out")

        print("\n--- System Administrator Management ---")
        print("3. Add New System Administrator")
        print("4. Update System Administrator Info")
        print("5. Delete System Administrator")
        print("6. Reset System Administrator Password")

        print("\n--- Restore Code Management ---")
        print("7. Generate Restore Code for System Admin Backup")
        print("8. Revoke Restore Code")

        print("\n--- Service Engineer Management ---")
        print("9. Add New Service Engineer")
        print("10. Update Service Engineer Info")
        print("11. Delete Service Engineer")
        print("12. Reset Service Engineer Password")

        print("\n--- Logs & Backup ---")
        print("13. View All System Logs")
        print("14. Make Backup")
        print("15. Restore Backup from Backup")

        print("\n--- Shared Traveller & Scooter Management ---")
        print("16. Add New Traveller")
        print("17. Update Traveller Info")
        print("18. Delete Traveller")
        print("19. Add New Scooter")
        print("20. Update Scooter Info")
        print("21. Delete Scooter")
