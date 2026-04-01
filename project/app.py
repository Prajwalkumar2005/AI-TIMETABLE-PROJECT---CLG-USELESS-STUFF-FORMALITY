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
    return render_template('dashboard.html', role=session.get('role', 'Administrator'))

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
