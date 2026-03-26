from flask import Blueprint, jsonify, request
from database.db import db
from ga_engine.genetic import GeneticAlgorithm
from datetime import datetime, timedelta
import random
import re

api_bp = Blueprint('api', __name__)

TIME_SLOTS = ['09:00:00', '13:30:00', '16:30:00']

def parse_date_range(date_range_str):
    """
    Accepts formats like 'Oct 12 - Oct 28, 2024' or '2024-10-12 - 2024-10-28'
    Returns list of dates inclusive. Fallback: next 14 days.
    """
    if not date_range_str:
        today = datetime.now().date()
        return [today + timedelta(days=i) for i in range(1, 15)]

    cleaned = date_range_str.replace('to', '-').replace('–', '-')
    parts = cleaned.split('-')
    if len(parts) < 2:
        today = datetime.now().date()
        return [today + timedelta(days=i) for i in range(1, 15)]

    left = parts[0].strip()
    right = '-'.join(parts[1:]).strip()

    # Try multiple patterns
    def try_parse(s, fallback_year=None):
        fmts = ['%b %d, %Y', '%b %d %Y', '%Y-%m-%d', '%d %b %Y', '%b %d']
        for fmt in fmts:
            try:
                dt = datetime.strptime(s, fmt)
                if '%Y' not in fmt and fallback_year:
                    dt = dt.replace(year=fallback_year)
                return dt.date()
            except Exception:
                continue
        return None

    # Attempt to get year from right part
    year_match = re.search(r'(20\\d{2})', right)
    fallback_year = int(year_match.group(1)) if year_match else datetime.now().year

    start_date = try_parse(left, fallback_year=fallback_year)
    end_date = try_parse(right, fallback_year=fallback_year)

    if not start_date or not end_date or start_date > end_date:
        today = datetime.now().date()
        return [today + timedelta(days=i) for i in range(1, 15)]

    days = []
    cur = start_date
    while cur <= end_date:
        days.append(cur)
        cur += timedelta(days=1)
    return days


def build_subject_map(subjects, faculty_map, class_map, student_counts, auto_fix=False, faculty_lookup=None, classes=None, default_dept=None):
    """
    Returns {subject_id: {...}} using explicit mappings, with optional auto-fix.
    faculty_map: {subject_id: faculty_id}
    class_map: {subject_id: class_id}
    student_counts: {class_id: student_count}
    auto_fix: if True, create fallback mappings
    """
    subjects_map = {}
    missing_links = []
    fixes = []

    # helper to pick faculty from same department
    def pick_faculty_from_dept(dept):
        if not faculty_lookup: return None
        if dept and dept in faculty_lookup and faculty_lookup[dept]:
            return random.choice(faculty_lookup[dept])
        # fallback: any available faculty
        flat = [f for arr in faculty_lookup.values() for f in arr]
        return random.choice(flat) if flat else None

    # helper to pick class from same dept
    def pick_class(dept):
        if not classes: return None
        if dept:
            same = [c for c in classes if c['department'] == dept]
            if same: return random.choice(same)
        return classes[0] if classes else None

    # average students for fallback
    avg_students = 0
    if student_counts:
        avg_students = sum(student_counts.values()) // len(student_counts)

    for sub in subjects:
        sid = sub['id']
        fac_id = faculty_map.get(sid)
        cid = class_map.get(sid)
        if (fac_id is None or cid is None) and not auto_fix:
            missing_links.append(sid)
            continue
        if auto_fix:
            # Faculty fallback
            if fac_id is None:
                fac_id = pick_faculty_from_dept(default_dept)
                if fac_id: fixes.append(f"Subject {sid}: assigned fallback faculty {fac_id}")
            # Class fallback
            if cid is None:
                chosen_class = pick_class(default_dept)
                if chosen_class:
                    cid = chosen_class['id']
                    fixes.append(f"Subject {sid}: linked to class {cid}")
        if fac_id is None or cid is None:
            missing_links.append(sid)
            continue
        student_count = student_counts.get(cid, avg_students)
        if student_count == 0 and avg_students > 0:
            student_count = avg_students
        subjects_map[sid] = {
            'type': sub['type'],
            'duration_minutes': sub.get('duration_minutes', 180) or 180,
            'faculty_id': fac_id,
            'division_id': cid,
            'students': student_count
        }
    return subjects_map, missing_links, fixes


def generate_multiple_schedules(payload):
    """
    Run GA and persist top 3 options to schedule_options.
    Returns the in-memory options for immediate UI display.
    """
    # 1. Fetch data from DB
    faculty = db.fetch_all("SELECT * FROM faculty")
    rooms = db.fetch_all("SELECT * FROM rooms")
    subjects = db.fetch_all("SELECT * FROM subjects")
    classes = db.fetch_all("SELECT * FROM classes")
    prefs_rows = db.fetch_all("SELECT faculty_id, preferred_date FROM faculty_preferences")
    subj_faculty_rows = db.fetch_all("SELECT subject_id, faculty_id FROM subject_faculty")
    subj_class_rows = db.fetch_all("SELECT subject_id, class_id FROM subject_class")
    class_students_rows = db.fetch_all("SELECT class_id, student_count FROM class_students")

    if not (faculty and rooms and subjects and classes):
        return {"success": False, "message": "Missing seed data in DB"}, []
    if not (subj_faculty_rows and subj_class_rows and class_students_rows):
        return {"success": False, "message": "Missing mapping data (subject_faculty / subject_class / class_students)."}, []

    rooms_data = {r['id']: {'type': r['type'], 'capacity': r['capacity']} for r in rooms}
    faculty_prefs = {}
    for row in prefs_rows:
        faculty_prefs.setdefault(row['faculty_id'], set()).add(row['preferred_date'])

    dates_available = parse_date_range(payload.get('dateRange'))

    faculty_map = {row['subject_id']: row['faculty_id'] for row in subj_faculty_rows}
    class_map = {row['subject_id']: row['class_id'] for row in subj_class_rows}
    student_counts = {row['class_id']: row['student_count'] for row in class_students_rows}
    faculty_lookup = {}
    for f in faculty:
        faculty_lookup.setdefault(f['department'], []).append(f['id'])

    subjects_data, missing_links, fixes = build_subject_map(
        subjects,
        faculty_map,
        class_map,
        student_counts,
        auto_fix=payload.get('auto_fix', False),
        faculty_lookup=faculty_lookup,
        classes=classes,
        default_dept=payload.get('department')
    )
    auto_fix_used = payload.get('auto_fix', False)

    if missing_links and not auto_fix_used:
        return {"success": False, "message": f"Missing mappings for subjects: {missing_links}"}, []
    if missing_links and auto_fix_used:
        # could not fix everything
        return {"success": False, "message": f"Auto-fix failed; remaining unmapped subjects: {missing_links}"}, []

    ga = GeneticAlgorithm(subjects_data, rooms_data, faculty_prefs, dates_available, TIME_SLOTS)

    top_3 = ga.run()

    # Clear old options (option_no 1-3)
    db.execute_query("DELETE FROM schedule_options")

    # Save new options to DB and collect serializable response
    options_payload = []
    for option_idx, option in enumerate(top_3):
        serial_schedule = []
        for gene in option['schedule']:
            serial_schedule.append({
                'subject_id': gene['subject_id'],
                'faculty_id': gene['faculty_id'],
                'division_id': gene['division_id'],
                'exam_date': gene['exam_date'].isoformat() if hasattr(gene['exam_date'], 'isoformat') else str(gene['exam_date']),
                'start_time': str(gene['start_time']),
                'end_time': str(gene['end_time']),
                'room_id': gene['room_id']
            })
            db.execute_query("""
                INSERT INTO schedule_options (option_no, subject_id, exam_date, start_time, end_time, room_id, fitness_score)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (option_idx+1, gene['subject_id'], gene['exam_date'], gene['start_time'], gene['end_time'], gene['room_id'], option['fitness']))
        options_payload.append({
            "option_no": option_idx+1,
            "fitness": option['fitness'],
            "schedule": serial_schedule
        })

    warning = None
    if auto_fix_used:
        warning = "Auto-fix used (may not be optimal). Applied fixes: " + "; ".join(fixes) if fixes else "Auto-fix used (may not be optimal)."

    return {"success": True, "message": "Top 3 schedules generated and saved.", "warning": warning}, options_payload


@api_bp.route('/generate', methods=['POST'])
def generate_timetable():
    payload = request.json or {}
    meta, options = generate_multiple_schedules(payload)
    status_code = 200 if meta.get("success") else 400
    return jsonify({
        "success": meta.get("success", False), 
        "message": meta.get("message", ""),
        "options": options
    }), status_code

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

@api_bp.route('/save_schedule', methods=['POST'])
def save_schedule():
    option_no = request.json.get('option_no')
    if not option_no:
        return jsonify({"success": False, "message": "Option number missing"}), 400
    
    # Save into final_schedule and also into schedules table for history
    options = db.fetch_all("SELECT * FROM schedule_options WHERE option_no = %s", (option_no,))
    if not options:
        return jsonify({"success": False, "message": "Option not found"}), 404
    
    db.execute_query("DELETE FROM final_schedule")
    db.execute_query("DELETE FROM schedules")
    for r in options:
        db.execute_query("""
            INSERT INTO final_schedule (subject_id, exam_date, start_time, end_time, room_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (r['subject_id'], r['exam_date'], r['start_time'], r['end_time'], r['room_id']))
        db.execute_query("""
            INSERT INTO schedules (subject_id, exam_date, start_time, end_time, room_id, option_no)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (r['subject_id'], r['exam_date'], r['start_time'], r['end_time'], r['room_id'], option_no))
        
    return jsonify({"success": True, "status": "saved", "message": f"Schedule Option {option_no} saved."})

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
