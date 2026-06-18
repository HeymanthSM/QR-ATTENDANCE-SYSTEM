import io
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, send_file, jsonify, flash, redirect, url_for
import pandas as pd
from database.connection import db
from models.user import User
from models.attendance import Attendance
from models.department import Department
from routes.auth import login_required

reports_bp = Blueprint('reports', __name__)

def get_filtered_query(report_type, start_date_str=None, end_date_str=None):
    today = datetime.now().date()
    query = Attendance.query.join(User)

    if report_type == 'daily':
        query = query.filter(Attendance.date == today)
    elif report_type == 'weekly':
        start_of_week = today - timedelta(days=today.weekday()) # Monday
        query = query.filter(Attendance.date >= start_of_week)
    elif report_type == 'monthly':
        start_of_month = today.replace(day=1)
        query = query.filter(Attendance.date >= start_of_month)
    elif report_type == 'custom':
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                query = query.filter(Attendance.date >= start_date)
            except ValueError:
                pass
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                query = query.filter(Attendance.date <= end_date)
            except ValueError:
                pass
    return query

@reports_bp.route('/reports')
@login_required
def index():
    report_type = request.args.get('type', 'daily') # daily, weekly, monthly, custom
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    dept_id = request.args.get('department_id', '')

    query = get_filtered_query(report_type, start_date, end_date)

    if dept_id:
        query = query.filter(User.department_id == dept_id)

    logs = query.order_by(Attendance.date.desc(), Attendance.time.desc()).all()
    departments = Department.query.order_by(Department.name).all()

    return render_template(
        'reports.html',
        logs=logs,
        departments=departments,
        report_type=report_type,
        start_date=start_date,
        end_date=end_date,
        selected_dept=dept_id
    )

@reports_bp.route('/reports/export/<format_type>')
@login_required
def export(format_type):
    report_type = request.args.get('type', 'daily')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    dept_id = request.args.get('department_id', '')

    query = get_filtered_query(report_type, start_date, end_date)
    if dept_id:
        query = query.filter(User.department_id == dept_id)

    logs = query.order_by(Attendance.date.desc(), Attendance.time.desc()).all()

    if not logs:
        flash('No records found to export.', 'warning')
        return redirect(url_for('reports.index', type=report_type, start_date=start_date, end_date=end_date, department_id=dept_id))

    # Prepare data for pandas DataFrame
    data = []
    for log in logs:
        data.append({
            'Date': log.date.strftime('%Y-%m-%d'),
            'Time': log.time.strftime('%I:%M %p'),
            'ID Code': log.user.user_code,
            'Name': log.user.name,
            'Department': log.user.department.name if log.user.department else 'N/A',
            'Email': log.user.email,
            'Phone': log.user.phone or 'N/A',
            'Status': log.status
        })

    df = pd.DataFrame(data)

    if format_type == 'csv':
        # Export to CSV
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        filename = f"attendance_report_{report_type}_{datetime.now().strftime('%Y%m%d')}.csv"
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )

    elif format_type == 'excel':
        # Export to Excel (XLSX)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Attendance Logs')
            
            # Simple column width adjustment using openpyxl
            workbook = writer.book
            worksheet = writer.sheets['Attendance Logs']
            for col in worksheet.columns:
                max_len = max(len(str(cell.value or '')) for cell in col)
                col_letter = col[0].column_letter
                worksheet.column_dimensions[col_letter].width = max(max_len + 3, 12)
                
        output.seek(0)
        
        filename = f"attendance_report_{report_type}_{datetime.now().strftime('%Y%m%d')}.xlsx"
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )

    else:
        flash('Invalid export format.', 'danger')
        return redirect(url_for('reports.index'))

@reports_bp.route('/reports/api/analytics')
@login_required
def analytics_data():
    """
    Returns JSON endpoint data for attendance trends (last 7 days present counts)
    and department distribution.
    """
    # 1. Trend analysis (Last 7 active days)
    today = datetime.now().date()
    dates = [today - timedelta(days=i) for i in range(6, -1, -1)]
    
    dates_str = [d.strftime('%b %d') for d in dates]
    attendance_counts = []
    
    for d in dates:
        count = Attendance.query.filter_by(date=d).count()
        attendance_counts.append(count)
        
    # 2. Department distribution (Present count by department for today)
    departments = Department.query.all()
    dept_labels = []
    dept_data = []
    
    for dept in departments:
        dept_labels.append(dept.code)
        # Count users of this department who checked in today
        count = Attendance.query.join(User).filter(
            Attendance.date == today,
            User.department_id == dept.id
        ).count()
        dept_data.append(count)

    return jsonify({
        'trend': {
            'labels': dates_str,
            'data': attendance_counts
        },
        'departments': {
            'labels': dept_labels,
            'data': dept_data
        }
    })
