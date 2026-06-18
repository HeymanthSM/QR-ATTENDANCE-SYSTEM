import os
from flask import Flask, redirect, url_for, session
from config import Config
from database.connection import db

# Import models so they are registered with SQLAlchemy
from models import Admin, Department, User, Attendance

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure upload and QR code paths exist (catch read-only filesystem errors)
    try:
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['QR_CODE_FOLDER'], exist_ok=True)
    except OSError as e:
        app.logger.warning(f"Could not create upload/QR directories on disk: {e}")

    # Initialize extensions
    db.init_app(app)

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

    # Initialize tables & auto-seed if empty
    with app.app_context():
        db.create_all()
        try:
            admin_exists = Admin.query.first()
            if not admin_exists:
                from werkzeug.security import generate_password_hash
                default_user = app.config.get('SEED_ADMIN_USER', 'admin')
                default_pass = app.config.get('SEED_ADMIN_PASS', 'admin123')
                
                hashed_password = generate_password_hash(default_pass)
                db_admin = Admin(username=default_user, password=hashed_password)
                db.session.add(db_admin)
                
                # Seed default departments
                if not Department.query.first():
                    d1 = Department(name="Computer Science")
                    d2 = Department(name="Information Technology")
                    d3 = Department(name="Electronics Engineering")
                    db.session.add_all([d1, d2, d3])
                
                db.session.commit()
                app.logger.info("Successfully auto-seeded database tables on startup.")
        except Exception as e:
            app.logger.error(f"Error during auto-seeding: {e}")

    return app

app = create_app()

if __name__ == '__main__':
    # Bind to all interfaces (useful if testing from mobile camera on local network!)
    app.run(host='0.0.0.0', port=5000, debug=True)
