"""
Unit tests for authentication, registration, and login workflows.
"""
from app.models.user import User


def test_login_page_renders(client):
    response = client.get('/auth/login')
    assert response.status_code == 200
    assert b'Sign In' in response.data


def test_register_page_renders(client):
    response = client.get('/auth/register')
    assert response.status_code == 200
    assert b'Create Account' in response.data


def test_successful_login(client):
    response = client.post('/auth/login', data={
        'email': 'seeker@test.com',
        'password': 'Seeker@12345'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Dashboard' in response.data or b'Welcome' in response.data


def test_invalid_password_login(client):
    response = client.post('/auth/login', data={
        'email': 'seeker@test.com',
        'password': 'WrongPassword123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Invalid email or password' in response.data


def test_user_registration(client, app):
    response = client.post('/auth/register', data={
        'full_name': 'New Registered Seeker',
        'email': 'newseeker@example.com',
        'password': 'Password@123',
        'confirm_password': 'Password@123',
        'role': 'seeker'
    }, follow_redirects=True)
    assert response.status_code == 200

    with app.app_context():
        u = User.query.filter_by(email='newseeker@example.com').first()
        assert u is not None
        assert u.role == 'seeker'
        assert u.check_password('Password@123')
