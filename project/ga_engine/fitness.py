from datetime import datetime, timedelta

def calculate_fitness(chromosome, faculty_preferences, subjects_data, rooms_data, classes_data):
    # Initial base score
    fitness = 10000 
    
    # Track assignments to detect overlaps
    faculty_schedules = {} # {faculty_id: [(date, start, end)]}
    room_schedules = {}    # {room_id: [(date, start, end)]}
    division_schedules = {} # {division_id: [date]}
    
    # 1. Process each gene (each subject exam)
    for gene in chromosome:
        sub_id = gene['subject_id']
        fac_id = gene['faculty_id']
        room_id = gene['room_id']
        div_id = gene['division_id']
        exam_date = gene['exam_date']
        start_time = gene['start_time']
        end_time = gene['end_time']
        
        # Room Type check (Lab vs Theory)
        subject_type = subjects_data.get(sub_id, {}).get('type', 'THEORY')
        room_type = rooms_data.get(room_id, {}).get('type', 'CLASSROOM')
        if subject_type == 'LAB' and room_type != 'LAB':
            fitness -= 1000 # Hard Penalty
        
        # Faculty Overlap
        if fac_id not in faculty_schedules: faculty_schedules[fac_id] = []
        for (d, s, e) in faculty_schedules[fac_id]:
            if d == exam_date and (start_time < e and s < end_time):
                fitness -= 2000 # Hard Penalty
        faculty_schedules[fac_id].append((exam_date, start_time, end_time))
        
        # Room Clash
        if room_id not in room_schedules: room_schedules[room_id] = []
        for (d, s, e) in room_schedules[room_id]:
            if d == exam_date and (start_time < e and s < end_time):
                fitness -= 2000 # Hard Penalty
        room_schedules[room_id].append((exam_date, start_time, end_time))
        
        # One exam per division per day
        if div_id not in division_schedules: division_schedules[div_id] = []
        if exam_date in division_schedules[div_id]:
            fitness -= 1500 # Hard Penalty
        division_schedules[div_id].append(exam_date)
        
        # Soft Constraints: Faculty Preferred Dates
        if fac_id in faculty_preferences and exam_date in faculty_preferences[fac_id]:
            fitness += 500 # Soft Reward
            
    # Soft: Avoid consecutive exams (this is more complex, but can be done roughly)
    for div, dates in division_schedules.items():
        sorted_dates = sorted(dates)
        for i in range(len(sorted_dates)-1):
            if (sorted_dates[i+1] - sorted_dates[i]).days < 2:
                fitness -= 100 # Soft Penalty
                
    return max(0, fitness)
