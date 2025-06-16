def show_main_menu(user):
    role = user["role"]
    username = user["username"]

    print(f"\n🔐 Logged in as: {username} ({role})\n")

    while True:
        if role == "super_admin":
            print("\n--- Super Administrator Menu ---")
            print("1. Create System Administrator")
            print("2. Manage System Administrators")
            print("3. View Logs")
            print("4. Manage Scooters & Travellers")
            print("5. Logout")

        elif role == "system_admin":
            print("\n--- System Administrator Menu ---")
            print("1. Manage Service Engineers")
            print("2. View Logs")
            print("3. Manage Scooters & Travellers")
            print("4. Logout")

        elif role == "service_engineer":
            print("\n--- Service Engineer Menu ---")
            print("1. Update Password")
            print("2. View & Update Scooter Info")
            print("3. Logout")

        else:
            print("❌ Unknown role.")
            break

        choice = input("Enter your choice: ").strip()

        if choice == "5" or (choice == "3" and role == "service_engineer"):
            print("👋 Logging out...")
            break

        # Placeholder for real actions
        print(f"⚙️ Selected option {choice}. (Feature not implemented yet)")
