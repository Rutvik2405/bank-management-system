import pytest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db
from models.user import User
from models.account import Account

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def init_database(app):
    admin = User(full_name='Admin Test', email='admin@test.com', phone='1234567890', role='admin')
    admin.set_password('admin123')
    
    customer = User(full_name='Customer Test', email='cust@test.com', phone='0987654321', role='customer')
    customer.set_password('cust123')
    
    db.session.add(admin)
    db.session.add(customer)
    db.session.commit()
    
    account = Account(user_id=customer.id, account_number='1000999888', account_type='Savings', balance=1000.0)
    db.session.add(account)
    db.session.commit()

    return {
        'admin': admin,
        'customer': customer,
        'account': account
    }
