from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from models import User
from peewee import IntegrityError

auth_bp = Blueprint(
    'auth',
    __name__,
    template_folder='templates',
    url_prefix='/auth'
)


#--------------------------------HELPER FUNCTIONS--------------------------------

def validate_login_credentials(username, password):
    if not username or not password:
        return False, "Username and password are required"
    return True, None


def validate_registration_data(username, email, password, confirm_password):
    if not username or not email or not password:
        return False, "All fields are required"
    
    if password != confirm_password:
        return False, "Passwords do not match"
    
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    
    return True, None


def check_email_exists(email):
    return User.get_or_none(User.email == email) is not None


def authenticate_user(username, password):
    user = User.get_or_none(User.username == username)
    
    if not user or not user.check_password(password):
        return None
    
    return user


def create_user_session(user):
    session.permanent = True
    session['user_id'] = user.id


def update_user_last_login(user):
    user.last_login = datetime.now()
    user.save()


def create_new_user(username, email, password):
    user = User(username=username, email=email)
    user.set_password(password)
    user.save()
    return user


def clear_user_session():
    session.clear()


#-------------------------------- ROUTE HANDLERS--------------------------------

@auth_bp.route('/', methods=['GET'])
def auth_page():
    mode = request.args.get('mode', 'login')
    return render_template('auth.html', mode=mode)


@auth_bp.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    
    is_valid, error_message = validate_login_credentials(username, password)
    if not is_valid:
        flash(error_message, "error")
        return redirect(url_for('auth.auth_page', mode='login'))
    
    user = authenticate_user(username, password)
    if not user:
        flash("Invalid username or password", "error")
        return redirect(url_for('auth.auth_page', mode='login'))
    
    create_user_session(user)
    update_user_last_login(user)
    
    flash(f"Welcome back, {user.username}!", "success")
    return redirect(url_for('dashboard'))


@auth_bp.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    is_valid, error_message = validate_registration_data(
        username, email, password, confirm_password
    )
    if not is_valid:
        flash(error_message, "error")
        return redirect(url_for('auth.auth_page', mode='register'))
    
    if check_email_exists(email):
        flash("Email already registered", "error")
        return redirect(url_for('auth.auth_page', mode='register'))
    
    try:
        create_new_user(username, email, password)
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('auth.auth_page', mode='login'))
    
    except IntegrityError:
        flash("Error creating account. Please try again.", "error")
        return redirect(url_for('auth.auth_page', mode='register'))


@auth_bp.route('/logout')
def logout():
    clear_user_session()
    flash("You have been logged out successfully", "success")
    return redirect(url_for('auth.auth_page', mode='login'))