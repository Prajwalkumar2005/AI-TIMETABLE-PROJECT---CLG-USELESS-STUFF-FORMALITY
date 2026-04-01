import random
import copy
from datetime import datetime, timedelta
from project.ga_engine.fitness import calculate_fitness
from project.ga_engine.mutation import mutate

class GeneticAlgorithm:
    def __init__(self, subjects, rooms, faculty_prefs, dates_available, time_slots):
        """
        subjects: {id: {type, duration_minutes, faculty_id, division_id, students}}
        rooms: {id: {type, capacity}}
        faculty_prefs: {fid: set(date)}
        dates_available: [date]
        time_slots: list of start time strings
        """
        self.subjects = subjects
        self.rooms = rooms
        self.faculty_prefs = faculty_prefs
        self.dates_available = dates_available
        self.time_slots = time_slots

        self.pop_size = 200
        self.generations = 500
        self.mutation_rate = 0.4
        self.crossover_rate = 0.8
        self.tournament_size = 5
        self.elite_count = 5

    def _build_gene(self, sub_id, data):
        start = random.choice(self.time_slots)
        duration = data.get('duration_minutes', 180)
        end_dt = (datetime.strptime(start, '%H:%M:%S') + timedelta(minutes=duration)).strftime('%H:%M:%S')

        # prefer rooms that fit constraints
        needed_capacity = data.get('students', 0)
        subj_type = data.get('type')
        viable_rooms = [rid for rid, r in self.rooms.items()
                        if r.get('capacity', 0) >= needed_capacity and (subj_type != 'LAB' or r.get('type') == 'LAB')]
        room_choice = random.choice(viable_rooms) if viable_rooms else random.choice(list(self.rooms.keys()))

        return {
            'subject_id': sub_id,
            'faculty_id': data['faculty_id'],
            'division_id': data['division_id'],
            'room_id': room_choice,
            'exam_date': random.choice(self.dates_available),
            'start_time': start,
            'end_time': end_dt,
            'students': needed_capacity
        }

    def initialize_population(self):
        population = []
        for _ in range(self.pop_size):
            chromosome = []
            for sub_id, data in self.subjects.items():
                chromosome.append(self._build_gene(sub_id, data))
            population.append(chromosome)
        return population

    def selection(self, population, fitness_scores):
        selected = []
        for _ in range(self.pop_size):
            tournament = random.sample(list(zip(population, fitness_scores)), self.tournament_size)
            winner = max(tournament, key=lambda x: x[1][0])[0]  # use fitness score
            selected.append(copy.deepcopy(winner))
        return selected

    def crossover(self, parent1, parent2):
        if len(parent1) != len(parent2) or len(parent1) == 0:
            return parent1, parent2
        if random.random() < self.crossover_rate:
            point = random.randint(1, len(parent1)-1)
            child1 = parent1[:point] + parent2[point:]
            child2 = parent2[:point] + parent1[point:]
            return child1, child2
        return parent1, parent2

    def run(self):
        population = self.initialize_population()
        meta = {
            'rooms_map': self.rooms,
            'dates': self.dates_available,
            'slots': self.time_slots,
            'subjects': self.subjects
        }

        for _ in range(self.generations):
            fitness_scores = [calculate_fitness(chrom, self.faculty_prefs, self.subjects, self.rooms) for chrom in population]

            # Elitism
            scored = list(zip(population, fitness_scores))
            elites = [copy.deepcopy(chrom) for chrom, score in sorted(scored, key=lambda x: x[1][0], reverse=True)[:self.elite_count]]

            mating_pool = self.selection(population, fitness_scores)

            next_generation = elites.copy()
            while len(next_generation) < self.pop_size:
                p1, p2 = random.choice(mating_pool), random.choice(mating_pool)
                c1, c2 = self.crossover(copy.deepcopy(p1), copy.deepcopy(p2))
                if random.random() < self.mutation_rate:
                    mutate(c1, meta)
                if random.random() < self.mutation_rate and len(next_generation)+1 < self.pop_size:
                    mutate(c2, meta)
                next_generation.append(c1)
                if len(next_generation) < self.pop_size:
                    next_generation.append(c2)

            population = next_generation

        final_fitness = [calculate_fitness(chrom, self.faculty_prefs, self.subjects, self.rooms) for chrom in population]
        scored_final = list(zip(population, final_fitness))

        # Keep conflict-free first, then best available
        conflict_free = [item for item in scored_final if item[1][1] is False]
        ranked = sorted(conflict_free or scored_final, key=lambda x: x[1][0], reverse=True)[:3]

        top_3 = []
        for chrom, (fit, _) in ranked:
            top_3.append({
                'fitness': fit,
                'schedule': chrom
            })

        return top_3
