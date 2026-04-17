from flask import Flask, render_template, redirect, url_for, session, request
from flask_cors import CORS
from project.routes.api import api_bp, generate_timetable, save_schedule
import os
import json
import uuid

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

from project.engine.allocation_engine import AllocationEngine, get_engine_data

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect(url_for('login'))
    
    # Analytics data
    data = {
        "total_classes": 1440,
        "faculty_count": 48,
        "occupancy": 92,
        "conflicts": 0,
        "utilization": 85,
        "avg_students_per_room": 35,
        "role": session.get('role', 'Administrator')
    }
    return render_template('dashboard.html', **data)

@app.route('/generate-allocation', methods=['POST'])
def generate_allocation():
    branches, rooms, faculty = get_engine_data()
    engine = AllocationEngine(branches, rooms, faculty)
    allocations, load = engine.generate_allocation()
    
    # Store result in session for UI renders
    session['last_allocation'] = allocations
    session['faculty_load'] = load
    
    return {"status": "success", "message": "Optimization Complete"}

@app.route('/seating')
def seating():
    if 'user' not in session: return redirect(url_for('login'))
    
    # Check for file-based result first
    filename = session.get('last_result_file')
    allocations = []
    if filename:
        filepath = os.path.join(os.getcwd(), 'scratch', filename)
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                data = json.load(f)
                allocations = data.get('allocations', [])
    
    if not allocations:
        allocations = session.get('last_allocation', [])
        
    students = []
    for room in allocations:
        students.extend(room['students'])
    
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    return render_template('seating.html', students=students, today=today, allocations=allocations)

@app.route('/generate-plan', methods=['POST'])
def generate_plan():
    data = request.json
    selected_branches = data.get('branches', [])
    subjects_map = data.get('subjects', {})
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')
    
    if not selected_branches or not subjects_map:
        return {"status": "error", "message": "Missing input data"}, 400

    from datetime import datetime, timedelta
    start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
    
    # Simple Timetable Generation: Each branch has 1 exam per day sequentially
    timetable = []
    max_days = 6 # Expecting 6 subjects per branch
    
    for day_idx in range(max_days):
        current_date = (start_dt + timedelta(days=day_idx)).strftime("%Y-%m-%d")
        for branch in selected_branches:
            branch_subjects = subjects_map.get(branch, [])
            if day_idx < len(branch_subjects):
                timetable.append({
                    "date": current_date,
                    "branch": branch,
                    "subject": branch_subjects[day_idx]
                })

    # Run Allocation Engine (Integration)
    from project.engine.allocation_engine import AllocationEngine, get_engine_data
    _branches_list, rooms, faculty = get_engine_data()
    # We use the selected branches from the request
    engine = AllocationEngine(selected_branches, rooms, faculty)
    allocations, _load = engine.generate_allocation()
    
    # Combine results
    result = {
        "status": "success",
        "timetable": timetable,
        "allocations": allocations
    }
    
    # Store in file to avoid session cookie limit
    filename = f"result_{uuid.uuid4().hex}.json"
    filepath = os.path.join(os.getcwd(), 'scratch', filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(result, f)
    
    session['last_result_file'] = filename
    
    return {"status": "success"}

@app.route('/result')
def result():
    if 'user' not in session: return redirect(url_for('login'))
    
    filename = session.get('last_result_file')
    if not filename:
        return redirect(url_for('dashboard'))
        
    filepath = os.path.join(os.getcwd(), 'scratch', filename)
    if not os.path.exists(filepath):
        return redirect(url_for('generate'))
        
    with open(filepath, 'r') as f:
        data = json.load(f)
        
    return render_template('result.html', **data)

@app.route('/export_pdf')
def export_pdf_route():
    try:
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        import io
        from flask import send_file

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        
        # Custom Styles
        title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], alignment=1, fontSize=18, spaceAfter=20)
        subtitle_style = ParagraphStyle('SubtitleStyle', parent=styles['Normal'], alignment=1, fontSize=12, spaceAfter=30, textColor=colors.grey)
        
        elements = []
        
        # Header - College Branding
        elements.append(Paragraph("<b>XYZ COLLEGE OF ENGINEERING & TECHNOLOGY</b>", title_style))
        elements.append(Paragraph("DEPARTMENT OF EXAMINATIONS - SEMESTER PLAN 2026", subtitle_style))
        elements.append(Paragraph(f"Generated Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
        elements.append(Spacer(1, 24))

        # Timetable Section
        elements.append(Paragraph("<b>I. EXAMINATION TIMETABLE</b>", styles['Heading2']))
        elements.append(Spacer(1, 12))
        
        last_result = session.get('last_result', {})
        # If last_result was large, it's stored in a file.
        filename = session.get('last_result_file')
        if filename:
            filepath = os.path.join(os.getcwd(), 'scratch', filename)
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    last_result = data

        timetable = last_result.get('timetable', [])
        if timetable:
            t_data = [["Date", "Branch", "Subject"]]
            for entry in timetable:
                t_data.append([entry['date'], entry['branch'], entry['subject']])
            
            t = Table(t_data, colWidths=[120, 100, 200])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))
            elements.append(t)
            elements.append(Spacer(1, 30))

        # Room Allocation Section
        elements.append(Paragraph("<b>II. CLASSROM ROOM ALLOCATIONS</b>", styles['Heading2']))
        elements.append(Spacer(1, 12))
        
        allocations = last_result.get('allocations', [])
        if not allocations:
            allocations = session.get('last_allocation', [])

        for room in allocations[:8]: # Show first 8 rooms for brevity in demo PDF
            elements.append(Paragraph(f"ROOM {room['room_id']} | Faculty: {room['faculty']} | Total: {room['count']}", styles['Normal']))
            elements.append(Spacer(1, 6))
            
            # Create Table for students (Small list for demo)
            s_data = [["Roll No", "Branch", "Roll No", "Branch"]]
            room_students = room['students']
            for i in range(0, min(10, len(room_students)), 2): # Show first 10 students in 2 columns
                s1 = room_students[i]
                s2 = room_students[i+1] if i+1 < len(room_students) else {'roll_no': '-', 'branch': '-'}
                s_data.append([s1['roll_no'], s1['branch'], s2['roll_no'], s2['branch']])
            
            st = Table(s_data, colWidths=[100, 80, 100, 80])
            st.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.2, colors.grey)
            ]))
            elements.append(st)
            elements.append(Spacer(1, 15))

        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Controller of Examinations ____________________", styles['Normal']))

        doc.build(elements)
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name="ScholarPrism_ExamPlan.pdf")
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
