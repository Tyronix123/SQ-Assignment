class SystemAdministrator(SuperAdministrator):
    def __init__(self, username, password_hash, firstname, lastname, regdate=None, db_manager=None, logger=None):
        super().__init__(username, password_hash, firstname, lastname, regdate, db_manager, logger)

    def addserviceengineer(self, username, password, firstname, lastname):
        if self._manage_user_account(username, password, firstname, lastname, "Service Engineer", "Creating a New Service Engineer"):
            if self._create_user_record(username, password, firstname, lastname, "ServiceEngineer"):
                print("Service Engineer was successfully added")
                self.logmyaction("Added Service Engineer", f"New Service Engineer '{username}' created.")

    def updateserviceengineerinfo(self, usernametochange, new_info):
        self._update_user_info(usernametochange, new_info, "ServiceEngineer")

    def deleteserviceengineer(self, usernametodelete):
        self._delete_user(usernametodelete, "ServiceEngineer", "ERROR: System admin cant be deleted using this function.")

    def resetengineerpassword(self, usernamereset, newpassword):
        self._reset_password(usernamereset, newpassword, "ServiceEngineer")

    def systemadminmenu(self):
        self.show_common_menu()
        print("System Admin Specific")
        print("3. Add New Service Engineer")
        print("4. Update Service Engineer Info")
        print("5. Delete Service Engineer")
        print("6. Reset Service Engineer Password")
        print("7. Add New Traveller")
        print("8. Update Traveller Info")
        print("9. Delete Traveller")
        print("10. Search Travellers")
        print("11. Add New Scooter")
        print("12. Update Scooter Info")
        print("13. Delete Scooter")
        print("14. Search Scooters")
        print("15. Make System Backup (Needs Super Admin Code)")
        print("16. Restore System Backup (Needs Super Admin Code)")
        print("17. View All System Logs")
        print("18. View All System Users and Roles")
        print("19. Check for Suspicious Activities (Logs)")