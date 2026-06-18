import os
import io
import qrcode
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, current_app, send_file
from models.user import User
from models.department import Department
from database.connection import db
from routes.auth import login_required

user_bp = Blueprint('user', __name__)

@user_bp.route('/users')
@login_required
def index():
    search_query = request.args.get('search', '').strip()
    dept_id = request.args.get('department_id', '')

    query = User.query
    if search_query:
        query = query.filter(
            (User.name.like(f'%{search_query}%')) | 
            (User.user_code.like(f'%{search_query}%')) |
            (User.email.like(f'%{search_query}%'))
        )
    if dept_id:
        query = query.filter(User.department_id == dept_id)

    users = query.order_by(User.name).all()
    departments = Department.query.order_by(Department.name).all()
    
    return render_template('users.html', users=users, departments=departments, search_query=search_query, selected_dept=dept_id)

@user_bp.route('/users/register', methods=['GET', 'POST'])
@login_required
def register():
    departments = Department.query.order_by(Department.name).all()
    
    if request.method == 'POST':
        user_code = request.form.get('user_code', '').strip().upper()
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        department_id = request.form.get('department_id', '')

        # Input Validation
        if not user_code or not name or not email or not department_id:
            flash('ID Code, Name, Email, and Department are required fields.', 'danger')
            return render_template('register.html', departments=departments)

        # Check unique constraints
        existing_code = User.query.filter_by(user_code=user_code).first()
        if existing_code:
            flash(f'User with ID Code "{user_code}" is already registered.', 'danger')
            return render_template('register.html', departments=departments)

        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash(f'User with email "{email}" is already registered.', 'danger')
            return render_template('register.html', departments=departments)

        # Generate unique QR code for the user
        # Directory check
        qr_dir = current_app.config['QR_CODE_FOLDER']
        if not os.path.exists(qr_dir):
            os.makedirs(qr_dir)

        qr_filename = f"{user_code}.png"
        qr_filepath = os.path.join(qr_dir, qr_filename)
        
        # QR Code Generation settings
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        # Store user code in the QR code content
        qr.add_data(user_code)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        
        # Database transaction
        new_user = User(
            user_code=user_code,
            name=name,
            email=email,
            phone=phone,
            department_id=department_id,
            qr_code_path=f"static/qr_codes/{qr_filename}"
        )

        try:
            db.session.add(new_user)
            db.session.commit()
            
            # Save the image only after db commit success
            try:
                img.save(qr_filepath)
            except OSError as e:
                current_app.logger.warning(f"Could not save QR code file to disk: {e}. Serving dynamically.")
            
            flash(f'User "{name}" registered and QR code generated successfully!', 'success')
            return redirect(url_for('user.index'))
        except Exception as e:
            db.session.rollback()
            # If image was saved somehow, remove it
            if os.path.exists(qr_filepath):
                try:
                    os.remove(qr_filepath)
                except:
                    pass
            flash(f'Registration failed: {str(e)}', 'danger')

    return render_template('register.html', departments=departments)

@user_bp.route('/users/profile/<int:user_id>')
@login_required
def profile(user_id):
    user = User.query.get_or_404(user_id)
    # Sort attendance in descending order
    attendances = sorted(user.attendances, key=lambda a: a.date, reverse=True)
    
    # Calculate present days
    total_days = len(attendances)
    
    return render_template('profile.html', user=user, attendances=attendances, total_days=total_days)

@user_bp.route('/users/download-qr/<int:user_id>')
@login_required
def download_qr(user_id):
    user = User.query.get_or_404(user_id)
    
    # Construct full path to QR Code if available
    base_dir = current_app.config['BASE_DIR']
    full_path = os.path.join(base_dir, user.qr_code_path.replace('/', os.sep)) if user.qr_code_path else None
    
    if full_path and os.path.exists(full_path):
        return send_file(full_path, as_attachment=True, download_name=f"{user.user_code}_qrcode.png")
    
    # Fallback to dynamic creation in-memory if physical file not present (e.g. Serverless Vercel)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(user.user_code)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name=f"{user.user_code}_qrcode.png", mimetype='image/png')

@user_bp.route('/qr/<user_code>')
@login_required
def get_qr_code(user_code):
    user = User.query.filter_by(user_code=user_code).first_or_404()
    
    # Try static file first
    qr_dir = current_app.config['QR_CODE_FOLDER']
    qr_filename = f"{user_code}.png"
    qr_filepath = os.path.join(qr_dir, qr_filename)
    
    if os.path.exists(qr_filepath):
        return send_file(qr_filepath, mimetype='image/png')
        
    # Create in memory if static file doesn't exist
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(user_code)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')
