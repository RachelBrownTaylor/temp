from flask import Flask
import os
from config import Config

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure database directory exists
    db_dir = os.path.dirname(app.config['DATABASE_PATH'])
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)

    # Initialize database
    from app.models import Database
    app.db = Database(app.config['DATABASE_PATH'])

    # Register blueprints
    from app.routes import main_bp
    from app.admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')

    return app
