import os
import shutil
import qrcode
from datetime import datetime, date, time, timedelta
from app import create_app
from database.connection import db
from models.admin import Admin
from models.department import Department
from models.user import User
from models.attendance import Attendance

def clear_existing_qr_codes(app):
    qr_dir = app.config['QR_CODE_FOLDER']
    if os.path.exists(qr_dir):
        # Clear files in folder
        for filename in os.listdir(qr_dir):
            file_path = os.path.join(qr_dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')
    else:
        os.makedirs(qr_dir, exist_ok=True)

def generate_qr_code(user_code, folder):
    qr_filename = f"{user_code}.png"
    qr_filepath = os.path.join(folder, qr_filename)
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(user_code)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(qr_filepath)
    return f"static/qr_codes/{qr_filename}"

def seed_database():
    app = create_app()
    with app.app_context():
        print("Initializing database tables...")
        # Drop and recreate tables to ensure clean seed
        db.drop_all()
        db.create_all()
        
        # Clear old QR codes
        clear_existing_qr_codes(app)

        # 1. Create Default Admin
        admin_username = app.config.get('SEED_ADMIN_USER', 'admin')
        admin_password = app.config.get('SEED_ADMIN_PASS', 'admin123')
        print(f"Creating Admin user: {admin_username}...")
        admin = Admin(username=admin_username, email="admin@attendance-system.com")
        admin.set_password(admin_password)
        db.session.add(admin)

        # 2. Create Departments
        print("Creating Departments...")
        departments_data = [
            {"code": "CS", "name": "Computer Science & Engineering"},
            {"code": "ECE", "name": "Electronics & Communication Engineering"},
            {"code": "IT", "name": "Information Technology"},
            {"code": "ME", "name": "Mechanical Engineering"},
            {"code": "CIVIL", "name": "Civil Engineering"},
        ]
        
        depts = {}
        for d_info in departments_data:
            dept = Department(code=d_info["code"], name=d_info["name"])
            db.session.add(dept)
            depts[d_info["code"]] = dept
            
        # Flush to get IDs
        db.session.flush()

        # 3. Create Sample Students / Employees
        print("Creating Users & Generating QR Codes...")
        users_data = [
            {"user_code": "STD101", "name": "Alice Johnson", "email": "alice.johnson@example.com", "phone": "9876543210", "dept": "CS"},
            {"user_code": "STD102", "name": "Bob Smith", "email": "bob.smith@example.com", "phone": "9876543211", "dept": "CS"},
            {"user_code": "STD103", "name": "Charlie Brown", "email": "charlie.brown@example.com", "phone": "9876543212", "dept": "ECE"},
            {"user_code": "EMP501", "name": "Dr. Sarah Miller", "email": "sarah.miller@example.com", "phone": "9876543213", "dept": "IT"},
            {"user_code": "EMP502", "name": "John Doe", "email": "john.doe@example.com", "phone": "9876543214", "dept": "ME"},
        ]

        users = []
        qr_dir = app.config['QR_CODE_FOLDER']
        for u_info in users_data:
            qr_path = generate_qr_code(u_info["user_code"], qr_dir)
            user = User(
                user_code=u_info["user_code"],
                name=u_info["name"],
                email=u_info["email"],
                phone=u_info["phone"],
                department_id=depts[u_info["dept"]].id,
                qr_code_path=qr_path
            )
            db.session.add(user)
            users.append(user)
            
        db.session.flush()

        # 4. Create Historical Attendance (for last 7 days of charts)
        print("Creating mock attendance history logs...")
        today = datetime.now().date()
        
        # We will mark historical attendance for the last 6 days
        # E.g. Alice and Bob check in daily, Charlie checks in on alternate days
        for i in range(6, 0, -1):
            date_past = today - timedelta(days=i)
            # Skip weekends (Saturday=5, Sunday=6)
            if date_past.weekday() in [5, 6]:
                continue
                
            # Log attendance
            # Date 1: Alice, Bob, Sarah, John present
            # Date 2: Alice, Bob, Charlie present
            # Date 3: Alice, Sarah present
            # Date 4: Bob, John present
            # Date 5: Alice, Bob, Charlie, Sarah, John present
            
            p_indices = []
            if i == 5:
                p_indices = [0, 1, 3, 4]
            elif i == 4:
                p_indices = [0, 1, 2]
            elif i == 3:
                p_indices = [0, 3]
            elif i == 2:
                p_indices = [1, 4]
            elif i == 1:
                p_indices = [0, 1, 2, 3, 4]
                
            for idx in p_indices:
                u = users[idx]
                check_in_time = time(9, 15 + idx * 3, 0) # e.g. 09:15, 09:18, etc.
                status = 'Present'
                if idx == 4:
                    status = 'Late' # John is late
                log = Attendance(
                    user_id=u.id,
                    date=date_past,
                    time=check_in_time,
                    status=status
                )
                db.session.add(log)

        db.session.commit()
        print("Seeding completed successfully!")
        print(f"Default admin login: username={admin_username}, password={admin_password}")

if __name__ == '__main__':
    seed_database()
