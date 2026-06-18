import os
from datetime import timedelta

class Config:
    # Basic settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'qr-attendance-super-secret-key-12345')
    
    # Base directory
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # Database Settings: Support both MySQL and fallback to SQLite
    # Example MySQL: mysql+pymysql://username:password@localhost/db_name
    DEFAULT_DB_PATH = os.path.join(BASE_DIR, 'attendance.db')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f'sqlite:///{DEFAULT_DB_PATH}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload & QR code folder settings
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    QR_CODE_FOLDER = os.path.join(BASE_DIR, 'static', 'qr_codes')
    
    # Session Settings
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    SESSION_USE_SIGNER = True
    
    # Email SMTP Settings (Mock config, editable by user)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@attendance-system.com')
    
    # Admin settings (Default seed username and password)
    SEED_ADMIN_USER = os.environ.get('SEED_ADMIN_USER', 'admin')
    SEED_ADMIN_PASS = os.environ.get('SEED_ADMIN_PASS', 'admin123')
