from datetime import datetime

HARD_PENALTY = 1_000_000

def to_minutes(time_str):
    # time_str e.g. "09:00:00" or "09:00"
    parts = time_str.split(':')
    h, m = int(parts[0]), int(parts[1])
    return h * 60 + m

def calculate_fitness(chromosome, faculty_preferences, subjects_map, rooms_map):
    """
    Returns (fitness_score, has_hard_violation)
    Hard constraints drop score by HARD_PENALTY; caller can filter those out.
    """
    fitness = 10000
    hard_violation = False

    faculty_sched = {}   # {fid: {date: [(start,end)]}}
    room_sched = {}      # {rid: {date: [(start,end)]}}
    division_sched = {}  # {division_id: [date]}

    for gene in chromosome:
        sub_id = gene['subject_id']
        fac_id = gene['faculty_id']
        room_id = gene['room_id']
        div_id = gene['division_id']
        exam_date = gene['exam_date']
        start_time = gene['start_time']
        end_time = gene['end_time']

        subject = subjects_map.get(sub_id, {})
        room = rooms_map.get(room_id, {})
        duration = subject.get('duration_minutes', 180)
        start_min = to_minutes(str(start_time))
        end_min = to_minutes(str(end_time)) if end_time else start_min + duration

        # Hard: lab in lab room
        if subject.get('type') == 'LAB' and room.get('type') != 'LAB':
            fitness -= HARD_PENALTY
            hard_violation = True

        # Hard: room capacity
        students = gene.get('students', 0)
        if room.get('capacity', 0) < students:
            fitness -= HARD_PENALTY
            hard_violation = True

        # Hard: one exam per division per day
        division_sched.setdefault(div_id, [])
        if exam_date in division_sched[div_id]:
            fitness -= HARD_PENALTY
            hard_violation = True
        division_sched[div_id].append(exam_date)

        # Hard: faculty overlap
        faculty_sched.setdefault(fac_id, {}).setdefault(exam_date, [])
        for (s, e) in faculty_sched[fac_id][exam_date]:
            if start_min < e and s < end_min:
                fitness -= HARD_PENALTY
                hard_violation = True
        faculty_sched[fac_id][exam_date].append((start_min, end_min))

        # Hard: room overlap
        room_sched.setdefault(room_id, {}).setdefault(exam_date, [])
        for (s, e) in room_sched[room_id][exam_date]:
            if start_min < e and s < end_min:
                fitness -= HARD_PENALTY
                hard_violation = True
        room_sched[room_id][exam_date].append((start_min, end_min))

        # Soft: faculty preferred date
        if fac_id in faculty_preferences and exam_date in faculty_preferences[fac_id]:
            fitness += 300

    # Soft: avoid consecutive exams for each division
    for div, dates in division_sched.items():
        sorted_dates = sorted(dates)
        for i in range(len(sorted_dates)-1):
            diff = (sorted_dates[i+1] - sorted_dates[i]).days
            if diff == 1:
                fitness -= 200

    # Soft: balanced distribution (penalize if span too tight)
    for div, dates in division_sched.items():
        if len(dates) > 2:
            span = (max(dates) - min(dates)).days + 1
            if span < len(dates) + 2:
                fitness -= 150

    return max(fitness, 0), hard_violation
