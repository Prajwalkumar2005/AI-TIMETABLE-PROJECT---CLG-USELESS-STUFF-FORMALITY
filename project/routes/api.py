from flask import Blueprint, jsonify, request
from database.db import db
from ga_engine.genetic import GeneticAlgorithm
from datetime import datetime, timedelta
import random

api_bp = Blueprint('api', __name__)

@api_bp.route('/generate', methods=['POST'])
def generate_timetable():
    # 1. Fetch data from DB
    faculty = db.fetch_all("SELECT * FROM faculty")
    rooms = db.fetch_all("SELECT * FROM rooms")
    subjects = db.fetch_all("SELECT * FROM subjects")
    classes = db.fetch_all("SELECT * FROM classes")
    
    # Map them for GA
    rooms_data = {r['id']: {'type': r['type'], 'capacity': r['capacity']} for r in rooms}
    
    # 2. Mock some relationships for this example
    # (In a real app, map subject to faculty and classes)
    subjects_data = {}
    for sub in subjects:
        # Just random assignment for mock purposes, in production logic would exist
        subjects_data[sub['id']] = {
            'type': sub['type'],
            'faculty_id': random.choice([f['id'] for f in faculty]),
            'division_id': random.choice([c['id'] for c in classes])
        }
        
    dates_available = [datetime.now().date() + timedelta(days=i) for i in range(1, 14)] # Next 2 weeks
    time_slots = ['09:00:00', '14:00:00']
    
    # 3. Create GA instance
    ga = GeneticAlgorithm(subjects_data, rooms_data, {}, dates_available, time_slots)
    
    # 4. Run GA
    top_3 = ga.run()
    
    # 5. Clear old options (option_no 1-3)
    db.execute_query("DELETE FROM schedule_options")
    
    # 6. Save new options to DB
    for option_idx, option in enumerate(top_3):
        for gene in option['schedule']:
            db.execute_query("""
                INSERT INTO schedule_options (option_no, subject_id, exam_date, start_time, end_time, room_id, fitness_score)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (option_idx+1, gene['subject_id'], gene['exam_date'], gene['start_time'], gene['end_time'], gene['room_id'], option['fitness']))
            
    return jsonify({
        "success": True, 
        "message": "Top 3 schedules generated and saved.", 
        "options": [o['fitness'] for o in top_3]
    })

@api_bp.route('/schedules', methods=['GET'])
def get_schedules():
    results = db.fetch_all("""
        SELECT 
            so.option_no,
            so.subject_id,
            s.name AS subject_name,
            so.exam_date,
            so.start_time,
            so.end_time,
            so.room_id,
            r.name AS room_name,
            so.fitness_score
        FROM schedule_options so
        JOIN subjects s ON so.subject_id = s.id
        JOIN rooms r ON so.room_id = r.id
        ORDER BY so.option_no, so.exam_date, so.start_time
    """)
    # Group by option_no
    grouped = {}
    for r in results:
        opt_no = r['option_no']
        if opt_no not in grouped: grouped[opt_no] = {'fitness': r['fitness_score'], 'schedule': []}
        grouped[opt_no]['schedule'].append({
            'subject_id': r['subject_id'],
            'subject_name': r.get('subject_name'),
            'date': r['exam_date'].strftime('%Y-%m-%d'),
            'start': str(r['start_time']),
            'end': str(r['end_time']),
            'room_id': r['room_id'],
            'room_name': r.get('room_name')
        })
    return jsonify({"success": True, "data": grouped})

@api_bp.route('/finalize', methods=['POST'])
def finalize_schedule():
    option_no = request.json.get('option_no')
    if not option_no: return jsonify({"success": False, "message": "Option number missing"}), 400
    
    # Copy from schedule_options to final_schedule
    options = db.fetch_all("SELECT * FROM schedule_options WHERE option_no = %s", (option_no,))
    db.execute_query("DELETE FROM final_schedule") # Clear existing final schedule
    for r in options:
        db.execute_query("""
            INSERT INTO final_schedule (subject_id, exam_date, start_time, end_time, room_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (r['subject_id'], r['exam_date'], r['start_time'], r['end_time'], r['room_id']))
        
    return jsonify({"success": True, "message": f"Schedule Option {option_no} finalized."})

@api_bp.route('/export/excel', methods=['GET'])
def export_excel():
    import pandas as pd
    from io import BytesIO
    from flask import send_file
    
    # Fetch final schedule
    final = db.fetch_all("""
        SELECT s.name AS Subject, fs.exam_date AS Date, fs.start_time AS Start, fs.end_time AS End, r.name AS Room 
        FROM final_schedule fs
        JOIN subjects s ON fs.subject_id = s.id
        JOIN rooms r ON fs.room_id = r.id
    """)
    if not final: return jsonify({"success": False, "message": "No finalized schedule found."}), 404
    
    df = pd.DataFrame(final)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Exam Timetable')
        
    output.seek(0)
    return send_file(output, as_attachment=True, download_name='Exam_Timetable.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
