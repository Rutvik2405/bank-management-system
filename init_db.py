from app import create_app
from models import db
from models.user import User
from models.account import Account
from models.transaction import Transaction
from routes.auth import generate_account_number

def init_database():
    app = create_app()
    with app.app_context():
        # Create tables
        db.create_all()

        print("Creating admin user...")
        admin = User.query.filter_by(email='admin@bank.com').first()
        if not admin:
            admin = User(
                full_name='System Admin',
                email='admin@bank.com',
                phone='0000000000',
                role='admin'
            )
            admin.set_password('Admin@123')
            db.session.add(admin)
            db.session.commit()
            print("Admin created.")

        print("Creating demo customers...")
        customers_data = [
            {'name': 'Rutvik Demo', 'email': 'rutvik@demo.com', 'phone': '9876543210', 'balance': 25500.0, 'type': 'Savings'},
            {'name': 'Alice Smith', 'email': 'alice@demo.com', 'phone': '8765432109', 'balance': 50000.0, 'type': 'Current'},
            {'name': 'Bob Johnson', 'email': 'bob@demo.com', 'phone': '7654321098', 'balance': 1500.0, 'type': 'Savings'}
        ]

        for c_data in customers_data:
            customer = User.query.filter_by(email=c_data['email']).first()
            if not customer:
                # Create user
                customer = User(
                    full_name=c_data['name'],
                    email=c_data['email'],
                    phone=c_data['phone'],
                    role='customer'
                )
                customer.set_password('Customer@123')
                db.session.add(customer)
                db.session.commit()
                
                # Create account
                account = Account(
                    user_id=customer.id,
                    account_number=generate_account_number(),
                    account_type=c_data['type'],
                    balance=c_data['balance']
                )
                db.session.add(account)
                db.session.commit()

                # Add a dummy initial deposit transaction if balance > 0
                if c_data['balance'] > 0:
                    from routes.customer import generate_reference_number
                    tx = Transaction(
                        account_id=account.id,
                        transaction_type='DEPOSIT',
                        amount=c_data['balance'],
                        description='Initial Deposit',
                        reference_number=generate_reference_number()
                    )
                    db.session.add(tx)
                    db.session.commit()
                
                print(f"Customer {c_data['name']} created with account {account.account_number}.")

        print("Database initialized successfully!")

if __name__ == '__main__':
    init_database()
