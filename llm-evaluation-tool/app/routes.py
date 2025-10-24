from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, current_app
from app.auth import login_required
import json

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Redirect to login or category selection"""
    if 'user_id' in session:
        return redirect(url_for('main.select_category'))
    return redirect(url_for('main.login'))

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = current_app.db.verify_user(username, password)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']

            if user['role'] == 'admin':
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('main.select_category'))
        else:
            flash('잘못된 사용자명 또는 비밀번호입니다.', 'error')

    return render_template('login.html')

@main_bp.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    flash('로그아웃되었습니다.', 'success')
    return redirect(url_for('main.login'))

@main_bp.route('/category')
@login_required
def select_category():
    """Category selection page"""
    categories = current_app.db.get_categories()
    return render_template('category_select.html', categories=categories)

@main_bp.route('/evaluate/<category>')
@login_required
def evaluate_category(category):
    """Evaluation interface for a specific category"""
    examples = current_app.db.get_examples_by_category(category)
    if not examples:
        flash('해당 카테고리에 문제가 없습니다.', 'error')
        return redirect(url_for('main.select_category'))

    # Get user's progress for this category
    progress = current_app.db.get_user_progress(session['user_id'], category)

    return render_template('evaluate.html',
                         category=category,
                         examples=examples,
                         progress=progress)

@main_bp.route('/api/rating', methods=['POST'])
@login_required
def save_rating():
    """API endpoint to save a rating"""
    data = request.get_json()
    example_id = data.get('example_id')
    model_name = data.get('model_name')
    rating = data.get('rating')

    if not all([example_id, model_name, rating]):
        return jsonify({'success': False, 'message': '필수 정보가 누락되었습니다.'}), 400

    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': '평점은 1~5 사이의 숫자여야 합니다.'}), 400

    current_app.db.save_rating(session['user_id'], example_id, model_name, rating)
    return jsonify({'success': True, 'message': '평가가 저장되었습니다.'})

@main_bp.route('/api/progress/<category>')
@login_required
def get_progress(category):
    """API endpoint to get user's progress"""
    progress = current_app.db.get_user_progress(session['user_id'], category)
    return jsonify({'success': True, 'progress': progress})
