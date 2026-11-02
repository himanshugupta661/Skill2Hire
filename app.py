"""
SKILL2HIRE - Application Factory
"""
import os
import logging
from flask import Flask, render_template
from config import config
from extensions import db, login_manager, csrf


def create_app(config_name=None):
    """Create and configure the Flask application."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
    app.config.from_object(config.get(config_name, config['default']))

    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join('instance'), exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Configure logging
    logging.basicConfig(
        level=logging.INFO if not app.config.get('DEBUG') else logging.DEBUG,
        format='%(asctime)s %(levelname)s %(name)s: %(message)s'
    )

    # Register blueprints
    from app.routes.public import public_bp
    from app.routes.auth import auth_bp
    from app.routes.job_seeker import seeker_bp
    from app.routes.employer import employer_bp
    from app.routes.admin import admin_bp
    from app.routes.api import api_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(seeker_bp, url_prefix='/seeker')
    app.register_blueprint(employer_bp, url_prefix='/employer')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')

    # Register error handlers
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        app.logger.error(f'Server error: {e}')
        return render_template('errors/500.html'), 500

    # User loader for Flask-Login
    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Create tables
    with app.app_context():
        db.create_all()

    return app
