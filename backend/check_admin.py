from database import get_connection, DATABASE_NAME

connection = get_connection()

print("\nDATABASE LOCATION:")
print(DATABASE_NAME)

print("\nADMIN ACCOUNTS:")

admins = connection.execute(
    "SELECT id, email, role FROM users WHERE role = ?",
    ("admin",)
).fetchall()

if admins:
    for admin in admins:
        print(dict(admin))
else:
    print("No administrator account found.")

connection.close()