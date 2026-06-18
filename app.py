import os
from flask import Flask, redirect, url_for, session
from flask_session import Session
from config import Config
from database.connection import db

# Import models so they are registered with SQLAlchemy
from models import Admin, Department, User, Attendance

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure upload and QR code paths exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['QR_CODE_FOLDER'], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    
    # Configure Server-side Session Management
    Session(app)

    # Register blueprints
    from routes.auth import auth_bp
    from routes.department import department_bp
    from routes.user import user_bp
    from routes.attendance import attendance_bp
    from routes.reports import reports_bp
    from routes.dashboard import dashboard_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(department_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(dashboard_bp)

    # Root route - redirect to dashboard (will require login) or login
    @app.route('/home')
    def home_redirect():
        if 'admin_id' in session:
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('auth.login'))

    # Context Processor to make site name or current user accessible in templates
    @app.context_processor
    def inject_global_vars():
        return {
            'current_user': session.get('admin_username')
        }

    # Initialize tables
    with app.app_context():
        db.create_all()

    return app

app = create_app()

if __name__ == '__main__':
    # Bind to all interfaces (useful if testing from mobile camera on local network!)
    app.run(host='0.0.0.0', port=5000, debug=True)
