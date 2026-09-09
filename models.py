from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# 7 Official Offices (រចនាសម្ព័ន្ធការិយាល័យទាំង ៧)
OFFICIAL_DEPARTMENTS = [
    {
        "name_kh": "ការិយាល័យបុគ្គលិក",
        "name_en": "Personnel Office",
        "code": "OFF-PERS",
        "description": "គ្រប់គ្រងកិច្ចការបុគ្គលិក កិច្ចសន្យា និងលក្ខន្តិកៈ"
    },
    {
        "name_kh": "ការិយាល័យគណនេយ្យ",
        "name_en": "Accounting Office",
        "code": "OFF-ACC",
        "description": "គ្រប់គ្រងគណនេយ្យ ហិរញ្ញវត្ថុ និងប្រាក់បៀវត្ស"
    },
    {
        "name_kh": "ការិយាល័យពិសោធន៍",
        "name_en": "Laboratory Office",
        "code": "OFF-LAB",
        "description": "ការងារពិសោធន៍ ស្រាវជ្រាវ និងត្រួតពិនិត្យគុណភាព"
    },
    {
        "name_kh": "ការិយាល័យទីផ្សា",
        "name_en": "Marketing Office",
        "code": "OFF-MKT",
        "description": "ការងារទីផ្សារ ផ្សព្វផ្សាយពាណិជ្ជកម្ម និងទំនាក់ទំនងអតិថិជន"
    },
    {
        "name_kh": "ការិយាល័យធនធានមនុស្ស",
        "name_en": "Human Resources Office",
        "code": "OFF-HR",
        "description": "គ្រប់គ្រងធនធានមនុស្ស ជ្រើសរើស និងបណ្តុះបណ្តាលបុគ្គលិក"
    },
    {
        "name_kh": "ការិយាល័យគ្រប់គ្រងការផលិត",
        "name_en": "Production Management Office",
        "code": "OFF-PROD",
        "description": "គ្រប់គ្រង ផែនការ និងត្រួតពិនិត្យខ្សែសង្វាក់ផលិតកម្ម"
    },
    {
        "name_kh": "ការិយាល័យពត៌មានវិទ្យា",
        "name_en": "Information Technology Office",
        "code": "OFF-IT",
        "description": "គ្រប់គ្រងហេដ្ឋារចនាសម្ព័ន្ធបច្ចេកវិទ្យា និងប្រព័ន្ធព័ត៌មានវិទ្យា"
    }
]

# 5 Official Positions/Roles (តួនាទីទាំង ៥)
OFFICIAL_POSITIONS_DATA = [
    {"name_kh": "អគ្គនាយក", "name_en": "Director General", "code": "POS-DG", "description": "ថ្នាក់ដឹកនាំកំពូល គ្រប់គ្រងទិសដៅយុទ្ធសាស្ត្រទូទៅ"},
    {"name_kh": "អគ្គនាយករង", "name_en": "Deputy Director General", "code": "POS-DDG", "description": "ជួយអគ្គនាយកក្នុងការដឹកនាំ និងគ្រប់គ្រងប្រតិបត្តិការ"},
    {"name_kh": "ប្រធានការិយាល័យ", "name_en": "Head of Office", "code": "POS-HEAD", "description": "ដឹកនាំ និងគ្រប់គ្រងការងារក្នុងអង្គភាពការិយាល័យ"},
    {"name_kh": "អនុប្រធានការិយាល័យ", "name_en": "Deputy Head of Office", "code": "POS-DEP", "description": "ជួយប្រធានការិយាល័យ និងទទួលបន្ទុកការងារជាក់លាក់"},
    {"name_kh": "បុគ្គលិក", "name_en": "Staff", "code": "POS-STAFF", "description": "អនុវត្តការងារជំនាញ និងប្រតិបត្តិការប្រចាំថ្ងៃ"}
]

OFFICIAL_POSITIONS = [p["name_kh"] for p in OFFICIAL_POSITIONS_DATA]

class Department(db.Model):
    __tablename__ = 'departments'
    
    id = db.Column(db.Integer, primary_key=True)
    name_kh = db.Column(db.String(100), nullable=False)
    name_en = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.String(255))
    
    employees = db.relationship('Employee', backref='department', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name_kh': self.name_kh,
            'name_en': self.name_en,
            'code': self.code,
            'employee_count': len(self.employees)
        }


class Position(db.Model):
    __tablename__ = 'positions'

    id = db.Column(db.Integer, primary_key=True)
    name_kh = db.Column(db.String(100), unique=True, nullable=False)
    name_en = db.Column(db.String(100), nullable=True)
    code = db.Column(db.String(30), unique=True, nullable=True)
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def employee_count(self):
        return Employee.query.filter_by(position=self.name_kh).count()

    def to_dict(self):
        return {
            'id': self.id,
            'name_kh': self.name_kh,
            'name_en': self.name_en,
            'code': self.code,
            'description': self.description,
            'employee_count': self.employee_count
        }


class Province(db.Model):
    __tablename__ = 'provinces'
    code = db.Column(db.String(10), primary_key=True)
    name_kh = db.Column(db.String(100), nullable=False)
    name_en = db.Column(db.String(100), nullable=False)
    
    districts = db.relationship('District', backref='province', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'code': self.code,
            'name_kh': self.name_kh,
            'name_en': self.name_en
        }


class District(db.Model):
    __tablename__ = 'districts'
    code = db.Column(db.String(10), primary_key=True)
    province_code = db.Column(db.String(10), db.ForeignKey('provinces.code'), nullable=False)
    name_kh = db.Column(db.String(100), nullable=False)
    name_en = db.Column(db.String(100), nullable=False)
    
    communes = db.relationship('Commune', backref='district', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'code': self.code,
            'province_code': self.province_code,
            'name_kh': self.name_kh,
            'name_en': self.name_en
        }


class Commune(db.Model):
    __tablename__ = 'communes'
    code = db.Column(db.String(10), primary_key=True)
    district_code = db.Column(db.String(10), db.ForeignKey('districts.code'), nullable=False)
    province_code = db.Column(db.String(10), nullable=False)
    name_kh = db.Column(db.String(100), nullable=False)
    name_en = db.Column(db.String(100), nullable=False)

    def to_dict(self):
        return {
            'code': self.code,
            'district_code': self.district_code,
            'province_code': self.province_code,
            'name_kh': self.name_kh,
            'name_en': self.name_en
        }


class Employee(db.Model):
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    emp_code = db.Column(db.String(30), unique=True, nullable=False)
    
    # 1. នាមត្រកូល នាមខ្លួន (Full Name KH & Latin)
    full_name_kh = db.Column(db.String(120), nullable=False)
    full_name_en = db.Column(db.String(120), nullable=False)
    
    # 2. ភេទ ជនជាតិ សញ្ជាតិ
    gender = db.Column(db.String(10), default='ប្រុស')  # ប្រុស, ស្រី
    ethnicity = db.Column(db.String(50), default='ខ្មែរ')  # ជនជាតិ
    nationality = db.Column(db.String(50), default='ខ្មែរ')  # សញ្ជាតិ
    
    # 3. ថ្ងៃខែឆ្នាំកំណើត
    dob = db.Column(db.Date, nullable=True)
    
    # 4. ទីកន្លែងកំណើត (Place of Birth)
    pob_village = db.Column(db.String(100), nullable=True)    # ភូមិ
    pob_commune = db.Column(db.String(100), nullable=True)    # ឃុំ/សង្កាត់
    pob_district = db.Column(db.String(100), nullable=True)   # ស្រុក/ខណ្ឌ
    pob_province = db.Column(db.String(100), nullable=True)   # រាជធានី/ខេត្ត
    
    # 5. កម្រិតវប្បធម៌សិក្សា & ឯកទេស
    education_level = db.Column(db.String(150), nullable=True) # កម្រិតវប្បធម៌សិក្សា
    education_major = db.Column(db.String(150), nullable=True) # ឯកទេស
    
    # 6. ចំណេះដឹងភាសាបរទេស
    foreign_languages = db.Column(db.String(255), nullable=True) # ភាសាបរទេស
    
    # 7. មុខជំនាញផ្សេងៗ
    other_skills = db.Column(db.String(255), nullable=True) # មុខជំនាញផ្សេងៗ
    
    # 8. ស្ថានភាពគ្រួសារ
    marital_status = db.Column(db.String(50), default='នៅលីវ') # នៅលីវ, មានប្តី ឬប្រពន្ធ
    
    # 9. បទពិសោធន៍ការងារ (១, ២, ៣)
    work_experience_1 = db.Column(db.Text, nullable=True)
    work_experience_2 = db.Column(db.Text, nullable=True)
    work_experience_3 = db.Column(db.Text, nullable=True)
    
    # 10. ព័ត៌មានឪពុក
    father_name = db.Column(db.String(120), nullable=True)
    father_age = db.Column(db.String(10), nullable=True)
    father_nationality = db.Column(db.String(50), default='ខ្មែរ')
    father_status = db.Column(db.String(20), default='រស់') # រស់, ស្លាប់
    father_job = db.Column(db.String(150), nullable=True)
    
    # 11. ព័ត៌មានម្តាយ
    mother_name = db.Column(db.String(120), nullable=True)
    mother_age = db.Column(db.String(10), nullable=True)
    mother_nationality = db.Column(db.String(50), default='ខ្មែរ')
    mother_status = db.Column(db.String(20), default='រស់') # រស់, ស្លាប់
    mother_job = db.Column(db.String(150), nullable=True)
    
    # 12. អាសយដ្ឋានបច្ចុប្បន្ន
    current_house_no = db.Column(db.String(50), nullable=True)  # ផ្ទះលេខ
    current_street_no = db.Column(db.String(50), nullable=True) # ផ្លូវលេខ
    current_village = db.Column(db.String(100), nullable=True)  # ភូមិ
    current_commune = db.Column(db.String(100), nullable=True)  # ឃុំ/សង្កាត់
    current_district = db.Column(db.String(100), nullable=True) # ស្រុក/ខណ្ឌ
    current_province = db.Column(db.String(100), nullable=True) # រាជធានី/ខេត្ត
    address = db.Column(db.Text, nullable=True) # Full formatted address
    
    # 13. ទំនាក់ទំនង
    phone = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    national_id = db.Column(db.String(50), nullable=True)
    
    # Employment Details (ក្រុមហ៊ុន)
    position = db.Column(db.String(100), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    hire_date = db.Column(db.Date, default=date.today)
    status = db.Column(db.String(30), default='active')  # active, probation, resigned, terminated
    base_salary = db.Column(db.Float, default=300.0)     # USD
    bank_account = db.Column(db.String(50), nullable=True)
    avatar = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    documents = db.relationship('EmployeeDocument', backref='employee', lazy=True, cascade='all, delete-orphan')
    attendances = db.relationship('Attendance', backref='employee', lazy=True, cascade='all, delete-orphan')
    leaves = db.relationship('LeaveRequest', backref='employee', lazy=True, cascade='all, delete-orphan')
    payrolls = db.relationship('Payroll', backref='employee', lazy=True, cascade='all, delete-orphan')

    @property
    def status_badge(self):
        badges = {
            'active': {'kh': 'សកម្ម', 'en': 'Active', 'class': 'badge-success'},
            'probation': {'kh': 'សាកល្បង', 'en': 'Probation', 'class': 'badge-warning'},
            'resigned': {'kh': 'លាលែង', 'en': 'Resigned', 'class': 'badge-secondary'},
            'terminated': {'kh': 'បញ្ឈប់', 'en': 'Terminated', 'class': 'badge-danger'}
        }
        return badges.get(self.status, {'kh': self.status, 'en': self.status, 'class': 'badge-secondary'})

    @property
    def formatted_pob(self):
        parts = []
        if self.pob_village: parts.append(f"ភូមិ {self.pob_village}")
        if self.pob_commune: parts.append(f"ឃុំ/សង្កាត់ {self.pob_commune}")
        if self.pob_district: parts.append(f"ស្រុក/ខណ្ឌ {self.pob_district}")
        if self.pob_province: parts.append(f"ខេត្ត/រាជធានី {self.pob_province}")
        return " ".join(parts) if parts else (self.address or "-")

    @property
    def formatted_current_address(self):
        parts = []
        if self.current_house_no: parts.append(f"ផ្ទះលេខ {self.current_house_no}")
        if self.current_street_no: parts.append(f"ផ្លូវលេខ {self.current_street_no}")
        if self.current_village: parts.append(f"ភូមិ {self.current_village}")
        if self.current_commune: parts.append(f"ឃុំ/សង្កាត់ {self.current_commune}")
        if self.current_district: parts.append(f"ស្រុក/ខណ្ឌ {self.current_district}")
        if self.current_province: parts.append(f"រាជធានី/ខេត្ត {self.current_province}")
        return " ".join(parts) if parts else (self.address or "-")


class EmployeeDocument(db.Model):
    __tablename__ = 'employee_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    doc_type = db.Column(db.String(50), nullable=False)  # contract, id_card, cv, other
    title = db.Column(db.String(200), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.String(50), nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)

    @property
    def doc_type_display(self):
        labels = {
            'contract': 'កិច្ចសន្យាការងារ (Employment Contract)',
            'id_card': 'អត្តសញ្ញាណប័ណ្ណ / Passport',
            'cv': 'ប្រវត្តិរូបសង្ខេប (CV / Resume)',
            'certificate': 'សញ្ញាបត្រ / វិញ្ញាបនបត្រ',
            'other': 'ឯកសារយោងផ្សេងៗ'
        }
        return labels.get(self.doc_type, self.doc_type)


class Attendance(db.Model):
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    check_in = db.Column(db.String(10), nullable=True)   # "08:00"
    check_out = db.Column(db.String(10), nullable=True)  # "17:00"
    status = db.Column(db.String(30), default='present') # present, late, half_day, absent, leave
    late_minutes = db.Column(db.Integer, default=0)
    work_hours = db.Column(db.Float, default=8.0)
    ot_hours = db.Column(db.Float, default=0.0)
    source = db.Column(db.String(30), default='manual')  # manual, biometric, card
    notes = db.Column(db.String(255), nullable=True)

    @property
    def status_info(self):
        info = {
            'present': {'kh': 'មានវត្តមាន', 'en': 'Present', 'class': 'badge-success'},
            'late': {'kh': 'មកយឺត', 'en': 'Late', 'class': 'badge-warning'},
            'half_day': {'kh': 'កន្លះថ្ងៃ', 'en': 'Half Day', 'class': 'badge-info'},
            'absent': {'kh': 'អវត្តមាន', 'en': 'Absent', 'class': 'badge-danger'},
            'leave': {'kh': 'ឈប់ច្បាប់', 'en': 'On Leave', 'class': 'badge-purple'}
        }
        return info.get(self.status, {'kh': self.status, 'en': self.status, 'class': 'badge-secondary'})


class LeaveRequest(db.Model):
    __tablename__ = 'leave_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    leave_type = db.Column(db.String(50), nullable=False) # sick, annual, maternity, special, unauthorized
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    total_days = db.Column(db.Float, default=1.0)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), default='pending') # pending, approved, rejected
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_by = db.Column(db.String(100), nullable=True)
    action_note = db.Column(db.String(255), nullable=True)

    @property
    def leave_type_display(self):
        types = {
            'sick': {'kh': 'ឈប់ឈឺ (Sick Leave)', 'icon': 'fa-solid fa-notes-medical'},
            'annual': {'kh': 'ឈប់សម្រាកប្រចាំឆ្នាំ (Annual Leave)', 'icon': 'fa-solid fa-umbrella-beach'},
            'maternity': {'kh': 'ឈប់សម្រាលកូន (Maternity Leave)', 'icon': 'fa-solid fa-baby'},
            'special': {'kh': 'ច្បាប់ពិសេស (Special Leave)', 'icon': 'fa-solid fa-heart'},
            'unauthorized': {'kh': 'អវត្តមានគ្មានច្បាប់ (Unauthorized Absence)', 'icon': 'fa-solid fa-triangle-exclamation'}
        }
        return types.get(self.leave_type, {'kh': self.leave_type, 'icon': 'fa-solid fa-calendar-day'})

    @property
    def status_info(self):
        info = {
            'pending': {'kh': 'រង់ចាំអនុម័ត', 'en': 'Pending', 'class': 'badge-warning'},
            'approved': {'kh': 'បានអនុម័ត', 'en': 'Approved', 'class': 'badge-success'},
            'rejected': {'kh': 'បដិសេធ', 'en': 'Rejected', 'class': 'badge-danger'}
        }
        return info.get(self.status, {'kh': self.status, 'en': self.status, 'class': 'badge-secondary'})


class Payroll(db.Model):
    __tablename__ = 'payrolls'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    month_year = db.Column(db.String(7), nullable=False) # e.g. "2026-09"
    
    # Calculation base
    base_salary = db.Column(db.Float, nullable=False, default=0.0)
    standard_work_days = db.Column(db.Integer, default=26)
    worked_days = db.Column(db.Float, default=26.0)
    
    # Overtime
    ot_hours = db.Column(db.Float, default=0.0)
    ot_rate = db.Column(db.Float, default=1.5)
    ot_amount = db.Column(db.Float, default=0.0)
    
    # Allowances & Bonuses
    bonus = db.Column(db.Float, default=0.0)
    allowance = db.Column(db.Float, default=0.0)
    gross_salary = db.Column(db.Float, default=0.0)
    
    # Deductions
    absent_days = db.Column(db.Float, default=0.0)
    absent_deduction = db.Column(db.Float, default=0.0)
    late_deduction = db.Column(db.Float, default=0.0)
    nssf_deduction = db.Column(db.Float, default=0.0) # ប.ស.ស (2%)
    salary_tax = db.Column(db.Float, default=0.0)     # ពន្ធលើប្រាក់បៀវត្ស
    advance_salary = db.Column(db.Float, default=0.0) # បើកប្រាក់ខែមុន
    other_deductions = db.Column(db.Float, default=0.0)
    total_deductions = db.Column(db.Float, default=0.0)
    
    # Net Pay
    net_salary = db.Column(db.Float, default=0.0)
    
    # Status
    payment_status = db.Column(db.String(30), default='draft') # draft, approved, paid
    payment_date = db.Column(db.Date, nullable=True)
    payment_method = db.Column(db.String(50), default='ABA Bank Transfer')
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def status_info(self):
        info = {
            'draft': {'kh': 'ព្រាង (Draft)', 'class': 'badge-secondary'},
            'approved': {'kh': 'បានអនុម័ត (Approved)', 'class': 'badge-primary'},
            'paid': {'kh': 'បានបើកប្រាក់ខែ (Paid)', 'class': 'badge-success'}
        }
        return info.get(self.payment_status, {'kh': self.payment_status, 'class': 'badge-secondary'})


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), nullable=False, default='staff') # admin, hr, accountant, staff
    phone = db.Column(db.String(50), nullable=True)
    employee_name = db.Column(db.String(120), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    approval_status = db.Column(db.String(30), default='approved') # approved, pending, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    employee = db.relationship('Employee', backref=db.backref('user_account', uselist=False), lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_permanent_admin(self):
        return self.username.upper() == 'ADMIN'

    @property
    def role_badge(self):
        roles = {
            'admin': {'kh': 'អ្នកគ្រប់គ្រង (Admin)', 'en': 'Admin', 'class': 'badge-danger', 'icon': 'fa-solid fa-shield-halved'},
            'hr': {'kh': 'ធនធានមនុស្ស (HR)', 'en': 'HR', 'class': 'badge-primary', 'icon': 'fa-solid fa-user-tie'},
            'accountant': {'kh': 'គណនេយ្យករ (Finance)', 'en': 'Accountant', 'class': 'badge-success', 'icon': 'fa-solid fa-calculator'},
            'staff': {'kh': 'បុគ្គលិក (Staff)', 'en': 'Staff', 'class': 'badge-secondary', 'icon': 'fa-solid fa-user'}
        }
        return roles.get(self.role, {'kh': self.role, 'en': self.role, 'class': 'badge-secondary', 'icon': 'fa-solid fa-user'})

    @property
    def role_kh(self):
        return self.role_badge.get('kh', self.role)

    @property
    def approval_badge(self):
        badges = {
            'pending': {'kh': 'រង់ចាំអនុម័ត', 'en': 'Pending', 'class': 'badge-warning', 'icon': 'fa-solid fa-hourglass-half'},
            'approved': {'kh': 'បានអនុម័ត', 'en': 'Approved', 'class': 'badge-success', 'icon': 'fa-solid fa-circle-check'},
            'rejected': {'kh': 'បដិសេធ', 'en': 'Rejected', 'class': 'badge-danger', 'icon': 'fa-solid fa-circle-xmark'}
        }
        return badges.get(self.approval_status or 'approved', {'kh': 'បានអនុម័ត', 'en': 'Approved', 'class': 'badge-success', 'icon': 'fa-solid fa-circle-check'})

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'phone': self.phone,
            'employee_name': self.employee_name,
            'employee_id': self.employee_id,
            'is_active': self.is_active,
            'approval_status': self.approval_status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'last_login': self.last_login.strftime('%Y-%m-%d %H:%M:%S') if self.last_login else None
        }
