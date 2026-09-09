import os
import random
from datetime import datetime, date, timedelta
from flask import Flask
from models import db, Department, Employee, EmployeeDocument, Attendance, LeaveRequest, Payroll, User
from payroll_calculator import compute_employee_payroll

def ensure_sample_users():
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

    emp1 = Employee.query.filter_by(emp_code='EMP-001').first()
    if emp1 and not User.query.filter_by(username='piseth').first():
        u1 = User(
            username='piseth',
            role='hr',
            phone=emp1.phone or '012 888 999',
            employee_name=emp1.full_name_kh,
            employee_id=emp1.id,
            is_active=True,
            approval_status='approved'
        )
        u1.set_password('hr123456')
        db.session.add(u1)

    db.session.commit()

def create_sample_data(app, force=False):
    with app.app_context():
        db.create_all()
        ensure_sample_users()
        
        # If database already has data and not forced, ensure geo data and exit safely
        if not force and Employee.query.first():
            from import_cambodia_geo import import_cambodia_locations
            from models import Province, Commune
            if Province.query.count() < 25 or Commune.query.count() < 1661:
                print("Updating Cambodia Administrative Locations...")
                import_cambodia_locations()
            print("Database already initialized with data.")
            return

        if force:
            db.drop_all()
            db.create_all()

        print("Seeding initial data with 100% official CV fields...")
        
        # 1. Departments (រចនាសម្ព័ន្ធការិយាល័យទាំង ៧)
        departments = [
            Department(name_kh="ការិយាល័យបុគ្គលិក", name_en="Personnel Office", code="OFF-PERS", description="គ្រប់គ្រងកិច្ចការបុគ្គលិក កិច្ចសន្យា និងលក្ខន្តិកៈ"),
            Department(name_kh="ការិយាល័យគណនេយ្យ", name_en="Accounting Office", code="OFF-ACC", description="គ្រប់គ្រងគណនេយ្យ ហិរញ្ញវត្ថុ និងប្រាក់បៀវត្ស"),
            Department(name_kh="ការិយាល័យពិសោធន៍", name_en="Laboratory Office", code="OFF-LAB", description="ការងារពិសោធន៍ ស្រាវជ្រាវ និងត្រួតពិនិត្យគុណភាព"),
            Department(name_kh="ការិយាល័យទីផ្សា", name_en="Marketing Office", code="OFF-MKT", description="ការងារទីផ្សារ ផ្សព្វផ្សាយពាណិជ្ជកម្ម និងទំនាក់ទំនងអតិថិជន"),
            Department(name_kh="ការិយាល័យធនធានមនុស្ស", name_en="Human Resources Office", code="OFF-HR", description="គ្រប់គ្រងធនធានមនុស្ស ជ្រើសរើស និងបណ្តុះបណ្តាលបុគ្គលិក"),
            Department(name_kh="ការិយាល័យគ្រប់គ្រងការផលិត", name_en="Production Management Office", code="OFF-PROD", description="គ្រប់គ្រង ផែនការ និងត្រួតពិនិត្យខ្សែសង្វាក់ផលិតកម្ម"),
            Department(name_kh="ការិយាល័យពត៌មានវិទ្យា", name_en="Information Technology Office", code="OFF-IT", description="គ្រប់គ្រងហេដ្ឋារចនាសម្ព័ន្ធបច្ចេកវិទ្យា និងប្រព័ន្ធព័ត៌មានវិទ្យា")
        ]
        db.session.add_all(departments)
        db.session.commit()

        # 2. Employees matching doc (01) fields 100%
        employees_data = [
            {
                "emp_code": "EMP-001",
                "full_name_kh": "សុខ ពិសិដ្ឋ",
                "full_name_en": "Sok Piseth",
                "gender": "ប្រុស",
                "ethnicity": "ខ្មែរ",
                "nationality": "ខ្មែរ",
                "dob": date(1992, 5, 14),
                "pob_village": "ព្រែកប្រា",
                "pob_commune": "ព្រែកប្រា",
                "pob_district": "ច្បារអំពៅ",
                "pob_province": "ភ្នំពេញ",
                "education_level": "បរិញ្ញាបត្រជាន់ខ្ពស់ (Master Degree)",
                "education_major": "វិទ្យាសាស្ត្រកុំព្យូទ័រ (Computer Science)",
                "foreign_languages": "អង់គ្លេស (ស្ទាត់ជំនាញ), ចិន (មធ្យម)",
                "other_skills": "Network Security, System Architecture, Docker, Cloud",
                "marital_status": "មានប្តី ឬប្រពន្ធ",
                "work_experience_1": "២០១៦-២០១៩៖ System Engineer នៅធនាគារកាណាឌីយ៉ា",
                "work_experience_2": "២០១៩-២០២១៖ Senior Backend Developer នៅ Smart Axiata",
                "work_experience_3": "២០២១-បច្ចុប្បន្ន៖ IT Manager នៅ HRMS Cambodia",
                "father_name": "សុខ សារ៉ាត",
                "father_age": "៦២",
                "father_nationality": "ខ្មែរ",
                "father_status": "រស់",
                "father_job": "មន្ត្រីរាជការចូលនិវត្តន៍",
                "mother_name": "អ៊ុំ សុផល",
                "mother_age": "៥៩",
                "mother_nationality": "ខ្មែរ",
                "mother_status": "រស់",
                "mother_job": "មេផ្ទះ",
                "current_house_no": "12B",
                "current_street_no": "155",
                "current_village": "ភូមិ៣",
                "current_commune": "ទួលទំពូង១",
                "current_district": "ចំការមន",
                "current_province": "ភ្នំពេញ",
                "address": "ផ្ទះលេខ 12B ផ្លូវលេខ 155 ភូមិ៣ សង្កាត់ទួលទំពូង១ ខណ្ឌចំការមន រាជធានីភ្នំពេញ",
                "phone": "012 889 900",
                "email": "piseth.sok@company.com.kh",
                "national_id": "010992384",
                "position": "ប្រធានការិយាល័យ",
                "dept_code": "OFF-IT",
                "hire_date": date(2021, 2, 1),
                "status": "active",
                "base_salary": 1600.0,
                "bank_account": "001 234 567 (ABA)",
                "avatar": "avatar_1.png"
            },
            {
                "emp_code": "EMP-002",
                "full_name_kh": "ចាន់ សុភា",
                "full_name_en": "Chan Sophear",
                "gender": "ស្រី",
                "ethnicity": "ខ្មែរ",
                "nationality": "ខ្មែរ",
                "dob": date(1994, 8, 22),
                "pob_village": "កំពង់ព្រះ",
                "pob_commune": "កំពង់ព្រះ",
                "pob_district": "សង្កែ",
                "pob_province": "បាត់ដំបង",
                "education_level": "បរិញ្ញាបត្រ (Bachelor Degree)",
                "education_major": "គ្រប់គ្រងធនធានមនុស្ស (Human Resources)",
                "foreign_languages": "អង់គ្លេស (ល្អប្រសើរ), បារាំង (បឋម)",
                "other_skills": "Talent Acquisition, Labour Law Compliance, Payroll Management",
                "marital_status": "នៅលីវ",
                "work_experience_1": "២០១៧-២០១៩៖ HR Officer នៅ Sokha Hotel Group",
                "work_experience_2": "២០១៩-២០២១៖ Senior HR Generalist នៅ Chip Mong Group",
                "work_experience_3": "២០២១-បច្ចុប្បន្ន៖ HR Manager នៅ HRMS Cambodia",
                "father_name": "ចាន់ សារឿន",
                "father_age": "៦៥",
                "father_nationality": "ខ្មែរ",
                "father_status": "រស់",
                "father_job": "កសិករ",
                "mother_name": "កែវ គឹមហៀង",
                "mother_age": "៦១",
                "mother_nationality": "ខ្មែរ",
                "mother_status": "រស់",
                "mother_job": "អាជីវករ",
                "current_house_no": "45A",
                "current_street_no": "289",
                "current_village": "ភូមិ៥",
                "current_commune": "បឹងកក់១",
                "current_district": "ទួលគោក",
                "current_province": "ភ្នំពេញ",
                "address": "ផ្ទះលេខ 45A ផ្លូវលេខ 289 ភូមិ៥ សង្កាត់បឹងកក់១ ខណ្ឌទួលគោក រាជធានីភ្នំពេញ",
                "phone": "017 445 566",
                "email": "sophear.chan@company.com.kh",
                "national_id": "010884729",
                "position": "ប្រធានការិយាល័យ",
                "dept_code": "OFF-HR",
                "hire_date": date(2021, 3, 15),
                "status": "active",
                "base_salary": 1400.0,
                "bank_account": "002 884 112 (ABA)",
                "avatar": "avatar_2.png"
            },
            {
                "emp_code": "EMP-003",
                "full_name_kh": "កែវ មុន្នី",
                "full_name_en": "Keo Mony",
                "gender": "ប្រុស",
                "ethnicity": "ខ្មែរ",
                "nationality": "ខ្មែរ",
                "dob": date(1996, 11, 3),
                "pob_village": "ព្រៃនប់",
                "pob_commune": "ព្រៃនប់",
                "pob_district": "ព្រៃនប់",
                "pob_province": "ព្រះសីហនុ",
                "education_level": "បរិញ្ញាបត្រ (Bachelor Degree)",
                "education_major": "វិស្វកម្មសូហ្វវែរ (Software Engineering)",
                "foreign_languages": "អង់គ្លេស (កម្រិតការងារ)",
                "other_skills": "Python, Flask, JavaScript, PostgreSQL, React",
                "marital_status": "នៅលីវ",
                "work_experience_1": "២០១៩-២០២១៖ Junior Full Stack Developer នៅ WebTech",
                "work_experience_2": "២០២១-២០២២៖ Software Developer នៅ Khmer Software Ltd",
                "work_experience_3": "២០២២-បច្ចុប្បន្ន៖ Senior Developer នៅ HRMS Cambodia",
                "father_name": "កែវ វណ្ណា",
                "father_age": "៥៨",
                "father_nationality": "ខ្មែរ",
                "father_status": "រស់",
                "father_job": "អ្នកនេសាទ",
                "mother_name": "សួស ផល្លា",
                "mother_age": "៥៥",
                "mother_nationality": "ខ្មែរ",
                "mother_status": "រស់",
                "mother_job": "មេផ្ទះ",
                "current_house_no": "88",
                "current_street_no": "ចោមចៅ",
                "current_village": "ព្រៃជីសាក់",
                "current_commune": "ចោមចៅ៣",
                "current_district": "ពោធិ៍សែនជ័យ",
                "current_province": "ភ្នំពេញ",
                "address": "ផ្ទះលេខ 88 ផ្លូវចោមចៅ ភូមិព្រៃជីសាក់ សង្កាត់ចោមចៅ៣ ខណ្ឌពោធិ៍សែនជ័យ រាជធានីភ្នំពេញ",
                "phone": "098 776 655",
                "email": "mony.keo@company.com.kh",
                "national_id": "010773912",
                "position": "អនុប្រធានការិយាល័យ",
                "dept_code": "OFF-IT",
                "hire_date": date(2022, 5, 10),
                "status": "active",
                "base_salary": 1250.0,
                "bank_account": "003 445 667 (ABA)",
                "avatar": "avatar_3.png"
            },
            {
                "emp_code": "EMP-004",
                "full_name_kh": "ហេង ស្រីពៅ",
                "full_name_en": "Heng Sreypov",
                "gender": "ស្រី",
                "ethnicity": "ខ្មែរ",
                "nationality": "ខ្មែរ",
                "dob": date(1995, 3, 18),
                "pob_village": "ស្វាយជ្រុំ",
                "pob_commune": "ស្វាយជ្រុំ",
                "pob_district": "ស្វាយជ្រុំ",
                "pob_province": "ស្វាយរៀង",
                "education_level": "បរិញ្ញាបត្រ (Bachelor Degree)",
                "education_major": "គណនេយ្យ និងហិរញ្ញវត្ថុ (Accounting)",
                "foreign_languages": "អង់គ្លេស (មធ្យម)",
                "other_skills": "QuickBooks, Tax Compliance, Financial Reporting, Audit",
                "marital_status": "មានប្តី ឬប្រពន្ធ",
                "work_experience_1": "២០១៧-២០១៩៖ Assistant Accountant នៅ PWC Cambodia",
                "work_experience_2": "២០១៩-២០២០៖ Senior Accountant នៅ NagaCorp",
                "work_experience_3": "២០២០-បច្ចុប្បន្ន៖ Chief Accountant នៅ HRMS Cambodia",
                "father_name": "ហេង សុខា",
                "father_age": "៦៧",
                "father_nationality": "ខ្មែរ",
                "father_status": "ស្លាប់",
                "father_job": "អតីតគ្រូបង្រៀន",
                "mother_name": "យឹម ស្រីមុំ",
                "mother_age": "៦៣",
                "mother_nationality": "ខ្មែរ",
                "mother_status": "រស់",
                "mother_job": "អាជីវករ",
                "current_house_no": "23",
                "current_street_no": "217",
                "current_village": "ទ្រា",
                "current_commune": "ស្ទឹងមានជ័យ",
                "current_district": "មានជ័យ",
                "current_province": "ភ្នំពេញ",
                "address": "ផ្ទះលេខ 23 ផ្លូវលេខ 217 ភូមិទ្រា សង្កាត់ស្ទឹងមានជ័យ ខណ្ឌមានជ័យ រាជធានីភ្នំពេញ",
                "phone": "089 332 211",
                "email": "sreypov.heng@company.com.kh",
                "national_id": "010443901",
                "position": "ប្រធានការិយាល័យ",
                "dept_code": "OFF-ACC",
                "hire_date": date(2020, 8, 1),
                "status": "active",
                "base_salary": 1350.0,
                "bank_account": "004 998 123 (ABA)",
                "avatar": "avatar_4.png"
            },
            {
                "emp_code": "EMP-005",
                "full_name_kh": "លី វ៉ាន់ណា",
                "full_name_en": "Ly Vanna",
                "gender": "ប្រុស",
                "ethnicity": "ខ្មែរ",
                "nationality": "ខ្មែរ",
                "dob": date(1997, 1, 30),
                "pob_village": "តាខ្មៅ",
                "pob_commune": "តាខ្មៅ",
                "pob_district": "តាខ្មៅ",
                "pob_province": "កណ្តាល",
                "education_level": "បរិញ្ញាបត្រ (Bachelor Degree)",
                "education_major": "ទីផ្សារឌីជីថល (Digital Marketing)",
                "foreign_languages": "អង់គ្លេស (ល្អ), ចិន (សន្ទនា)",
                "other_skills": "SEO, Google Ads, Meta Ads, Copywriting, Branding",
                "marital_status": "នៅលីវ",
                "work_experience_1": "២០១៩-២០២១៖ Content Creator នៅ Havas Champagne",
                "work_experience_2": "២០២១-២០២២៖ Digital Marketer នៅ E-GetS",
                "work_experience_3": "២០២២-បច្ចុប្បន្ន៖ Digital Marketing Lead នៅ HRMS Cambodia",
                "father_name": "លី ហុង",
                "father_age": "៦០",
                "father_nationality": "ខ្មែរ",
                "father_status": "រស់",
                "father_job": "អាជីវករលក់ដូរ",
                "mother_name": "តាន់ ម៉ាលី",
                "mother_age": "៥៦",
                "mother_nationality": "ខ្មែរ",
                "mother_status": "រស់",
                "mother_job": "អាជីវករ",
                "current_house_no": "19",
                "current_street_no": "134",
                "current_village": "ភូមិ២",
                "current_commune": "ផ្សារដេប៉ូ២",
                "current_district": "៧មករា",
                "current_province": "ភ្នំពេញ",
                "address": "ផ្ទះលេខ 19 ផ្លូវលេខ 134 ភូមិ២ សង្កាត់ផ្សារដេប៉ូ២ ខណ្ឌ៧មករា រាជធានីភ្នំពេញ",
                "phone": "085 667 788",
                "email": "vanna.ly@company.com.kh",
                "national_id": "010662118",
                "position": "ប្រធានការិយាល័យ",
                "dept_code": "OFF-MKT",
                "hire_date": date(2022, 9, 1),
                "status": "active",
                "base_salary": 950.0,
                "bank_account": "005 334 887 (Wing)",
                "avatar": "avatar_5.png"
            },
            {
                "emp_code": "EMP-006",
                "full_name_kh": "ជា វិចិត្រ",
                "full_name_en": "Chea Vichetr",
                "gender": "ប្រុស",
                "ethnicity": "ខ្មែរ",
                "nationality": "ខ្មែរ",
                "dob": date(1980, 4, 12),
                "pob_village": "ផ្សារកណ្តាល",
                "pob_commune": "ផ្សារកណ្តាល១",
                "pob_district": "ដូនពេញ",
                "pob_province": "ភ្នំពេញ",
                "education_level": "បរិញ្ញាបត្រជាន់ខ្ពស់ (Master Degree)",
                "education_major": "គ្រប់គ្រងពាណិជ្ជកម្ម (Executive MBA)",
                "foreign_languages": "អង់គ្លេស (ស្ទាត់ជំនាញ), បារាំង (ល្អ)",
                "other_skills": "Strategic Leadership, Enterprise Management, Corporate Governance",
                "marital_status": "មានប្តី ឬប្រពន្ធ",
                "work_experience_1": "២០០៨-២០១៨៖ General Director នៅ Sunrise Holding",
                "work_experience_2": "២០១៨-បច្ចុប្បន្ន៖ អគ្គនាយក នៅ HRMS Cambodia",
                "father_name": "ជា មុនី",
                "father_age": "៧២",
                "father_nationality": "ខ្មែរ",
                "father_status": "រស់",
                "father_job": "មន្ត្រីរាជការចូលនិវត្តន៍",
                "mother_name": "ស៊ុន ធីតា",
                "mother_age": "៦៨",
                "mother_nationality": "ខ្មែរ",
                "mother_status": "រស់",
                "mother_job": "មេផ្ទះ",
                "current_house_no": "100",
                "current_street_no": "214",
                "current_village": "ភូមិ១",
                "current_commune": "បឹងរាំង",
                "current_district": "ដូនពេញ",
                "current_province": "ភ្នំពេញ",
                "address": "ផ្ទះលេខ 100 ផ្លូវលេខ 214 ភូមិ១ សង្កាត់បឹងរាំង ខណ្ឌដូនពេញ រាជធានីភ្នំពេញ",
                "phone": "012 111 222",
                "email": "vichetr.chea@company.com.kh",
                "national_id": "010111222",
                "position": "អគ្គនាយក",
                "dept_code": "OFF-PERS",
                "hire_date": date(2018, 1, 15),
                "status": "active",
                "base_salary": 3500.0,
                "bank_account": "001 888 999 (ABA)",
                "avatar": "avatar_1.png"
            },
            {
                "emp_code": "EMP-007",
                "full_name_kh": "អ៊ុក សុវណ្ណ",
                "full_name_en": "Ouk Sovann",
                "gender": "ប្រុស",
                "ethnicity": "ខ្មែរ",
                "nationality": "ខ្មែរ",
                "dob": date(1983, 8, 20),
                "pob_village": "វាលវង់",
                "pob_commune": "វាលវង់",
                "pob_district": "៧មករា",
                "pob_province": "ភ្នំពេញ",
                "education_level": "បរិញ្ញាបត្រជាន់ខ្ពស់ (Master Degree)",
                "education_major": "ហិរញ្ញវត្ថុ និងធនាគារ (Banking & Finance)",
                "foreign_languages": "អង់គ្លេស (ស្ទាត់ជំនាញ)",
                "other_skills": "Operations, Budgeting, Risk Management",
                "marital_status": "មានប្តី ឬប្រពន្ធ",
                "work_experience_1": "២០១២-២០១៩៖ Operations Director នៅ BRED Bank",
                "work_experience_2": "២០១៩-បច្ចុប្បន្ន៖ អគ្គនាយករង នៅ HRMS Cambodia",
                "father_name": "អ៊ុក គង់",
                "father_age": "៧០",
                "father_nationality": "ខ្មែរ",
                "father_status": "រស់",
                "father_job": "ចូលនិវត្តន៍",
                "mother_name": "ហែម ពិសី",
                "mother_age": "៦៦",
                "mother_nationality": "ខ្មែរ",
                "mother_status": "រស់",
                "mother_job": "មេផ្ទះ",
                "current_house_no": "55",
                "current_street_no": "182",
                "current_village": "ភូមិ៣",
                "current_commune": "វាលវង់",
                "current_district": "៧មករា",
                "current_province": "ភ្នំពេញ",
                "address": "ផ្ទះលេខ 55 ផ្លូវលេខ 182 ភូមិ៣ សង្កាត់វាលវង់ ខណ្ឌ៧មករា រាជធានីភ្នំពេញ",
                "phone": "012 333 444",
                "email": "sovann.ouk@company.com.kh",
                "national_id": "010333444",
                "position": "អគ្គនាយករង",
                "dept_code": "OFF-PERS",
                "hire_date": date(2019, 3, 1),
                "status": "active",
                "base_salary": 2800.0,
                "bank_account": "001 777 666 (ABA)",
                "avatar": "avatar_3.png"
            },
            {
                "emp_code": "EMP-008",
                "full_name_kh": "ស៊ុំ វឌ្ឍនា",
                "full_name_en": "Sum Vathana",
                "gender": "ស្រី",
                "ethnicity": "ខ្មែរ",
                "nationality": "ខ្មែរ",
                "dob": date(1993, 6, 15),
                "pob_village": "ព្រែកប្រា",
                "pob_commune": "ព្រែកប្រា",
                "pob_district": "ច្បារអំពៅ",
                "pob_province": "ភ្នំពេញ",
                "education_level": "បរិញ្ញាបត្រ (Bachelor Degree)",
                "education_major": "គីមីវិទ្យា និងជីវបច្ចេកវិទ្យា (Chemical & Biotechnology)",
                "foreign_languages": "អង់គ្លេស (ល្អ)",
                "other_skills": "Laboratory Testing, Quality Assurance, ISO 17025",
                "marital_status": "នៅលីវ",
                "work_experience_1": "២០១៦-២០២០៖ Lab Chemist នៅ CamControl",
                "work_experience_2": "២០២០-បច្ចុប្បន្ន៖ ប្រធានការិយាល័យពិសោធន៍ នៅ HRMS Cambodia",
                "father_name": "ស៊ុំ សុភាព",
                "father_age": "៦១",
                "father_nationality": "ខ្មែរ",
                "father_status": "រស់",
                "father_job": "កសិករ",
                "mother_name": "ឡេង ណារី",
                "mother_age": "៥៧",
                "mother_nationality": "ខ្មែរ",
                "mother_status": "រស់",
                "mother_job": "មេផ្ទះ",
                "current_house_no": "77",
                "current_street_no": "369",
                "current_village": "ភូមិព្រែកប្រា",
                "current_commune": "ព្រែកប្រា",
                "current_district": "ច្បារអំពៅ",
                "current_province": "ភ្នំពេញ",
                "address": "ផ្ទះលេខ 77 ផ្លូវលេខ 369 ភូមិព្រែកប្រា សង្កាត់ព្រែកប្រា ខណ្ឌច្បារអំពៅ រាជធានីភ្នំពេញ",
                "phone": "017 888 777",
                "email": "vathana.sum@company.com.kh",
                "national_id": "010888777",
                "position": "ប្រធានការិយាល័យ",
                "dept_code": "OFF-LAB",
                "hire_date": date(2020, 6, 1),
                "status": "active",
                "base_salary": 1400.0,
                "bank_account": "002 555 444 (ABA)",
                "avatar": "avatar_2.png"
            },
            {
                "emp_code": "EMP-009",
                "full_name_kh": "ឌៀប សុខុម",
                "full_name_en": "Diep Sokhom",
                "gender": "ប្រុស",
                "ethnicity": "ខ្មែរ",
                "nationality": "ខ្មែរ",
                "dob": date(1991, 10, 10),
                "pob_village": "ស្វាយពោធិ៍",
                "pob_commune": "ស្វាយពោធិ៍",
                "pob_district": "ស្រីសន្ធរ",
                "pob_province": "កំពង់ចាម",
                "education_level": "បរិញ្ញាបត្រ (Bachelor Degree)",
                "education_major": "វិស្វកម្មឧស្សាហកម្ម (Industrial Engineering)",
                "foreign_languages": "អង់គ្លេស (មធ្យម)",
                "other_skills": "Production Scheduling, Lean Manufacturing, Six Sigma, Supply Chain",
                "marital_status": "មានប្តី ឬប្រពន្ធ",
                "work_experience_1": "២០១៥-២០១៩៖ Production Supervisor នៅ Mengly J. Quach Group",
                "work_experience_2": "២០១៩-បច្ចុប្បន្ន៖ ប្រធានការិយាល័យគ្រប់គ្រងការផលិត នៅ HRMS Cambodia",
                "father_name": "ឌៀប ហៀង",
                "father_age": "៦៦",
                "father_nationality": "ខ្មែរ",
                "father_status": "រស់",
                "father_job": "កសិករ",
                "mother_name": "អាន សុខខេង",
                "mother_age": "៦២",
                "mother_nationality": "ខ្មែរ",
                "mother_status": "រស់",
                "mother_job": "មេផ្ទះ",
                "current_house_no": "12",
                "current_street_no": "Veng Sreng",
                "current_village": "ភូមិត្រពាំងថ្លឹង",
                "current_commune": "ចោមចៅ១",
                "current_district": "ពោធិ៍សែនជ័យ",
                "current_province": "ភ្នំពេញ",
                "address": "ផ្ទះលេខ 12 ផ្លូវវេងស្រេង ភូមិត្រពាំងថ្លឹង សង្កាត់ចោមចៅ១ ខណ្ឌពោធិ៍សែនជ័យ រាជធានីភ្នំពេញ",
                "phone": "088 666 555",
                "email": "sokhom.diep@company.com.kh",
                "national_id": "010666555",
                "position": "ប្រធានការិយាល័យ",
                "dept_code": "OFF-PROD",
                "hire_date": date(2019, 10, 1),
                "status": "active",
                "base_salary": 1450.0,
                "bank_account": "003 222 111 (ABA)",
                "avatar": "avatar_4.png"
            },
            {
                "emp_code": "EMP-010",
                "full_name_kh": "ប៉ែន វ៉ាន់នី",
                "full_name_en": "Pen Vanny",
                "gender": "ស្រី",
                "ethnicity": "ខ្មែរ",
                "nationality": "ខ្មែរ",
                "dob": date(1998, 2, 25),
                "pob_village": "រកាកោង",
                "pob_commune": "រកាកោង១",
                "pob_district": "មុខកំពូល",
                "pob_province": "កណ្តាល",
                "education_level": "បរិញ្ញាបត្រ (Bachelor Degree)",
                "education_major": "រដ្ឋបាលសាធារណៈ (Public Administration)",
                "foreign_languages": "អង់គ្លេស (មធ្យម)",
                "other_skills": "Administrative Support, Document Filing, Data Entry",
                "marital_status": "នៅលីវ",
                "work_experience_1": "២០២១-២០២៣៖ Admin Assistant នៅ Royal Group",
                "work_experience_2": "២០២៣-បច្ចុប្បន្ន៖ បុគ្គលិកការិយាល័យបុគ្គលិក នៅ HRMS Cambodia",
                "father_name": "ប៉ែន ធឿន",
                "father_age": "៥៩",
                "father_nationality": "ខ្មែរ",
                "father_status": "រស់",
                "father_job": "កសិករ",
                "mother_name": "ម៉ម សុវណ្ណារី",
                "mother_age": "៥៤",
                "mother_nationality": "ខ្មែរ",
                "mother_status": "រស់",
                "mother_job": "មេផ្ទះ",
                "current_house_no": "64",
                "current_street_no": "598",
                "current_village": "ភូមិទួលគោក",
                "current_commune": "ទួលសង្កែ១",
                "current_district": "ឫស្សីកែវ",
                "current_province": "ភ្នំពេញ",
                "address": "ផ្ទះលេខ 64 ផ្លូវលេខ 598 ភូមិទួលគោក សង្កាត់ទួលសង្កែ១ ខណ្ឌឫស្សីកែវ រាជធានីភ្នំពេញ",
                "phone": "096 444 333",
                "email": "vanny.pen@company.com.kh",
                "national_id": "010444333",
                "position": "បុគ្គលិក",
                "dept_code": "OFF-PERS",
                "hire_date": date(2023, 1, 10),
                "status": "active",
                "base_salary": 650.0,
                "bank_account": "004 888 777 (Wing)",
                "avatar": "avatar_5.png"
            }
        ]

        dept_map = {d.code: d.id for d in Department.query.all()}
        created_employees = []
        
        for data in employees_data:
            dept_id = dept_map.get(data["dept_code"])
            emp = Employee(
                emp_code=data["emp_code"],
                full_name_kh=data["full_name_kh"],
                full_name_en=data["full_name_en"],
                gender=data["gender"],
                ethnicity=data["ethnicity"],
                nationality=data["nationality"],
                dob=data["dob"],
                pob_village=data["pob_village"],
                pob_commune=data["pob_commune"],
                pob_district=data["pob_district"],
                pob_province=data["pob_province"],
                education_level=data["education_level"],
                education_major=data["education_major"],
                foreign_languages=data["foreign_languages"],
                other_skills=data["other_skills"],
                marital_status=data["marital_status"],
                work_experience_1=data["work_experience_1"],
                work_experience_2=data["work_experience_2"],
                work_experience_3=data["work_experience_3"],
                father_name=data["father_name"],
                father_age=data["father_age"],
                father_nationality=data["father_nationality"],
                father_status=data["father_status"],
                father_job=data["father_job"],
                mother_name=data["mother_name"],
                mother_age=data["mother_age"],
                mother_nationality=data["mother_nationality"],
                mother_status=data["mother_status"],
                mother_job=data["mother_job"],
                current_house_no=data["current_house_no"],
                current_street_no=data["current_street_no"],
                current_village=data["current_village"],
                current_commune=data["current_commune"],
                current_district=data["current_district"],
                current_province=data["current_province"],
                address=data["address"],
                phone=data["phone"],
                email=data["email"],
                national_id=data["national_id"],
                position=data["position"],
                department_id=dept_id,
                hire_date=data["hire_date"],
                status=data["status"],
                base_salary=data["base_salary"],
                bank_account=data["bank_account"],
                avatar=data["avatar"]
            )
            db.session.add(emp)
            created_employees.append(emp)
        
        db.session.commit()

        # 3. Sample Documents
        sample_docs = [
            ("contract", "កិច្ចសន្យាការងារមានថិរវេលាកំណត់ (FDC Contract)", "contract_sample.pdf", "1.2 MB"),
            ("id_card", "អត្តសញ្ញាណប័ណ្ណសញ្ជាតិខ្មែរ (National ID Copy)", "national_id.pdf", "850 KB"),
            ("cv", "ប្រវត្តិរូបសង្ខេបបច្ចុប្បន្ន (Curriculum Vitae)", "cv_resume.pdf", "650 KB")
        ]
        for emp in created_employees:
            for doc_type, title, filename, size in sample_docs:
                doc = EmployeeDocument(
                    employee_id=emp.id,
                    doc_type=doc_type,
                    title=f"{title} - {emp.full_name_kh}",
                    file_name=filename,
                    file_size=size,
                    notes="ឯកសារបានផ្ទៀងផ្ទាត់រួចរាល់ដោយផ្នែកធនធានមនុស្ស"
                )
                db.session.add(doc)
        db.session.commit()

        # 4. Attendance
        current_date = date.today()
        for day_offset in range(14, -1, -1):
            att_date = current_date - timedelta(days=day_offset)
            if att_date.weekday() == 6:
                continue
            for emp in created_employees:
                roll = random.random()
                if roll < 0.8:
                    check_in = f"07:{random.randint(45, 59):02d}"
                    check_out = f"17:{random.randint(0, 15):02d}"
                    ot = 1.5 if (roll < 0.25 and att_date.weekday() in [2, 4]) else 0.0
                    att = Attendance(
                        employee_id=emp.id,
                        date=att_date,
                        check_in=check_in,
                        check_out=check_out,
                        status="present",
                        late_minutes=0,
                        work_hours=8.0 + ot,
                        ot_hours=ot,
                        source="biometric",
                        notes="វត្តមានធម្មតា"
                    )
                elif roll < 0.92:
                    late_min = random.randint(10, 35)
                    att = Attendance(
                        employee_id=emp.id,
                        date=att_date,
                        check_in=f"08:{late_min:02d}",
                        check_out="17:00",
                        status="late",
                        late_minutes=late_min,
                        work_hours=7.5,
                        ot_hours=0.0,
                        source="biometric",
                        notes=f"មកយឺត {late_min} នាទី"
                    )
                else:
                    att = Attendance(
                        employee_id=emp.id,
                        date=att_date,
                        check_in=None,
                        check_out=None,
                        status="leave",
                        late_minutes=0,
                        work_hours=0.0,
                        ot_hours=0.0,
                        source="manual",
                        notes="ច្បាប់អនុញ្ញាត"
                    )
                db.session.add(att)
        db.session.commit()

        # 5. Leaves
        leaves_data = [
            {
                "emp_id": created_employees[1].id,
                "leave_type": "annual",
                "start_date": current_date + timedelta(days=5),
                "end_date": current_date + timedelta(days=7),
                "total_days": 3.0,
                "reason": "ដំណើរកម្សាន្តប្រចាំឆ្នាំជាមួយក្រុមគ្រួសារ",
                "status": "approved",
                "approved_by": "នាយកប្រតិបត្តិ (CEO)"
            },
            {
                "emp_id": created_employees[2].id,
                "leave_type": "sick",
                "start_date": current_date - timedelta(days=3),
                "end_date": current_date - timedelta(days=2),
                "total_days": 2.0,
                "reason": "មានជំងឺផ្តាសាយធំ និងក្អកខ្លាំង",
                "status": "approved",
                "approved_by": "ប្រធានផ្នែក HR"
            }
        ]
        for l_data in leaves_data:
            leave = LeaveRequest(
                employee_id=l_data["emp_id"],
                leave_type=l_data["leave_type"],
                start_date=l_data["start_date"],
                end_date=l_data["end_date"],
                total_days=l_data["total_days"],
                reason=l_data["reason"],
                status=l_data["status"],
                approved_by=l_data["approved_by"]
            )
            db.session.add(leave)
        db.session.commit()

        # 6. Payroll
        current_month_str = current_date.strftime("%Y-%m")
        for idx, emp in enumerate(created_employees):
            calc = compute_employee_payroll(
                base_salary=emp.base_salary,
                worked_days=26.0,
                standard_days=26,
                ot_hours=8.0 if idx in [0, 2] else 0.0,
                bonus=50.0 if idx == 1 else 0.0,
                allowance=40.0,
                absent_days=0.0
            )
            payroll = Payroll(
                employee_id=emp.id,
                month_year=current_month_str,
                base_salary=calc['base_salary'],
                standard_work_days=calc['standard_work_days'],
                worked_days=calc['worked_days'],
                ot_hours=calc['ot_hours'],
                ot_rate=calc['ot_rate'],
                ot_amount=calc['ot_amount'],
                bonus=calc['bonus'],
                allowance=calc['allowance'],
                gross_salary=calc['gross_salary'],
                absent_days=0.0,
                absent_deduction=0.0,
                late_deduction=0.0,
                nssf_deduction=calc['nssf_deduction'],
                salary_tax=calc['salary_tax'],
                advance_salary=0.0,
                other_deductions=0.0,
                total_deductions=calc['total_deductions'],
                net_salary=calc['net_salary'],
                payment_status='paid' if idx < 3 else 'approved',
                payment_date=date.today(),
                payment_method=emp.bank_account or "ABA Bank",
                notes="ទូទាត់ប្រាក់បៀវត្សតាមការកំណត់"
            )
            db.session.add(payroll)
        
        db.session.commit()
        
        # Also seed Cambodia Administrative Locations from CSV
        from import_cambodia_geo import import_cambodia_locations
        geo_res = import_cambodia_locations()
        print(f"Geo locations seeded: {geo_res}")
        
        print("Data seeded successfully with official CV layout and Cambodia locations!")

if __name__ == "__main__":
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hrms.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    create_sample_data(app)
