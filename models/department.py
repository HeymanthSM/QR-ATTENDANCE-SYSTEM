from datetime import datetime
from database.connection import db

class Department(db.Model):
    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to users
    users = db.relationship('User', backref='department', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Department {self.code} - {self.name}>"
