import unittest
from datetime import date
from app import app, db
from models import Employee, Department, Attendance, LeaveRequest, Payroll, User

class HRMSTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        for code in ['EMP-TEST-99', 'EMP-GEO-001']:
            old_emp = Employee.query.filter_by(emp_code=code).first()
            if old_emp:
                db.session.delete(old_emp)
        for u in User.query.filter(User.username.in_(['reg_user', 'new_user', 'test_staff'])).all():
            db.session.delete(u)
        db.session.commit()

    def tearDown(self):
        for code in ['EMP-TEST-99', 'EMP-GEO-001']:
            old_emp = Employee.query.filter_by(emp_code=code).first()
            if old_emp:
                db.session.delete(old_emp)
        for u in User.query.filter(User.username.in_(['reg_user', 'new_user', 'test_staff'])).all():
            db.session.delete(u)
        db.session.commit()
        self.app_context.pop()

    def test_01_dashboard(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('HRMS កម្ពុជា'.encode('utf-8'), response.data)
        self.assertIn('ផ្ទាំងព័ត៌មាន'.encode('utf-8'), response.data)

    def test_02_employee_list_and_search(self):
        response = self.client.get('/employees')
        self.assertEqual(response.status_code, 200)
        self.assertIn('បញ្ជីបុគ្គលិក'.encode('utf-8'), response.data)

        # Search test
        response_search = self.client.get('/employees?search=Sok')
        self.assertEqual(response_search.status_code, 200)

    def test_03_employee_create_and_detail(self):
        dept = Department.query.first()
        post_data = {
            'emp_code': 'EMP-TEST-99',
            'full_name_kh': 'តេស្ត បុគ្គលិក',
            'full_name_en': 'Test Employee',
            'gender': 'ប្រុស',
            'dob': '1995-01-01',
            'phone': '012999888',
            'email': 'test@company.com',
            'address': 'ភ្នំពេញ',
            'position': 'បុគ្គលិក',
            'department_id': str(dept.id),
            'hire_date': '2026-01-01',
            'status': 'active',
            'base_salary': '600.00',
            'bank_account': '001 999 888 (ABA)'
        }
        res = self.client.post('/employees/create', data=post_data, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn('តេស្ត បុគ្គលិក'.encode('utf-8'), res.data)

        # Query and view detail
        emp = Employee.query.filter_by(emp_code='EMP-TEST-99').first()
        self.assertIsNotNone(emp)
        res_detail = self.client.get(f'/employees/{emp.id}')
        self.assertEqual(res_detail.status_code, 200)
        self.assertIn('បុគ្គលិក'.encode('utf-8'), res_detail.data)

        # Test official CV 100% replica route
        res_cv = self.client.get(f'/employees/{emp.id}/official-cv')
        self.assertEqual(res_cv.status_code, 200)
        self.assertIn('ប្រវត្តិរូបសង្ខេប'.encode('utf-8'), res_cv.data)
        self.assertIn('ព្រះរាជាណាចក្រកម្ពុជា'.encode('utf-8'), res_cv.data)

    def test_04_attendance_daily_and_scanner(self):
        res = self.client.get('/attendance')
        self.assertEqual(res.status_code, 200)
        self.assertIn('វត្តមានប្រចាំថ្ងៃ'.encode('utf-8'), res.data)

        emp = Employee.query.first()
        # Simulate single punch in
        res_sim = self.client.post('/attendance/simulate-scanner', data={
            'mode': 'single',
            'employee_id': str(emp.id),
            'punch_type': 'in',
            'punch_time': '07:55',
            'source': 'biometric',
            'date': date.today().strftime('%Y-%m-%d')
        }, follow_redirects=True)
        self.assertEqual(res_sim.status_code, 200)

        # Batch punch all
        res_batch = self.client.post('/attendance/simulate-scanner', data={
            'mode': 'batch_all',
            'date': date.today().strftime('%Y-%m-%d')
        }, follow_redirects=True)
        self.assertEqual(res_batch.status_code, 200)

    def test_05_leaves_management(self):
        res = self.client.get('/attendance/leaves')
        self.assertEqual(res.status_code, 200)
        self.assertIn('ច្បាប់ឈប់សម្រាក'.encode('utf-8'), res.data)

        # Submit leave
        emp = Employee.query.first()
        res_submit = self.client.post('/attendance/leaves/request', data={
            'employee_id': str(emp.id),
            'leave_type': 'annual',
            'start_date': date.today().strftime('%Y-%m-%d'),
            'end_date': date.today().strftime('%Y-%m-%d'),
            'reason': 'សុំច្បាប់កិច្ចការបន្ទាន់'
        }, follow_redirects=True)
        self.assertEqual(res_submit.status_code, 200)

        # Approve leave
        leave = LeaveRequest.query.filter_by(employee_id=emp.id, status='pending').first()
        if leave:
            res_act = self.client.post(f'/attendance/leaves/{leave.id}/action', data={
                'action': 'approve',
                'admin_name': 'HR Director'
            }, follow_redirects=True)
            self.assertEqual(res_act.status_code, 200)

    def test_06_payroll_and_payslip(self):
        current_month = date.today().strftime('%Y-%m')
        res = self.client.get(f'/payroll?month={current_month}')
        self.assertEqual(res.status_code, 200)
        self.assertIn('គ្រប់គ្រងប្រាក់បៀវត្ស'.encode('utf-8'), res.data)

        # Generate payroll
        res_gen = self.client.post('/payroll/generate', data={
            'month_year': current_month
        }, follow_redirects=True)
        self.assertEqual(res_gen.status_code, 200)

        # Check payslip
        payroll = Payroll.query.filter_by(month_year=current_month).first()
        self.assertIsNotNone(payroll)
        res_slip = self.client.get(f'/payroll/{payroll.id}/payslip')
        self.assertEqual(res_slip.status_code, 200)
        self.assertIn('វិក្កយបត្រប្រាក់ខែ'.encode('utf-8'), res_slip.data)
        self.assertIn('SALARY PAYSLIP'.encode('utf-8'), res_slip.data)

    def test_07_reports_and_csv_exports(self):
        current_month = date.today().strftime('%Y-%m')

        # Attendance Report
        res_att_rep = self.client.get(f'/attendance/report?month={current_month}')
        self.assertEqual(res_att_rep.status_code, 200)

        # Attendance CSV Export
        res_att_csv = self.client.get(f'/attendance/export-csv?month={current_month}')
        self.assertEqual(res_att_csv.status_code, 200)
        self.assertEqual(res_att_csv.content_type, 'text/csv; charset=utf-8')

        # Payroll Report
        res_pay_rep = self.client.get(f'/payroll/report?month={current_month}')
        self.assertEqual(res_pay_rep.status_code, 200)

        # Payroll CSV Export
        res_pay_csv = self.client.get(f'/payroll/export-csv?month={current_month}')
        self.assertEqual(res_pay_csv.status_code, 200)
        self.assertEqual(res_pay_csv.content_type, 'text/csv; charset=utf-8')

    def test_08_geo_apis_and_explorer(self):
        # 1. Test provinces API
        res_p = self.client.get('/api/geo/provinces')
        self.assertEqual(res_p.status_code, 200)
        self.assertEqual(len(res_p.json), 25)

        # 2. Test districts API (Phnom Penh code 12)
        res_d = self.client.get('/api/geo/districts?province_code=12')
        self.assertEqual(res_d.status_code, 200)
        self.assertEqual(len(res_d.json), 14)

        # 3. Test communes API (Chamkar Mon code 1201)
        res_c = self.client.get('/api/geo/communes?district_code=1201')
        self.assertEqual(res_c.status_code, 200)
        self.assertEqual(len(res_c.json), 5)

        # 4. Test geo locations explorer page
        res_page = self.client.get('/geo-locations')
        self.assertEqual(res_page.status_code, 200)
        self.assertIn('ទិន្នន័យភូមិសាស្ត្ររដ្ឋបាលកម្ពុជា'.encode('utf-8'), res_page.data)

        # 5. Test search filter
        res_search = self.client.get('/geo-locations?search=ទន្លេបាសាក់')
        self.assertEqual(res_search.status_code, 200)
        self.assertIn('Tonle Basak'.encode('utf-8'), res_search.data)

    def test_09_employee_geo_integration(self):
        dept = Department.query.first()
        post_data = {
            'emp_code': 'EMP-GEO-001',
            'full_name_kh': 'គង់ វឌ្ឍនៈ',
            'full_name_en': 'Kong Vattana',
            'gender': 'ប្រុស',
            'dob': '1996-05-15',
            # Place of Birth
            'pob_province': 'ខេត្តបាត់ដំបង',
            'pob_district': 'ក្រុងបាត់ដំបង',
            'pob_commune': 'ស្វាយប៉ោ',
            'pob_village': 'ព្រែកមហាទេព',
            # Current Address
            'current_province': 'រាជធានីភ្នំពេញ',
            'current_district': 'ខណ្ឌចំការមន',
            'current_commune': 'ទន្លេបាសាក់',
            'current_village': 'ភូមិ ១',
            'current_house_no': '12B',
            'current_street_no': '271',
            # Employment
            'phone': '098765432',
            'position': 'បុគ្គលិក',
            'department_id': str(dept.id),
            'hire_date': '2026-03-01',
            'status': 'active',
            'base_salary': '850.00'
        }
        res = self.client.post('/employees/create', data=post_data, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        emp = Employee.query.filter_by(emp_code='EMP-GEO-001').first()
        self.assertIsNotNone(emp)
        self.assertEqual(emp.pob_province, 'ខេត្តបាត់ដំបង')
        self.assertEqual(emp.pob_district, 'ក្រុងបាត់ដំបង')
        self.assertEqual(emp.pob_commune, 'ស្វាយប៉ោ')
        self.assertEqual(emp.pob_village, 'ព្រែកមហាទេព')

        self.assertEqual(emp.current_province, 'រាជធានីភ្នំពេញ')
        self.assertEqual(emp.current_district, 'ខណ្ឌចំការមន')
        self.assertEqual(emp.current_commune, 'ទន្លេបាសាក់')
        self.assertEqual(emp.current_village, 'ភូមិ ១')

        # Test official CV displays the exact locations
        res_cv = self.client.get(f'/employees/{emp.id}/official-cv')
        self.assertEqual(res_cv.status_code, 200)
        self.assertIn('ខេត្តបាត់ដំបង'.encode('utf-8'), res_cv.data)
        self.assertIn('ស្វាយប៉ោ'.encode('utf-8'), res_cv.data)
        self.assertIn('ទន្លេបាសាក់'.encode('utf-8'), res_cv.data)

    def test_10_user_registration(self):
        # 1. GET /register
        res = self.client.get('/register')
        self.assertEqual(res.status_code, 200)
        self.assertIn('ចុះឈ្មោះគណនីប្រើប្រាស់'.encode('utf-8'), res.data)

        # 2. POST valid registration (should be pending approval)
        res_post = self.client.post('/register', data={
            'username': 'reg_user',
            'role': 'hr',
            'password': 'password123',
            'confirm_password': 'password123',
            'phone': '012999777',
            'employee_name': 'កញ្ញា រស្មី',
        }, follow_redirects=True)
        self.assertEqual(res_post.status_code, 200)
        self.assertIn('រង់ចាំការអនុម័តពី ADMIN'.encode('utf-8'), res_post.data)

        # Verify in DB that status is pending and is_active is False
        u = User.query.filter_by(username='reg_user').first()
        self.assertIsNotNone(u)
        self.assertEqual(u.employee_name, 'កញ្ញា រស្មី')
        self.assertEqual(u.role, 'hr')
        self.assertEqual(u.approval_status, 'pending')
        self.assertFalse(u.is_active)
        self.assertTrue(u.check_password('password123'))

        # 3. Attempt to login with pending user should be blocked
        res_login_pending = self.client.post('/login', data={
            'username': 'reg_user',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(res_login_pending.status_code, 200)
        self.assertIn('រង់ចាំការអនុម័តពី ADMIN'.encode('utf-8'), res_login_pending.data)

        # 4. ADMIN approves user
        res_appr = self.client.post(f'/users/{u.id}/approve', follow_redirects=True)
        self.assertEqual(res_appr.status_code, 200)
        db.session.refresh(u)
        self.assertEqual(u.approval_status, 'approved')
        self.assertTrue(u.is_active)

        # 5. Now approved user can login
        res_login_approved = self.client.post('/login', data={
            'username': 'reg_user',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(res_login_approved.status_code, 200)
        self.assertIn('សូមស្វាគមន៍មកកាន់ប្រព័ន្ធ'.encode('utf-8'), res_login_approved.data)

        # 6. Duplicate username or registering ADMIN should fail
        res_dup_admin = self.client.post('/register', data={
            'username': 'ADMIN',
            'role': 'staff',
            'password': 'password123',
            'confirm_password': 'password123',
            'employee_name': 'Admin ស្ទួន',
        }, follow_redirects=True)
        self.assertEqual(res_dup_admin.status_code, 200)
        self.assertIn('គណនីអចិន្ត្រៃយ៍'.encode('utf-8'), res_dup_admin.data)

    def test_11_user_login_and_logout(self):
        # 1. GET /login
        res_get = self.client.get('/login')
        self.assertEqual(res_get.status_code, 200)
        self.assertIn('ចូលប្រើប្រាស់ (Sign In)'.encode('utf-8'), res_get.data)
        # Ensure demo credentials box is NOT displayed
        self.assertNotIn('Admin សាកល្បង'.encode('utf-8'), res_get.data)

        # 2. POST wrong password with ADMIN
        res_wrong = self.client.post('/login', data={
            'username': 'ADMIN',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        self.assertEqual(res_wrong.status_code, 200)
        self.assertIn('មិនត្រឹមត្រូវទេ'.encode('utf-8'), res_wrong.data)

        # 3. POST correct password with permanent ADMIN / syd001
        res_ok = self.client.post('/login', data={
            'username': 'ADMIN',
            'password': 'syd001'
        }, follow_redirects=True)
        self.assertEqual(res_ok.status_code, 200)
        self.assertIn('សូមស្វាគមន៍មកកាន់ប្រព័ន្ធ'.encode('utf-8'), res_ok.data)

        # 4. GET /logout
        res_logout = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(res_logout.status_code, 200)
        self.assertIn('បានចាកចេញពីប្រព័ន្ធដោយជោគជ័យ'.encode('utf-8'), res_logout.data)

    def test_12_user_management_crud(self):
        # 1. User listing
        res_list = self.client.get('/users')
        self.assertEqual(res_list.status_code, 200)
        self.assertIn('គ្រប់គ្រងអ្នកប្រើប្រាស់'.encode('utf-8'), res_list.data)

        # 2. Verify permanent ADMIN protection
        admin = User.query.filter(User.username.ilike('ADMIN')).first()
        self.assertIsNotNone(admin)
        self.assertTrue(admin.is_permanent_admin)

        # Attempt to delete ADMIN should fail
        res_del_admin = self.client.post(f'/users/{admin.id}/delete', follow_redirects=True)
        self.assertEqual(res_del_admin.status_code, 200)
        self.assertIn('មិនអាចលុបគណនីអចិន្ត្រៃយ៍ ADMIN'.encode('utf-8'), res_del_admin.data)

        # Attempt to toggle status of ADMIN should fail
        res_tog_admin = self.client.post(f'/users/{admin.id}/toggle-status', follow_redirects=True)
        self.assertEqual(res_tog_admin.status_code, 200)
        self.assertIn('មិនអាចផ្អាកដំណើរការគណនីអចិន្ត្រៃយ៍ ADMIN'.encode('utf-8'), res_tog_admin.data)

        # 3. Create regular user by admin
        res_create = self.client.post('/users/create', data={
            'username': 'test_staff',
            'role': 'staff',
            'password': 'staffpassword123',
            'phone': '098111222',
            'employee_name': 'លោក ចាន់ដារ៉ា',
            'is_active': '1'
        }, follow_redirects=True)
        self.assertEqual(res_create.status_code, 200)
        self.assertIn('បានបង្កើតគណនី'.encode('utf-8'), res_create.data)

        u = User.query.filter_by(username='test_staff').first()
        self.assertIsNotNone(u)
        self.assertEqual(u.approval_status, 'approved')

        # 4. Edit user
        res_edit = self.client.post(f'/users/{u.id}/edit', data={
            'employee_name': 'លោក ចាន់ដារ៉ា (កែប្រែ)',
            'role': 'accountant',
            'phone': '098333444',
            'is_active': '1',
            'approval_status': 'approved'
        }, follow_redirects=True)
        self.assertEqual(res_edit.status_code, 200)
        db.session.refresh(u)
        self.assertEqual(u.employee_name, 'លោក ចាន់ដារ៉ា (កែប្រែ)')
        self.assertEqual(u.role, 'accountant')

        # 5. Change password
        res_pwd = self.client.post(f'/users/{u.id}/change-password', data={
            'new_password': 'newsecretpass',
            'confirm_password': 'newsecretpass'
        }, follow_redirects=True)
        self.assertEqual(res_pwd.status_code, 200)
        db.session.refresh(u)
        self.assertTrue(u.check_password('newsecretpass'))

        # 6. Reject user
        res_rej = self.client.post(f'/users/{u.id}/reject', follow_redirects=True)
        self.assertEqual(res_rej.status_code, 200)
        db.session.refresh(u)
        self.assertEqual(u.approval_status, 'rejected')
        self.assertFalse(u.is_active)

        # 7. Delete user
        res_del = self.client.post(f'/users/{u.id}/delete', follow_redirects=True)
        self.assertEqual(res_del.status_code, 200)
        self.assertIsNone(User.query.filter_by(username='test_staff').first())

    def test_13_non_admin_cannot_see_or_access_users(self):
        """Test that regular non-admin users cannot see or access the User Management feature"""
        with app.app_context():
            # Create a regular staff user and approve
            staff = User.query.filter_by(username='regular_staff').first()
            if not staff:
                staff = User(
                    username='regular_staff',
                    role='staff',
                    phone='012999888',
                    employee_name='បុគ្គលិក ធម្មតា',
                    is_active=True,
                    approval_status='approved'
                )
                staff.set_password('staff123456')
                db.session.add(staff)
                db.session.commit()

        # 1. Login as regular staff user
        login_res = self.client.post('/login', data={
            'username': 'regular_staff',
            'password': 'staff123456'
        }, follow_redirects=True)
        self.assertEqual(login_res.status_code, 200)

        # 2. Check Dashboard page HTML - Users menu must NOT be visible to non-admin
        dash_res = self.client.get('/')
        self.assertEqual(dash_res.status_code, 200)
        self.assertNotIn('គ្រប់គ្រងអ្នកប្រើ (Users)'.encode('utf-8'), dash_res.data)
        self.assertNotIn('/users'.encode('utf-8'), dash_res.data)

        # 3. Non-admin directly attempts to access GET /users - must be blocked and redirected
        users_get_res = self.client.get('/users', follow_redirects=True)
        self.assertEqual(users_get_res.status_code, 200)
        self.assertIn('លោកអ្នកមិនមានសិទ្ធិគ្រប់គ្រងផ្នែកនេះទេ'.encode('utf-8'), users_get_res.data)
        # Should be on dashboard, not on users list
        self.assertNotIn('User Management'.encode('utf-8'), users_get_res.data)

        # 4. Non-admin directly attempts to POST to /users/create - must be blocked
        users_post_res = self.client.post('/users/create', data={
            'username': 'hacker',
            'password': 'password123',
            'role': 'admin',
            'employee_name': 'Hacker'
        }, follow_redirects=True)
        self.assertEqual(users_post_res.status_code, 200)
        self.assertIn('លោកអ្នកមិនមានសិទ្ធិគ្រប់គ្រងផ្នែកនេះទេ'.encode('utf-8'), users_post_res.data)
        with app.app_context():
            self.assertIsNone(User.query.filter_by(username='hacker').first())

        # 5. Logout and Login as ADMIN
        self.client.get('/logout', follow_redirects=True)
        admin_login_res = self.client.post('/login', data={
            'username': 'ADMIN',
            'password': 'syd001'
        }, follow_redirects=True)
        self.assertEqual(admin_login_res.status_code, 200)

        # 6. Admin CAN see Users menu in dashboard
        admin_dash_res = self.client.get('/')
        self.assertEqual(admin_dash_res.status_code, 200)
        self.assertIn('គ្រប់គ្រងអ្នកប្រើ (Users)'.encode('utf-8'), admin_dash_res.data)

        # 7. Admin CAN access /users
        admin_users_res = self.client.get('/users')
        self.assertEqual(admin_users_res.status_code, 200)
        self.assertIn('User Management'.encode('utf-8'), admin_users_res.data)

    def test_14_organization_structure(self):
        """Test the 7 official offices and 5 official positions, and ensure all other depts are deleted"""
        from models import OFFICIAL_DEPARTMENTS, OFFICIAL_POSITIONS
        
        with app.app_context():
            # 1. Verify exact 7 offices exist
            depts = Department.query.all()
            self.assertEqual(len(depts), 7)
            dept_names = [d.name_kh for d in depts]
            expected_names = [d['name_kh'] for d in OFFICIAL_DEPARTMENTS]
            self.assertEqual(set(dept_names), set(expected_names))

            # 2. Verify all employees have positions in OFFICIAL_POSITIONS
            for emp in Employee.query.all():
                self.assertIn(emp.position, OFFICIAL_POSITIONS)
                self.assertIn(emp.department.name_kh, expected_names)

        # 3. Test employee form displays 7 offices and 5 positions in dropdowns
        form_res = self.client.get('/employees/create')
        self.assertEqual(form_res.status_code, 200)
        for d in OFFICIAL_DEPARTMENTS:
            self.assertIn(d['name_kh'].encode('utf-8'), form_res.data)
        for pos in OFFICIAL_POSITIONS:
            self.assertIn(pos.encode('utf-8'), form_res.data)

        # 4. Verify employee list filter contains the offices and positions
        list_res = self.client.get('/employees')
        self.assertEqual(list_res.status_code, 200)
        self.assertIn('ការិយាល័យទាំងអស់'.encode('utf-8'), list_res.data)
        self.assertIn('តួនាទីទាំងអស់'.encode('utf-8'), list_res.data)

    def test_15_organization_crud(self):
        """Test full CRUD operations for departments/offices and positions/roles"""
        from models import Position, Department, Employee
        
        # 1. Admin accesses /organization
        res_org = self.client.get('/organization')
        self.assertEqual(res_org.status_code, 200)
        self.assertIn('គ្រប់គ្រងរចនាសម្ព័ន្ធ & តួនាទី'.encode('utf-8'), res_org.data)
        self.assertIn('ការិយាល័យបុគ្គលិក'.encode('utf-8'), res_org.data)

        # 2. Tab positions
        res_pos_tab = self.client.get('/organization?tab=positions')
        self.assertEqual(res_pos_tab.status_code, 200)
        self.assertIn('បញ្ជីតួនាទី និងមុខតំណែងទាំងអស់'.encode('utf-8'), res_pos_tab.data)
        self.assertIn('អគ្គនាយក'.encode('utf-8'), res_pos_tab.data)

        # 3. Create a new Department
        new_dept_data = {
            'name_kh': 'ការិយាល័យទំនាក់ទំនងសាធារណៈ',
            'name_en': 'Public Relations Office',
            'code': 'OFF-PR',
            'description': 'គ្រប់គ្រងទំនាក់ទំនងសាធារណៈ និងព័ត៌មាន'
        }
        res_create_dept = self.client.post('/organization/departments/create', data=new_dept_data, follow_redirects=True)
        self.assertEqual(res_create_dept.status_code, 200)
        self.assertIn('ការិយាល័យទំនាក់ទំនងសាធារណៈ'.encode('utf-8'), res_create_dept.data)
        
        dept = Department.query.filter_by(code='OFF-PR').first()
        self.assertIsNotNone(dept)
        self.assertEqual(dept.name_kh, 'ការិយាល័យទំនាក់ទំនងសាធារណៈ')

        # 4. Edit the Department
        edit_dept_data = {
            'name_kh': 'ការិយាល័យទំនាក់ទំនងសាធារណៈថ្មី',
            'name_en': 'Public Relations New Office',
            'code': 'OFF-PRM',
            'description': 'គ្រប់គ្រងការផ្សព្វផ្សាយ'
        }
        res_edit_dept = self.client.post(f'/organization/departments/{dept.id}/edit', data=edit_dept_data, follow_redirects=True)
        self.assertEqual(res_edit_dept.status_code, 200)
        self.assertIn('បានកែប្រែព័ត៌មានការិយាល័យ'.encode('utf-8'), res_edit_dept.data)
        self.assertEqual(dept.code, 'OFF-PRM')

        # 5. Create a new Position
        new_pos_data = {
            'name_kh': 'ទីប្រឹក្សាជាន់ខ្ពស់',
            'name_en': 'Senior Advisor',
            'code': 'POS-ADV',
            'description': 'ផ្តល់យោបល់ និងប្រឹក្សាយុទ្ធសាស្ត្រ'
        }
        res_create_pos = self.client.post('/organization/positions/create', data=new_pos_data, follow_redirects=True)
        self.assertEqual(res_create_pos.status_code, 200)
        self.assertIn('ទីប្រឹក្សាជាន់ខ្ពស់'.encode('utf-8'), res_create_pos.data)

        pos = Position.query.filter_by(name_kh='ទីប្រឹក្សាជាន់ខ្ពស់').first()
        self.assertIsNotNone(pos)
        self.assertEqual(pos.code, 'POS-ADV')

        # 6. Verify newly created office & position dynamically appear in employee create form dropdowns!
        res_emp_form = self.client.get('/employees/create')
        self.assertEqual(res_emp_form.status_code, 200)
        self.assertIn('ការិយាល័យទំនាក់ទំនងសាធារណៈថ្មី'.encode('utf-8'), res_emp_form.data)
        self.assertIn('ទីប្រឹក្សាជាន់ខ្ពស់'.encode('utf-8'), res_emp_form.data)

        # 7. Edit Position
        edit_pos_data = {
            'name_kh': 'ទីប្រឹក្សាយុទ្ធសាស្ត្រជាន់ខ្ពស់',
            'name_en': 'Senior Strategic Advisor',
            'code': 'POS-SADV',
            'description': 'ការប្រឹក្សាយុទ្ធសាស្ត្រជាន់ខ្ពស់'
        }
        res_edit_pos = self.client.post(f'/organization/positions/{pos.id}/edit', data=edit_pos_data, follow_redirects=True)
        self.assertEqual(res_edit_pos.status_code, 200)
        self.assertIn('បានកែប្រែតួនាទី'.encode('utf-8'), res_edit_pos.data)
        self.assertEqual(pos.name_kh, 'ទីប្រឹក្សាយុទ្ធសាស្ត្រជាន់ខ្ពស់')

        # 8. Delete Position (has 0 employees, should succeed)
        res_del_pos = self.client.post(f'/organization/positions/{pos.id}/delete', follow_redirects=True)
        self.assertEqual(res_del_pos.status_code, 200)
        self.assertIn('បានលុបតួនាទី'.encode('utf-8'), res_del_pos.data)
        self.assertIsNone(Position.query.filter_by(id=pos.id).first())

        # 9. Delete Department (has 0 employees, should succeed)
        res_del_dept = self.client.post(f'/organization/departments/{dept.id}/delete', follow_redirects=True)
        self.assertEqual(res_del_dept.status_code, 200)
        self.assertIn('បានលុបការិយាល័យ'.encode('utf-8'), res_del_dept.data)
        self.assertIsNone(Department.query.filter_by(id=dept.id).first())

        # 10. Safety check: try deleting a department that has employees (e.g. การិយាល័យបុគ្គលិក)
        dept_with_emp = Department.query.filter(Department.employees.any()).first()
        if dept_with_emp:
            res_safe_del = self.client.post(f'/organization/departments/{dept_with_emp.id}/delete', follow_redirects=True)
            self.assertEqual(res_safe_del.status_code, 200)
            self.assertIn('មិនអាចលុបការិយាល័យ'.encode('utf-8'), res_safe_del.data)
            self.assertIsNotNone(Department.query.filter_by(id=dept_with_emp.id).first())


if __name__ == '__main__':
    unittest.main()

