# Scholar Prism – AI Exam Timetable Generator

Lightweight Flask app that uses a genetic algorithm to generate and curate exam timetables (rooms, faculty, clashes) with an Excel export. Frontend is Tailwind-based.

## New: Decision Support System (DSS) Features
The system now includes a production-grade **Exam Classroom & Faculty Allotment System**:
- **Automated Seating Allocation**: Intelligent distribution of students across classrooms.
- **Anti-Cheating Logic**: Round-robin interleaving of students from different branches.
- **Visual Seating Grid**: Interactive grid view for invigilators.
- **Professional PDF Reporting**: Branded export with college headers and formatted tables.
- **File-Based Caching**: Optimized for large datasets (e.g., 240+ students).

## Stack
- Python 3.10+ (Flask, mysql-connector-python, pandas, openpyxl)
- MySQL for persistence (`schema.sql` seeds sample data)
- Tailwind CDN templates in `project/templates`

## Quickstart
```bash
# 1) Create env
py -m venv .venv
.venv\Scripts\activate

# 2) Install deps
pip install -r project/requirements.txt

# 3) Prep database (edit creds in project/database/db.py if needed)
mysql -u root -p < project/database/schema.sql

# 4) Run
python project/app.py
# Visit http://localhost:5000  (login: admin@scholarprism.edu / admin123)
```

## Useful Endpoints
- `POST /api/generate` – runs GA, stores top 3 schedules.
- `GET /api/schedules` – returns generated options.
- `POST /api/finalize` – promote an option into `final_schedule`.
- `GET /api/export/excel` – download finalized timetable as XLSX.

## Repo Layout
- `project/app.py` – Flask app + routes
- `project/routes/api.py` – API endpoints
- `project/ga_engine/` – genetic algorithm pieces
- `project/database/` – MySQL helper + schema/seed
- `project/templates/` – Tailwind UI screens

## Deployment Notes
- Set `FLASK_ENV=production` and change `app.secret_key`.
- Put DB credentials in env vars or `.env` (not in source).
- Add TLS + WAF if exposed publicly.
