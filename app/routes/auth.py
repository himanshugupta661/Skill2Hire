"""
Authentication routes - register, login, logout.
"""
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from app.models.user import User, UserRole, SeekerProfile
from app.models.employer import Employer

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return _redirect_to_dashboard()

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role', 'seeker')
        company_name = request.form.get('company_name', '').strip()

        # Validation
        errors = []
        if not full_name or len(full_name) < 2:
            errors.append('Full name must be at least 2 characters.')
        if not email or '@' not in email:
            errors.append('A valid email address is required.')
        if len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
        if role not in [UserRole.SEEKER, UserRole.EMPLOYER]:
            errors.append('Invalid account type.')
        if role == UserRole.EMPLOYER and not company_name:
            errors.append('Company name is required for employer accounts.')

        # Duplicate check
        if not errors and User.query.filter_by(email_normalized=email).first():
            errors.append('An account with this email already exists.')

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('register.html',
                                   full_name=full_name, email=email,
                                   role=role, company_name=company_name)

        # Create user
        user = User(
            full_name=full_name,
            email=email,
            email_normalized=email,
            role=role,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        # Create role-specific profile
        if role == UserRole.SEEKER:
            profile = SeekerProfile(user_id=user.id)
            db.session.add(profile)
        elif role == UserRole.EMPLOYER:
            employer = Employer(
                user_id=user.id,
                company_name=company_name,
                company_name_normalized=company_name.lower().strip(),
            )
            db.session.add(employer)

        db.session.commit()
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return _redirect_to_dashboard()

    next_page = request.args.get('next')

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'

        user = User.query.filter_by(email_normalized=email).first()

        if not user or not user.check_password(password):
            flash('Invalid email or password.', 'danger')
            return render_template('login.html', email=email)

        if not user.is_active:
            flash('Your account has been suspended. Please contact support.', 'danger')
            return render_template('login.html', email=email)

        login_user(user, remember=remember)
        user.last_login_at = datetime.utcnow()
        db.session.commit()

        flash(f'Welcome back, {user.full_name}!', 'success')

        # Safe redirect — only allow relative URLs
        if next_page and next_page.startswith('/') and not next_page.startswith('//'):
            return redirect(next_page)
        return _redirect_to_dashboard()

    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('public.index'))


def _redirect_to_dashboard():
    """Redirect to appropriate dashboard based on role."""
    if current_user.is_seeker:
        return redirect(url_for('seeker.dashboard'))
    elif current_user.is_employer:
        return redirect(url_for('employer.dashboard'))
    elif current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('public.index'))
