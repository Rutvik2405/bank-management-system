from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from models import db
from models.user import User
from models.account import Account
from models.transaction import Transaction
from routes.auth import login_required
import string
import random

customer_bp = Blueprint('customer', __name__)

def generate_reference_number():
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=12))

@customer_bp.route('/dashboard')
@login_required
def dashboard():
    account = Account.query.filter_by(user_id=g.user.id).first()
    recent_transactions = []
    if account:
        recent_transactions = Transaction.query.filter_by(account_id=account.id).order_by(Transaction.created_at.desc()).limit(5).all()
    return render_template('dashboard.html', account=account, recent_transactions=recent_transactions)

@customer_bp.route('/account')
@login_required
def account_details():
    account = Account.query.filter_by(user_id=g.user.id).first()
    return render_template('account.html', account=account)

@customer_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')

        if not full_name or not phone:
            flash('Name and phone cannot be empty.', 'danger')
            return redirect(url_for('customer.profile'))
        
        g.user.full_name = full_name
        g.user.phone = phone
        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('customer.profile'))

    return render_template('profile.html')

@customer_bp.route('/deposit', methods=['GET', 'POST'])
@login_required
def deposit():
    account = Account.query.filter_by(user_id=g.user.id).first()
    
    if request.method == 'POST':
        if account.status != 'Active':
            flash('This account is currently blocked or closed.', 'danger')
            return redirect(url_for('customer.deposit'))

        try:
            amount = float(request.form.get('amount'))
        except ValueError:
            flash('Invalid amount.', 'danger')
            return redirect(url_for('customer.deposit'))

        if amount <= 0:
            flash('Amount must be greater than zero.', 'danger')
            return redirect(url_for('customer.deposit'))

        # Process deposit
        account.balance += amount
        transaction = Transaction(
            account_id=account.id,
            transaction_type='DEPOSIT',
            amount=amount,
            description=request.form.get('description') or 'Deposit',
            reference_number=generate_reference_number()
        )
        db.session.add(transaction)
        db.session.commit()

        flash(f'Successfully deposited ₹{amount:,.2f}.', 'success')
        return redirect(url_for('customer.dashboard'))

    return render_template('deposit.html', account=account)

@customer_bp.route('/withdraw', methods=['GET', 'POST'])
@login_required
def withdraw():
    account = Account.query.filter_by(user_id=g.user.id).first()
    
    if request.method == 'POST':
        if account.status != 'Active':
            flash('This account is currently blocked or closed.', 'danger')
            return redirect(url_for('customer.withdraw'))

        try:
            amount = float(request.form.get('amount'))
        except ValueError:
            flash('Invalid amount.', 'danger')
            return redirect(url_for('customer.withdraw'))

        if amount <= 0:
            flash('Amount must be greater than zero.', 'danger')
            return redirect(url_for('customer.withdraw'))
            
        if amount > account.balance:
            flash('Insufficient balance.', 'danger')
            return redirect(url_for('customer.withdraw'))

        # Process withdrawal
        account.balance -= amount
        transaction = Transaction(
            account_id=account.id,
            transaction_type='WITHDRAW',
            amount=amount,
            description=request.form.get('description') or 'Withdrawal',
            reference_number=generate_reference_number()
        )
        db.session.add(transaction)
        db.session.commit()

        flash(f'Successfully withdrew ₹{amount:,.2f}.', 'success')
        return redirect(url_for('customer.dashboard'))

    return render_template('withdraw.html', account=account)

@customer_bp.route('/transfer', methods=['GET', 'POST'])
@login_required
def transfer():
    sender_account = Account.query.filter_by(user_id=g.user.id).first()
    
    if request.method == 'POST':
        if sender_account.status != 'Active':
            flash('This account is currently blocked or closed.', 'danger')
            return redirect(url_for('customer.transfer'))

        receiver_account_number = request.form.get('receiver_account_number')
        description = request.form.get('description') or 'Transfer'
        
        try:
            amount = float(request.form.get('amount'))
        except ValueError:
            flash('Invalid amount.', 'danger')
            return redirect(url_for('customer.transfer'))

        if amount <= 0:
            flash('Amount must be greater than zero.', 'danger')
            return redirect(url_for('customer.transfer'))
            
        if amount > sender_account.balance:
            flash('Insufficient balance.', 'danger')
            return redirect(url_for('customer.transfer'))

        if receiver_account_number == sender_account.account_number:
            flash('Cannot transfer to the same account.', 'danger')
            return redirect(url_for('customer.transfer'))

        receiver_account = Account.query.filter_by(account_number=receiver_account_number).first()
        
        if not receiver_account:
            flash('Receiver account not found.', 'danger')
            return redirect(url_for('customer.transfer'))
            
        if receiver_account.status != 'Active':
            flash('Receiver account is not active.', 'danger')
            return redirect(url_for('customer.transfer'))

        try:
            # Transaction block
            sender_account.balance -= amount
            receiver_account.balance += amount
            
            ref_number = generate_reference_number()
            
            sender_tx = Transaction(
                account_id=sender_account.id,
                transaction_type='TRANSFER',
                amount=-amount,
                description=f'Transfer to {receiver_account_number} - {description}',
                reference_number=ref_number + '-S'
            )
            
            receiver_tx = Transaction(
                account_id=receiver_account.id,
                transaction_type='TRANSFER',
                amount=amount,
                description=f'Transfer from {sender_account.account_number} - {description}',
                reference_number=ref_number + '-R'
            )

            db.session.add(sender_tx)
            db.session.add(receiver_tx)
            db.session.commit()
            
            flash(f'Successfully transferred ₹{amount:,.2f} to {receiver_account.user.full_name}.', 'success')
            return redirect(url_for('customer.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during transfer. Transaction aborted.', 'danger')
            print(f"Transfer error: {e}")

    return render_template('transfer.html', account=sender_account)

@customer_bp.route('/transactions')
@login_required
def transactions():
    account = Account.query.filter_by(user_id=g.user.id).first()
    
    tx_type = request.args.get('type', 'all')
    
    query = Transaction.query.filter_by(account_id=account.id)
    
    if tx_type.upper() in ['DEPOSIT', 'WITHDRAW', 'TRANSFER']:
        query = query.filter_by(transaction_type=tx_type.upper())
        
    transactions = query.order_by(Transaction.created_at.desc()).all()
    
    return render_template('transactions.html', transactions=transactions, current_filter=tx_type)
