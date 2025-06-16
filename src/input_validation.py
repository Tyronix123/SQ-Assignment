import re
from datetime import datetime

class InputValidation:
    def __init__(self, valid_roles=None, valid_cities=None):
        self.valid_roles = valid_roles or ['SuperAdministrator', 'SystemAdministrator', 'ServiceEngineer']
        self.valid_cities = valid_cities or []

    def is_valid_name(self, name):
        if not isinstance(name, str): return False
        return re.fullmatch(r"[A-Za-z][A-Za-z\s\-']{1,}", name) is not None

    def is_valid_date(self, date_string):
        return re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_string) is not None

    def is_valid_gender(self, gender):
        if not isinstance(gender, str): return False
        return gender.lower() in ["male", "female"]

    def is_valid_streetname(self, streetname):
        if not isinstance(streetname, str): return False
        return re.fullmatch(r"[A-Za-z][A-Za-z\s\.\-']{1,}", streetname) is not None

    def is_valid_housenumber(self, housenumber):
        if not isinstance(housenumber, str): return False
        return re.fullmatch(r"\d+[ ]?[a-zA-Z\-]?$", housenumber) is not None

    def is_valid_zip(self, zip_code):
        return re.fullmatch(r"\d{4}[A-Z]{2}", zip_code) is not None

    def is_valid_city(self, city):
        if not isinstance(city, str): return False
        return city.lower() in [c.lower() for c in self.valid_cities]
    
    def is_valid_email(self, email):
        return re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email) is not None

    def is_valid_phone(self, phone):
        return re.fullmatch(r"^\d{8}$", phone) is not None

    def is_valid_license(self, license_number):
        return re.fullmatch(r"[A-Z]{1,2}\d{7}", license_number) is not None

    def is_valid_username(self, username: str) -> bool:
        if not isinstance(username, str): return False
        if not (8 <= len(username) <= 10): return False
        if not re.match(r"^[a-z_]", username.lower()): return False
        if not re.fullmatch(r"[a-z0-9_'.]{8,10}", username.lower()): return False
        return True

    def is_valid_password(self, password):
        if not isinstance(password, str): return False
        if not (12 <= len(password) <= 30): return False
        if not any(char.isupper() for char in password): return False
        if not any(char.islower() for char in password): return False
        if not any(char.isdigit() for char in password): return False
    
        special_chars = "[~!@#$%&_\-+=`|\\(){}\[\]:;'<>,.?/]"
        if not any(char in special_chars for char in password): return False
        return True

    def is_valid_role(self, role):
        return role in self.valid_roles

    def is_valid_brand(self, brand: str) -> bool:
        return isinstance(brand, str) and len(brand.strip()) > 0

    def is_valid_model(self, model: str) -> bool:
        return isinstance(model, str) and len(model.strip()) > 0

    def is_valid_serial_number(self, serial: str) -> bool:
        return bool(re.fullmatch(r'[A-Za-z0-9]{10,17}', serial))

    def is_valid_top_speed(self, speed: float) -> bool:
        return isinstance(speed, (int, float)) and 5 <= speed <= 100

    def is_valid_battery_capacity(self, capacity: float) -> bool:
        return isinstance(capacity, (int, float)) and 50 <= capacity <= 5000

    def is_valid_soc(self, soc: float) -> bool:
        return isinstance(soc, (int, float)) and 0 <= soc <= 100

    def is_valid_target_soc_range(self, min_soc: float, max_soc: float) -> bool:
        return (
            self.is_valid_soc(min_soc) and
            self.is_valid_soc(max_soc) and
            min_soc < max_soc
        )

    def is_valid_location(self, latitude: float, longitude: float) -> bool:
        return (
            51.85 <= latitude <= 52.00 and
            4.35 <= longitude <= 4.55 and
            self.has_five_decimals(latitude) and
            self.has_five_decimals(longitude)
        )

    def has_five_decimals(self, number: float) -> bool:
        try:
            return len(str(number).split('.')[-1]) >= 5
        except Exception:
            return False

    def is_valid_out_of_service(self, status: bool) -> bool:
        return isinstance(status, bool)

    def is_valid_mileage(self, mileage: float) -> bool:
        return isinstance(mileage, (int, float)) and mileage >= 0

    def is_valid_maintenance_date(self, date_str: str) -> bool:
        try:
            datetime.fromisoformat(date_str)
            return True
        except ValueError:
            return False
