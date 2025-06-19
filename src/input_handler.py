from input_validation import InputValidation


class InputHandler:
    def __init__(self, input_validation: InputValidation, valid_cities):
        self.input_validation = input_validation
        self.valid_cities = valid_cities

    def clean_first_name(self, value: str) -> str:
        value = value.strip()
        if not self.input_validation.is_valid_name(value):
            raise ValueError("Invalid first name.")
        return value.title()

    def clean_last_name(self, value: str) -> str:
        value = value.strip()
        if not self.input_validation.is_valid_name(value):
            raise ValueError("Invalid last name.")
        return value.title()

    def clean_username(self, value: str) -> str:
        v = value.strip()
        if not self.input_validation.is_valid_username(v):
            raise ValueError("Invalid username (must be 8‑10 chars, lowercase letters, numbers, _, ', . allowed).")
        return v.lower()

    def clean_password(self, value: str) -> str:
        if not self.input_validation.is_valid_password(value):
            raise ValueError("Invalid password (must be 12‑30 chars, upper, lower, digit, special char required).")
        return value

    def clean_role(self, value: str) -> str:
        v = value.strip()
        if not self.input_validation.is_valid_role(v):
            raise ValueError("Invalid role.")
        return v

    def clean_birthday(self, value: str) -> str:
        if not self.input_validation.is_valid_date(value.strip()):
            raise ValueError("Invalid birthday format (expected YYYY-MM-DD).")
        return value.strip()

    def clean_gender(self, value: str) -> str:
        g = value.strip().lower()
        if not self.input_validation.is_valid_gender(g):
            raise ValueError("Invalid gender (must be 'male' or 'female').")
        return g.capitalize()

    def clean_street(self, value: str) -> str:
        value = value.strip()
        if not self.input_validation.is_valid_streetname(value):
            raise ValueError("Invalid street name.")
        return value.title()

    def clean_house_number(self, value: str) -> str:
        v = value.strip()
        if not self.input_validation.is_valid_housenumber(v):
            raise ValueError("Invalid house number.")
        return v

    def clean_zip(self, value: str) -> str:
        v = value.strip().upper()
        if not self.input_validation.is_valid_zip(v):
            raise ValueError("Invalid zip code.")
        return v

    def clean_city(self, value: str) -> str:
        v = value.strip()
        if not self.input_validation.is_valid_city(v):
            raise ValueError("Invalid city.")
        return v.title()

    def clean_email(self, value: str) -> str:
        v = value.strip()
        if not self.input_validation.is_valid_email(v):
            raise ValueError("Invalid email address.")
        return v.lower()

    def clean_phone(self, value: str) -> str:
        v = value.strip()
        if not self.input_validation.is_valid_phone(v):
            raise ValueError("Invalid phone number (must be 8 digits).")
        return "+31-6-" + v

    def clean_license(self, value: str) -> str:
        v = value.strip().upper()
        if not self.input_validation.is_valid_license(v):
            raise ValueError("Invalid driving license number.")
        return v

    def clean_brand(self, value: str) -> str:
        v = value.strip()
        if not self.input_validation.is_valid_brand(v):
            raise ValueError("Invalid scooter brand.")
        return v.title()

    def clean_model(self, value: str) -> str:
        v = value.strip()
        if not self.input_validation.is_valid_model(v):
            raise ValueError("Invalid scooter model.")
        return v

    def clean_serial_number(self, value: str) -> str:
        v = value.strip().upper()
        if not self.input_validation.is_valid_serial_number(v):
            raise ValueError("Invalid serial number (must be 10 to 17 alphanumeric characters).")
        return v

    def clean_top_speed(self, value) -> str:
        try:
            speed = int(value)
        except ValueError:
            raise ValueError("Top speed must be a valid number.")

        if not self.input_validation.is_valid_top_speed(speed):
            raise ValueError("Invalid top speed (must be between 5 and 100 km/h).")

        return value

    def clean_battery_capacity(self, value) -> str:
        try:
            capacity = int(value)
        except ValueError:
            raise ValueError("Battery capacity must be a whole number in Wh.")

        if not self.input_validation.is_valid_battery_capacity(capacity):
            raise ValueError("Invalid battery capacity (must be positive in Wh).")

        return capacity

    def clean_soc(self, value) -> str:
        try:
            soc = int(value)
        except ValueError:
            raise ValueError("State-of-charge must be a whole number (0-100).")

        if not self.input_validation.is_valid_soc(soc):
            raise ValueError("Invalid state of charge (must be 0-100).")

        return value

    def clean_target_soc_range(self, min_soc: str, max_soc: str) -> str:
        try:
            min_soc = int(min_soc)
            max_soc = int(max_soc)
        except ValueError:
            raise ValueError("Target SoC values must be whole numbers.")

        if not self.input_validation.is_valid_soc(min_soc) or not self.input_validation.is_valid_soc(max_soc):
            raise ValueError("Target SoC values must be between 0 and 100.")

        if min_soc >= max_soc:
            raise ValueError("Minimum SoC must be less than maximum SoC.")

        return f"{min_soc}-{max_soc}"


    def clean_location(self, lat_str, long_str) -> str:
        try:
            latitude = round(float(lat_str), 5)
            longitude = round(float(long_str), 5)
            lat_formatted = f"{latitude:.5f}"
            long_formatted = f"{longitude:.5f}"
        except ValueError:
            raise ValueError("Latitude and Longitude must be valid numbers.")
        
        if not self.input_validation.is_valid_location(lat_formatted, long_formatted):
            raise ValueError("Invalid GPS coordinates.")

        return f"{lat_formatted}, {long_formatted}"

    def clean_out_of_service(self, value: str) -> str:
        if not self.input_validation.is_valid_out_of_service(value):
            raise ValueError("Out-of-service status must be 0 or 1.")
        return value

    def clean_mileage(self, value) -> str:
        try:
            mileage = int(value)
        except ValueError:
            raise ValueError("Mileage must be a whole number in km.")
        
        if not self.input_validation.is_valid_mileage(mileage):
            raise ValueError("Invalid mileage (must be positive).")
        
        return value

    def clean_last_maintenance_date(self, value: str) -> str:
        if not self.input_validation.is_valid_date(value):
            raise ValueError("Invalid date format for last maintenance (expected YYYY-MM-DD).")
        return value

    def handle_traveller_data(self, data: dict) -> dict:
        return {
            "first_name":             self.clean_first_name(data.get("first_name", "")),
            "last_name":              self.clean_last_name(data.get("last_name", "")),
            "birthday":               self.clean_birthday(data.get("birthday", "")),
            "gender":                 self.clean_gender(data.get("gender", "")),
            "street_name":            self.clean_street(data.get("street_name", "")),
            "house_number":           self.clean_house_number(data.get("house_number", "")),
            "zip_code":               self.clean_zip(data.get("zip_code", "")),
            "city":                   self.clean_city(data.get("city", "")),
            "email":          self.clean_email(data.get("email", "")),
            "mobile_phone":           self.clean_phone(data.get("mobile_phone", "")),
            "driving_license": self.clean_license(data.get("driving_license", "")),
        }
    
    def handle_scooter_data(self, data: dict) -> dict:
        location_dict = data.get("location", {"latitude": 0.0, "longitude": 0.0})
        lat_str = str(location_dict.get("latitude", 0.0))
        long_str = str(location_dict.get("longitude", 0.0))

        target_range = data.get("soc_range", {"target_min_soc": 0, "target_max_soc": 100})
        target_min_soc = target_range.get("target_min_soc", 0)
        target_max_soc = target_range.get("target_max_soc", 100)

        return {
            "brand":                 self.clean_brand(data.get("brand", "")),
            "model":                 self.clean_model(data.get("model", "")),
            "serial_number":         self.clean_serial_number(data.get("serial_number", "")),
            "top_speed":             self.clean_top_speed(data.get("top_speed", 0)),
            "battery_capacity":      self.clean_battery_capacity(data.get("battery_capacity", 0)),
            "soc":                   self.clean_soc(data.get("soc", 0)),
            "soc_range":      self.clean_target_soc_range(target_min_soc, target_max_soc),
            "location":              self.clean_location(lat_str, long_str),
            "out_of_service":        self.clean_out_of_service(data.get("out_of_service", False)),
            "mileage":               self.clean_mileage(data.get("mileage", 0)),
            "last_maintenance": self.clean_last_maintenance_date(data.get("last_maintenance", ""))
        }



    def handle_user_data(self, data: dict) -> dict:
        return {
            "username":  self.clean_username(data.get("username", "")),
            "password":  self.clean_password(data.get("password", "")),
            "first_name": self.clean_first_name(data.get("firstname", "")),
            "last_name":  self.clean_last_name(data.get("lastname", "")),
            "role":      self.clean_role(data.get("role", "")),
        }
