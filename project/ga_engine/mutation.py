import random
from datetime import datetime, timedelta

def mutate(chromosome, meta):
    """
    Smarter mutation: change date/time/room while staying within allowed sets and duration.
    meta = {rooms_map, dates_available, time_slots, subjects_map}
    """
    rooms_map = meta['rooms_map']
    dates = meta['dates']
    slots = meta['slots']
    subjects = meta['subjects']

    gene_idx = random.randint(0, len(chromosome)-1)
    gene = chromosome[gene_idx]

    mutation_type = random.choice(['room', 'date', 'time'])

    if mutation_type == 'room':
        # prefer rooms that fit capacity & type
        subj = subjects.get(gene['subject_id'], {})
        needed_capacity = gene.get('students', 0)
        subj_type = subj.get('type')
        viable = [rid for rid, r in rooms_map.items()
                  if r.get('capacity', 0) >= needed_capacity and (subj_type != 'LAB' or r.get('type') == 'LAB')]
        gene['room_id'] = random.choice(viable) if viable else random.choice(list(rooms_map.keys()))

    elif mutation_type == 'date':
        gene['exam_date'] = random.choice(dates)

    elif mutation_type == 'time':
        slot = random.choice(slots)
        gene['start_time'] = slot
        duration = subjects.get(gene['subject_id'], {}).get('duration_minutes', 180)
        h, m, s = map(int, slot.split(':'))
        end = datetime.strptime(slot, '%H:%M:%S') + timedelta(minutes=duration)
        gene['end_time'] = end.strftime('%H:%M:%S')

    chromosome[gene_idx] = gene
    return chromosome
