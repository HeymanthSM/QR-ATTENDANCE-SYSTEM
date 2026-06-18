from datetime import datetime
from flask import Blueprint, render_template, request
from models.user import User
from models.attendance import Attendance
from database.connection import db
from routes.auth import login_required

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    today = datetime.now().date()
    
    # 1. Total Registered Users
    total_users = User.query.count()
    
    # 2. Present Today
    present_today = Attendance.query.filter_by(date=today).count()
    
    # 3. Attendance Percentage for Today
    attendance_percentage = 0.0
    if total_users > 0:
        attendance_percentage = round((present_today / total_users) * 100, 1)

    # 4. Search and Filter recent records (on dashboard)
    search_query = request.args.get('search', '').strip()
    
    # Fetch logs for today (default) or search query across all dates
    query = Attendance.query
    
    if search_query:
        # Filter by user name or user code or status
        query = query.join(User).filter(
            (User.name.like(f'%{search_query}%')) |
            (User.user_code.like(f'%{search_query}%')) |
            (Attendance.status.like(f'%{search_query}%'))
        )
    else:
        # Default to show today's attendance logs
        query = query.filter(Attendance.date == today)
        
    recent_logs = query.order_by(Attendance.date.desc(), Attendance.time.desc()).limit(15).all()

    return render_template(
        'dashboard.html',
        total_users=total_users,
        present_today=present_today,
        attendance_percentage=attendance_percentage,
        recent_logs=recent_logs,
        search_query=search_query
    )
