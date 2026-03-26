CREATE DATABASE IF NOT EXISTS timetable_ai;
USE timetable_ai;

CREATE TABLE IF NOT EXISTS faculty (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    department VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS subjects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type ENUM('THEORY', 'LAB') NOT NULL,
    duration_minutes INT DEFAULT 180
);

CREATE TABLE IF NOT EXISTS rooms (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    type ENUM('CLASSROOM', 'LAB') NOT NULL,
    capacity INT NOT NULL
);

CREATE TABLE IF NOT EXISTS classes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    department VARCHAR(50) NOT NULL,
    year INT NOT NULL,
    division VARCHAR(5) NOT NULL
);

CREATE TABLE IF NOT EXISTS faculty_preferences (
    id INT AUTO_INCREMENT PRIMARY KEY,
    faculty_id INT NOT NULL,
    preferred_date DATE NOT NULL,
    FOREIGN KEY (faculty_id) REFERENCES faculty(id)
);

CREATE TABLE IF NOT EXISTS schedule_options (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    option_no INT NOT NULL,
    subject_id INT NOT NULL,
    exam_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    room_id INT NOT NULL,
    fitness_score DECIMAL(10, 4),
    FOREIGN KEY (subject_id) REFERENCES subjects(id),
    FOREIGN KEY (room_id) REFERENCES rooms(id)
);

CREATE TABLE IF NOT EXISTS final_schedule (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    subject_id INT NOT NULL,
    exam_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    room_id INT NOT NULL,
    FOREIGN KEY (subject_id) REFERENCES subjects(id),
    FOREIGN KEY (room_id) REFERENCES rooms(id)
);

-- Simple view-like table to satisfy "schedules" naming if needed by tools
CREATE TABLE IF NOT EXISTS schedules (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    subject_id INT NOT NULL,
    exam_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    room_id INT NOT NULL,
    option_no INT DEFAULT 1,
    FOREIGN KEY (subject_id) REFERENCES subjects(id),
    FOREIGN KEY (room_id) REFERENCES rooms(id)
);

-- Student counts per class/division
CREATE TABLE IF NOT EXISTS class_students (
    class_id INT NOT NULL,
    student_count INT NOT NULL DEFAULT 0,
    FOREIGN KEY (class_id) REFERENCES classes(id)
);

-- Explicit subject-to-faculty mapping
CREATE TABLE IF NOT EXISTS subject_faculty (
    subject_id INT NOT NULL,
    faculty_id INT NOT NULL,
    FOREIGN KEY (subject_id) REFERENCES subjects(id),
    FOREIGN KEY (faculty_id) REFERENCES faculty(id)
);

-- Explicit subject-to-class/division mapping
CREATE TABLE IF NOT EXISTS subject_class (
    subject_id INT NOT NULL,
    class_id INT NOT NULL,
    FOREIGN KEY (subject_id) REFERENCES subjects(id),
    FOREIGN KEY (class_id) REFERENCES classes(id)
);

-- Seed Data (Optional but helpful for testing)
INSERT INTO faculty (name, department) VALUES ('Dr. Julian Vance', 'CSE'), ('Dr. Sarah Jenkins', 'CSE'), ('Prof. Marcus Thorne', 'CSE');
INSERT INTO rooms (name, type, capacity) VALUES ('Hall 4C', 'CLASSROOM', 60), ('Lab 102', 'LAB', 30), ('Auditorium B', 'CLASSROOM', 200);
INSERT INTO subjects (name, type) VALUES ('Advanced Quantum Mechanics', 'THEORY'), ('Neural Networks', 'LAB'), ('Ethics in AI', 'THEORY');
INSERT INTO classes (department, year, division) VALUES ('CSE', 4, 'A'), ('CSE', 4, 'B');
