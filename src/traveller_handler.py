from datetime import datetime
from input_validation import *
from db_handler import insert_traveller

VALID_CITIES = [
    "Rotterdam", "Amsterdam", "Utrecht", "Delft", "The Hague",
    "Leiden", "Eindhoven", "Breda", "Zwolle", "Haarlem"
]

def add_new_traveller():
    print("\n--- Add New Traveller ---")

    first_name = input("First name: ")
    while not is_valid_name(first_name):
        print("Invalid first name.")
        first_name = input("First name: ")

    last_name = input("Last name: ")
    while not is_valid_name(last_name):
        print("Invalid last name.")
        last_name = input("Last name: ")

    birthday = input("Birthday (YYYY-MM-DD): ")
    while not is_valid_date(birthday):
        print("Invalid date format.")
        birthday = input("Birthday (YYYY-MM-DD): ")

    gender = input("Gender (male/female): ")
    while not is_valid_gender(gender):
        print("Invalid gender.")
        gender = input("Gender (male/female): ")

    street_name = input("Street name: ")
    while not is_valid_streetname(street_name):
        print("Invalid street name.")
        street_name = input("Street name: ")

    house_number = input("House number: ")
    while not is_valid_housenumber(house_number):
        print("Invalid house number.")
        house_number = input("House number: ")

    zip_code = input("Zip code (DDDDXX): ")
    while not is_valid_zip(zip_code):
        print("Invalid zip code format.")
        zip_code = input("Zip code (DDDDXX): ")

    city = input("City name: ")
    while not is_valid_city(city, VALID_CITIES):
        print("Invalid city.")
        print(", ".join(VALID_CITIES))
        city = input("City name: ")

    email = input("Email address: ")
    while not is_valid_email(email):
        print("Invalid email.")
        email = input("Email address: ")

    phone = input("Phone number: ")
    while not is_valid_phone(phone):
        print("Phone number must be 8 digits.")
        phone = input("Phone number: ")
    phone = f"+31-6-{phone}"

    license_number = input("Driving license number: ")
    while not is_valid_license(license_number):
        print("Invalid format.")
        license_number = input("Driving license number: ")

    registration_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    insert_traveller(first_name, last_name, birthday, gender, street_name, house_number, zip_code, city, email, phone, license_number, registration_date)
    print("Traveller successfully added.")

