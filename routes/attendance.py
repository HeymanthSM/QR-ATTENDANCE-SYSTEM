from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, flash, current_app
from models.user import User
from models.attendance import Attendance
from database.connection import db
from routes.auth import login_required
import smtplib
from email.mime.text import MIMEText

attendance_bp = Blueprint('attendance', __name__)

def send_attendance_email(user, check_in_time):
    """
    Sends an email notification when attendance is marked.
    If SMTP credentials are not configured, it logs/prints the email.
    """
    subject = f"Attendance Marked: {user.name}"
    body = f"Hello {user.name},\n\nYour attendance has been successfully marked for today ({datetime.now().strftime('%Y-%m-%d')}) at {check_in_time}.\n\nThank you,\nAttendance Management System"
    
    sender = current_app.config.get('MAIL_DEFAULT_SENDER')
    recipient = user.email
    
    # Check if SMTP details are provided in configuration
    smtp_server = current_app.config.get('MAIL_SERVER')
    smtp_port = current_app.config.get('MAIL_PORT')
    username = current_app.config.get('MAIL_USERNAME')
    password = current_app.config.get('MAIL_PASSWORD')
    
    if smtp_server and username and password:
        try:
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = sender
            msg['To'] = recipient
            
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                if current_app.config.get('MAIL_USE_TLS'):
                    server.starttls()
                server.login(username, password)
                server.sendmail(sender, [recipient], msg.as_string())
            print(f"[EMAIL SNT] Sent attendance email to {recipient}")
            return True
        except Exception as e:
            print(f"[EMAIL ERR] Failed to send email to {recipient}: {str(e)}")
            return False
    else:
        # Mock Email log when SMTP is not configured
        print(f"\n[EMAIL SIMULATION - SMTP NOT CONFIGURED]")
        print(f"From: {sender}")
        print(f"To: {recipient}")
        print(f"Subject: {subject}")
        print(f"Body:\n{body}")
        print(f"----------------------------------------\n")
        return True

@attendance_bp.route('/scan')
@login_required
def scan():
    return render_template('scan.html')

@attendance_bp.route('/attendance/mark', methods=['POST'])
def mark_attendance():
    # Parse scan input
    data = request.get_json() or {}
    user_code = data.get('user_code', '').strip().upper()

    if not user_code:
        return jsonify({'success': False, 'message': 'Invalid QR code data.'}), 400

    # Retrieve user
    user = User.query.filter_by(user_code=user_code).first()
    if not user:
        return jsonify({'success': False, 'message': f'No registered user found for code "{user_code}".'}), 404

    # Prevent duplicate attendance on the same day
    today = datetime.now().date()
    existing_log = Attendance.query.filter_by(user_id=user.id, date=today).first()
    if existing_log:
        return jsonify({
            'success': False, 
            'message': f'Attendance already marked today for {user.name} ({user_code}) at {existing_log.time.strftime("%I:%M %p")}.'
        }), 400

    # Mark attendance
    now = datetime.now()
    check_in_time = now.time()
    
    try:
        new_attendance = Attendance(
            user_id=user.id,
            date=today,
            time=check_in_time,
            status='Present' # Default to Present, can be customized based on time threshold
        )
        db.session.add(new_attendance)
        db.session.commit()
        
        # Async-like simulated or real email sending
        send_attendance_email(user, check_in_time.strftime("%I:%M %p"))
        
        return jsonify({
            'success': True,
            'message': f'Attendance marked successfully!',
            'data': {
                'user_code': user.user_code,
                'name': user.name,
                'department': user.department.name,
                'date': today.strftime('%Y-%m-%d'),
                'time': check_in_time.strftime('%I:%M %p'),
                'status': 'Present'
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
