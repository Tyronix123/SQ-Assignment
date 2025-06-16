# import bcrypt
# #from db_handler import get_user_by_username

# SUPER_ADMIN_USERNAME = "super_admin"
# SUPER_ADMIN_PASSWORD = "Admin_123?"
# SUPER_ADMIN_ROLE = "super_admin"

# def hash_password(password: str) -> str:
#     """Hash a password and return the hashed string (UTF-8)."""
#     hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
#     return hashed.decode()

# def verify_password(password: str, hashed_password: str) -> bool:
#     """Verify a password against a stored hash."""
#     return bcrypt.checkpw(password.encode(), hashed_password.encode())

# def login_user():
#     print("\n=== Login ===")
#     username = input("Username: ").strip().lower()
#     password = input("Password: ")

#     if username == SUPER_ADMIN_USERNAME and password == SUPER_ADMIN_PASSWORD:
#         print("✅ Super Administrator login successful.")
#         return {"username": username, "role": SUPER_ADMIN_ROLE}

#     user_record = get_user_by_username(username)

#     if user_record is None:
#         print("❌ User not found.")
#         return None

#     stored_hash = user_record["password_hash"]
#     role = user_record["role"]

#     if verify_password(password, stored_hash):
#         print(f"✅ Login successful as {role}.")
#         return {"username": username, "role": role}
#     else:
#         print("❌ Invalid password.")
#         return None
