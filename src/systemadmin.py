from superadmin import SuperAdministrator
import re
from input_validation import InputValidation
from db_handler import DBHandler
from logger import Logger
from input_handler import InputHandler
from traveller_handler import TravellerHandler
from scooter_handler import ScooterHandler

class SystemAdministrator(SuperAdministrator):
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

    def handle_menu_choice(self, choice):
        if choice == '3':    self.changesystemadmininfo()        
        elif choice == '4':  self.deletesystemadmin()
        elif choice == '5':  self.addserviceengineer()
        elif choice == '6':  self.updateserviceengineerinfo()
        elif choice == '7':  self.deleteserviceengineer()
        elif choice == '8':  self.resetengineerpassword()
        elif choice == '9':  self.addtraveller()
        elif choice == '10': self.updatetraveller()
        elif choice == '11': self.deletetraveller()
        elif choice == '12': self.searchtraveller()
        elif choice == '13': self.addscooter()
        elif choice == '14': self.updatescooter()
        elif choice == '15': self.deletescooter()
        elif choice == '16': self.searchscooter()
        elif choice == '17': self.makebackup()
        elif choice == '18': self.restoresystembackup()
        elif choice == '19': self.viewlogs()
        elif choice == '20': self.viewallusers()
        else: print("That's not a valid option. Please try again.")

    def show_menu(self):
        print("1. Change My Password")
        print("2. Log Out")
        print("3. Update Own Profile")
        print("4. Delete Own Account")
        print("5. Add New Service Engineer")
        print("6. Update Service Engineer Info")
        print("7. Delete Service Engineer")
        print("8. Reset Service Engineer Password")
        print("9. Add New Traveller")
        print("10. Update Traveller Info")
        print("11. Delete Traveller")
        print("12. Search Travellers")
        print("13. Add New Scooter")
        print("14. Update Scooter Info")
        print("15. Delete Scooter")
        print("16. Search Scooters")
        print("17. Make System Backup (Needs Super Admin Code)")
        print("18. Restore System Backup (Needs Super Admin Code)")
        print("19. View All System Logs")
        print("20. View All System Users and Roles")
        #print("19. Check for Suspicious Activities (Logs)")