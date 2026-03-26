import random
import copy
from datetime import datetime, timedelta
from ga_engine.fitness import calculate_fitness
from ga_engine.mutation import mutate

class GeneticAlgorithm:
    def __init__(self, subjects, rooms, faculty_prefs, dates_available, time_slots):
        self.subjects = subjects # {id: {type, duration_minutes}}
        self.rooms = rooms       # {id: {type, capacity}}
        self.faculty_prefs = faculty_prefs # {faculty_id: [date]}
        self.dates_available = dates_available # [datetime.date]
        self.time_slots = time_slots # ['09:00:00', '14:00:00']
        
        self.pop_size = 50
        self.generations = 100
        self.mutation_rate = 0.3
        self.crossover_rate = 0.8
        self.tournament_size = 5

    def initialize_population(self):
        population = []
        for _ in range(self.pop_size):
            chromosome = []
            for sub_id, data in self.subjects.items():
                start = random.choice(self.time_slots) # e.g. '09:00:00'
                h, m, s = map(int, start.split(':'))
                # Assuming 3 hours default duration
                end_dt = (datetime.strptime(start, '%H:%M:%S') + timedelta(minutes=data.get('duration_minutes', 180))).strftime('%H:%M:%S')
                
                gene = {
                    'subject_id': sub_id,
                    'faculty_id': data['faculty_id'],
                    'room_id': random.choice(list(self.rooms.keys())),
                    'division_id': data['division_id'],
                    'exam_date': random.choice(self.dates_available),
                    'start_time': start,
                    'end_time': end_dt
                }
                chromosome.append(gene)
            population.append(chromosome)
        return population

    def selection(self, population, fitness_scores):
        # Tournament Selection
        selected = []
        for _ in range(self.pop_size):
            tournament = random.sample(list(zip(population, fitness_scores)), self.tournament_size)
            winner = max(tournament, key=lambda x: x[1])[0]
            selected.append(copy.deepcopy(winner))
        return selected

    def crossover(self, parent1, parent2):
        if random.random() < self.crossover_rate:
            point = random.randint(1, len(parent1)-1)
            child1 = parent1[:point] + parent2[point:]
            child2 = parent2[:point] + parent1[point:]
            return child1, child2
        return parent1, parent2

    def run(self):
        # Initial Population
        population = self.initialize_population()
        
        for gen in range(self.generations):
            # Evaluate Fitness
            fitness_scores = [calculate_fitness(chrom, self.faculty_prefs, self.subjects, self.rooms, {}) for chrom in population]
            
            # Selection
            mating_pool = self.selection(population, fitness_scores)
            
            # Create Next Generation (Crossover)
            next_generation = []
            for i in range(0, self.pop_size, 2):
                p1, p2 = mating_pool[i], mating_pool[i+1]
                c1, c2 = self.crossover(p1, p2)
                next_generation.extend([c1, c2])
            
            # Mutation
            for chrom in next_generation:
                if random.random() < self.mutation_rate:
                    mutate(chrom, self.rooms, self.dates_available, self.time_slots)
            
            population = next_generation
            
            # (Optional) Log best fitness 
            # best_fitness = max(fitness_scores)
            # print(f"Generation {gen}: Best Fitness = {best_fitness}")
            
        # Final Evaluation
        final_fitness = [calculate_fitness(chrom, self.faculty_prefs, self.subjects, self.rooms, {}) for chrom in population]
        best_indices = sorted(range(len(final_fitness)), key=lambda i: final_fitness[i], reverse=True)[:3]
        
        top_3 = []
        for idx in best_indices:
            top_3.append({
                'fitness': final_fitness[idx],
                'schedule': population[idx]
            })
            
        return top_3
