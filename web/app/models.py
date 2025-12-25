from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import ARRAY

# --- Core Users ---
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.BigInteger, primary_key=True)
    username = db.Column(db.Text, unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)
    role = db.Column(db.Text, nullable=False) # 'student', 'teacher', 'admin'

    # Relationships
    student = db.relationship("Student", back_populates="user", uselist=False)
    teacher = db.relationship("Teacher", back_populates="user", uselist=False)

# --- Entities ---
class Class(db.Model):
    __tablename__ = 'classes'
    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.Text, nullable=False)

    students = db.relationship("Student", back_populates="class_")
    teacher_subjects = db.relationship("TeacherSubject", back_populates="class_")

class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.Text)
    code = db.Column(db.Text)

class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.Text)
    roll_no = db.Column(db.Text, unique=True)
    class_id = db.Column(db.BigInteger, db.ForeignKey('classes.id'))
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id'))
    folder_id = db.Column(db.String) # Drive Folder ID
    gender = db.Column(db.String)

    user = db.relationship("User", back_populates="student")
    class_ = db.relationship("Class", back_populates="students")
    attendance_records = db.relationship("Attendance", back_populates="student")
    images = db.relationship("StudentImage", back_populates="student")

class Teacher(db.Model):
    __tablename__ = 'teachers'
    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.Text)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id'))
    gender = db.Column(db.String)

    user = db.relationship("User", back_populates="teacher")
    teacher_subjects = db.relationship("TeacherSubject", back_populates="teacher")

# --- Schedule & Logic ---
class TeacherSubject(db.Model):
    __tablename__ = 'teachersubjects'
    id = db.Column(db.BigInteger, primary_key=True)
    teacher_id = db.Column(db.BigInteger, db.ForeignKey('teachers.id'))
    subject_id = db.Column(db.BigInteger, db.ForeignKey('subjects.id'))
    class_id = db.Column(db.BigInteger, db.ForeignKey('classes.id'))

    class_ = db.relationship("Class", back_populates="teacher_subjects")
    teacher = db.relationship("Teacher", back_populates="teacher_subjects")
    subject = db.relationship("Subject", backref="teacher_subjects")
    periods = db.relationship("Period", back_populates="teacher_subject")
    weekly_periods = db.relationship("WeeklyPeriod", back_populates="teacher_subject")

class WeeklyPeriod(db.Model):
    __tablename__ = 'weekly_periods'
    id = db.Column(db.BigInteger, primary_key=True)
    teacher_subject_id = db.Column(db.BigInteger, db.ForeignKey('teachersubjects.id'))
    day = db.Column(db.BigInteger) # 0-6
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)

    teacher_subject = db.relationship("TeacherSubject", back_populates="weekly_periods")

class Period(db.Model):
    __tablename__ = 'periods'
    id = db.Column(db.BigInteger, primary_key=True)
    teacher_subject_id = db.Column(db.BigInteger, db.ForeignKey('teachersubjects.id'))
    date = db.Column(db.Date)
    day = db.Column(db.BigInteger)
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)
    is_manual = db.Column(db.BigInteger, default=0)
    status = db.Column(db.Text, default='scheduled')

    teacher_subject = db.relationship("TeacherSubject", back_populates="periods")
    attendance_records = db.relationship("Attendance", back_populates="period")

class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.BigInteger, primary_key=True)
    student_id = db.Column(db.BigInteger, db.ForeignKey('students.id'))
    period_id = db.Column(db.BigInteger, db.ForeignKey('periods.id'))
    status = db.Column(db.Text)

    student = db.relationship("Student", back_populates="attendance_records")
    period = db.relationship("Period", back_populates="attendance_records")

# --- Biometrics ---
class StudentImage(db.Model):
    __tablename__ = 'students_images'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'))
    drive_file_id = db.Column(db.Text, nullable=False)
    file_name = db.Column(db.Text)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship("Student", back_populates="images")
    embeddings = db.relationship("StudentEmbedding", back_populates="image")

class StudentEmbedding(db.Model):
    __tablename__ = 'students_embeddings'
    id = db.Column(db.Integer, primary_key=True)
    image_id = db.Column(db.Integer, db.ForeignKey('students_images.id'))
    vector = db.Column(ARRAY(db.Float), nullable=False) # PostgreSQL Array
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    image = db.relationship("StudentImage", back_populates="embeddings")