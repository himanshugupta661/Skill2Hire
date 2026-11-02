"""
Custom decorators for role-based access control.
Backend enforcement — frontend UI alone is insufficient.
"""
from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user


def seeker_required(f):
    """Restrict access to job seekers only."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.is_seeker:
            abort(403)
        return f(*args, **kwargs)
    return decorated


def employer_required(f):
    """Restrict access to employers only."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.is_employer:
            abort(403)
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Restrict access to administrators only."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated


def active_account_required(f):
    """Require an active (non-suspended) account."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.is_authenticated and not current_user.is_active:
            flash('Your account has been suspended. Please contact support.', 'danger')
            return redirect(url_for('auth.logout'))
        return f(*args, **kwargs)
    return decorated
