import pytest
from models.user import User
from models.account import Account

def test_register(client, app):
    response = client.post('/register', data={
        'full_name': 'New User',
        'email': 'newuser@test.com',
        'phone': '5551234567',
        'password': 'password123',
        'confirm_password': 'password123',
        'account_type': 'Savings'
    }, follow_redirects=True)
    
    assert b'Registration successful' in response.data
    
    with app.app_context():
        user = User.query.filter_by(email='newuser@test.com').first()
        assert user is not None
        assert user.full_name == 'New User'
        
        account = Account.query.filter_by(user_id=user.id).first()
        assert account is not None
        assert account.balance == 0.0

def test_login_success(client, init_database):
    response = client.post('/login', data={
        'email': 'cust@test.com',
        'password': 'cust123'
    }, follow_redirects=True)
    
    assert b'Logged in successfully.' in response.data
    assert b'Welcome, Customer Test' in response.data

def test_login_failure(client, init_database):
    response = client.post('/login', data={
        'email': 'cust@test.com',
        'password': 'wrongpassword'
    }, follow_redirects=True)
    
    assert b'Invalid email or password.' in response.data

def test_admin_access(client, init_database):
    # Login as admin
    client.post('/login', data={'email': 'admin@test.com', 'password': 'admin123'})
    
    response = client.get('/admin/dashboard')
    assert response.status_code == 200
    assert b'Admin Dashboard' in response.data

def test_customer_cannot_access_admin(client, init_database):
    # Login as customer
    client.post('/login', data={'email': 'cust@test.com', 'password': 'cust123'})
    
    response = client.get('/admin/dashboard', follow_redirects=True)
    # Should be redirected and shown an error message
    assert b'You do not have permission to access this page' in response.data
