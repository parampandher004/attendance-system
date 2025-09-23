-- Users table (students + teachers)
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT CHECK(role IN ('student', 'teacher'))
);

-- Students table
CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    roll_no TEXT UNIQUE,
    user_id INTEGER,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

-- Attendance table
CREATE TABLE attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    date TEXT,
    status TEXT,
    FOREIGN KEY(student_id) REFERENCES students(id)
);

-- Face encodings table
CREATE TABLE face_encodings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    encoding BLOB,
    FOREIGN KEY(student_id) REFERENCES students(id)
);
