import random
from datetime import datetime, timedelta

def mutate(chromosome, rooms_data, dates_available, time_slots):
    # Mutate a random gene (0.3 chance based on prompt)
    gene_idx = random.randint(0, len(chromosome)-1)
    gene = chromosome[gene_idx]
    
    # 1. Randomly change either room, date or start_time
    mutation_type = random.choice(['room', 'date', 'time'])
    
    if mutation_type == 'room':
        gene['room_id'] = random.choice(list(rooms_data.keys()))
    elif mutation_type == 'date':
        gene['exam_date'] = random.choice(dates_available)
    elif mutation_type == 'time':
        slot = random.choice(time_slots) # e.g. slot = '09:00:00'
        gene['start_time'] = slot
        # Assuming fixed duration (e.g. 3 hours)
        h, m, s = map(int, slot.split(':'))
        end = datetime.strptime(slot, '%H:%M:%S') + timedelta(hours=3)
        gene['end_time'] = end.strftime('%H:%M:%S')
    
    chromosome[gene_idx] = gene
    return chromosome
