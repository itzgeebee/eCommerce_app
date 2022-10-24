import json

from flask import url_for
from faker import Faker
from src import create_app, app, bcrypt
import pytest
import tempfile
import os
from src.models import Customer

fake = Faker()

new_test_user = {
    "first_name": fake.first_name(),
    "last_name": fake.last_name(),
    "street": fake.street_address(),
    "city": fake.city(),
    "zip": fake.zipcode(),
    "mail": fake.email(),
    "phone": fake.phone_number(),
    "password": bcrypt.generate_password_hash(fake.password()),
    "role": 1
}


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


def test_new_user_with_fixture(new_user):
    """
    GIVEN a User model
    WHEN a new User is created
    THEN check the email, hashed_password, and role fields are defined correctly
    """

    assert new_user.mail == new_test_user["mail"]
    assert new_user.first_name == new_test_user["first_name"]
    assert new_user.role == new_test_user["role"]
