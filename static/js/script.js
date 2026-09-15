// Custom JS for Bank Management System

function validateRegistration() {
    const password = document.getElementById('password').value;
    const confirm_password = document.getElementById('confirm_password').value;
    
    if (password.length < 6) {
        alert("Password must be at least 6 characters long.");
        return false;
    }
    
    if (password !== confirm_password) {
        alert("Passwords do not match!");
        return false;
    }
    
    return true;
}

function validateWithdrawal(balance) {
    const amountStr = document.getElementById('amount').value;
    const amount = parseFloat(amountStr);
    const errorDiv = document.getElementById('amountError');
    
    if (isNaN(amount) || amount <= 0) {
        errorDiv.textContent = "Please enter a valid positive amount.";
        errorDiv.classList.remove('d-none');
        return false;
    }
    
    if (amount > balance) {
        errorDiv.textContent = "Insufficient balance.";
        errorDiv.classList.remove('d-none');
        return false;
    }
    
    errorDiv.classList.add('d-none');
    return true;
}

function validateTransfer(balance, currentAccount) {
    const receiver = document.getElementById('receiver_account_number').value;
    const amountStr = document.getElementById('amount').value;
    const amount = parseFloat(amountStr);
    
    const accountErrorDiv = document.getElementById('accountError');
    const amountErrorDiv = document.getElementById('amountError');
    
    let isValid = true;
    
    if (receiver === currentAccount) {
        accountErrorDiv.classList.remove('d-none');
        isValid = false;
    } else {
        accountErrorDiv.classList.add('d-none');
    }
    
    if (isNaN(amount) || amount <= 0) {
        amountErrorDiv.textContent = "Please enter a valid positive amount.";
        amountErrorDiv.classList.remove('d-none');
        isValid = false;
    } else if (amount > balance) {
        amountErrorDiv.textContent = "Insufficient balance for this transfer.";
        amountErrorDiv.classList.remove('d-none');
        isValid = false;
    } else {
        amountErrorDiv.classList.add('d-none');
    }
    
    if (isValid) {
        return true;
    }
    return false;
}
