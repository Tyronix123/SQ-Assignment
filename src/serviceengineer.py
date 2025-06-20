import datetime
import hashlib
import secrets
import re
from db_handler import DBHandler
from logger import Logger

from input_validation import InputValidation
from input_handler import InputHandler
from superadmin import SuperAdministrator
from traveller_handler import TravellerHandler
from scooter_handler import ScooterHandler
from user import User


class ServiceEngineer(SuperAdministrator):
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
        if choice == '3': self.updatescooter()
        elif choice == '4': self.searchscooter()
        else: print("That's not a valid option. Please try again.")

    def show_menu(self):
        print("1. Change My Password")
        print("2. Log Out")
        print("3. Update Scooter Info")
        print("4. Search Scooter")