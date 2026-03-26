from flask import Flask, render_template, redirect, url_for, session, request
from flask_cors import CORS
from routes.api import api_bp, generate_timetable, save_schedule
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
        # Simple local auth for demo
        email = request.form.get('email')
        password = request.form.get('password')
        if email == 'admin@scholarprism.edu' and password == 'admin123':
            session['user'] = 'admin'
            return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect(url_for('login'))
    return render_template('dashboard.html')

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
