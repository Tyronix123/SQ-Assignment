def insert_traveller(data):
    """
    Insert a new traveller into the database.
    Expects a tuple in the exact order:
    (first_name, last_name, birthday, gender, street_name, house_number,
     zip_code, city, email, mobile_phone, driving_license, registration_date)
    """
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO travellers (
        first_name, last_name, birthday, gender,
        street_name, house_number, zip_code, city,
        email, mobile_phone, driving_license, registration_date
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, data)

    conn.commit()
    conn.close()
