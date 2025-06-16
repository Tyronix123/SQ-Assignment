# from input_validation import is_valid_username, is_valid_password, is_valid_name
# from user_auth import hash_password
# from db_handler import insert_user, user_exists
# from datetime import datetime

# def get_valid_input(prompt, validator, transform=lambda x: x.strip()):
#     while True:
#         raw = input(prompt)
#         cleaned = transform(raw)
#         if validator(cleaned):
#             return cleaned
#         print("Invalid input. Try again.")

# def register_user(role: str, created_by: str):
#     print(f"\n--- Register New {role.replace('_', ' ').title()} ---")

#     username = get_valid_input("New username (8–10 chars): ", is_valid_username).lower()

#     if user_exists(username):
#         print("This username already exists.")
#         return

#     password = get_valid_input("New password (12–30 chars): ", is_valid_password)
#     password_hash = hash_password(password)

#     first_name = get_valid_input("First name: ", is_valid_name)
#     last_name = get_valid_input("Last name: ", is_valid_name)
#     registration_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

#     insert_user(username, password_hash, role, first_name, last_name, registration_date)
#     print(f"✅ {role.replace('_', ' ').title()} '{username}' registered successfully by {created_by}.")
