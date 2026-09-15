import pytest
from models.account import Account
from models.transaction import Transaction
from models.user import User
from models import db

def test_transfer_success(client, init_database, app):
    # Setup a second user to receive the transfer
    with app.app_context():
        receiver_user = User(full_name='Receiver', email='rec@test.com', phone='111', role='customer')
        receiver_user.set_password('pass')
        db.session.add(receiver_user)
        db.session.commit()
        
        receiver_account = Account(user_id=receiver_user.id, account_number='1000111222', account_type='Savings', balance=0)
        db.session.add(receiver_account)
        db.session.commit()

    # Login as original customer
    client.post('/login', data={'email': 'cust@test.com', 'password': 'cust123'})
    
    response = client.post('/transfer', data={
        'receiver_account_number': '1000111222',
        'amount': '300.00',
        'description': 'Gift'
    }, follow_redirects=True)
    
    assert b'Successfully transferred' in response.data
    
    with app.app_context():
        sender = Account.query.filter_by(account_number='1000999888').first()
        receiver = Account.query.filter_by(account_number='1000111222').first()
        
        assert sender.balance == 700.00
        assert receiver.balance == 300.00
        
        txs = Transaction.query.all()
        assert len(txs) == 2 # 1 for sender, 1 for receiver
        assert txs[0].reference_number[:-2] == txs[1].reference_number[:-2]
        assert txs[0].amount == -300.00 or txs[0].amount == 300.00
        
def test_transfer_invalid_receiver(client, init_database):
    client.post('/login', data={'email': 'cust@test.com', 'password': 'cust123'})
    
    response = client.post('/transfer', data={
        'receiver_account_number': '9999999999',
        'amount': '300.00',
        'description': 'Gift'
    }, follow_redirects=True)
    
    assert b'Receiver account not found' in response.data
