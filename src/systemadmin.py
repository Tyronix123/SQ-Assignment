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
<<<<<<< HEAD
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
=======
        if choice == '3':
            new_u = input("New Username (leave empty to skip, (8-10 chars, must start with a letter or _, allowed: a-z, 0-9, _, ', .)): ")
            new_f = input("New First Name (leave empty to skip): ")
            new_l = input("New Last Name (leave empty to skip): ")
            
            data = {}
            if new_u: data['username'] = new_u
            if new_f: data['first_name'] = new_f
            if new_l: data['last_name'] = new_l

            self.changesystemadmininfo(self.username, data)        
        elif choice == '4':
            self.deletesystemadmin(self.username)
        elif choice == '5':
            u = input("New Service Engineer Username (must be between 8-10 char): ")
            p = input("New Service Engineer Password (12-30 characters, must include lowercase, uppercase, digit, special character): ")
            f = input("New Service Engineer First Name: ")
            l = input("New Service Engineer Last Name: ")
            self.addserviceengineer(u, p, f, l)
        elif choice == '6':
            u = input("Username of Service Engineer to update: ")
            nf = input("New First Name (leave empty to skip): ")
            nl = input("New Last Name (leave empty to skip): ")
            nu = input("New Username (leave empty to skip, 8-10 chars, must start with a letter or _, allowed: a-z, _, ', .): ")
            data = {}
            if nf: data['first_name'] = nf
            if nl: data['last_name'] = nl
            if nu: data['username'] = nu
            self.updateserviceengineerinfo(u, data)
        elif choice == '7':
            u = input("Username of Service Engineer to delete: ")
            self.deleteserviceengineer(u)
        elif choice == '8':
            u = input("Username of Service Engineer to reset password: ")
            np = input("New password for Service Engineer (12-30 chars, must include lowercase, uppercase, digit, special char): ")
            self.resetengineerpassword(u, np)
        elif choice == '9':
            self.addtraveller()
        elif choice == '10':
            self.updatetraveller()
        elif choice == '11':
            self.deletetraveller()
        elif choice == '12':
            self.searchtraveller()
        elif choice == '13':
            self.addscooter()
        elif choice == '14':
            self.updatescooter()
        elif choice == '15':
            self.deletescooter()
        elif choice == '16':
            self.searchscooter()
        elif choice == '17':
            self.makebackup()
        elif choice == '18':
            self.restoresystembackup()
        elif choice == '19':
            self.viewlogs()
        elif choice == '20':
            self.viewallusers()

        else:
            print("That's not a valid option. Please try again.")
>>>>>>> 8f4348ff2208f4ca75f29c87418e154ec9c02e45

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