from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from models import db
from models.user import User
from models.account import Account
from models.transaction import Transaction
from routes.auth import admin_required
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    total_customers = User.query.filter_by(role='customer').count()
    total_accounts = Account.query.count()
    
    # Calculate totals securely using SQLAlchemy
    total_deposits = db.session.query(func.sum(Transaction.amount)).filter(Transaction.transaction_type == 'DEPOSIT').scalar() or 0
    total_withdrawals = db.session.query(func.sum(Transaction.amount)).filter(Transaction.transaction_type == 'WITHDRAW').scalar() or 0
    
    # Transfers are recorded as both negative (sender) and positive (receiver) in this system.
    # We will sum the positive transfer amounts to get the total volume.
    total_transfers = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.transaction_type == 'TRANSFER', 
        Transaction.amount > 0
    ).scalar() or 0
    
    total_balance = db.session.query(func.sum(Account.balance)).scalar() or 0

    stats = {
        'total_customers': total_customers,
        'total_accounts': total_accounts,
        'total_deposits': total_deposits,
        'total_withdrawals': total_withdrawals,
        'total_transfers': total_transfers,
        'total_balance': total_balance
    }
    return render_template('admin/dashboard.html', stats=stats)

@admin_bp.route('/customers')
@admin_required
def customers():
    search = request.args.get('search', '')
    query = User.query.filter_by(role='customer')
    
    if search:
        search_pattern = f"%{search}%"
        query = query.join(Account).filter(
            (User.full_name.ilike(search_pattern)) | 
            (User.email.ilike(search_pattern)) | 
            (User.phone.ilike(search_pattern)) |
            (Account.account_number.ilike(search_pattern))
        )
        
    users = query.all()
    return render_template('admin/customers.html', customers=users, search=search)

@admin_bp.route('/transactions')
@admin_required
def transactions():
    transactions = Transaction.query.order_by(Transaction.created_at.desc()).limit(100).all()
    return render_template('admin/transactions.html', transactions=transactions)

@admin_bp.route('/account/<int:account_id>/block', methods=['POST'])
@admin_required
def block_account(account_id):
    account = Account.query.get_or_404(account_id)
    if account.status == 'Active':
        account.status = 'Blocked'
        db.session.commit()
        flash(f'Account {account.account_number} blocked successfully.', 'success')
    return redirect(request.referrer or url_for('admin.customers'))

@admin_bp.route('/account/<int:account_id>/activate', methods=['POST'])
@admin_required
def activate_account(account_id):
    account = Account.query.get_or_404(account_id)
    if account.status == 'Blocked':
        account.status = 'Active'
        db.session.commit()
        flash(f'Account {account.account_number} activated successfully.', 'success')
    return redirect(request.referrer or url_for('admin.customers'))
