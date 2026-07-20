from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Будь ласка, увійдіть, щоб продовжити.'

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    from app.routes.auth import auth_bp
    from app.routes.chat import chat_bp
    from app.routes.presets import presets_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(chat_bp, url_prefix='/chat')
    app.register_blueprint(presets_bp, url_prefix='/presets')

    @app.route('/')
    def index():
        from flask import redirect, url_for
        return redirect(url_for('chat.chat_view'))

    return app