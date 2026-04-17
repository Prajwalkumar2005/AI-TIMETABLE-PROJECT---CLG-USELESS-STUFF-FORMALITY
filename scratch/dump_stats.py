
import sys
import os
sys.path.append(os.getcwd())
from project.database.db import db

def dump_stats():
    print("--- COLLEGE CONTEXT STATS ---")
    
    # 1. Departments/Branches
    branches = db.fetch_all("SELECT department, COUNT(*) as div_count FROM classes GROUP BY department")
    print(f"Branches: {branches}")
    
    # 2. Total Students
    students = db.fetch_all("SELECT SUM(student_count) as total FROM class_students")
    print(f"Total Students (Seeded): {students[0]['total'] if students else 0}")
    
    # 3. Classrooms
    rooms = db.fetch_all("SELECT COUNT(*) as total, SUM(capacity) as total_cap FROM rooms")
    print(f"Total Classrooms: {rooms[0]['total'] if rooms else 0}")
    print(f"Total Capacity: {rooms[0]['total_cap'] if rooms else 0}")
    
    # 4. Faculty
    faculty = db.fetch_all("SELECT COUNT(*) as total FROM faculty")
    print(f"Total Faculty: {faculty[0]['total'] if faculty else 0}")
    
    # 5. Divisions detail
    divs = db.fetch_all("SELECT department, year, division FROM classes")
    print(f"Divisions: {divs}")

if __name__ == "__main__":
    dump_stats()
