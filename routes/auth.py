from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from models.database import create_owner, get_owner_by_email
from functools import wraps
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import re

auth_bp = Blueprint('auth', __name__)

# Initialize limiter for auth blueprint
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["10 per minute"]
)

def validate_email(email):
    """Validate email format using regex"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength (minimum 8 characters)"""
    return len(password) >= 8

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        oid = session.get('owner_id')
        if oid is None or (isinstance(oid, str) and oid.strip() == ''):
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        business_name = request.form.get('business_name', '').strip()
        business_type = request.form.get('business_type', '').strip()
        
        # Validation errors
        errors = []
        
        if not name:
            errors.append('Name is required.')
        elif len(name) < 2:
            errors.append('Name must be at least 2 characters long.')
            
        if not email:
            errors.append('Email is required.')
        elif not validate_email(email):
            errors.append('Please enter a valid email address.')
            
        if not password:
            errors.append('Password is required.')
        elif not validate_password(password):
            errors.append('Password must be at least 8 characters long.')
            
        if not business_name:
            errors.append('Business name is required.')
        elif len(business_name) < 2:
            errors.append('Business name must be at least 2 characters long.')
            
        if not business_type:
            errors.append('Business type is required.')
        elif business_type not in ['hotel', 'restaurant', 'tour']:
            errors.append('Please select a valid business type.')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('signup.html')
        
        # If validation passes, proceed with signup
        password_hash = generate_password_hash(password)
        try:
            owner_resp = create_owner(email, password_hash, name, business_name, business_type)
            
            if owner_resp and owner_resp.data:
                print("✅ SIGNUP SUCCESS - User created successfully")
                flash('Signup successful! Please log in.', 'success')
                return redirect(url_for('auth.login'))
            else:
                print("❌ SIGNUP FAILED - No data in response")
                error_detail = getattr(owner_resp, 'error', None) if owner_resp else None
                if error_detail:
                    error_msg = error_detail.get('message', 'Unknown database error')
                    if 'duplicate key' in error_msg.lower() or 'unique constraint' in error_msg.lower():
                        flash('Email already registered. Please use a different email.', 'danger')
                    else:
                        flash(f'Signup failed: {error_msg}', 'danger')
                else:
                    flash('Signup failed. Please try again.', 'danger')
        except Exception as e:
            print(f"SIGNUP EXCEPTION: {type(e).__name__}: {str(e)}")
            flash(f'Error during signup: {str(e)}', 'danger')
        return render_template('signup.html')
    return render_template('signup.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        # Validation errors
        errors = []
        
        if not email:
            errors.append('Email is required.')
        elif not validate_email(email):
            errors.append('Please enter a valid email address.')
            
        if not password:
            errors.append('Password is required.')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('login.html')
        
        # If validation passes, proceed with login
        try:
            print(f"\n=== LOGIN ATTEMPT ===")
            print(f"Email: {email}")
            print(f"Password: {'*' * len(password)}")
            
            owner = get_owner_by_email(email)
            print(f"USER FOUND: {owner is not None}")
            
            if owner:
                print(f"USER ID: {owner.get('id')}")
                print(f"USER EMAIL: {owner.get('email')}")
                print(f"HAS PASSWORD_HASH: {'password_hash' in owner}")
                print(f"PASSWORD_HASH LENGTH: {len(owner.get('password_hash', ''))}")
                
                password_match = check_password_hash(owner['password_hash'], password)
                print(f"PASSWORD MATCH: {password_match}")
                
                if password_match:
                    print("✅ LOGIN SUCCESS - Authentication successful")
                    # Store as string so session/JSON and Supabase filters always match chat-saved bookings
                    session['owner_id'] = str(owner['id']) if owner.get('id') is not None else None
                    session['email'] = owner['email']
                    session.permanent = True  # Make session permanent with 24-hour timeout
                    flash('Login successful!', 'success')
                    return redirect(url_for('dashboard.dashboard'))
                else:
                    print("❌ LOGIN FAILED - Password does not match")
                    flash('Invalid email or password.', 'danger')
            else:
                print("❌ LOGIN FAILED - User not found")
                flash('Invalid email or password.', 'danger')
        except Exception as e:
            print(f"\n=== LOGIN EXCEPTION ===")
            print(f"Exception Type: {type(e).__name__}")
            print(f"Exception Message: {str(e)}")
            import traceback
            print(f"Full Traceback: {traceback.format_exc()}")
            flash(f'Error during login: {str(e)}', 'danger')
        return render_template('login.html')
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('auth.login'))
