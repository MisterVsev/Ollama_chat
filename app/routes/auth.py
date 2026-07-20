from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from app import db
from app.models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        bio = request.form.get('bio')

        if User.query.filter_by(username=username).first():
            flash('Користувач з таким іменем вже існує.', 'danger')
            return render_template('register.html')

        user = User(username=username, email=email, bio=bio)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Реєстрація успішна! Тепер увійдіть.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
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