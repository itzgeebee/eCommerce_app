import pytest
import tempfile
import os
from faker import Faker
from src.models import Customer
from src import bcrypt, create_app, app

fake = Faker()

new_test_user = {
    "first_name": "Gideon",
    "last_name": fake.name(),
    "street": fake.street_address(),
    "city": fake.city(),
    "zip": fake.zipcode(),
    "mail": fake.email(),
    "phone": fake.phone_number(),
    "password": bcrypt.generate_password_hash(fake.password()),
    "role": 1
}


@pytest.fixture(scope='module')
def app():
    db_fd, db_path = tempfile.mkstemp()

    # app.config.update({
    #     'TESTING': True,
    #     'SQLALCHEMY_DATABASE_URI':
    #         "postgresql://teamworkadmin:teamworkpassword@localhost:5432/ecom_test"
    # })
    app = create_app({'TESTING': True,
                      "SQLALCHEMY_DATABASE_URI":
                          "postgresql://teamworkadmin:teamworkpassword@localhost:5432/ecom_test"})

    yield app

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture(scope="module")
def new_user():
    user = Customer(
        first_name=new_test_user["first_name"],
        last_name=new_test_user["last_name"],
        street=new_test_user["street"],
        city=new_test_user["city"],
        zip=new_test_user["zip"],
        mail=new_test_user["mail"],
        phone=new_test_user["phone"],
        password=new_test_user["password"],
        role=new_test_user["role"])
    return user


@pytest.fixture()
def test_client(app):
    with app.test_client() as testing_client:
        with app.app_context():
            yield testing_client


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()
