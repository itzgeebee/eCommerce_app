from src import create_app, app


def test_config():
    assert not create_app().testing
    assert create_app({'TESTING': True}).testing


def test_get_products():
    response = app.test_client().get('/api/v1/')
    assert response.status_code == 200
    assert b'products' in response.data
