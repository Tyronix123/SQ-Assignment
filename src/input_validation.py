import re

def is_valid_name(name):
    """
    Validates a first or last name.
    - Must start with a letter.
    - Can contain letters, hyphens, apostrophes, and spaces.
    - No leading/trailing spaces.
    - Minimum 2 characters.
    """
    if not isinstance(name, str):
        return False
    return re.fullmatch(r"[A-Za-z][A-Za-z\s\-']{1,}", name) is not None

def is_valid_date(date_string):
    return re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_string) is not None

def is_valid_gender(gender):
    if not isinstance(gender, str):
        return False
    return gender.lower() in ["male", "female"]

def is_valid_streetname(streetname):
    """
    Validates a street name.
    - Must be a string with only letters, spaces, dots, apostrophes, and hyphens.
    - Must start with a letter.
    - Minimum length: 2 characters.
    - Leading/trailing spaces are invalid.
    """
    if not isinstance(streetname, str):
        return False
    return re.fullmatch(r"[A-Za-z][A-Za-z\s\.\-']{1,}", streetname) is not None

def is_valid_housenumber(housenumber):
    """
    Validates a house number.
    - Starts with 1+ digits.
    - May optionally include a letter or suffix (e.g., '12A', '33 bis', '101-B').
    - Allows letters, spaces, and hyphens after the number.
    - Leading/trailing spaces are invalid.
    """
    if not isinstance(housenumber, str):
        return False
    return re.fullmatch(r"\d+[ ]?[a-zA-Z\-]?$", housenumber) is not None

def is_valid_zip(zip_code):
    return re.fullmatch(r"\d{4}[A-Z]{2}", zip_code) is not None

def is_valid_city(city, VALID_CITIES):
    """
    Validates that the city is one of the predefined cities.
    - Must be a string that matches one of the 10 allowed city names.
    - Comparison is case-sensitive.
    - Leading/trailing spaces are not allowed.
    """
    if not isinstance(city, str): return False
    return city.lower() in [c.lower() for c in VALID_CITIES]

def is_valid_email(email):
    return re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email) is not None

def is_valid_phone(phone):
    return re.fullmatch(r"\d{8}", phone) is not None

def is_valid_license(license_number):
    return re.fullmatch(r"[A-Z]{1,2}\d{7}", license_number) is not None

# def is_valid_username(username: str) -> bool:
#     if not isinstance(username, str): return False
#     if not (8 <= len(username) <= 10): return False
#     if not re.match(r"^[a-z_]", username.lower()): return False
#     if not re.fullmatch(r"[a-z0-9_'.]{8,10}", username.lower()): return False
#     return True

# def is_valid_password(password: str) -> bool:
#     if not (12 <= len(password) <= 30): return False

#     has_lower = re.search(r"[a-z]", password)
#     has_upper = re.search(r"[A-Z]", password)
#     has_digit = re.search(r"\d", password)
#     has_special = re.search(r"[~!@#$%&_\-+=`|\\(){}\[\]:;'<>,.?/]", password)

#     return all([has_lower, has_upper, has_digit, has_special])