import random
from collections import defaultdict

class AllocationEngine:
    def __init__(self, branches, classrooms, faculty_list):
        self.branches = branches  # List of branch codes
        self.classrooms = classrooms # List of room dicts: {'id': 101, 'capacity': 40}
        self.faculty_list = faculty_list # List of names or dicts
        self.students = self._generate_dummy_students()
        
    def _generate_dummy_students(self):
        # 8 branches, 3 divisions each, ~60 per div
        student_data = []
        divisions = ['A', 'B', 'C']
        for branch in self.branches:
            for div in divisions:
                for i in range(1, 61):
                    student_data.append({
                        'roll_no': f"24{branch}{div}{i:02d}",
                        'branch': branch,
                        'div': div
                    })
        random.shuffle(student_data)
        return student_data

    def interleave_students(self, students):
        """Anti-cheating interleaved seating logic"""
        # Group by branch
        branch_groups = defaultdict(list)
        for s in students:
            branch_groups[s['branch']].append(s)
        
        # Round robin interleaving
        interleaved = []
        branch_keys = list(branch_groups.keys())
        max_len = max(len(v) for v in branch_groups.values())
        
        for i in range(max_len):
            for b in branch_keys:
                if i < len(branch_groups[b]):
                    interleaved.append(branch_groups[b][i])
        return interleaved

    def calculate_score(self, room_students):
        """Smart Scoring System"""
        score = 0
        if not room_students: return 0
        
        # Diversity Reward
        unique_branches = len(set(s['branch'] for s in room_students))
        if unique_branches >= 3:
            score += 50
        
        # Branch Clustering Penalty
        for i in range(len(room_students) - 1):
            if room_students[i]['branch'] == room_students[i+1]['branch']:
                score -= 100
        
        return score

    def generate_allocation(self):
        """Full pipeline: Students -> Rooms -> Faculty -> Explanability"""
        all_allocations = []
        remaining_students = self.students.copy()
        faculty_load = {f: 0 for f in self.faculty_list}
        
        for room in self.classrooms:
            if not remaining_students: break
            
            capacity = room['capacity']
            # Take exactly enough or all remaining
            count = min(capacity, len(remaining_students))
            room_students = remaining_students[:count]
            remaining_students = remaining_students[count:]
            
            # Apply interleaving
            interleaved = self.interleave_students(room_students)
            
            # Assign faculty (Least load first)
            available_faculty = sorted(self.faculty_list, key=lambda f: faculty_load[f])
            assigned_faculty = available_faculty[0]
            faculty_load[assigned_faculty] += 1
            
            # Smart Scoring
            room_score = self.calculate_score(interleaved)
            
            # Explanation (DSS)
            branches = set(s['branch'] for s in interleaved)
            explanation = f"Room {room['id']} mixed {len(branches)} branches to maximize exam integrity. Score: {room_score}"
            
            all_allocations.append({
                'room_id': room['id'],
                'faculty': assigned_faculty,
                'students': interleaved,
                'count': len(interleaved),
                'score': room_score,
                'explanation': explanation,
                'status': 'Optimized' if room_score > 0 else 'Sub-optimal'
            })
            
        return all_allocations, faculty_load

def get_engine_data():
    # Helper to bootstrap data
    branches = ['AIDS', 'CS', 'IT', 'ENTC', 'Civil', 'Mech', 'Instr', 'Robotics']
    rooms = [{'id': 100 + i, 'capacity': 40} for i in range(1, 42)]
    faculty = [
        "Dr. Rajesh Kumar", "Prof. Sneha Patil", "Dr. Amit Sharma", 
        "Prof. Priya Deshmukh", "Dr. Vikram Singh", "Prof. Anjali Gupta",
        "Dr. Sanjay Mehta", "Prof. Kavita Joshi", "Dr. Rahul Verma",
        "Prof. Meera Kulkarni", "Dr. Deepak Sawant", "Prof. Shweta More"
    ]
    return branches, rooms, faculty
