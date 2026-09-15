import pytest
from models.account import Account
from models import db

def test_deposit(client, init_database, app):
    client.post('/login', data={'email': 'cust@test.com', 'password': 'cust123'})
    
    response = client.post('/deposit', data={
        'amount': '500.50',
        'description': 'Test deposit'
    }, follow_redirects=True)
    
    assert b'Successfully deposited' in response.data
    
    with app.app_context():
        account = Account.query.filter_by(account_number='1000999888').first()
        assert account.balance == 1500.50

def test_withdraw_success(client, init_database, app):
    client.post('/login', data={'email': 'cust@test.com', 'password': 'cust123'})
    
    response = client.post('/withdraw', data={
        'amount': '200.00',
        'description': 'Test withdraw'
    }, follow_redirects=True)
    
    assert b'Successfully withdrew' in response.data
    
    with app.app_context():
        account = Account.query.filter_by(account_number='1000999888').first()
        assert account.balance == 800.00

def test_withdraw_insufficient_balance(client, init_database, app):
    client.post('/login', data={'email': 'cust@test.com', 'password': 'cust123'})
    
    response = client.post('/withdraw', data={
        'amount': '2000.00',
        'description': 'Test withdraw huge'
    }, follow_redirects=True)
    
    assert b'Insufficient balance' in response.data
    
    with app.app_context():
        account = Account.query.filter_by(account_number='1000999888').first()
        assert account.balance == 1000.00 # Balance unchanged

def test_blocked_account_cannot_transact(client, init_database, app):
    with app.app_context():
        account = Account.query.filter_by(account_number='1000999888').first()
        account.status = 'Blocked'
        db.session.commit()
        
    client.post('/login', data={'email': 'cust@test.com', 'password': 'cust123'})
    
    response = client.post('/deposit', data={'amount': '100'}, follow_redirects=True)
    assert b'This account is currently blocked or closed' in response.data
    
    response = client.post('/withdraw', data={'amount': '100'}, follow_redirects=True)
    assert b'This account is currently blocked or closed' in response.data
