from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from app.repositories import get_user_by_username, get_user_by_email, create_user_with_password

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        bio = request.form.get('bio')

        if len(username) < 3:
            flash('Ім\'я користувача повинно містити не менше 3 символів.', 'danger')
            return render_template('register.html')
        if not password or len(password) < 6:
            flash('Пароль повинен містити не менше 6 символів.', 'danger')
            return render_template('register.html')

        if get_user_by_username(username):
            flash('Користувач з таким іменем вже існує.', 'danger')
            return render_template('register.html')
        if email and get_user_by_email(email):
            flash('Користувач з таким email вже існує.', 'danger')
            return render_template('register.html')

        create_user_with_password(username, email, password, bio)
        flash('Реєстрація успішна! Тепер увійдіть.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = get_user_by_username(username)
        if user and user.check_password(password):
            login_user(user)
            flash('Вхід виконано!', 'success')
            return redirect(url_for('chat.chat_view'))
        else:
            flash('Невірне ім’я або пароль.', 'danger')
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Ви вийшли.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/install-guide')
def install_guide():
    return render_template('install_guide.html')