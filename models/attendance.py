from datetime import datetime
from database.connection import db

class Attendance(db.Model):
    __tablename__ = 'attendance'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, index=True)
    time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default='Present') # e.g. Present, Late, etc.

    # Unique constraint to prevent duplicate scans on the same day
    __table_args__ = (
        db.UniqueConstraint('user_id', 'date', name='uq_user_date'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_code': self.user.user_code if self.user else None,
            'name': self.user.name if self.user else None,
            'department': self.user.department.name if self.user and self.user.department else None,
            'date': self.date.strftime('%Y-%m-%d'),
            'time': self.time.strftime('%H:%M:%S'),
            'status': self.status
        }

    def __repr__(self):
        return f"<Attendance User {self.user_id} on {self.date}>"
