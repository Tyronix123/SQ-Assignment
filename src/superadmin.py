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
import zipfile


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
                username = input("Username (8-10 chars, must start with a letter or _, allowed: a-z, 0-9, _, ', .): ")
                password = input("Password (12-30 chars, must include lowercase, uppercase, digit, special char: ")
                firstname = input("First name: ")
                lastname = input("Last name: ")

        username = validated_user_data["username"]
        password = validated_user_data["password"]
        firstname = validated_user_data["first_name"]
        lastname = validated_user_data["last_name"]
        role = validated_user_data["role"]

        all_users = self.db_handler.getdata('users')
        if any(u['username'].lower() == username.lower() for u in all_users):
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
            if decrypted_username.lower() == usernametochange.lower() and user['role'] == role:
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
                if any(u['username'].lower() == new_username.lower() for u in all_users):
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
            print("You are deleting your own account. This will log you out and permanently remove access.")
            confirm = input("Are you absolutely sure you want to delete your account? Type 'yes' to confirm: ")

            if confirm == 'yes':
                self.logger.writelog(
                    self.username,
                    f"Delete {role} (Self)",
                    f"Deleted own account ({username_to_delete}).",
                    issuspicious=False
                )
                self.db_handler.deleterecord('users', 'username', username_to_delete)
                print("Your account has been deleted.")
                self.logout()
                return True
            else:
                print("Account deletion cancelled.")
                self.logger.writelog(
                    self.username,
                    f"Delete {role} (Self) Cancelled",
                    f"Attempt to delete own account ({username_to_delete}) was cancelled by user.",
                    issuspicious=False
                )
                return False

        all_users_raw = self.db_handler.getrawdata('users')
        target_user = None

        for user in all_users_raw:
            try:
                decrypted_username = self.db_handler.decryptdata(user['username'])
                if decrypted_username.lower() == username_to_delete.lower() and user.get('role') == role:
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
            f"Are you certain you want to delete {role} '{username_to_delete}'? This cannot be undone. (type 'yes' to confirm): ")
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
            if user['username'].lower() == username_reset.lower() and user['role'] == role:
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

    def list_users_by_role(self, role):
        users = self.db_handler.get_users_by_role(role)
        
        if not users:
            print(f"No {role}s found.")
            self.logger.writelog(self.username, "List users by role", f"No {role}s found")
            return []

        print(f"{role}s:")
        for idx, user in enumerate(users, start=1):
            print(f"{idx}. {user['first_name']} {user['last_name']} (Username: {user['username']})")
        
        self.logger.writelog(self.username, f"List {role}s", f"Listed {len(users)} {role}s")
        return users
    
    def select_user_from_list(self, user_list, prompt_message="Select a user by number:"):
        try:
            selection = int(input(prompt_message))
            if 1 <= selection <= len(user_list):
                return user_list[selection - 1]
            else:
                print("Invalid selection.")
                self.logger.writelog(self.username, "User Selection Failed", "Invalid selection number", issuspicious=True)
                return None
        except ValueError:
            print("Please enter a valid number.")
            self.logger.writelog(self.username, "User Selection Failed", "Non-integer input during selection", issuspicious=True)
            return None

    def addsystemadmin(self):
        u = input("New System Admin Username (8-10 chars, must start with a letter or _, allowed: a-z, 0-9, _, ', .): ")
        p = input("New System Admin Password (12-30 chars, must include lowercase, uppercase, digit, special char): ")
        f = input("New System Admin First Name: ")
        l = input("New System Admin Last Name: ")
        if self._manage_user_account(u, p, f, l, "SystemAdministrator", "Creating a New System Administrator"):
            if self._create_user_record(u, p, f, l, "SystemAdministrator"):
                print("System Administrator was successfully added")
                self.logger.writelog(self.username, "Add System Admin", f"New System Admin '{u}' created.")

    def changesystemadmininfo(self):
        if self.role == "SuperAdministrator":
            system_admins = self.list_users_by_role("SystemAdministrator")
            if not system_admins:
                return

            selected_admin = self.select_user_from_list(system_admins, "Select a system administrator by number: ")
            if not selected_admin:
                return
            current_username = selected_admin['username']
        else:
            current_username = self.username

        print("\nLeave a field empty to skip updating it.")
        new_u = input("New Username (8‑10 chars, must start with a letter or _, allowed: a‑z, 0‑9, _, ', .): ")
        new_f = input("New First Name: ")
        new_l = input("New Last Name: ")

        data = {}
        if new_u: data['username']   = new_u
        if new_f: data['first_name'] = new_f
        if new_l: data['last_name']  = new_l

        if data:
            self._update_user_info(current_username, data, "SystemAdministrator")
            self.logger.writelog(self.username, "Update SystemAdmin", f"Updated {list(data.keys())} for '{current_username}'")
        else:
            print("No changes provided. Nothing was updated.")
            self.logger.writelog(self.username, "Update SystemAdmin Skipped", f"No changes for '{current_username}'")

    def deletesystemadmin(self):
        if self.role == "SuperAdministrator":
            system_admins = self.list_users_by_role("SystemAdministrator")
            if not system_admins:
                return

            selected_admin = self.select_user_from_list(system_admins, "Select a system administrator to delete by number: ")
            if not selected_admin:
                self.logger.writelog(self.username, "Delete SystemAdmin Failed", "Invalid or no selection made", issuspicious=True)
                return

            sysadmin_to_delete = selected_admin['username']
        else:
            sysadmin_to_delete = self.username
            
        self._delete_user(sysadmin_to_delete, "SystemAdministrator", "Can't delete Super Administrator account")
        self.logger.writelog(self.username, "Delete SystemAdmin", f"Deleted system administrator: {sysadmin_to_delete}")
    
    def resetpasswordsysadmin(self):
        system_admins = self.list_users_by_role("SystemAdministrator")
        if not system_admins:
            return

        selected_admin = self.select_user_from_list(system_admins, "Select a system administrator to reset password by number: ")
        if not selected_admin:
            return

        usernamereset = selected_admin['username']
        newpassword = input("New password for System Admin (12-30 chars, must include lowercase, uppercase, digit, special char): ")

        self._reset_password(usernamereset, newpassword, "SystemAdministrator")
        self.logger.writelog(self.username, "Reset Password", f"Reset password for system administrator: {usernamereset}")

    def createrestorecode(self):
        print("Do you want to create a restore code for:")
        print("1. Yourself")
        print("2. A System Administrator")

        choice = input("Enter 1 or 2: ").strip()

        if choice == "1":
            target_username = self.username
        elif choice == "2":
            system_admins = self.list_users_by_role("SystemAdministrator")
            if not system_admins:
                print("No system administrators found.")
                self.logger.writelog(self.username, "Generate Restore Code Failed", "No system administrators found", issuspicious=True)
                return

            print("Select a System Administrator:")
            for idx, admin in enumerate(system_admins, start=1):
                print(f"{idx}. {admin['first_name']} {admin['last_name']} (Username: {admin['username']})")

            selected_admin = self.select_user_from_list(system_admins, "Select a system administrator to create a restore code for: ")
            if not selected_admin:
                return         
            target_username = selected_admin['username']

        else:
            print("Invalid choice.")
            self.logger.writelog(self.username, "Generate Restore Code Failed", "Invalid choice input", issuspicious=True)
            return

        print(f"\nGenerating Restore Code for Administrator: {target_username}")

        if not self.db_handler:
            print("Error: Database not connected.")
            self.logger.writelog(self.username, "Generate Restore Code Failed", "Database not connected", issuspicious=True)
            return

        all_users_raw = self.db_handler.getrawdata('users')
        creator_raw   = None
        target_raw    = None

        for row in all_users_raw:
            try:
                uname = self.db_handler.decryptdata(row['username'])
            except Exception:
                continue

            if uname == self.username:
                creator_raw = row
            if uname == target_username:
                target_raw  = row

        if not creator_raw:
            print("Creator record not found – DB inconsistent.")
            self.logger.writelog(self.username, "Generate Restore Code Failed", "Creator record not found", issuspicious=True)
            return

        allowed_roles = {"SystemAdministrator", "SuperAdministrator"}
        if not target_raw or target_raw["role"] not in allowed_roles:
            print(f"Error: '{target_username}' is not an eligible administrator.")
            self.logger.writelog(
                self.username,
                "Generate Restore Code Failed",
                f"'{target_username}' ineligible for restore-code",
                issuspicious=True,
            )
            return

        restore_code = secrets.token_urlsafe(16)
        backup_id    = secrets.token_hex(8)
        expiry_date  = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()

        try:
            self.db_handler.addnewrecord(
                "restore_codes",
                {
                    "code"            : restore_code,
                    "backup_id"       : backup_id,
                    "backup_file_name": None,
                    "created_by"      : creator_raw["username"],
                    "for_user"        : target_raw["username"],
                    "expiry_date"     : expiry_date,
                    "used"            : 0,
                },
            )
            print(
                f"\nRestore‑code created for '{target_username}'.\n"
                f"  Code       : {restore_code}\n"
                f"  Backup ID  : {backup_id}\n"
                f"  Expires    : {expiry_date}\n"
                "  (one‑time use only)"
            )
            self.logger.writelog(
                self.username,
                "Generate Restore Code",
                f"Code for '{target_username}', backup ID {backup_id}",
            )
            return restore_code

        except Exception as e:
            print(f"Could not generate restore code: {e}")
            self.logger.writelog(
                self.username, "Generate Restore Code Failed", str(e), issuspicious=True
            )
            return

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

    def makebackup(self):
        print("\n--- Initiating System Backup ---")

        restore_codes = self.db_handler.getdata('restore_codes', {'used': 0})
        if not restore_codes:
            print("No available restore codes found.")
            return

        print("\nAvailable Restore Codes:")
        for idx, rc in enumerate(restore_codes, start=1):
            print(
                f"{idx}. Code: {rc['code']} | For: {self.db_handler.decryptdata(rc['for_user'])} | "
                f"Created By: {self.db_handler.decryptdata(rc['created_by'])} | Expiry: {rc['expiry_date']}"
            )
        try:
            selected = int(input("\nSelect a restore code by number: ")) - 1
            if selected < 0 or selected >= len(restore_codes):
                print("Invalid selection.")
                return
            restorecode = restore_codes[selected]['code']
            restore_for_user = restore_codes[selected]['for_user']
            is_revoked = restore_codes[selected].get('used', 0)
        except ValueError:
            print("Invalid input.")
            return

        if is_revoked == 1:
            print("Selected restore code is revoked.")
            self.logger.writelog(self.username, "Backup Attempt Failed", f"Restore code '{restorecode}' is revoked", issuspicious=True)
            return

        if self.username != restore_for_user and self.username == 'superadmin':
            print("Superadmin cannot make a backup for another system administrator.")
            self.logger.writelog(self.username, "Backup Attempt Failed", f"Unauthorized backup attempt for '{restore_for_user}'", issuspicious=True)
            return

        dbpath = self.db_handler.db_name
        if not os.path.exists(dbpath):
            print(f"Database not found at '{dbpath}'.")
            self.logger.writelog(self.username, "Backup Failed", f"Database not found at {dbpath}", issuspicious=True)
            return

        backupdir = os.path.join("src", "backup")
        os.makedirs(backupdir, exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{timestamp}.zip"
        backup_full_path = os.path.join(backupdir, backup_filename)

        try:
            with zipfile.ZipFile(backup_full_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(dbpath, arcname=os.path.basename(dbpath))

            self.db_handler.updateexistingrecord('restore_codes', 'code', restorecode, {
                'backup_file_name': backup_filename,
            })

            print(f"\nBackup completed successfully: {backup_filename}")
            self.logger.writelog(self.username, "System Backup", f"Backup zip created at '{backup_full_path}' using restore code '{restorecode}'")
        except Exception as e:
            print(f"\nBackup failed: {e}")
            self.logger.writelog(self.username, "System Backup Failed", f"Exception: {e}", issuspicious=True)


        
    def restoresystembackup(self) -> None:
        print("\n--- Restore a System Backup ---")

        if not self.db_handler:
            print("Error: Database not connected.")
            self.logger.writelog(self.getmyusername(),
                                "Restore Backup Failed",
                                "DB not connected")
            return

        all_codes = self.db_handler.getdata("restore_codes", {"used": 0})
        if not all_codes:
            print("No available restore codes.")
            return

        user_codes = []
        today = datetime.date.today()

        for rc in all_codes:
            try:
                code_for_user = self.db_handler.decryptdata(rc["for_user"])
                if code_for_user != self.username:
                    continue

                expiry = datetime.date.fromisoformat(rc["expiry_date"])
                if today > expiry:
                    continue

                user_codes.append(rc)
            except Exception:
                continue

        if not user_codes:
            print("You have no valid restore codes (or all are expired).")
            return

        print("\nAvailable Restore Codes:")
        for idx, rc in enumerate(user_codes, 1):
            print(
                f"{idx}. Code: {rc['code']} | "
                f"Created By: {self.db_handler.decryptdata(rc['created_by'])} | "
                f"Expiry: {rc['expiry_date']}"
            )

        try:
            selection = int(input("\nSelect a restore-code by number: ")) - 1
            if selection not in range(len(user_codes)):
                print("Invalid selection.")
                return
        except ValueError:
            print("Invalid input.")
            return

        code_record   = user_codes[selection]
        restore_code  = code_record["code"]
        backup_id     = code_record["backup_id"]
        backup_file   = code_record["backup_file_name"]

        if not backup_file:
            print("Backup file name missing in restore‑code record.")
            return

        backup_dir  = os.path.join("src", "backup")
        backup_path = os.path.join(backup_dir, backup_file)
        db_path     = self.db_handler.db_name

        if not os.path.exists(backup_path):
            print(f"Backup file not found at '{backup_path}'.")
            self.logger.writelog(self.getmyusername(),
                                "Restore Backup Failed",
                                f"Missing file {backup_file}")
            return

        pre_copy = os.path.join(
            backup_dir,
            f"pre_restore_{datetime.datetime.now():%Y%m%d_%H%M%S}.db",
        )
        try:
            shutil.copy2(db_path, pre_copy)
            print(f"Saved current DB to '{pre_copy}'.")
        except Exception as e:
            print(f"Could not create pre‑restore copy: {e}")
            self.logger.writelog(self.getmyusername(),
                                "Restore Backup Failed",
                                f"Pre‑copy error {e}")
            return

        try:
            with zipfile.ZipFile(backup_path, "r") as zf:
                zf.extract(os.path.basename(db_path), path=os.path.dirname(db_path))

            print("Marking restore code as used...")    
            self.db_handler.updateexistingrecord('restore_codes', 'code', restore_code, {
                'used': 1,
                'backup_file_name': backup_file
            })

            print("Database restored successfully.")
            self.logger.writelog(
                self.getmyusername(),
                "Restore Backup",
                f"Restored from {backup_file} ({backup_id}), "
                f"pre‑copy at {pre_copy}",
            )
        except Exception as e:
            print(f"Restore failed: {e}")
            self.logger.writelog(self.getmyusername(),
                                "Restore Backup Failed",
                                str(e))


    def addtraveller(self):
        self.traveller_handler.add_traveller(self.username)

    def updatetraveller(self):
        self.traveller_handler.update_traveller(self.username)

    def deletetraveller(self, ):
        self.traveller_handler.delete_traveller(self.username)

    def searchtraveller(self):
        return self.traveller_handler.search_traveller(self.username)

    def addscooter(self):
        self.scooter_handler.add_scooter(self.username)

    def updatescooter(self):
        if self.role == "ServiceEngineer":
            self.scooter_handler.updatescooterlimit(self.username)
        else:
            self.scooter_handler.update_scooter(self.username)

    def deletescooter(self):
        self.scooter_handler.delete_scooter(self.username)

    def searchscooter(self):
        return self.scooter_handler.search_scooter(self.username)

    def addserviceengineer(self):
        u = input("New Service Engineer Username (must be between 8-10 char): ")
        p = input("New Service Engineer Password (12-30 characters, must include lowercase, uppercase, digit, special character): ")
        f = input("New Service Engineer First Name: ")
        l = input("New Service Engineer Last Name: ")
        if self._manage_user_account(u, p, f, l, "ServiceEngineer", "Creating a New Service Engineer"):
            if self._create_user_record(u, p, f, l, "ServiceEngineer"):
                print("Service Engineer was successfully added")
                self.logger.writelog(self.username, "Added Service Engineer", f"New Service Engineer '{u}' created.")

    def updateserviceengineerinfo(self):
        service_engineers = self.list_users_by_role("ServiceEngineer")
        if not service_engineers:
            return

        selected_engineer = self.select_user_from_list(service_engineers, "Select a service engineer to update their info: ")
        if not selected_engineer:
            return         
        username_to_change = selected_engineer['username']

        print("\nLeave a field empty to skip updating it.")
        new_u = input("New Username (8-10 chars, must start with a letter or _, allowed: a-z, 0-9, _, ', .): ")
        new_f = input("New First Name (leave empty to skip): ")
        new_l = input("New Last Name (leave empty to skip): ")

        data = {}
        if new_u: data['username'] = new_u
        if new_f: data['first_name'] = new_f
        if new_l: data['last_name'] = new_l

        if data:
            self._update_user_info(username_to_change, data, "ServiceEngineer")
            self.logger.writelog(self.username, "Update Service Engineer Info", f"Updated fields {list(data.keys())} for '{username_to_change}'")
        else:
            print("No changes provided. Nothing was updated.")
            self.logger.writelog(self.username, "Update Service Engineer Info Skipped", f"No changes provided for '{username_to_change}'")

    def deleteserviceengineer(self):
        service_engineers = self.list_users_by_role("ServiceEngineer")
        if not service_engineers:
            return

        selected_engineer = self.select_user_from_list(service_engineers, "Select a service engineer to delete: ")
        if not selected_engineer:
            return         
        username_to_delete = selected_engineer['username']

        self._delete_user(username_to_delete, "ServiceEngineer", "ERROR: System admin can't be deleted using this function.")
        self.logger.writelog(self.username, "Delete Service Engineer", f"Deleted service engineer '{username_to_delete}'")

    def resetengineerpassword(self):
        service_engineers = self.list_users_by_role("ServiceEngineer")
        if not service_engineers:
            return

        selected_engineer = self.select_user_from_list(service_engineers, "Select a service engineer to reset their password: ")
        if not selected_engineer:
            return         
        username_to_reset = selected_engineer['username']

        newpassword = input("New password for Service Engineer (12-30 chars, must include lowercase, uppercase, digit, special char): ")
        
        self._reset_password(username_to_reset, newpassword, "ServiceEngineer")
        self.logger.writelog(self.username, "Reset Service Engineer Password", f"Reset password for service engineer '{username_to_reset}'")

    def viewlogs(self):
        if self.logger:
            self.logger.show_logs_to_admin()
        else:
            print("Logger not available to view logs.")

    def viewallusers(self):
        if not self.db_handler:
            print("Error: Database not connected. Can't view users.")
            return

        users = self.db_handler.getdata('users')
        if not users:
            print("No users found in the system.")
            return

        print("\n--- List of Users and Roles ---")
        for user in users:
            username = user.get('username', 'Unknown')
            role = user.get('role', 'No Role Assigned')
            print(f"Username: {username} | Role: {role}")
        self.logger.writelog(self.username, "View Users", "Viewed all system users and roles.")

    def handle_menu_choice(self, choice):
        if   choice == '3':  self.addsystemadmin()
        elif choice == '4':  self.changesystemadmininfo()
        elif choice == '5':  self.deletesystemadmin()
        elif choice == '6':  self.resetpasswordsysadmin()
        elif choice == '7':  self.createrestorecode()
        elif choice == '8':  self.revokerestorecode()
        elif choice == '9':  self.addserviceengineer()
        elif choice == '10': self.updateserviceengineerinfo()
        elif choice == '11': self.deleteserviceengineer()
        elif choice == '12': self.resetengineerpassword()
        elif choice == '13': self.viewallusers()
        elif choice == '14': self.viewlogs()
        elif choice == '15': self.makebackup()
        elif choice == '16': self.restoresystembackup()
        elif choice == '17': self.addtraveller()
        elif choice == '18': self.updatetraveller()
        elif choice == '19': self.deletetraveller()
        elif choice == '20': self.searchtraveller()
        elif choice == '21': self.addscooter()
        elif choice == '22': self.updatescooter()
        elif choice == '23': self.deletescooter()
        elif choice == '24': self.searchscooter()
        else: print("That's not a valid option. Please try again.")


    def show_menu(self):
        print("1. Change My Password")
        print("2. Log Out")
        print("3. Add New System Administrator")
        print("4. Update System Administrator Info")
        print("5. Delete System Administrator")
        print("6. Reset System Administrator Password")
        print("7. Generate Restore Code for System Admin Backup")
        print("8. Revoke Restore Code")
        print("9. Add New Service Engineer")
        print("10. Update Service Engineer Info")
        print("11. Delete Service Engineer")
        print("12. Reset Service Engineer Password")
        print("13. View All Users")
        print("14. View All System Logs")
        print("15. Make Backup")
        print("16. Restore Backup from Backup")
        print("17. Add New Traveller")
        print("18. Update Traveller Info")
        print("19. Delete Traveller")
        print("20. Search Traveller")
        print("21. Add New Scooter")
        print("22. Update Scooter Info")
        print("23. Delete Scooter")
        print("24. Search Scooter")
