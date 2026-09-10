# ប្រព័ន្ធគ្រប់គ្រងធនធានមនុស្សកម្ពុជា (Cambodia HRMS)

ប្រព័ន្ធគ្រប់គ្រងធនធានមនុស្ស (HRMS) ពេញលេញដែលត្រូវបានរចនាឡើងយ៉ាងយកចិត្តទុកដាក់តាមស្តង់ដារការងារ និងរដ្ឋបាលនៅកម្ពុជា។

- **GitHub Repository**: [https://github.com/SayanndaraKH/HR](https://github.com/SayanndaraKH/HR)
- **បច្ចេកវិទ្យា**: Python 3.12, Flask, Flask-SQLAlchemy, SQLite/PostgreSQL, HTML5, Vanilla CSS, Chart.js

---

## 🌟 មុខងារចម្បងៗ (Key Features)

1. **ការគ្រប់គ្រងអ្នកប្រើប្រាស់ & សិទ្ធិ (User Management & RBAC)**:
   - គណនី Admin អចិន្ត្រៃយ៍៖ User: `ADMIN` / Password: `syd001`
   - ទម្រង់ចុះឈ្មោះ និងចូលប្រើប្រាស់ (Login / Register)
   - ប្រព័ន្ធអនុម័តគណនីមុនពេលអាចចូលប្រើប្រាស់ (Admin Approval Workflow)
   - សិទ្ធិតាមតួនាទី (Admin, HR, Accountant, Staff)
2. **រចនាសម្ព័ន្ធស្ថាប័ន & តួនាទី (Organization & Positions CRUD)**:
   - គ្រប់គ្រងការិយាល័យទាំង ៧ និងតួនាទីទាំង ៥ ផ្លូវការ
   - អាចបន្ថែម កែប្រែ និងលុបការិយាល័យ ឬតួនាទីថ្មីៗបានភ្លាមៗ
3. **គ្រប់គ្រងព័ត៌មានបុគ្គលិក (Employee Records)**:
   - ប្រវត្តិរូបសង្ខេបផ្លូវការ (Official Cambodia CV Template)
   - ភ្ជាប់ទិន្នន័យភូមិសាស្ត្ររដ្ឋបាលកម្ពុជា ២៥ ខេត្ត/រាជធានី, ២០៩ ក្រុង/ស្រុក/ខណ្ឌ, ១,៦៦១ ឃុំ/សង្កាត់
4. **វត្តមាន និងច្បាប់ឈប់សម្រាក (Daily Attendance & Leaves)**:
   - កត់ត្រាវត្តមានប្រចាំថ្ងៃ និងបង្កើត QR Code ស្កេនវត្តមាន
   - ស្នើសុំ និងអនុម័តច្បាប់ឈប់សម្រាក
5. **ប្រាក់បៀវត្ស និងពន្ធលើប្រាក់បៀវត្សកម្ពុជា (Cambodia Payroll & Tax)**:
   - គណនាប្រាក់បៀវត្សតាមច្បាប់ការងារកម្ពុជា
   - កាត់កង ប.ស.ស (NSSF) និងពន្ធលើប្រាក់បៀវត្សតាមកាំពន្ធផ្លូវការ (Salary Tax Bands)
   - បង្កើត និងបោះពុម្ពប័ណ្ណបើកប្រាក់បៀវត្ស (Official Payslip)

---

## 🚀 របៀប Push ទៅកាន់ GitHub និងធ្វើបច្ចុប្បន្នភាព (Push & Update)

### ជម្រើសទី ១៖ ចុចលើ File `push.bat` (ងាយស្រួលបំផុត សម្រាប់ Windows)
រាល់ពេលដែលលោកអ្នកបានកែប្រែ ឬបន្ថែម File ថ្មីៗ លោកអ្នកគ្រាន់តែ៖
1. **Double-click លើ File `push.bat`**
2. ផ្ទាំង Command នឹងបើកឡើង ហើយបង្ហាញបញ្ជី File ដែលបានកែប្រែ
3. វាយបញ្ចូល Commit Message (ឬចុច **ENTER** ដើម្បីប្រើសារស្វ័យប្រវត្តិ)
4. ប្រព័ន្ធនឹងធ្វើការ `git add .`, `git commit` និង `git push` ទៅកាន់ `https://github.com/SayanndaraKH/HR` ដោយស្វ័យប្រវត្តិ!

---

### ជម្រើសទី ២៖ ប្រើ Command Line (Git CLI)
```bash
# 1. ពិនិត្យមើលស្ថានភាព File
git status

# 2. បន្ថែម File ទាំងអស់
git add .

# 3. Commit ការផ្លាស់ប្តូរ
git commit -m "Update feature XYZ"

# 4. Push ទៅកាន់ GitHub
git push -u origin main
```

---

## 🌐 របៀប Deploy ដាក់ឱ្យដំណើរការលើ Cloud (Deployment Options)

### ជម្រើសទី ១៖ Deploy លើ Render.com (ឥតគិតថ្លៃ / Free Tier)
1. ចូលទៅកាន់ [Render.com](https://render.com) រួចចុះឈ្មោះ/ចូលដោយប្រើគណនី GitHub
2. ចុច **New +** -> ជ្រើសរើស **Web Service**
3. ភ្ជាប់ជាមួយ Repository `SayanndaraKH/HR`
4. Render នឹងស្គាល់ File `Procfile` និង `render.yaml` ដោយស្វ័យប្រវត្តិ៖
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 4`
5. ចុច **Deploy Web Service** ជាការស្រេច!

---

### ជម្រើសទី ២៖ Deploy ជាមួយ Docker & Docker Compose
```bash
# ចាប់ផ្តើមដំណើរការ Container
docker-compose up -d --build

# ពិនិត្យមើលស្ថានភាព
docker-compose ps

# បើកមើលតាម Browser: http://localhost:5000
```

---

### ជម្រើសទី ៣៖ Deploy លើ VPS ឬ Server ផ្ទាល់ខ្លួន (Windows / Linux)

#### សម្រាប់ Windows Server:
1. Clone Repository: `git clone https://github.com/SayanndaraKH/HR.git`
2. Double-click លើ `run.bat` ដើម្បីចាប់ផ្តើម Server
3. ដើម្បី Update នៅពេលមានកូដថ្មី៖ គ្រាន់តែ double-click លើ **`update.bat`** នោះប្រព័ន្ធនឹង Pull កូដថ្មី ដំឡើង Package និង Restart Server ដោយស្វ័យប្រវត្តិ!

#### សម្រាប់ Linux / Ubuntu VPS:
```bash
# 1. Clone repo
git clone https://github.com/SayanndaraKH/HR.git
cd HR

# 2. ដំឡើង virtualenv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. ដំណើរការ Server ជាមួយ Gunicorn
gunicorn app:app --bind 0.0.0.0:5000 --workers 4

# 4. នៅពេលចង់ Update កូដថ្មី
chmod +x update.sh
./update.sh
```

---

## 🛠️ រចនាសម្ព័ន្ធឯកសារ (Project File Structure)

```text
HR-M/
├── .github/workflows/ci.yml # Automated CI tests on push
├── instance/hrms.db         # SQLite database file
├── static/                  # CSS stylesheets, JS scripts
├── templates/               # HTML Jinja2 templates (Khmer UI)
│   ├── attendance/          # វត្តមាន & ច្បាប់ឈប់សម្រាក
│   ├── auth/                # Login & Register
│   ├── employees/           # បញ្ជីបុគ្គលិក & ប្រវត្តិរូប
│   ├── geo/                 # ភូមិសាស្ត្ររដ្ឋបាលកម្ពុជា
│   ├── organization/        # គ្រប់គ្រងរចនាសម្ព័ន្ធ & តួនាទី
│   ├── payroll/             # ប្រាក់បៀវត្ស & Payslip
│   └── users/               # គ្រប់គ្រងអ្នកប្រើប្រាស់
├── uploads/                 # រូបថតបុគ្គលិក និងឯកសារ
├── app.py                   # Main Flask Application
├── models.py                # Database Schema & Models
├── payroll_calculator.py    # NSSF & Cambodia Tax Calculator
├── seed_data.py             # Sample Data Seeder
├── test_app.py              # Unit Tests suite (15/15 tests)
├── requirements.txt         # Python Dependencies
├── Procfile                 # Cloud deployment command
├── render.yaml              # Render blueprint
├── Dockerfile               # Container build file
├── docker-compose.yml       # Docker Compose service
├── push.bat                 # 1-Click Push to GitHub (Windows)
├── push.sh                  # 1-Click Push to GitHub (Linux/Mac)
├── run.bat                  # 1-Click Run Server (Windows)
├── stop.bat                 # 1-Click Stop Server (Windows)
├── update.bat               # 1-Click Server Update (Windows)
└── update.sh                # 1-Click Server Update (Linux)
```

---

## 🔑 គណនីចូលប្រើប្រាស់លំនាំដើម (Default Credentials)

- **Username**: `ADMIN`
- **Password**: `syd001`
- **សិទ្ធិ**: Admin ពេញលេញលើប្រព័ន្ធទាំងមូល

---

## 🚀 របៀប Hosting ជាមួយ Railway (Railway Deployment)

1. ចុច `push.bat` ដើម្បីរុញកូដចុងក្រោយទៅកាន់ GitHub
2. ចូលទៅកាន់ [railway.app](https://railway.app/) ហើយ Login ជាមួយ GitHub
3. ចុច **New Project** -> **Deploy from GitHub repo** -> ជ្រើសរើស repository `HR`
4. នៅក្នុងផ្ទាំង **Settings** របស់ Service -> ផ្នែក **Networking** -> ចុច **Generate Domain**
5. ប្រព័ន្ធនឹងផ្តល់ជូន Public Domain (ឧទាហរណ៍៖ `https://hr-production-xxxx.up.railway.app`) សម្រាប់ចូលប្រើប្រាស់បានភ្លាមៗ!

