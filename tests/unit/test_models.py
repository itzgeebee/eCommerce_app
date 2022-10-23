from faker import Faker
from src.models import Customer
from src import bcrypt


def test_new_user_with_fixture(new_user):
    """
    GIVEN a User model
    WHEN a new User is created
    THEN check the email, hashed_password, and role fields are defined correctly
    """

    assert new_user.mail == new_user.mail
    assert new_user.first_name == "Gideon"
    assert new_user.role == 1

