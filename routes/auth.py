from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from models import db
from models.user import User
from models.account import Account
import random
from functools import wraps

auth_bp = Blueprint('auth', __name__)

def generate_account_number():
    while True:
        num = '1000' + str(random.randint(100000, 999999))
        if not Account.query.filter_by(account_number=num).first():
            return num

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            flash('Please log in to access this page.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None or g.user.role != 'admin':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        account_type = request.form.get('account_type')

        # Validation
        if not all([full_name, email, phone, password, confirm_password, account_type]):
            flash('All fields are required.', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email address already registered.', 'danger')
            return render_template('register.html')

        try:
            # Create user
            user = User(full_name=full_name, email=email, phone=phone, role='customer')
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            # Create account for the user
            account_number = generate_account_number()
            account = Account(
                user_id=user.id,
                account_number=account_number,
                account_type=account_type,
                balance=0.0,
                status='Active'
            )
            db.session.add(account)
            db.session.commit()

            flash(f'Registration successful! Your Account Number is {account_number}. Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'danger')
            print(f"Error: {e}")

    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            session.clear()
            session['user_id'] = user.id
            flash('Logged in successfully.', 'success')
            
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('customer.dashboard'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))
