from datetime import datetime
from database.connection import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    user_code = db.Column(db.String(50), unique=True, nullable=False, index=True) # ID Code: EMP101, STD202
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    qr_code_path = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to attendance logs
    attendances = db.relationship('Attendance', backref='user', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'user_code': self.user_code,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'department': self.department.name if self.department else None,
            'department_code': self.department.code if self.department else None,
            'qr_code_path': self.qr_code_path,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

    def __repr__(self):
        return f"<User {self.user_code} - {self.name}>"
