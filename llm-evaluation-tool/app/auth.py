from functools import wraps
from flask import session, redirect, url_for, flash, current_app

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('로그인이 필요합니다.', 'error')
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('로그인이 필요합니다.', 'error')
            return redirect(url_for('main.login'))

        user = current_app.db.get_user_by_id(session['user_id'])
        if not user or user['role'] != 'admin':
            flash('관리자 권한이 필요합니다.', 'error')
            return redirect(url_for('main.select_category'))

        return f(*args, **kwargs)
    return decorated_function
