import json

from src import create_app


def test_config():
    assert not create_app().testing
    assert create_app({'TESTING': True}).testing


def test_home_page_with_fixture(test_client):
    response = test_client.get('/')
    assert response.status_code == 200