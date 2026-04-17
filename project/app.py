from flask import Flask, render_template, redirect, url_for, session, request
from flask_cors import CORS
from project.routes.api import api_bp, generate_timetable, save_schedule
import os

app = Flask(__name__)
app.secret_key = 'ScholarPrism_2024' # Change this for production
CORS(app)

# Register Blueprints
app.register_blueprint(api_bp, url_prefix='/api')

# Template Routes
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Simple local auth for demo with Role-Based routing (Phase 2)
        email = request.form.get('email')
        password = request.form.get('password')
        
        if email == 'admin@scholarprism.edu' and password == 'admin123':
            session['user'] = 'admin'
            session['role'] = 'Administrator'
            return redirect(url_for('dashboard'))
        elif email == 'teacher@scholarprism.edu' and password == 'teacher123':
            session['user'] = 'teacher'
            session['role'] = 'Teacher'
            return redirect(url_for('teacher_dashboard'))
        elif email == 'student@scholarprism.edu' and password == 'student123':
            session['user'] = 'student'
            session['role'] = 'Student'
            return redirect(url_for('student_dashboard'))
        else:
            return render_template('login.html', error="Invalid credentials")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect(url_for('login'))
    data = {
        "total_classes": 1284,
        "faculty_count": 342,
        "occupancy": 88,
        "conflicts": 12,
        "role": session.get('role', 'Administrator')
    }
    return render_template('dashboard.html', **data)

@app.route("/scheduler")
def scheduler():
    timetable = [
        {"time": "09:00", "subject": "Algorithms", "conflict": False},
        {"time": "10:00", "subject": "Data Structures", "conflict": True},
        {"time": "11:00", "subject": None, "conflict": False},
    ]
    return render_template("scheduler.html", timetable=timetable)

# --- ALLOCATION ENGINE LOGIC ---

def get_mock_students():
    students = []
    for i in range(1, 31):
        branch = "CSE" if i % 2 == 0 else "ME"
        students.append({"roll_no": f"2024{branch}{i:03d}", "branch": branch})
    return students

def interleave_students(students):
    # Split by branch
    cse = [s for s in students if s['branch'] == 'CSE']
    me = [s for s in students if s['branch'] == 'ME']
    
    interleaved = []
    for i in range(max(len(cse), len(me))):
        if i < len(cse): interleaved.append(cse[i])
        if i < len(me): interleaved.append(me[i])
    return interleaved

@app.route('/generate-allocation', methods=['POST'])
def generate_allocation():
    students = get_mock_students()
    # Apply seating mix (Interleaving)
    mixed_students = interleave_students(students)
    # Store in session for the demo view
    session['current_seating'] = mixed_students
    return {"status": "success", "message": "Allocation optimized"}

@app.route('/seating')
def seating():
    if 'user' not in session: return redirect(url_for('login'))
    students = session.get('current_seating', get_mock_students())
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    return render_template('seating.html', students=students, today=today)

@app.route('/export_pdf')
def export_pdf_route():
    try:
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        import io
        from flask import send_file

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer)
        styles = getSampleStyleSheet()
        elements = [Paragraph("Scholar Prism | Seating Plan", styles['Title']), Spacer(1, 12)]
        
        students = session.get('current_seating', get_mock_students())
        for s in students:
            elements.append(Paragraph(f"Roll No: {s['roll_no']} | Branch: {s['branch']}", styles['Normal']))
        
        doc.build(elements)
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name="seating_plan.pdf")
    except ImportError:
        return {"error": "reportlab not installed"}, 500

def detect_conflicts(assignments):
    conflicts = []
    faculty_map = {}
    for a in assignments:
        key = (a['faculty_id'], a['time'])
        if key in faculty_map:
            conflicts.append(a)
        else:
            faculty_map[key] = True
    return conflicts

# --- EXISTING ROUTES ---

@app.route('/teacher_dashboard')
def teacher_dashboard():
    if 'user' not in session or session.get('role') != 'Teacher': return redirect(url_for('login'))
    return render_template('dashboard.html', role='Teacher')

@app.route('/student_dashboard')
def student_dashboard():
    if 'user' not in session or session.get('role') != 'Student': return redirect(url_for('login'))
    return render_template('dashboard.html', role='Student')

@app.route('/generate')
def generate():
    if 'user' not in session: return redirect(url_for('login'))
    return render_template('generate.html')

@app.route('/schedules')
def schedules():
    if 'user' not in session: return redirect(url_for('login'))
    return render_template('editor.html')

@app.route('/admin')
def admin():
    if 'user' not in session: return redirect(url_for('login'))
    return render_template('admin.html')

@app.route('/export')
def export():
    if 'user' not in session: return redirect(url_for('login'))
    return render_template('export.html')

@app.route('/settings')
def settings():
    if 'user' not in session: return redirect(url_for('login'))
    return render_template('settings.html')

# Alias route requested: POST /generate_api
@app.route('/generate_api', methods=['POST'])
def generate_api():
    # Reuse the blueprint handler so logic stays in one place
    return generate_timetable()

# Alias for save schedule at root level if frontend calls /save_schedule
@app.route('/save_schedule', methods=['POST'])
def save_schedule_root():
    return save_schedule()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
