import os
import csv
import io
from functools import wraps
from datetime import datetime, date, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, Response, session, g
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, Department, Position, Employee, EmployeeDocument, Attendance, LeaveRequest, Payroll, Province, District, Commune, User, OFFICIAL_DEPARTMENTS, OFFICIAL_POSITIONS, OFFICIAL_POSITIONS_DATA
from payroll_calculator import compute_employee_payroll, KHR_PER_USD

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'cambodia-hrms-secret-key-2026')
db_uri = os.environ.get('DATABASE_URL', 'sqlite:///hrms.db')
if db_uri and db_uri.startswith('postgres://'):
    db_uri = db_uri.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Upload folders
UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')
AVATAR_FOLDER = os.path.join(UPLOAD_FOLDER, 'avatars')
DOC_FOLDER = os.path.join(UPLOAD_FOLDER, 'documents')

os.makedirs(AVATAR_FOLDER, exist_ok=True)
os.makedirs(DOC_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

db.init_app(app)


def ensure_organization_structure():
    """Ensures only the 7 official offices and 5 official positions exist, deleting any other departments."""
    try:
        target_codes = [d['code'] for d in OFFICIAL_DEPARTMENTS]
        office_map = {}

        # 1. Upsert official 7 offices
        for d_data in OFFICIAL_DEPARTMENTS:
            dept = Department.query.filter(
                (Department.code == d_data['code']) | (Department.name_kh == d_data['name_kh'])
            ).first()
            if not dept:
                dept = Department(
                    name_kh=d_data['name_kh'],
                    name_en=d_data['name_en'],
                    code=d_data['code'],
                    description=d_data['description']
                )
                db.session.add(dept)
                db.session.flush()
            else:
                dept.name_kh = d_data['name_kh']
                dept.name_en = d_data['name_en']
                dept.code = d_data['code']
                dept.description = d_data['description']
            office_map[d_data['code']] = dept

        db.session.commit()

        # 2. Upsert official 5 positions into Position table
        for p_data in OFFICIAL_POSITIONS_DATA:
            pos = Position.query.filter_by(name_kh=p_data['name_kh']).first()
            if not pos:
                pos = Position(
                    name_kh=p_data['name_kh'],
                    name_en=p_data['name_en'],
                    code=p_data['code'],
                    description=p_data['description']
                )
                db.session.add(pos)
            else:
                if not pos.name_en: pos.name_en = p_data['name_en']
                if not pos.code: pos.code = p_data['code']
                if not pos.description: pos.description = p_data['description']
        db.session.commit()

        it_office = office_map.get('OFF-IT')
        hr_office = office_map.get('OFF-HR')
        acc_office = office_map.get('OFF-ACC')
        mkt_office = office_map.get('OFF-MKT')
        pers_office = office_map.get('OFF-PERS')

        # 3. Reassign employees attached to old departments and normalize position
        for emp in Employee.query.all():
            if emp.department and emp.department.code not in target_codes:
                old_name = emp.department.name_kh
                old_code = emp.department.code
                if 'ព័ត៌មានវិទ្យា' in old_name or 'IT' in old_code:
                    emp.department_id = it_office.id if it_office else emp.department_id
                elif 'ធនធានមនុស្ស' in old_name or 'HR' in old_code:
                    emp.department_id = hr_office.id if hr_office else emp.department_id
                elif 'គណនេយ្យ' in old_name or 'ហិរញ្ញវត្ថុ' in old_name or 'FIN' in old_code:
                    emp.department_id = acc_office.id if acc_office else emp.department_id
                elif 'ទីផ្សារ' in old_name or 'MKT' in old_code:
                    emp.department_id = mkt_office.id if mkt_office else emp.department_id
                else:
                    emp.department_id = pers_office.id if pers_office else emp.department_id

            # Normalize position to the 5 official positions
            if emp.position not in OFFICIAL_POSITIONS:
                if 'អគ្គនាយករង' in emp.position:
                    emp.position = 'អគ្គនាយករង'
                elif 'អគ្គនាយក' in emp.position:
                    emp.position = 'អគ្គនាយក'
                elif 'ប្រធាន' in emp.position or 'Manager' in emp.position or 'Lead' in emp.position or 'Chief' in emp.position:
                    emp.position = 'ប្រធានការិយាល័យ'
                elif 'អនុប្រធាន' in emp.position or 'Senior' in emp.position or 'Assistant' in emp.position:
                    emp.position = 'អនុប្រធានការិយាល័យ'
                else:
                    emp.position = 'បុគ្គលិក'

        db.session.commit()

        # 4. Delete any departments NOT in target 7 offices ("ក្រៅពីនេះ សុំលុបចោល")
        old_depts = Department.query.filter(~Department.code.in_(target_codes)).all()
        for od in old_depts:
            for emp in od.employees:
                emp.department_id = pers_office.id
            db.session.delete(od)
        db.session.commit()
        print("Organization structure ensured: 7 offices, 5 positions. Other departments removed.")
    except Exception as e:
        db.session.rollback()
        print("ensure_organization_structure error:", e)


def ensure_default_admin():
    """Ensure database schema is up-to-date and permanent ADMIN account exists with password syd001"""
    try:
        # Check SQLite table column approval_status
        import sqlite3
        db_path = os.path.join(app.instance_path, 'hrms.db')
        if os.path.exists(db_path):
            con = sqlite3.connect(db_path)
            cur = con.cursor()
            cur.execute("PRAGMA table_info(users);")
            cols = [r[1] for r in cur.fetchall()]
            if 'approval_status' not in cols:
                cur.execute("ALTER TABLE users ADD COLUMN approval_status VARCHAR(30) DEFAULT 'approved';")
                con.commit()
            con.close()

        # Permanent super admin: ADMIN / syd001
        admin = User.query.filter(User.username.ilike('ADMIN')).first()
        if admin:
            admin.username = 'ADMIN'
            admin.role = 'admin'
            admin.set_password('syd001')
            admin.is_active = True
            admin.approval_status = 'approved'
            admin.employee_name = 'អ្នកគ្រប់គ្រងប្រព័ន្ធ (Super Admin)'
        else:
            admin = User(
                username='ADMIN',
                role='admin',
                phone='012 345 678',
                employee_name='អ្នកគ្រប់គ្រងប្រព័ន្ធ (Super Admin)',
                is_active=True,
                approval_status='approved'
            )
            admin.set_password('syd001')
            db.session.add(admin)
        db.session.commit()
        print("Permanent ADMIN account ensured: ADMIN / syd001")
    except Exception as e:
        db.session.rollback()
        print("ensure_default_admin error:", e)


with app.app_context():
    db.create_all()
    ensure_organization_structure()
    ensure_default_admin()


@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = db.session.get(User, user_id)
        if not g.user or not g.user.is_active:
            session.clear()
            g.user = None


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None and not app.config.get('TESTING', False):
            flash('សូមចូលគណនីជាមុនសិនដើម្បីបន្ត។', 'warning')
            return redirect(url_for('login', next=request.url))
        return view(*args, **kwargs)
    return wrapped_view


def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None and not app.config.get('TESTING', False):
            flash('សូមចូលគណនីជាមុនសិនដើម្បីបន្ត។', 'warning')
            return redirect(url_for('login', next=request.url))
        if g.user and g.user.role != 'admin':
            flash('លោកអ្នកមិនមានសិទ្ធិគ្រប់គ្រងផ្នែកនេះទេ (សម្រាប់តែ Admin)!', 'danger')
            return redirect(url_for('dashboard'))
        return view(*args, **kwargs)
    return wrapped_view


# Helper template context
@app.context_processor
def inject_global_vars():
    today = date.today()
    current_month = today.strftime("%Y-%m")
    try:
        pending_leaves_count = LeaveRequest.query.filter_by(status='pending').count()
    except Exception:
        pending_leaves_count = 0
    try:
        if hasattr(g, 'user') and g.user and g.user.role == 'admin':
            pending_users_count = User.query.filter_by(approval_status='pending').count()
        else:
            pending_users_count = 0
    except Exception:
        pending_users_count = 0

    try:
        positions_objs = Position.query.order_by(Position.id.asc()).all()
        positions_list = [p.name_kh for p in positions_objs] if positions_objs else OFFICIAL_POSITIONS
    except Exception:
        positions_list = OFFICIAL_POSITIONS

    return {
        'today': today,
        'current_month': current_month,
        'pending_leaves_count': pending_leaves_count,
        'pending_users_count': pending_users_count,
        'departments_list': Department.query.order_by(Department.id.asc()).all() if Department.query.first() else [],
        'provinces_list': Province.query.order_by(Province.code).all() if Province.query.first() else [],
        'official_positions': positions_list,
        'current_user': g.user if hasattr(g, 'user') else None
    }


# ==========================================
# CAMBODIA ADMINISTRATIVE GEOGRAPHY APIS
# ==========================================
@app.route('/api/geo/provinces')
def api_geo_provinces():
    provinces = Province.query.order_by(Province.code).all()
    return jsonify([p.to_dict() for p in provinces])


@app.route('/api/geo/districts')
def api_geo_districts():
    p_code = request.args.get('province_code', '').strip()
    p_name = request.args.get('province_name', '').strip()
    
    query = District.query
    if p_code:
        query = query.filter_by(province_code=p_code)
    elif p_name:
        clean_name = p_name.replace('ខេត្ត', '').replace('រាជធានី', '').strip()
        prov = Province.query.filter(Province.name_kh.ilike(f'%{clean_name}%')).first()
        if prov:
            query = query.filter_by(province_code=prov.code)
            
    districts = query.order_by(District.code).all()
    return jsonify([d.to_dict() for d in districts])


@app.route('/api/geo/communes')
def api_geo_communes():
    d_code = request.args.get('district_code', '').strip()
    d_name = request.args.get('district_name', '').strip()
    
    query = Commune.query
    if d_code:
        query = query.filter_by(district_code=d_code)
    elif d_name:
        clean_name = d_name.replace('ស្រុក', '').replace('ខណ្ឌ', '').replace('ក្រុង', '').strip()
        dist = District.query.filter(District.name_kh.ilike(f'%{clean_name}%')).first()
        if dist:
            query = query.filter_by(district_code=dist.code)
            
    communes = query.order_by(Commune.code).all()
    return jsonify([c.to_dict() for c in communes])


# ==========================================
# CAMBODIA ADMINISTRATIVE GEOGRAPHY EXPLORER
# ==========================================
@app.route('/geo-locations')
def geo_locations():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    province_code = request.args.get('province_code', '').strip()
    district_code = request.args.get('district_code', '').strip()
    
    query = Commune.query.join(District, Commune.district_code == District.code).join(Province, Commune.province_code == Province.code)
    
    if province_code:
        query = query.filter(Commune.province_code == province_code)
    if district_code:
        query = query.filter(Commune.district_code == district_code)
    if search:
        query = query.filter(
            (Commune.name_kh.ilike(f'%{search}%')) |
            (Commune.name_en.ilike(f'%{search}%')) |
            (Commune.code.ilike(f'%{search}%')) |
            (District.name_kh.ilike(f'%{search}%')) |
            (District.name_en.ilike(f'%{search}%')) |
            (Province.name_kh.ilike(f'%{search}%')) |
            (Province.name_en.ilike(f'%{search}%'))
        )
        
    pagination = query.order_by(Commune.code.asc()).paginate(page=page, per_page=30, error_out=False)
    
    provinces = Province.query.order_by(Province.code).all()
    districts = District.query.filter_by(province_code=province_code).order_by(District.code).all() if province_code else District.query.order_by(District.code).all()
    
    total_provinces = Province.query.count()
    total_districts = District.query.count()
    total_communes = Commune.query.count()
    
    return render_template(
        'geo/list.html',
        pagination=pagination,
        communes=pagination.items,
        provinces=provinces,
        districts=districts,
        selected_province=province_code,
        selected_district=district_code,
        search=search,
        total_provinces=total_provinces,
        total_districts=total_districts,
        total_communes=total_communes
    )


@app.route('/geo-locations/sync', methods=['POST'])
def geo_locations_sync():
    from import_cambodia_geo import import_cambodia_locations
    csv_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'doc', 'CambodiaCommuneList2025.csv')
    res = import_cambodia_locations(csv_file)
    if res.get('success'):
        flash(f'បានធ្វើបច្ចុប្បន្នភាពទិន្នន័យភូមិសាស្ត្រកម្ពុជាពី CSV ដោយជោគជ័យ! សរុប {res["provinces"]} ខេត្ត/រាជធានី, {res["districts"]} ក្រុង/ស្រុក/ខណ្ឌ, និង {res["communes"]} ឃុំ/សង្កាត់។', 'success')
    else:
        flash(f'បរាជ័យក្នុងការធ្វើបច្ចុប្បន្នភាព៖ {res.get("error")}', 'danger')
    return redirect(url_for('geo_locations'))


# ==========================================
# AUTHENTICATION & USER MANAGEMENT
# ==========================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.user:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        remember = bool(request.form.get('remember'))
        
        if not username or not password:
            flash('សូមបំពេញគណនីប្រើប្រាស់ និងលេខសម្ងាត់!', 'warning')
            return render_template('auth/login.html', username=username)
            
        user = User.query.filter(User.username.ilike(username)).first()
        if not user or not user.check_password(password):
            flash('គណនីប្រើប្រាស់ ឬលេខសម្ងាត់មិនត្រឹមត្រូវទេ!', 'danger')
            return render_template('auth/login.html', username=username)
            
        if user.approval_status == 'pending':
            flash('គណនីនេះកំពុងស្ថិតក្នុងការរង់ចាំការអនុម័តពី ADMIN នៅឡើយ! សូមរង់ចាំការអនុម័ត ឬទាក់ទង ADMIN។', 'warning')
            return render_template('auth/login.html', username=username)

        if user.approval_status == 'rejected':
            flash('គណនីនេះត្រូវបានបដិសេធដោយ ADMIN! សូមទាក់ទង ADMIN សម្រាប់ព័ត៌មានបន្ថែម។', 'danger')
            return render_template('auth/login.html', username=username)

        if not user.is_active:
            flash('គណនីនេះត្រូវបានផ្អាកដំណើរការ! សូមទាក់ទងរដ្ឋបាល (ADMIN)។', 'danger')
            return render_template('auth/login.html', username=username)
            
        # Login success
        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role
        session.permanent = remember
        
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        flash(f'សូមស្វាគមន៍មកកាន់ប្រព័ន្ធ, {user.employee_name} ({user.role_kh})!', 'success')
        next_url = request.args.get('next')
        if next_url and next_url.startswith('/'):
            return redirect(next_url)
        return redirect(url_for('dashboard'))
        
    return render_template('auth/login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    employees = Employee.query.order_by(Employee.full_name_kh.asc()).all()
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        role = request.form.get('role', 'staff').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        phone = request.form.get('phone', '').strip()
        employee_name = request.form.get('employee_name', '').strip()
        employee_id_raw = request.form.get('employee_id', '').strip()
        employee_id = int(employee_id_raw) if employee_id_raw and employee_id_raw.isdigit() else None
        
        # If linked employee chosen and employee_name is empty, autofill from employee
        if employee_id:
            emp = db.session.get(Employee, employee_id)
            if emp and not employee_name:
                employee_name = emp.full_name_kh
                if not phone and emp.phone:
                    phone = emp.phone

        # Validation
        errors = []
        if not username:
            errors.append('សូមបញ្ចូលគណនីប្រើប្រាស់ (Username)')
        elif len(username) < 3:
            errors.append('គណនីប្រើប្រាស់ត្រូវមានយ៉ាងហោចណាស់ ៣ តួអក្សរ')
        elif username.upper() == 'ADMIN':
            errors.append('គណនី ADMIN គឺជាគណនីអចិន្ត្រៃយ៍របស់ប្រព័ន្ធ មិនអាចចុះឈ្មោះស្ទួនបានទេ!')
        elif User.query.filter(User.username.ilike(username)).first():
            errors.append('គណនីប្រើប្រាស់នេះមានរួចហើយក្នុងប្រព័ន្ធ! សូមជ្រើសរើសឈ្មោះផ្សេង។')
            
        if not employee_name:
            errors.append('សូមបញ្ចូលឈ្មោះបុគ្គលិក')
            
        if not password:
            errors.append('សូមបញ្ចូលលេខសម្ងាត់')
        elif len(password) < 6:
            errors.append('លេខសម្ងាត់ត្រូវមានយ៉ាងហោចណាស់ ៦ តួអក្សរ')
            
        if password != confirm_password:
            errors.append('លេខសម្ងាត់ និងការបញ្ជាក់លេខសម្ងាត់មិនត្រូវគ្នាទេ')
            
        valid_roles = ['admin', 'hr', 'accountant', 'staff']
        if role not in valid_roles:
            role = 'staff'
            
        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template(
                'auth/register.html',
                employees=employees,
                username=username,
                role=role,
                phone=phone,
                employee_name=employee_name,
                employee_id=employee_id
            )
            
        # Create user awaiting ADMIN approval
        new_user = User(
            username=username,
            role=role,
            phone=phone,
            employee_name=employee_name,
            employee_id=employee_id,
            is_active=False,
            approval_status='pending'
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        flash(f'បានចុះឈ្មោះគណនី "{username}" ដោយជោគជ័យ! គណនីនេះត្រូវរង់ចាំការអនុម័តពី ADMIN ជាមុនសិន ទើបអាចចូលប្រើប្រាស់បាន។', 'warning')
        return redirect(url_for('login'))
        
    return render_template('auth/register.html', employees=employees)


@app.route('/logout')
def logout():
    session.clear()
    flash('លោកអ្នកបានចាកចេញពីប្រព័ន្ធដោយជោគជ័យ។', 'info')
    return redirect(url_for('login'))


@app.route('/users')
@admin_required
def user_list():
    query = User.query
    
    search = request.args.get('search', '').strip()
    role_filter = request.args.get('role', '').strip()
    status_filter = request.args.get('status', '').strip()
    approval_filter = request.args.get('approval', '').strip()
    
    if search:
        query = query.filter(
            (User.username.ilike(f'%{search}%')) |
            (User.employee_name.ilike(f'%{search}%')) |
            (User.phone.ilike(f'%{search}%'))
        )
    if role_filter:
        query = query.filter_by(role=role_filter)
    if status_filter != '':
        is_act = True if status_filter in ['1', 'true', 'active'] else False
        query = query.filter_by(is_active=is_act)
    if approval_filter:
        query = query.filter_by(approval_status=approval_filter)
        
    users = query.order_by(User.created_at.desc()).all()
    employees = Employee.query.order_by(Employee.full_name_kh.asc()).all()
    
    total_users = User.query.count()
    admin_users = User.query.filter_by(role='admin').count()
    hr_fin_users = User.query.filter(User.role.in_(['hr', 'accountant'])).count()
    active_users = User.query.filter_by(is_active=True).count()
    pending_users = User.query.filter_by(approval_status='pending').count()
    
    return render_template(
        'users/list.html',
        users=users,
        employees=employees,
        search=search,
        selected_role=role_filter,
        selected_status=status_filter,
        selected_approval=approval_filter,
        total_users=total_users,
        admin_users=admin_users,
        hr_fin_users=hr_fin_users,
        active_users=active_users,
        pending_users=pending_users
    )


@app.route('/users/create', methods=['POST'])
@admin_required
def user_create():
    username = request.form.get('username', '').strip()
    role = request.form.get('role', 'staff').strip()
    password = request.form.get('password', '').strip()
    phone = request.form.get('phone', '').strip()
    employee_name = request.form.get('employee_name', '').strip()
    employee_id_raw = request.form.get('employee_id', '').strip()
    employee_id = int(employee_id_raw) if employee_id_raw and employee_id_raw.isdigit() else None
    is_active = True if request.form.get('is_active') == '1' else False
    
    if employee_id:
        emp = db.session.get(Employee, employee_id)
        if emp and not employee_name:
            employee_name = emp.full_name_kh
            if not phone and emp.phone:
                phone = emp.phone
                
    if not username or not password or not employee_name:
        flash('សូមបំពេញគណនីប្រើប្រាស់ ឈ្មោះបុគ្គលិក និងលេខសម្ងាត់!', 'danger')
        return redirect(url_for('user_list'))
        
    if User.query.filter(User.username.ilike(username)).first():
        flash('គណនីប្រើប្រាស់នេះមានរួចហើយ!', 'danger')
        return redirect(url_for('user_list'))
        
    new_user = User(
        username=username,
        role=role if role in ['admin', 'hr', 'accountant', 'staff'] else 'staff',
        phone=phone,
        employee_name=employee_name,
        employee_id=employee_id,
        is_active=is_active,
        approval_status='approved'
    )
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    
    flash(f'បានបង្កើតគណនី "{username}" ដោយជោគជ័យ!', 'success')
    return redirect(url_for('user_list'))


@app.route('/users/<int:user_id>/approve', methods=['POST'])
@admin_required
def user_approve(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash('រកមិនឃើញគណនីនេះទេ!', 'danger')
        return redirect(url_for('user_list'))
        
    user.approval_status = 'approved'
    user.is_active = True
    db.session.commit()
    flash(f'បានអនុម័តគណនី "{user.username}" ឱ្យចូលប្រើប្រាស់ប្រព័ន្ធដោយជោគជ័យ!', 'success')
    return redirect(url_for('user_list'))


@app.route('/users/<int:user_id>/reject', methods=['POST'])
@admin_required
def user_reject(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash('រកមិនឃើញគណនីនេះទេ!', 'danger')
        return redirect(url_for('user_list'))
        
    if user.is_permanent_admin:
        flash('មិនអាចបដិសេធគណនីអចិន្ត្រៃយ៍ ADMIN បានទេ!', 'danger')
        return redirect(url_for('user_list'))
        
    user.approval_status = 'rejected'
    user.is_active = False
    db.session.commit()
    flash(f'បានបដិសេធគណនី "{user.username}"!', 'warning')
    return redirect(url_for('user_list'))


@app.route('/users/<int:user_id>/edit', methods=['POST'])
@admin_required
def user_edit(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash('រកមិនឃើញគណនីនេះទេ!', 'danger')
        return redirect(url_for('user_list'))
        
    employee_name = request.form.get('employee_name', '').strip()
    role = request.form.get('role', user.role).strip()
    phone = request.form.get('phone', '').strip()
    employee_id_raw = request.form.get('employee_id', '').strip()
    employee_id = int(employee_id_raw) if employee_id_raw and employee_id_raw.isdigit() else None
    is_active = True if request.form.get('is_active') == '1' else False
    approval_status = request.form.get('approval_status', user.approval_status).strip()
    
    if not employee_name:
        flash('សូមបំពេញឈ្មោះបុគ្គលិក!', 'danger')
        return redirect(url_for('user_list'))
        
    # Protection for permanent ADMIN
    if user.is_permanent_admin:
        if role != 'admin':
            flash('មិនអាចប្តូរតួនាទីគណនីអចិន្ត្រៃយ៍ ADMIN បានទេ!', 'danger')
            return redirect(url_for('user_list'))
        if not is_active:
            flash('មិនអាចផ្អាកដំណើរការគណនីអចិន្ត្រៃយ៍ ADMIN បានទេ!', 'danger')
            return redirect(url_for('user_list'))

    # Prevent removing last active admin
    if user.role == 'admin' and (role != 'admin' or not is_active):
        admin_count = User.query.filter_by(role='admin', is_active=True).count()
        if admin_count <= 1:
            flash('មិនអាចផ្អាក ឬដកសិទ្ធិ Admin ចុងក្រោយនៃប្រព័ន្ធបានទេ!', 'danger')
            return redirect(url_for('user_list'))

    user.employee_name = employee_name
    user.role = role if role in ['admin', 'hr', 'accountant', 'staff'] else user.role
    user.phone = phone
    user.employee_id = employee_id
    user.is_active = is_active
    if approval_status in ['approved', 'pending', 'rejected']:
        user.approval_status = approval_status
    db.session.commit()
    
    flash(f'បានកែប្រែទិន្នន័យគណនី "{user.username}" ដោយជោគជ័យ!', 'success')
    return redirect(url_for('user_list'))


@app.route('/users/<int:user_id>/change-password', methods=['POST'])
@admin_required
def user_change_password(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash('រកមិនឃើញគណនីនេះទេ!', 'danger')
        return redirect(url_for('user_list'))
        
    new_password = request.form.get('new_password', '').strip()
    confirm_password = request.form.get('confirm_password', '').strip()
    
    if not new_password or len(new_password) < 6:
        flash('លេខសម្ងាត់ថ្មីត្រូវមានយ៉ាងតិច ៦ តួអក្សរ!', 'danger')
        return redirect(url_for('user_list'))
        
    if new_password != confirm_password:
        flash('លេខសម្ងាត់ថ្មី និងការបញ្ជាក់លេខសម្ងាត់មិនត្រូវគ្នាទេ!', 'danger')
        return redirect(url_for('user_list'))
        
    user.set_password(new_password)
    db.session.commit()
    flash(f'បានប្តូរលេខសម្ងាត់សម្រាប់គណនី "{user.username}" ដោយជោគជ័យ!', 'success')
    return redirect(url_for('user_list'))


@app.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@admin_required
def user_toggle_status(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash('រកមិនឃើញគណនីនេះទេ!', 'danger')
        return redirect(url_for('user_list'))
        
    if user.is_permanent_admin:
        flash('មិនអាចផ្អាកដំណើរការគណនីអចិន្ត្រៃយ៍ ADMIN បានទេ!', 'danger')
        return redirect(url_for('user_list'))
        
    if g.user and g.user.id == user.id:
        flash('លោកអ្នកមិនអាចផ្អាកដំណើរការគណនីផ្ទាល់ខ្លួនបានទេ!', 'danger')
        return redirect(url_for('user_list'))
        
    if user.role == 'admin' and user.is_active:
        admin_count = User.query.filter_by(role='admin', is_active=True).count()
        if admin_count <= 1:
            flash('មិនអាចផ្អាក Admin ចុងក្រោយនៃប្រព័ន្ធបានទេ!', 'danger')
            return redirect(url_for('user_list'))
            
    user.is_active = not user.is_active
    db.session.commit()
    status_text = "ដំណើរការឡើងវិញ" if user.is_active else "ផ្អាកដំណើរការ"
    flash(f'បាន{status_text}គណនី "{user.username}"!', 'success')
    return redirect(url_for('user_list'))


@app.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def user_delete(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash('រកមិនឃើញគណនីនេះទេ!', 'danger')
        return redirect(url_for('user_list'))
        
    if user.is_permanent_admin:
        flash('មិនអាចលុបគណនីអចិន្ត្រៃយ៍ ADMIN បានទេ!', 'danger')
        return redirect(url_for('user_list'))
        
    if g.user and g.user.id == user.id:
        flash('លោកអ្នកមិនអាចលុបគណនីផ្ទាល់ខ្លួនដែលកំពុងប្រើប្រាស់បានទេ!', 'danger')
        return redirect(url_for('user_list'))
        
    if user.role == 'admin':
        admin_count = User.query.filter_by(role='admin', is_active=True).count()
        if admin_count <= 1:
            flash('មិនអាចលុប Admin ចុងក្រោយនៃប្រព័ន្ធបានទេ!', 'danger')
            return redirect(url_for('user_list'))
            
    username = user.username
    db.session.delete(user)
    db.session.commit()
    flash(f'បានលុបគណនី "{username}" ដោយជោគជ័យ!', 'success')
    return redirect(url_for('user_list'))


# ==========================================
# ORGANIZATION & ROLES/POSITIONS MANAGEMENT
# ==========================================

@app.route('/organization')
@admin_required
def organization_manage():
    active_tab = request.args.get('tab', 'departments')
    departments = Department.query.order_by(Department.id.asc()).all()
    positions = Position.query.order_by(Position.id.asc()).all()
    total_employees = Employee.query.count()
    
    return render_template(
        'organization/manage.html',
        departments=departments,
        positions=positions,
        active_tab=active_tab,
        total_employees=total_employees
    )


# --- DEPARTMENTS / OFFICES CRUD ---

@app.route('/organization/departments/create', methods=['POST'])
@admin_required
def department_create():
    name_kh = request.form.get('name_kh', '').strip()
    name_en = request.form.get('name_en', '').strip()
    code = request.form.get('code', '').strip().upper()
    description = request.form.get('description', '').strip()
    
    if not name_kh or not code:
        flash('សូមបំពេញឈ្មោះការិយាល័យ និងកូដសម្គាល់!', 'danger')
        return redirect(url_for('organization_manage', tab='departments'))
        
    if Department.query.filter_by(code=code).first():
        flash(f'កូដសម្គាល់ "{code}" មានរួចហើយ! សូមជ្រើសរើសកូដផ្សេង។', 'danger')
        return redirect(url_for('organization_manage', tab='departments'))

    if Department.query.filter_by(name_kh=name_kh).first():
        flash(f'ការិយាល័យ "{name_kh}" មានក្នុងប្រព័ន្ធរួចហើយ!', 'danger')
        return redirect(url_for('organization_manage', tab='departments'))

    dept = Department(
        name_kh=name_kh,
        name_en=name_en or name_kh,
        code=code,
        description=description
    )
    db.session.add(dept)
    db.session.commit()
    flash(f'បានបង្កើតការិយាល័យ "{name_kh}" ({code}) ដោយជោគជ័យ!', 'success')
    return redirect(url_for('organization_manage', tab='departments'))


@app.route('/organization/departments/<int:dept_id>/edit', methods=['POST'])
@admin_required
def department_edit(dept_id):
    dept = db.session.get(Department, dept_id)
    if not dept:
        flash('រកមិនឃើញការិយាល័យនេះទេ!', 'danger')
        return redirect(url_for('organization_manage', tab='departments'))
        
    name_kh = request.form.get('name_kh', '').strip()
    name_en = request.form.get('name_en', '').strip()
    code = request.form.get('code', '').strip().upper()
    description = request.form.get('description', '').strip()
    
    if not name_kh or not code:
        flash('សូមបំពេញឈ្មោះការិយាល័យ និងកូដសម្គាល់!', 'danger')
        return redirect(url_for('organization_manage', tab='departments'))
        
    existing_code = Department.query.filter(Department.code == code, Department.id != dept_id).first()
    if existing_code:
        flash(f'កូដ "{code}" ត្រូវបានប្រើប្រាស់ដោយការិយាល័យផ្សេងរួចហើយ!', 'danger')
        return redirect(url_for('organization_manage', tab='departments'))

    dept.name_kh = name_kh
    dept.name_en = name_en or name_kh
    dept.code = code
    dept.description = description
    db.session.commit()
    
    flash(f'បានកែប្រែព័ត៌មានការិយាល័យ "{name_kh}" ដោយជោគជ័យ!', 'success')
    return redirect(url_for('organization_manage', tab='departments'))


@app.route('/organization/departments/<int:dept_id>/delete', methods=['POST'])
@admin_required
def department_delete(dept_id):
    dept = db.session.get(Department, dept_id)
    if not dept:
        flash('រកមិនឃើញការិយាល័យនេះទេ!', 'danger')
        return redirect(url_for('organization_manage', tab='departments'))
        
    emp_count = len(dept.employees)
    if emp_count > 0:
        flash(f'មិនអាចលុបការិយាល័យ "{dept.name_kh}" បានទេ ពីព្រោះមានបុគ្គលិកចំនួន {emp_count} នាក់កំពុងបំពេញការងារនៅទីនេះ! សូមផ្ទេរបុគ្គលិកចេញជាមុនសិន។', 'danger')
        return redirect(url_for('organization_manage', tab='departments'))

    name_kh = dept.name_kh
    db.session.delete(dept)
    db.session.commit()
    flash(f'បានលុបការិយាល័យ "{name_kh}" ដោយជោគជ័យ!', 'success')
    return redirect(url_for('organization_manage', tab='departments'))


# --- POSITIONS / ROLES CRUD ---

@app.route('/organization/positions/create', methods=['POST'])
@admin_required
def position_create():
    name_kh = request.form.get('name_kh', '').strip()
    name_en = request.form.get('name_en', '').strip()
    code = request.form.get('code', '').strip().upper()
    description = request.form.get('description', '').strip()
    
    if not name_kh:
        flash('សូមបំពេញឈ្មោះតួនាទីជាភាសាខ្មែរ!', 'danger')
        return redirect(url_for('organization_manage', tab='positions'))
        
    if Position.query.filter_by(name_kh=name_kh).first():
        flash(f'តួនាទី "{name_kh}" មានក្នុងប្រព័ន្ធរួចហើយ!', 'danger')
        return redirect(url_for('organization_manage', tab='positions'))

    if code and Position.query.filter_by(code=code).first():
        flash(f'កូដតួនាទី "{code}" មានរួចហើយ!', 'danger')
        return redirect(url_for('organization_manage', tab='positions'))

    pos = Position(
        name_kh=name_kh,
        name_en=name_en,
        code=code or None,
        description=description
    )
    db.session.add(pos)
    db.session.commit()
    flash(f'បានបង្កើតតួនាទីថ្មី "{name_kh}" ដោយជោគជ័យ!', 'success')
    return redirect(url_for('organization_manage', tab='positions'))


@app.route('/organization/positions/<int:pos_id>/edit', methods=['POST'])
@admin_required
def position_edit(pos_id):
    pos = db.session.get(Position, pos_id)
    if not pos:
        flash('រកមិនឃើញតួនាទីនេះទេ!', 'danger')
        return redirect(url_for('organization_manage', tab='positions'))
        
    name_kh = request.form.get('name_kh', '').strip()
    name_en = request.form.get('name_en', '').strip()
    code = request.form.get('code', '').strip().upper()
    description = request.form.get('description', '').strip()
    
    if not name_kh:
        flash('សូមបំពេញឈ្មោះតួនាទី!', 'danger')
        return redirect(url_for('organization_manage', tab='positions'))
        
    existing = Position.query.filter(Position.name_kh == name_kh, Position.id != pos_id).first()
    if existing:
        flash(f'ឈ្មោះតួនាទី "{name_kh}" មានរួចហើយ!', 'danger')
        return redirect(url_for('organization_manage', tab='positions'))

    old_name = pos.name_kh
    pos.name_kh = name_kh
    pos.name_en = name_en
    pos.code = code or None
    pos.description = description
    
    # Update employees who had the old position name
    if old_name != name_kh:
        for emp in Employee.query.filter_by(position=old_name).all():
            emp.position = name_kh

    db.session.commit()
    flash(f'បានកែប្រែតួនាទី "{name_kh}" ដោយជោគជ័យ!', 'success')
    return redirect(url_for('organization_manage', tab='positions'))


@app.route('/organization/positions/<int:pos_id>/delete', methods=['POST'])
@admin_required
def position_delete(pos_id):
    pos = db.session.get(Position, pos_id)
    if not pos:
        flash('រកមិនឃើញតួនាទីនេះទេ!', 'danger')
        return redirect(url_for('organization_manage', tab='positions'))
        
    emp_count = pos.employee_count
    if emp_count > 0:
        flash(f'មិនអាចលុបតួនាទី "{pos.name_kh}" បានទេ ពីព្រោះមានបុគ្គលិកចំនួន {emp_count} នាក់កំពុងកាន់តួនាទីនេះ! សូមផ្លាស់ប្តូរតួនាទីបុគ្គលិកទាំងនោះជាមុនសិន។', 'danger')
        return redirect(url_for('organization_manage', tab='positions'))

    name_kh = pos.name_kh
    db.session.delete(pos)
    db.session.commit()
    flash(f'បានលុបតួនាទី "{name_kh}" ដោយជោគជ័យ!', 'success')
    return redirect(url_for('organization_manage', tab='positions'))


# ==========================================
# 0. DASHBOARD
# ==========================================
@app.route('/')
@login_required
def dashboard():
    today = date.today()
    current_month = today.strftime("%Y-%m")
    
    # KPI Stats
    total_employees = Employee.query.count()
    active_employees = Employee.query.filter_by(status='active').count()
    probation_employees = Employee.query.filter_by(status='probation').count()
    
    # Today's attendance stats
    today_attendances = Attendance.query.filter_by(date=today).all()
    present_today = sum(1 for a in today_attendances if a.status in ['present', 'late'])
    late_today = sum(1 for a in today_attendances if a.status == 'late')
    leave_today = sum(1 for a in today_attendances if a.status == 'leave')
    absent_today = sum(1 for a in today_attendances if a.status == 'absent')
    
    # Attendance rate
    att_rate = round((present_today / total_employees * 100), 1) if total_employees > 0 else 0
    
    # Pending leaves
    pending_leaves = LeaveRequest.query.filter_by(status='pending').order_by(LeaveRequest.applied_at.desc()).limit(5).all()
    
    # Current month payroll total
    payrolls = Payroll.query.filter_by(month_year=current_month).all()
    total_payroll_cost = sum(p.net_salary for p in payrolls)
    total_payroll_gross = sum(p.gross_salary for p in payrolls)
    
    # Department breakdown for chart
    departments = Department.query.all()
    dept_labels = [d.name_kh for d in departments]
    dept_counts = [len(d.employees) for d in departments]
    dept_payroll = []
    for d in departments:
        emp_ids = [e.id for e in d.employees]
        dept_sum = sum(p.net_salary for p in payrolls if p.employee_id in emp_ids)
        dept_payroll.append(round(dept_sum, 2))

    # Recent attendances
    recent_attendances = Attendance.query.order_by(Attendance.date.desc(), Attendance.id.desc()).limit(8).all()

    return render_template(
        'dashboard.html',
        total_employees=total_employees,
        active_employees=active_employees,
        probation_employees=probation_employees,
        present_today=present_today,
        late_today=late_today,
        leave_today=leave_today,
        absent_today=absent_today,
        att_rate=att_rate,
        pending_leaves=pending_leaves,
        total_payroll_cost=total_payroll_cost,
        total_payroll_gross=total_payroll_gross,
        dept_labels=dept_labels,
        dept_counts=dept_counts,
        dept_payroll=dept_payroll,
        recent_attendances=recent_attendances,
        current_month=current_month
    )


# ==========================================
# 1. EMPLOYEE MANAGEMENT (CRUD & DOCUMENTS)
# ==========================================
@app.route('/employees')
def employee_list():
    query = Employee.query
    
    # Search filter
    search = request.args.get('search', '').strip()
    if search:
        query = query.filter(
            (Employee.emp_code.ilike(f'%{search}%')) |
            (Employee.full_name_kh.ilike(f'%{search}%')) |
            (Employee.full_name_en.ilike(f'%{search}%')) |
            (Employee.phone.ilike(f'%{search}%')) |
            (Employee.position.ilike(f'%{search}%'))
        )
        
    # Department filter
    dept_id = request.args.get('department_id', type=int)
    if dept_id:
        query = query.filter(Employee.department_id == dept_id)
        
    # Status filter
    status = request.args.get('status', '').strip()
    if status:
        query = query.filter(Employee.status == status)

    # Position filter
    pos_filter = request.args.get('position', '').strip()
    if pos_filter:
        query = query.filter(Employee.position == pos_filter)

    employees = query.order_by(Employee.id.asc()).all()
    departments = Department.query.order_by(Department.id.asc()).all()
    
    return render_template(
        'employees/list.html',
        employees=employees,
        departments=departments,
        search=search,
        selected_dept=dept_id,
        selected_status=status,
        selected_pos=pos_filter,
        official_positions=OFFICIAL_POSITIONS
    )


@app.route('/employees/create', methods=['GET', 'POST'])
def employee_create():
    if request.method == 'POST':
        emp_code = request.form.get('emp_code', '').strip()
        full_name_kh = request.form.get('full_name_kh', '').strip()
        full_name_en = request.form.get('full_name_en', '').strip()
        
        # Check uniqueness of emp_code
        if Employee.query.filter_by(emp_code=emp_code).first():
            flash('លេខកូដបុគ្គលិកនេះមានក្នុងប្រព័ន្ធរួចហើយ! (Employee ID already exists)', 'danger')
            return redirect(url_for('employee_create'))

        dob_str = request.form.get('dob')
        hire_date_str = request.form.get('hire_date')
        
        dob = datetime.strptime(dob_str, '%Y-%m-%d').date() if dob_str else None
        hire_date = datetime.strptime(hire_date_str, '%Y-%m-%d').date() if hire_date_str else date.today()
        
        # Handle Avatar Upload
        avatar_filename = None
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file and file.filename != '':
                filename = secure_filename(f"{emp_code}_{file.filename}")
                file.save(os.path.join(AVATAR_FOLDER, filename))
                avatar_filename = filename

        # Construct full current address
        h_no = request.form.get('current_house_no', '').strip()
        s_no = request.form.get('current_street_no', '').strip()
        v_name = request.form.get('current_village', '').strip()
        c_name = request.form.get('current_commune', '').strip()
        d_name = request.form.get('current_district', '').strip()
        p_name = request.form.get('current_province', '').strip()
        
        addr_parts = []
        if h_no: addr_parts.append(f"ផ្ទះលេខ {h_no}")
        if s_no: addr_parts.append(f"ផ្លូវលេខ {s_no}")
        if v_name: addr_parts.append(f"ភូមិ {v_name}")
        if c_name: addr_parts.append(f"ឃុំ/សង្កាត់ {c_name}")
        if d_name: addr_parts.append(f"ស្រុក/ខណ្ឌ {d_name}")
        if p_name: addr_parts.append(f"រាជធានី/ខេត្ត {p_name}")
        full_address = " ".join(addr_parts) if addr_parts else request.form.get('address', '').strip()

        emp = Employee(
            emp_code=emp_code,
            full_name_kh=full_name_kh,
            full_name_en=full_name_en,
            gender=request.form.get('gender', 'ប្រុស'),
            ethnicity=request.form.get('ethnicity', 'ខ្មែរ').strip(),
            nationality=request.form.get('nationality', 'ខ្មែរ').strip(),
            dob=dob,
            pob_village=request.form.get('pob_village', '').strip(),
            pob_commune=request.form.get('pob_commune', '').strip(),
            pob_district=request.form.get('pob_district', '').strip(),
            pob_province=request.form.get('pob_province', '').strip(),
            education_level=request.form.get('education_level', '').strip(),
            education_major=request.form.get('education_major', '').strip(),
            foreign_languages=request.form.get('foreign_languages', '').strip(),
            other_skills=request.form.get('other_skills', '').strip(),
            marital_status=request.form.get('marital_status', 'នៅលីវ'),
            work_experience_1=request.form.get('work_experience_1', '').strip(),
            work_experience_2=request.form.get('work_experience_2', '').strip(),
            work_experience_3=request.form.get('work_experience_3', '').strip(),
            father_name=request.form.get('father_name', '').strip(),
            father_age=request.form.get('father_age', '').strip(),
            father_nationality=request.form.get('father_nationality', 'ខ្មែរ').strip(),
            father_status=request.form.get('father_status', 'រស់'),
            father_job=request.form.get('father_job', '').strip(),
            mother_name=request.form.get('mother_name', '').strip(),
            mother_age=request.form.get('mother_age', '').strip(),
            mother_nationality=request.form.get('mother_nationality', 'ខ្មែរ').strip(),
            mother_status=request.form.get('mother_status', 'រស់'),
            mother_job=request.form.get('mother_job', '').strip(),
            current_house_no=h_no,
            current_street_no=s_no,
            current_village=v_name,
            current_commune=c_name,
            current_district=d_name,
            current_province=p_name,
            address=full_address,
            phone=request.form.get('phone', '').strip(),
            email=request.form.get('email', '').strip(),
            national_id=request.form.get('national_id', '').strip(),
            position=request.form.get('position', '').strip(),
            department_id=int(request.form.get('department_id')),
            hire_date=hire_date,
            status=request.form.get('status', 'active'),
            base_salary=float(request.form.get('base_salary', 300.0)),
            bank_account=request.form.get('bank_account', '').strip(),
            avatar=avatar_filename
        )
        db.session.add(emp)
        db.session.flush() # get emp.id

        # Handle Initial Document Upload if any
        if 'document_file' in request.files:
            doc_file = request.files['document_file']
            if doc_file and doc_file.filename != '':
                doc_name = secure_filename(f"{emp_code}_{doc_file.filename}")
                doc_path = os.path.join(DOC_FOLDER, doc_name)
                doc_file.save(doc_path)
                
                size_bytes = os.path.getsize(doc_path)
                size_str = f"{round(size_bytes / 1024, 1)} KB" if size_bytes < 1024*1024 else f"{round(size_bytes / (1024*1024), 2)} MB"
                
                doc = EmployeeDocument(
                    employee_id=emp.id,
                    doc_type=request.form.get('document_type', 'contract'),
                    title=request.form.get('document_title', 'កិច្ចសន្យាការងារ'),
                    file_name=doc_name,
                    file_size=size_str,
                    notes=request.form.get('document_notes', '')
                )
                db.session.add(doc)

        db.session.commit()
        flash(f'បានបង្កើតទិន្នន័យប្រវត្តិរូបបុគ្គលិក {full_name_kh} តាមទម្រង់ផ្លូវការដោយជោគជ័យ!', 'success')
        return redirect(url_for('employee_detail', emp_id=emp.id))

    # Auto generate next emp code
    last_emp = Employee.query.order_by(Employee.id.desc()).first()
    next_num = (last_emp.id + 1) if last_emp else 1
    suggested_code = f"EMP-{next_num:03d}"

    departments = Department.query.order_by(Department.name_kh).all()
    return render_template('employees/form.html', departments=departments, suggested_code=suggested_code, is_edit=False)


@app.route('/employees/<int:emp_id>')
def employee_detail(emp_id):
    emp = Employee.query.get_or_404(emp_id)
    documents = EmployeeDocument.query.filter_by(employee_id=emp.id).order_by(EmployeeDocument.uploaded_at.desc()).all()
    attendances = Attendance.query.filter_by(employee_id=emp.id).order_by(Attendance.date.desc()).limit(30).all()
    payrolls = Payroll.query.filter_by(employee_id=emp.id).order_by(Payroll.month_year.desc()).limit(12).all()
    leaves = LeaveRequest.query.filter_by(employee_id=emp.id).order_by(LeaveRequest.applied_at.desc()).all()

    # Attendance summary stats
    total_days = len(attendances)
    present_days = sum(1 for a in attendances if a.status in ['present', 'late'])
    late_days = sum(1 for a in attendances if a.status == 'late')
    ot_hours_total = sum(a.ot_hours for a in attendances)

    return render_template(
        'employees/detail.html',
        emp=emp,
        documents=documents,
        attendances=attendances,
        payrolls=payrolls,
        leaves=leaves,
        present_days=present_days,
        late_days=late_days,
        ot_hours_total=round(ot_hours_total, 1)
    )


@app.route('/employees/<int:emp_id>/official-cv')
def employee_official_cv(emp_id):
    """
    100% replica of the official Cambodian CV / Biography form from doc (01).png
    """
    emp = Employee.query.get_or_404(emp_id)
    return render_template('employees/official_cv.html', emp=emp)


@app.route('/employees/<int:emp_id>/edit', methods=['GET', 'POST'])
def employee_edit(emp_id):
    emp = Employee.query.get_or_404(emp_id)
    if request.method == 'POST':
        emp.emp_code = request.form.get('emp_code', emp.emp_code).strip()
        emp.full_name_kh = request.form.get('full_name_kh', emp.full_name_kh).strip()
        emp.full_name_en = request.form.get('full_name_en', emp.full_name_en).strip()
        emp.gender = request.form.get('gender', emp.gender)
        emp.ethnicity = request.form.get('ethnicity', emp.ethnicity or 'ខ្មែរ').strip()
        emp.nationality = request.form.get('nationality', emp.nationality or 'ខ្មែរ').strip()
        
        dob_str = request.form.get('dob')
        if dob_str:
            emp.dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
            
        emp.pob_village = request.form.get('pob_village', emp.pob_village).strip()
        emp.pob_commune = request.form.get('pob_commune', emp.pob_commune).strip()
        emp.pob_district = request.form.get('pob_district', emp.pob_district).strip()
        emp.pob_province = request.form.get('pob_province', emp.pob_province).strip()
        
        emp.education_level = request.form.get('education_level', emp.education_level).strip()
        emp.education_major = request.form.get('education_major', emp.education_major).strip()
        emp.foreign_languages = request.form.get('foreign_languages', emp.foreign_languages).strip()
        emp.other_skills = request.form.get('other_skills', emp.other_skills).strip()
        emp.marital_status = request.form.get('marital_status', emp.marital_status)
        
        emp.work_experience_1 = request.form.get('work_experience_1', emp.work_experience_1).strip()
        emp.work_experience_2 = request.form.get('work_experience_2', emp.work_experience_2).strip()
        emp.work_experience_3 = request.form.get('work_experience_3', emp.work_experience_3).strip()
        
        emp.father_name = request.form.get('father_name', emp.father_name).strip()
        emp.father_age = request.form.get('father_age', emp.father_age).strip()
        emp.father_nationality = request.form.get('father_nationality', emp.father_nationality).strip()
        emp.father_status = request.form.get('father_status', emp.father_status)
        emp.father_job = request.form.get('father_job', emp.father_job).strip()
        
        emp.mother_name = request.form.get('mother_name', emp.mother_name).strip()
        emp.mother_age = request.form.get('mother_age', emp.mother_age).strip()
        emp.mother_nationality = request.form.get('mother_nationality', emp.mother_nationality).strip()
        emp.mother_status = request.form.get('mother_status', emp.mother_status)
        emp.mother_job = request.form.get('mother_job', emp.mother_job).strip()
        
        h_no = request.form.get('current_house_no', '').strip()
        s_no = request.form.get('current_street_no', '').strip()
        v_name = request.form.get('current_village', '').strip()
        c_name = request.form.get('current_commune', '').strip()
        d_name = request.form.get('current_district', '').strip()
        p_name = request.form.get('current_province', '').strip()
        
        emp.current_house_no = h_no
        emp.current_street_no = s_no
        emp.current_village = v_name
        emp.current_commune = c_name
        emp.current_district = d_name
        emp.current_province = p_name
        
        addr_parts = []
        if h_no: addr_parts.append(f"ផ្ទះលេខ {h_no}")
        if s_no: addr_parts.append(f"ផ្លូវលេខ {s_no}")
        if v_name: addr_parts.append(f"ភូមិ {v_name}")
        if c_name: addr_parts.append(f"ឃុំ/សង្កាត់ {c_name}")
        if d_name: addr_parts.append(f"ស្រុក/ខណ្ឌ {d_name}")
        if p_name: addr_parts.append(f"រាជធានី/ខេត្ត {p_name}")
        emp.address = " ".join(addr_parts) if addr_parts else request.form.get('address', emp.address).strip()
            
        hire_date_str = request.form.get('hire_date')
        if hire_date_str:
            emp.hire_date = datetime.strptime(hire_date_str, '%Y-%m-%d').date()
            
        emp.phone = request.form.get('phone', '').strip()
        emp.email = request.form.get('email', '').strip()
        emp.national_id = request.form.get('national_id', '').strip()
        emp.position = request.form.get('position', '').strip()
        emp.department_id = int(request.form.get('department_id'))
        emp.status = request.form.get('status', 'active')
        emp.base_salary = float(request.form.get('base_salary', emp.base_salary))
        emp.bank_account = request.form.get('bank_account', '').strip()
        
        # New avatar if uploaded
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file and file.filename != '':
                filename = secure_filename(f"{emp.emp_code}_{file.filename}")
                file.save(os.path.join(AVATAR_FOLDER, filename))
                emp.avatar = filename

        db.session.commit()
        flash(f'បានកែប្រែព័ត៌មានប្រវត្តិរូប {emp.full_name_kh} ដោយជោគជ័យ!', 'success')
        return redirect(url_for('employee_detail', emp_id=emp.id))

    departments = Department.query.order_by(Department.name_kh).all()
    return render_template('employees/form.html', emp=emp, departments=departments, is_edit=True)


@app.route('/employees/<int:emp_id>/delete', methods=['POST'])
def employee_delete(emp_id):
    emp = Employee.query.get_or_404(emp_id)
    name = emp.full_name_kh
    db.session.delete(emp)
    db.session.commit()
    flash(f'បានលុបទិន្នន័យបុគ្គលិក {name} ដោយជោគជ័យ!', 'warning')
    return redirect(url_for('employee_list'))


@app.route('/employees/<int:emp_id>/upload-doc', methods=['POST'])
def upload_employee_doc(emp_id):
    emp = Employee.query.get_or_404(emp_id)
    if 'document_file' not in request.files:
        flash('សូមជ្រើសរើសឯកសារដែលត្រូវ Upload!', 'danger')
        return redirect(url_for('employee_detail', emp_id=emp.id))
        
    doc_file = request.files['document_file']
    if doc_file.filename == '':
        flash('មិនមានឯកសារត្រូវបានជ្រើសរើសទេ!', 'danger')
        return redirect(url_for('employee_detail', emp_id=emp.id))

    filename = secure_filename(f"{emp.emp_code}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{doc_file.filename}")
    filepath = os.path.join(DOC_FOLDER, filename)
    doc_file.save(filepath)

    size_bytes = os.path.getsize(filepath)
    size_str = f"{round(size_bytes / 1024, 1)} KB" if size_bytes < 1024*1024 else f"{round(size_bytes / (1024*1024), 2)} MB"

    doc = EmployeeDocument(
        employee_id=emp.id,
        doc_type=request.form.get('document_type', 'other'),
        title=request.form.get('document_title', doc_file.filename),
        file_name=filename,
        file_size=size_str,
        notes=request.form.get('document_notes', '')
    )
    db.session.add(doc)
    db.session.commit()
    flash('បានបញ្ចូលឯកសារដោយជោគជ័យ!', 'success')
    return redirect(url_for('employee_detail', emp_id=emp.id))


@app.route('/documents/<int:doc_id>/delete', methods=['POST'])
def delete_document(doc_id):
    doc = EmployeeDocument.query.get_or_404(doc_id)
    emp_id = doc.employee_id
    filepath = os.path.join(DOC_FOLDER, doc.file_name)
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
        except Exception:
            pass
    db.session.delete(doc)
    db.session.commit()
    flash('បានលុបឯកសារដោយជោគជ័យ!', 'success')
    return redirect(url_for('employee_detail', emp_id=emp_id))


@app.route('/uploads/<folder>/<filename>')
def serve_upload(folder, filename):
    if folder == 'avatars':
        return send_from_directory(AVATAR_FOLDER, filename)
    elif folder == 'documents':
        return send_from_directory(DOC_FOLDER, filename)
    return "Not Found", 404


# ==========================================
# 2. ATTENDANCE & LEAVES MANAGEMENT
# ==========================================
@app.route('/attendance')
def attendance_daily():
    date_str = request.args.get('date', date.today().strftime('%Y-%m-%d'))
    try:
        query_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        query_date = date.today()
        date_str = query_date.strftime('%Y-%m-%d')

    dept_id = request.args.get('department_id', type=int)

    # Fetch employees
    emp_query = Employee.query.filter(Employee.status.in_(['active', 'probation']))
    if dept_id:
        emp_query = emp_query.filter(Employee.department_id == dept_id)
    employees = emp_query.order_by(Employee.emp_code.asc()).all()

    # Fetch existing attendance records for the date
    attendances = Attendance.query.filter_by(date=query_date).all()
    att_dict = {a.employee_id: a for a in attendances}

    # Summary counts
    present_cnt = sum(1 for a in attendances if a.status in ['present', 'late'])
    late_cnt = sum(1 for a in attendances if a.status == 'late')
    leave_cnt = sum(1 for a in attendances if a.status == 'leave')
    absent_cnt = sum(1 for a in attendances if a.status == 'absent')
    ot_hours_total = sum(a.ot_hours for a in attendances)

    return render_template(
        'attendance/daily.html',
        selected_date=query_date,
        date_str=date_str,
        employees=employees,
        att_dict=att_dict,
        present_cnt=present_cnt,
        late_cnt=late_cnt,
        leave_cnt=leave_cnt,
        absent_cnt=absent_cnt,
        ot_hours_total=round(ot_hours_total, 1),
        selected_dept=dept_id,
        departments=Department.query.order_by(Department.name_kh).all()
    )


@app.route('/attendance/record', methods=['POST'])
def attendance_record():
    emp_id = int(request.form.get('employee_id'))
    date_str = request.form.get('date')
    att_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    
    check_in = request.form.get('check_in', '').strip() or None
    check_out = request.form.get('check_out', '').strip() or None
    status = request.form.get('status', 'present')
    ot_hours = float(request.form.get('ot_hours', 0.0) or 0.0)
    notes = request.form.get('notes', '').strip()
    
    # Calculate late minutes if check_in provided
    late_minutes = 0
    if check_in and status != 'leave':
        try:
            in_h, in_m = map(int, check_in.split(':'))
            # standard check-in 08:00
            diff = (in_h * 60 + in_m) - (8 * 60)
            if diff > 0:
                late_minutes = diff
                if status == 'present':
                    status = 'late'
        except Exception:
            pass

    # Work hours
    work_hours = 8.0 + ot_hours if status in ['present', 'late'] else 0.0

    att = Attendance.query.filter_by(employee_id=emp_id, date=att_date).first()
    if not att:
        att = Attendance(employee_id=emp_id, date=att_date)
        db.session.add(att)

    att.check_in = check_in
    att.check_out = check_out
    att.status = status
    att.late_minutes = late_minutes
    att.work_hours = work_hours
    att.ot_hours = ot_hours
    att.source = request.form.get('source', 'manual')
    att.notes = notes

    db.session.commit()
    flash('បានកត់ត្រាវត្តមានដោយជោគជ័យ!', 'success')
    return redirect(url_for('attendance_daily', date=date_str))


@app.route('/attendance/simulate-scanner', methods=['POST'])
def simulate_biometric():
    """
    Simulates Biometric Fingerprint or RFID Card Scanner punch events.
    Can simulate a single punch or auto-punch all staff for today.
    """
    mode = request.form.get('mode', 'single')
    today = date.today()
    date_str = request.form.get('date', today.strftime('%Y-%m-%d'))
    att_date = datetime.strptime(date_str, '%Y-%m-%d').date()

    if mode == 'batch_all':
        # Auto-punch for all active employees
        employees = Employee.query.filter(Employee.status.in_(['active', 'probation'])).all()
        for emp in employees:
            att = Attendance.query.filter_by(employee_id=emp.id, date=att_date).first()
            if not att:
                att = Attendance(employee_id=emp.id, date=att_date)
                db.session.add(att)
            
            att.check_in = "07:58"
            att.check_out = "17:05"
            att.status = "present"
            att.late_minutes = 0
            att.work_hours = 8.0
            att.ot_hours = 0.0
            att.source = "biometric"
            att.notes = "ស្កេនម្រាមដៃដោយម៉ាស៊ីន Biometric Scanner (Auto)"
        
        db.session.commit()
        flash('បានក្លែងធ្វើការស្កេនម្រាមដៃ (Biometric Punch) សម្រាប់បុគ្គលិកទាំងអស់ដោយជោគជ័យ!', 'success')
    else:
        emp_id = int(request.form.get('employee_id'))
        emp = Employee.query.get_or_404(emp_id)
        punch_type = request.form.get('punch_type', 'in') # in or out
        punch_time = request.form.get('punch_time') or datetime.now().strftime('%H:%M')
        
        att = Attendance.query.filter_by(employee_id=emp.id, date=att_date).first()
        if not att:
            att = Attendance(employee_id=emp.id, date=att_date)
            db.session.add(att)

        if punch_type == 'in':
            att.check_in = punch_time
            # Check late
            in_h, in_m = map(int, punch_time.split(':'))
            diff = (in_h * 60 + in_m) - (8 * 60)
            if diff > 0:
                att.status = 'late'
                att.late_minutes = diff
            else:
                att.status = 'present'
                att.late_minutes = 0
        else:
            att.check_out = punch_time
            # check overtime if out > 17:00
            out_h, out_m = map(int, punch_time.split(':'))
            ot_diff_hours = max(0.0, ((out_h * 60 + out_m) - (17 * 60)) / 60.0)
            if ot_diff_hours >= 0.5:
                att.ot_hours = round(ot_diff_hours, 1)
                att.work_hours = round(8.0 + att.ot_hours, 1)

        att.source = request.form.get('source', 'biometric')
        att.notes = f"ស្កេន {punch_type.upper()} តាមរយៈម៉ាស៊ីន Fingerprint / RFID Card ({att.source})"
        db.session.commit()
        flash(f'បានកត់ត្រាការស្កេនរបស់ {emp.full_name_kh} វេលាម៉ោង {punch_time}!', 'success')

    return redirect(url_for('attendance_daily', date=date_str))


@app.route('/attendance/leaves')
def attendance_leaves():
    leaves = LeaveRequest.query.order_by(LeaveRequest.applied_at.desc()).all()
    employees = Employee.query.filter(Employee.status.in_(['active', 'probation'])).order_by(Employee.full_name_kh).all()
    
    pending_leaves = [l for l in leaves if l.status == 'pending']
    approved_leaves = [l for l in leaves if l.status == 'approved']
    
    return render_template(
        'attendance/leaves.html',
        leaves=leaves,
        pending_leaves=pending_leaves,
        approved_leaves=approved_leaves,
        employees=employees
    )


@app.route('/attendance/leaves/request', methods=['POST'])
def leave_request_submit():
    emp_id = int(request.form.get('employee_id'))
    leave_type = request.form.get('leave_type')
    start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
    end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
    reason = request.form.get('reason', '').strip()
    
    total_days = max(1.0, float((end_date - start_date).days + 1))

    leave = LeaveRequest(
        employee_id=emp_id,
        leave_type=leave_type,
        start_date=start_date,
        end_date=end_date,
        total_days=total_days,
        reason=reason,
        status='pending'
    )
    db.session.add(leave)
    db.session.commit()
    flash('បានដាក់ពាក្យស្នើសុំច្បាប់ឈប់សម្រាកដោយជោគជ័យ! សូមរង់ចាំការអនុម័ត។', 'success')
    return redirect(url_for('attendance_leaves'))


@app.route('/attendance/leaves/<int:leave_id>/action', methods=['POST'])
def leave_action(leave_id):
    leave = LeaveRequest.query.get_or_404(leave_id)
    action = request.form.get('action') # approve, reject
    admin_name = request.form.get('admin_name', 'នាយកដ្ឋានធនធានមនុស្ស (HR Dept)')
    note = request.form.get('note', '')

    if action == 'approve':
        leave.status = 'approved'
        leave.approved_by = admin_name
        leave.action_note = note
        
        # Mark attendance table as 'leave' for these dates
        curr = leave.start_date
        while curr <= leave.end_date:
            if curr.weekday() != 6: # Skip Sunday
                att = Attendance.query.filter_by(employee_id=leave.employee_id, date=curr).first()
                if not att:
                    att = Attendance(employee_id=leave.employee_id, date=curr)
                    db.session.add(att)
                att.status = 'leave'
                att.work_hours = 0.0
                att.ot_hours = 0.0
                att.notes = f"ច្បាប់ឈប់សម្រាក ({leave.leave_type_display['kh']})"
            curr += timedelta(days=1)
            
        flash('បានអនុម័តពាក្យស្នើសុំច្បាប់ដោយជោគជ័យ!', 'success')
    elif action == 'reject':
        leave.status = 'rejected'
        leave.approved_by = admin_name
        leave.action_note = note
        flash('បានបដិសេធពាក្យស្នើសុំច្បាប់។', 'warning')

    db.session.commit()
    return redirect(url_for('attendance_leaves'))


@app.route('/attendance/report')
def attendance_report():
    month_str = request.args.get('month', date.today().strftime('%Y-%m'))
    try:
        year, month = map(int, month_str.split('-'))
    except Exception:
        today = date.today()
        year, month = today.year, today.month
        month_str = today.strftime('%Y-%m')

    dept_id = request.args.get('department_id', type=int)

    emp_query = Employee.query.filter(Employee.status.in_(['active', 'probation']))
    if dept_id:
        emp_query = emp_query.filter(Employee.department_id == dept_id)
    employees = emp_query.order_by(Employee.emp_code.asc()).all()

    # Aggregate attendance for this month
    report_data = []
    for emp in employees:
        # Query attendance in this month
        atts = Attendance.query.filter(
            Attendance.employee_id == emp.id,
            db.extract('year', Attendance.date) == year,
            db.extract('month', Attendance.date) == month
        ).all()

        worked_days = sum(1 for a in atts if a.status in ['present', 'late', 'half_day'])
        late_days = sum(1 for a in atts if a.status == 'late')
        total_late_min = sum(a.late_minutes for a in atts)
        leave_days = sum(1 for a in atts if a.status == 'leave')
        absent_days = sum(1 for a in atts if a.status == 'absent')
        total_ot = sum(a.ot_hours for a in atts)
        total_work_hours = sum(a.work_hours for a in atts)

        report_data.append({
            'employee': emp,
            'worked_days': worked_days,
            'late_days': late_days,
            'total_late_min': total_late_min,
            'leave_days': leave_days,
            'absent_days': absent_days,
            'total_ot': round(total_ot, 1),
            'total_work_hours': round(total_work_hours, 1)
        })

    return render_template(
        'attendance/report.html',
        report_data=report_data,
        selected_month=month_str,
        selected_dept=dept_id,
        departments=Department.query.order_by(Department.name_kh).all()
    )


@app.route('/attendance/export-csv')
def attendance_export_csv():
    month_str = request.args.get('month', date.today().strftime('%Y-%m'))
    year, month = map(int, month_str.split('-'))
    
    employees = Employee.query.order_by(Employee.emp_code.asc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'Employee ID', 'Full Name (KH)', 'Full Name (EN)', 'Department', 
        'Worked Days', 'Leave Days', 'Absent Days', 'Late Count', 'Late Minutes', 'OT Hours'
    ])
    
    for emp in employees:
        atts = Attendance.query.filter(
            Attendance.employee_id == emp.id,
            db.extract('year', Attendance.date) == year,
            db.extract('month', Attendance.date) == month
        ).all()
        worked_days = sum(1 for a in atts if a.status in ['present', 'late', 'half_day'])
        late_days = sum(1 for a in atts if a.status == 'late')
        total_late_min = sum(a.late_minutes for a in atts)
        leave_days = sum(1 for a in atts if a.status == 'leave')
        absent_days = sum(1 for a in atts if a.status == 'absent')
        total_ot = sum(a.ot_hours for a in atts)
        
        writer.writerow([
            emp.emp_code, emp.full_name_kh, emp.full_name_en, emp.department.name_kh,
            worked_days, leave_days, absent_days, late_days, total_late_min, total_ot
        ])
        
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=attendance_report_{month_str}.csv"}
    )


# ==========================================
# 3. PAYROLL MANAGEMENT & PAYSLIPS
# ==========================================
@app.route('/payroll')
def payroll_list():
    month_str = request.args.get('month', date.today().strftime('%Y-%m'))
    dept_id = request.args.get('department_id', type=int)

    query = Payroll.query.filter_by(month_year=month_str)
    if dept_id:
        query = query.join(Employee).filter(Employee.department_id == dept_id)
        
    payrolls = query.all()

    # KPI stats
    total_gross = sum(p.gross_salary for p in payrolls)
    total_deductions = sum(p.total_deductions for p in payrolls)
    total_net = sum(p.net_salary for p in payrolls)
    total_nssf = sum(p.nssf_deduction for p in payrolls)
    total_tax = sum(p.salary_tax for p in payrolls)
    paid_count = sum(1 for p in payrolls if p.payment_status == 'paid')

    return render_template(
        'payroll/list.html',
        payrolls=payrolls,
        selected_month=month_str,
        selected_dept=dept_id,
        total_gross=round(total_gross, 2),
        total_deductions=round(total_deductions, 2),
        total_net=round(total_net, 2),
        total_net_khr=round(total_net * KHR_PER_USD, 0),
        total_nssf=round(total_nssf, 2),
        total_tax=round(total_tax, 2),
        paid_count=paid_count,
        departments=Department.query.order_by(Department.name_kh).all()
    )


@app.route('/payroll/generate', methods=['POST'])
def payroll_generate():
    """
    1-Click Auto Payroll Generation:
    Pulls real attendance metrics for the given month (worked days, OT hours, late minutes, absences)
    and computes salary, allowances, NSSF, Cambodian tax, and net pay.
    """
    month_str = request.form.get('month_year', date.today().strftime('%Y-%m'))
    year, month = map(int, month_str.split('-'))
    
    employees = Employee.query.filter(Employee.status.in_(['active', 'probation'])).all()
    standard_days = 26

    count = 0
    for emp in employees:
        # Calculate attendance aggregates
        atts = Attendance.query.filter(
            Attendance.employee_id == emp.id,
            db.extract('year', Attendance.date) == year,
            db.extract('month', Attendance.date) == month
        ).all()

        worked_days = float(sum(1 for a in atts if a.status in ['present', 'late', 'half_day']))
        # If no attendance record exists (e.g. fresh month), default to standard 26
        if len(atts) == 0:
            worked_days = 26.0
        
        absent_days = float(sum(1 for a in atts if a.status == 'absent'))
        ot_hours = float(sum(a.ot_hours for a in atts))
        late_minutes = sum(a.late_minutes for a in atts)

        # Check existing payroll record to preserve any manual bonuses/advances already keyed
        existing = Payroll.query.filter_by(employee_id=emp.id, month_year=month_str).first()
        bonus = existing.bonus if existing else 0.0
        allowance = existing.allowance if existing else 40.0 # standard allowance
        advance = existing.advance_salary if existing else 0.0

        calc = compute_employee_payroll(
            base_salary=emp.base_salary,
            worked_days=worked_days,
            standard_days=standard_days,
            ot_hours=ot_hours,
            bonus=bonus,
            allowance=allowance,
            absent_days=absent_days,
            late_minutes=late_minutes,
            advance_salary=advance
        )

        if not existing:
            existing = Payroll(employee_id=emp.id, month_year=month_str)
            db.session.add(existing)

        existing.base_salary = calc['base_salary']
        existing.standard_work_days = calc['standard_work_days']
        existing.worked_days = calc['worked_days']
        existing.ot_hours = calc['ot_hours']
        existing.ot_rate = calc['ot_rate']
        existing.ot_amount = calc['ot_amount']
        existing.bonus = calc['bonus']
        existing.allowance = calc['allowance']
        existing.gross_salary = calc['gross_salary']
        existing.absent_days = calc['absent_days']
        existing.absent_deduction = calc['absent_deduction']
        existing.late_deduction = calc['late_deduction']
        existing.nssf_deduction = calc['nssf_deduction']
        existing.salary_tax = calc['salary_tax']
        existing.advance_salary = calc['advance_salary']
        existing.total_deductions = calc['total_deductions']
        existing.net_salary = calc['net_salary']
        existing.payment_method = emp.bank_account or "ABA Bank"
        if not existing.payment_status:
            existing.payment_status = 'draft'

        count += 1

    db.session.commit()
    flash(f'បានគណនាប្រាក់បៀវត្សសម្រាប់បុគ្គលិកចំនួន {count} នាក់ក្នុងខែ {month_str} ដោយជោគជ័យ!', 'success')
    return redirect(url_for('payroll_list', month=month_str))


@app.route('/payroll/<int:payroll_id>/edit', methods=['POST'])
def payroll_edit(payroll_id):
    p = Payroll.query.get_or_404(payroll_id)
    
    bonus = float(request.form.get('bonus', 0.0) or 0.0)
    allowance = float(request.form.get('allowance', 0.0) or 0.0)
    advance = float(request.form.get('advance_salary', 0.0) or 0.0)
    other_deductions = float(request.form.get('other_deductions', 0.0) or 0.0)
    notes = request.form.get('notes', '').strip()

    # Recalculate
    calc = compute_employee_payroll(
        base_salary=p.base_salary,
        worked_days=p.worked_days,
        standard_days=p.standard_work_days,
        ot_hours=p.ot_hours,
        bonus=bonus,
        allowance=allowance,
        absent_days=p.absent_days,
        advance_salary=advance,
        other_deductions=other_deductions
    )

    p.bonus = calc['bonus']
    p.allowance = calc['allowance']
    p.gross_salary = calc['gross_salary']
    p.advance_salary = calc['advance_salary']
    p.other_deductions = calc['other_deductions']
    p.nssf_deduction = calc['nssf_deduction']
    p.salary_tax = calc['salary_tax']
    p.total_deductions = calc['total_deductions']
    p.net_salary = calc['net_salary']
    p.notes = notes

    db.session.commit()
    flash(f'បានកែសម្រួលប្រាក់បន្ថែម និងការកាត់ប្រាក់សម្រាប់ {p.employee.full_name_kh}!', 'success')
    return redirect(url_for('payroll_list', month=p.month_year))


@app.route('/payroll/<int:payroll_id>/status', methods=['POST'])
def payroll_update_status(payroll_id):
    p = Payroll.query.get_or_404(payroll_id)
    status = request.form.get('payment_status', 'draft')
    p.payment_status = status
    if status == 'paid':
        p.payment_date = date.today()
    db.session.commit()
    flash(f'បានផ្លាស់ប្តូរស្ថានភាពទៅជា: {p.status_info["kh"]}', 'success')
    return redirect(url_for('payroll_list', month=p.month_year))


@app.route('/payroll/<int:payroll_id>/payslip')
def payroll_payslip(payroll_id):
    p = Payroll.query.get_or_404(payroll_id)
    net_khr = round(p.net_salary * KHR_PER_USD, 0)
    return render_template('payroll/payslip.html', p=p, net_khr=f"{net_khr:,.0f}")


@app.route('/payroll/report')
def payroll_report():
    month_str = request.args.get('month', date.today().strftime('%Y-%m'))
    payrolls = Payroll.query.filter_by(month_year=month_str).all()

    # Department aggregation
    departments = Department.query.order_by(Department.name_kh).all()
    dept_summary = []
    
    total_company_gross = sum(p.gross_salary for p in payrolls)
    total_company_net = sum(p.net_salary for p in payrolls)
    total_company_tax = sum(p.salary_tax for p in payrolls)
    total_company_nssf = sum(p.nssf_deduction for p in payrolls)

    for d in departments:
        emp_ids = [e.id for e in d.employees]
        dept_payrolls = [p for p in payrolls if p.employee_id in emp_ids]
        
        d_gross = sum(p.gross_salary for p in dept_payrolls)
        d_net = sum(p.net_salary for p in dept_payrolls)
        d_ot = sum(p.ot_amount for p in dept_payrolls)
        d_tax = sum(p.salary_tax for p in dept_payrolls)
        d_nssf = sum(p.nssf_deduction for p in dept_payrolls)

        dept_summary.append({
            'department': d,
            'count': len(dept_payrolls),
            'gross': round(d_gross, 2),
            'net': round(d_net, 2),
            'ot': round(d_ot, 2),
            'tax': round(d_tax, 2),
            'nssf': round(d_nssf, 2)
        })

    # Prepare chart labels & values
    chart_labels = [d.name_kh for d in departments]
    chart_values = [next((s['net'] for s in dept_summary if s['department'].id == d.id), 0.0) for d in departments]

    return render_template(
        'payroll/report.html',
        selected_month=month_str,
        dept_summary=dept_summary,
        chart_labels=chart_labels,
        chart_values=chart_values,
        total_company_gross=round(total_company_gross, 2),
        total_company_net=round(total_company_net, 2),
        total_company_tax=round(total_company_tax, 2),
        total_company_nssf=round(total_company_nssf, 2)
    )


@app.route('/payroll/export-csv')
def payroll_export_csv():
    month_str = request.args.get('month', date.today().strftime('%Y-%m'))
    payrolls = Payroll.query.filter_by(month_year=month_str).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'Emp Code', 'Name (KH)', 'Name (EN)', 'Department', 'Position',
        'Base Salary', 'Worked Days', 'OT Hours', 'OT Pay', 'Bonus', 'Allowance',
        'Gross Salary', 'Absent Deduction', 'NSSF', 'Salary Tax', 'Advance Salary',
        'Total Deductions', 'Net Salary (USD)', 'Status'
    ])

    for p in payrolls:
        writer.writerow([
            p.employee.emp_code, p.employee.full_name_kh, p.employee.full_name_en,
            p.employee.department.name_kh, p.employee.position,
            p.base_salary, p.worked_days, p.ot_hours, p.ot_amount, p.bonus, p.allowance,
            p.gross_salary, p.absent_deduction, p.nssf_deduction, p.salary_tax, p.advance_salary,
            p.total_deductions, p.net_salary, p.payment_status
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=payroll_report_{month_str}.csv"}
    )


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        ensure_default_admin()
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() in ('true', '1')
    app.run(host='0.0.0.0', port=port, debug=debug)
