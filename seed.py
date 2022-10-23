import os

from src.models import Role, Customer
from src import db, bcrypt


def add_roles():
    print("adding roles")
    admin = Role(name="admin")
    customer = Role(name="customer")
    db.session.add(admin)
    db.session.add(customer)
    try:
        db.session.commit()
    except Exception as e:
        print(e)
        print("an error occurred")
        db.session.rollback()
        pass
    else:
        print("Roles added successfully")
    finally:
        db.session.close()


def add_admin():
    print("adding admin")
    admin = Customer(
        first_name="admin",
        last_name="admin",
        mail="codergideon@gmail.com",
        password=bcrypt.generate_password_hash(
            os.environ.get("ADMIN_PASSWORD"),
            12).decode("utf-8"),
        role=1,
        phone="0700000000",
        street="admin street",
        city="admin city",
        zip="0000"
    )
    db.session.add(admin)
    try:
        db.session.commit()
    except Exception as e:
        print(e)
        print("an error occurred")
        db.session.rollback()
        pass
    else:
        print("Admin added successfully")
    finally:
        db.session.close()


add_roles()
add_admin()
