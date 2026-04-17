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
    allocations = session.get('last_allocation', [])
    # Flatten or select a specific room
    room_id = request.args.get('room', type=int)
    if room_id:
        room_data = next((a for a in allocations if a['room_id'] == room_id), None)
        students = room_data['students'] if room_data else []
    else:
        students = allocations[0]['students'] if allocations else []
        
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    return render_template('seating.html', students=students, today=today, allocations=allocations)

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
        
        # Header
        elements.append(Paragraph("XYZ INSTITUTE OF TECHNOLOGY & SCIENCE", title_style))
        elements.append(Paragraph("OFFICIAL SEMESTER EXAMINATION SEATING PLAN", subtitle_style))
        
        allocations = session.get('last_allocation', [])
        
        for room in allocations[:5]: # Export first 5 rooms for demo
            elements.append(Paragraph(f"ROOM ALLOCATION: {room['room_id']}", styles['Heading2']))
            elements.append(Paragraph(f"Supervisor: {room['faculty']} | Total Students: {room['count']}", styles['Normal']))
            elements.append(Spacer(1, 12))
            
            # Create Table for students
            data = [["Roll Number", "Branch", "Sign"]]
            for s in room['students'][:20]: # Show first 20 for table layout
                data.append([s['roll_no'], s['branch'], "__________"])
            
            t = Table(data, colWidths=[150, 100, 100])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.indigo),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))
            elements.append(t)
            elements.append(Spacer(1, 24))
            elements.append(Paragraph("Supervisor Signature: ____________________", styles['Normal']))
            elements.append(Spacer(1, 40))
        
        doc.build(elements)
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name="Official_Seating_Plan.pdf")
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
