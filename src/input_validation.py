import re

class InputValidation:
    @staticmethod
    def is_valid_name(name):
        if not isinstance(name, str): return False
        return re.fullmatch(r"[A-Za-z][A-Za-z\s\-']{1,}", name) is not None

    @staticmethod
    def is_valid_date(date_string):
        return re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_string) is not None

    @staticmethod
    def is_valid_gender(gender):
        if not isinstance(gender, str): return False
        return gender.lower() in ["male", "female"]

    @staticmethod
    def is_valid_streetname(streetname):
        if not isinstance(streetname, str): return False
        return re.fullmatch(r"[A-Za-z][A-Za-z\s\.\-']{1,}", streetname) is not None

    @staticmethod
    def is_valid_housenumber(housenumber):
        if not isinstance(housenumber, str): return False
        return re.fullmatch(r"\d+[ ]?[a-zA-Z\-]?$", housenumber) is not None

    @staticmethod
    def is_valid_zip(zip_code):
        return re.fullmatch(r"\d{4}[A-Z]{2}", zip_code) is not None

    @staticmethod
    def is_valid_city(city, VALID_CITIES):
        if not isinstance(city, str): return False
        return city.lower() in [c.lower() for c in VALID_CITIES]
    
    @staticmethod
    def is_valid_email(email):
        return re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email) is not None

    @staticmethod
    def is_valid_phone(phone):
        return re.fullmatch(r"\d{8}", phone) is not None

    @staticmethod
    def is_valid_license(license_number):
        return re.fullmatch(r"[A-Z]{1,2}\d{7}", license_number) is not None

    @staticmethod
    def is_valid_username(username: str) -> bool:
        if not isinstance(username, str): return False
        if not (8 <= len(username) <= 10): return False
        if not re.match(r"^[a-z_]", username.lower()): return False
        if not re.fullmatch(r"[a-z0-9_'.]{8,10}", username.lower()): return False
        return True

    @staticmethod
    def is_valid_password(password):
        if not isinstance(password, str): return False
        if not (12 <= len(password) <= 30): return False
        if not any(char.isupper() for char in password): return False
        if not any(char.islower() for char in password): return False
        if not any(char.isdigit() for char in password): return False
    
        special_chars = "[~!@#$%&_\-+=`|\\(){}\[\]:;'<>,.?/]"
        if not any(char in special_chars for char in password): return False
        return True
