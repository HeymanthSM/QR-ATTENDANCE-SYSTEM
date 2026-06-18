from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.department import Department
from database.connection import db
from routes.auth import login_required

department_bp = Blueprint('department', __name__)

@department_bp.route('/departments', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        code = request.form.get('code', '').strip().upper()
        name = request.form.get('name', '').strip()

        if not code or not name:
            flash('Both Department Code and Name are required.', 'danger')
            return redirect(url_for('department.index'))

        existing_dept = Department.query.filter_by(code=code).first()
        if existing_dept:
            flash(f'Department with code "{code}" already exists.', 'danger')
            return redirect(url_for('department.index'))

        try:
            new_dept = Department(code=code, name=name)
            db.session.add(new_dept)
            db.session.commit()
            flash(f'Department "{name}" ({code}) registered successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating department: {str(e)}', 'danger')

        return redirect(url_for('department.index'))

    departments = Department.query.order_by(Department.code).all()
    return render_template('departments.html', departments=departments)

@department_bp.route('/departments/delete/<int:dept_id>', methods=['POST'])
@login_required
def delete(dept_id):
    dept = Department.query.get_or_404(dept_id)
    try:
        db.session.delete(dept)
        db.session.commit()
        flash(f'Department "{dept.name}" deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting department: {str(e)}', 'danger')
        
    return redirect(url_for('department.index'))
