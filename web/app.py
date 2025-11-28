from datetime import date, datetime, time

import requests
from apscheduler.schedulers.background import BackgroundScheduler
import os, pickle, hashlib
from flask import Flask, jsonify, render_template, request, redirect, session, flash
from drive_uploader import upload_to_drive
from werkzeug.utils import secure_filename
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)
app.secret_key = "secret_key"  # change in production
UPLOAD_FOLDER = "dataset/"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Day map to convert integer (as stored in db)  day to string day 
DAY_MAP = {
    "0": "Sunday",
    "1": "Monday",
    "2": "Tuesday",
    "3": "Wednesday",
    "4": "Thursday",
    "5": "Friday",
    "6": "Saturday",
}

UPLOAD_FOLDER = "temp_uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- DB Helper ----------------
def get_db():
    DATABASE_URL = os.getenv("DATABASE_URL")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    return cur

def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

def _format_time(v):
    try:
        # Format to "H:MM AM/PM" (removes leading zero)
        s = v.strftime("%I:%M %p")
        return s.lstrip("0")
    except Exception:
        return v

def serialize_rows(rows):
    out = []
    for r in rows:
        row = dict(r)
        for k, v in row.items():
            if isinstance(v, datetime):
                row[k] = v.strftime("%d/%m/%Y") # Convert from YYYY-MM-DD
                continue
            if isinstance(v, date):
                row[k] = v.strftime("%d/%m/%Y") # Convert from YYYY-MM-DD
                continue
            if isinstance(v, time): 
                row[k] = _format_time(v) # Convert from HH:MM:SS
                continue
            if hasattr(v, "isoformat") and not isinstance(v, str):
                try:
                    row[k] = v.isoformat()
                except Exception:
                    row[k] = str(v)
            if k.lower() == "status" and isinstance(v, str):
                row[k] = v.capitalize() # Convert lowercase status
        out.append(row)
    return out

def get_students_folder_id(student_id):
    db = get_db()
    db.execute("SELECT folder_id from students where id=%s", (student_id,))
    folder_id = db.fetchone()["folder_id"]
    db.connection.close()
    return folder_id

def save_drive_file(student_id, drive_file_id, file_name):
    db = get_db()
    db.execute("INSERT INTO students_images (student_id, drive_file_id, file_name) VALUES (%s, %s, %s)",
               (student_id, drive_file_id, file_name))
    db.connection.commit()
    db.connection.close()

# --------- Generate Today's periods ----------
def generate_today_periods():
    today = date.today()
    db = get_db()
    
    db.execute("""
        INSERT INTO periods (teacher_subject_id, day, start_time, end_time, date, is_manual, status)
        SELECT teacher_subject_id, day, start_time, end_time, %s, 0, 'scheduled' FROM weekly_periods
        WHERE day = %s
        """, (today.strftime("%d/%m/%Y"), today.strftime("%w")))
    print(f"Generated periods for {today.strftime('%w')}")
    db.connection.commit()
    db.connection.close()
    
# --- Update period statuses automatically ----
def update_period_status():
    now = datetime.now()
    today = date.today()
    db = get_db()
    db.execute("""
        UPDATE periods
        SET status = 'running'
        WHERE date = %s AND start_time <= %s AND end_time >= %s AND status = 'scheduled'
        """, (today.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"), now.strftime("%H:%M:%S")))
    
    db.execute("""
        UPDATE periods
        SET status = 'completed'
        WHERE date = %s AND end_time < %s AND status IN ('scheduled', 'running')
        """, (today.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")))
    print(f"Updated period statuses at {datetime.now().strftime('%H:%M:%S')}")
    db.connection.commit()
    db.connection.close()
 
# ---------------- Scheduler Setup ----------------   
scheduler = BackgroundScheduler()
scheduler.add_job(generate_today_periods, 'cron', hour=15, minute=27)
scheduler.add_job(update_period_status, 'interval', minutes=1)



# ---------------- Sign Up Page ----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]  # "student" or "teacher"
        name = request.form.get("name")
        roll_no = request.form.get("roll_no")  # Only for student

        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        db = get_db()

        try:
            # Insert into users using RETURNING id for Postgres
            db.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s) RETURNING id",
                       (username, hashed_password, role))
            user_id = db.fetchone()["id"]
            db.connection.commit()

            # If student, insert into students table
            if role == "student" and name and roll_no:
                db.execute("INSERT INTO students (name, roll_no, user_id) VALUES (%s, %s, %s)",
                           (name, roll_no, user_id))
                db.connection.commit()
            
            elif role == "teacher" and name:
                db.execute("INSERT INTO teachers (name, user_id) VALUES (%s, %s)",
                           (name, user_id))
                db.connection.commit()
                
            flash("Account created successfully! Please log in.", "success")
            db.connection.close()
            return redirect("/") 
        except psycopg2.IntegrityError:
            db.connection.rollback()
            db.connection.close()
            flash("Username already exists!", "error")
            return render_template("signup.html")

    return render_template("signup.html")

# ---------------- Login ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        db = get_db()
        db.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, hashed_password))
        user = db.fetchone()
        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            if user["role"] == "student": # For students
                db.execute("SELECT name, class_id FROM students Where user_id=%s", (user["id"],))
                student = db.fetchone()
                session["name"] = student["name"].capitalize()
                session["class_id"] = student["class_id"]
               
                flash(f"Welcome, {session['name']}! You are logged in as a {session['role']}.", "success")
                db.connection.close()
                return redirect("/student")
            elif user["role"] == "teacher": # For teachers
                db.execute("SELECT name, id from teachers where user_id=%s", (user["id"],))
                teacher = db.fetchone()
                session["name"] = teacher["name"].capitalize()
                flash(f"Welcome, {session['name']}! You are logged in as a {session['role']}.", "success")
                db.connection.close()
                return redirect("/teacher")
            elif user["role"] == "admin": # For Admin
                session["name"] = "Admin"
                flash(f"Welcome, {session['name']}! You are successfuly logged in", "success")
                db.connection.close()
                return redirect("/admin")
        else:
            db.connection.close()
            flash("Invalid credentials!", "error")
            return render_template("login.html")
    return render_template("login.html")

# ---------------- Logout ----------------
@app.route("/logout")
def logout():
    session.clear()  # Clears all session data
    flash("You have been logged out.", "success")
    return redirect("/")  # Redirect to login page


# ---------------- Student Dashboard ----------------
@app.route("/student")
def student_dashboard():
    if session.get("role") != "student":
        return redirect("/")
    db = get_db()
    db.execute("""
        SELECT 
            sub.code as subject_code, 
            sub.name as subject, 
            t.name as teacher, 
            c.name as class_name, 
            c.id as class_id, 
            COUNT(DISTINCT p.id) AS total_classes,
            SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) AS attended,
            ROUND(
                (
                    SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END)::numeric
                    / NULLIF(COUNT(DISTINCT p.id), 0)::numeric
                    * 100
                )::numeric, 1
            ) AS percentage 
        FROM students s
        JOIN classes c ON s.class_id = c.id
        JOIN teacherSubjects ts ON c.id = ts.class_id
        JOIN subjects sub ON ts.subject_id = sub.id
        JOIN teachers t ON ts.teacher_id = t.id
        LEFT JOIN periods p ON ts.id = p.teacher_subject_id
        LEFT JOIN attendance a ON p.id = a.period_id AND a.student_id = s.id
        WHERE s.user_id=%s
        GROUP BY ts.id, sub.code, sub.name, t.name, c.name, c.id
        ORDER BY sub.name
    """, (session["user_id"],))
    subjects = db.fetchall()

    session["class_name"] = subjects[0]["class_name"] if subjects else None
    session["class_id"] = subjects[0]["class_id"] if subjects else None

    db.execute("""
        SELECT sub.name as subject_name, p.day, p.start_time, p.end_time FROM weekly_periods p
        JOIN teacherSubjects ts ON p.teacher_subject_id = ts.id
        JOIN subjects sub ON ts.subject_id = sub.id
        WHERE ts.class_id = %s
    """, (session["class_id"],))
    rows = db.fetchall()
    timetables = [
        {"subject_name": row["subject_name"], "day": DAY_MAP[f"{row['day']}"], "start_time": _format_time(row["start_time"]), "end_time": _format_time(row["end_time"])}
        for row in rows
    ]

    db.execute("""
        SELECT p.date, COALESCE(a.status, 'absent') as status, sub.name as subject, p.day as day FROM periods p 
        JOIN teacherSubjects ts ON p.teacher_subject_id = ts.id
        JOIN subjects sub ON ts.subject_id = sub.id
        JOIN classes c ON ts.class_id = c.id
        JOIN students s ON c.id = s.class_id
        LEFT JOIN attendance a ON p.id = a.period_id AND a.student_id = s.id
        WHERE s.user_id=%s
    """, (session["user_id"],))
    rows = db.fetchall()

    attendance = [{"date": row["date"], "status": row["status"], "subject": row["subject"], "day": DAY_MAP[f"{row['day']}"]} for row in rows]
    db.connection.close()
    return render_template("student_dashboard.html", subjects=subjects, attendance=serialize_rows(attendance), timetables=timetables)

# ---------------- Teacher Dashboard ----------------
@app.route("/teacher")
def teacher_dashboard():
    if session.get("role") != "teacher":
        return redirect("/")
    db = get_db()
    db.execute("""
        SELECT DISTINCT ts.id, c.name as class_name, sub.code as subject_code, sub.name as subject FROM classes c
        JOIN teacherSubjects ts ON c.id = ts.class_id
        JOIN subjects sub ON ts.subject_id = sub.id
        JOIN teachers t ON ts.teacher_id = t.id
        WHERE t.user_id=%s
    """, (session["user_id"],))
    rows = db.fetchall()
    
    classes = []
    for row in rows:
        classes.append(dict(id=row["id"], class_name=row["class_name"], subject_code=row["subject_code"], subject=row["subject"]))
    
    db.execute("""
        SELECT c.name as class_name, sub.name as subject_name, p.day, p.start_time, p.end_time FROM weekly_periods p
        JOIN teacherSubjects ts ON p.teacher_subject_id = ts.id
        JOIN subjects sub ON ts.subject_id = sub.id
        JOIN classes c ON ts.class_id = c.id
        WHERE ts.teacher_id = (SELECT id FROM teachers WHERE user_id=%s)
    """, (session["user_id"],))
    rows = db.fetchall()
    
    timetables = [
        {"class_name": row["class_name"], "subject_name": row["subject_name"], "day": DAY_MAP[f"{row['day']}"], "start_time": _format_time(row["start_time"]), "end_time": _format_time(row["end_time"])} 
        for row in rows
    ]
    
    db.execute("""
        SELECT s.name as name, s.roll_no, p.date, p.day, sub.name as subject, COALESCE(a.status, 'absent') as status
        FROM students s
        JOIN teacherSubjects ts ON s.class_id = ts.class_id
        JOIN periods p ON ts.id = p.teacher_subject_id
        JOIN subjects sub ON ts.subject_id = sub.id
        LEFT JOIN attendance a ON p.id = a.period_id AND a.student_id = s.id
        WHERE ts.teacher_id = (SELECT id FROM teachers WHERE user_id=%s)
        ORDER BY p.date DESC 
        """, (session["user_id"],))
    rows = db.fetchall()

    attendance = [{"name": row["name"], "roll_no": row["roll_no"], "date": row["date"], "day": DAY_MAP[f"{row['day']}"], "subject": row["subject"], "status": row["status"]} for row in rows]
    db.connection.close()
    return render_template("teacher_dashboard.html", attendance=serialize_rows(attendance), classes=classes, timetables=timetables)

# ---------------Admin Dashboard ----------------
@app.route("/admin")
def admin_dashboard():
    db = get_db()
    if session.get("role") != "admin":
        return redirect("/")
    db.execute("""
               SELECT ts.id, c.name as class_name, sub.code as subject_code, sub.name as subject, t.name as teacher FROM classes c
               JOIN teacherSubjects ts ON c.id = ts.class_id
               JOIN subjects sub ON ts.subject_id = sub.id
               JOIN teachers t ON ts.teacher_id = t.id
               """)
    rows = db.fetchall()
    classes = []
    for row in rows:
        classes.append(dict(id=row["id"], class_name=row["class_name"], subject_code=row["subject_code"], subject=row["subject"], teacher=row["teacher"]))
    
    db.execute("""
        SELECT c.name as class_name, sub.name as subject_name, t.name as teacher_name, p.day, p.start_time, p.end_time FROM weekly_periods p
        JOIN teacherSubjects ts ON p.teacher_subject_id = ts.id
        JOIN teachers t ON ts.teacher_id = t.id
        JOIN subjects sub ON ts.subject_id = sub.id
        JOIN classes c ON ts.class_id = c.id
    """)
    rows = db.fetchall()
    timetables = [
        {"class_name": row["class_name"], "subject_name": row["subject_name"], "teacher_name": row["teacher_name"], "day": DAY_MAP[f"{row['day']}"], "start_time": _format_time(row["start_time"]), "end_time": _format_time(row["end_time"])} 
        for row in rows
    ]
    
    db.execute("""
        SELECT s.id, s.name, s.roll_no, c.name as class_name FROM students s
        LEFT JOIN classes c ON s.class_id = c.id
        """)
    rows = db.fetchall()
    pending_students = []
    students = []
    for row in rows:
        if row["class_name"] == None:
            pending_students += [dict(id=row["id"], name=row["name"], roll_no=row["roll_no"])]
        else :
            students += [dict(id=row["id"], name=row["name"], roll_no=row["roll_no"], class_name=row["class_name"])]
    
    db.execute("""
        SELECT t.id, t.name, c.name as class_name, sub.name as subject_name FROM teachers t
        LEFT JOIN teacherSubjects ts ON t.id = ts.teacher_id
        LEFT JOIN classes c ON ts.class_id = c.id
        LEFT JOIN subjects sub ON ts.subject_id = sub.id
        """)
    rows = db.fetchall()
    pending_teachers = []
    teachers = []
    for row in rows:
        if row["class_name"] == None:
            pending_teachers += [dict(id=row["id"], name=row["name"])]
        else :
            teachers += [dict(id=row["id"], name=row["name"], class_name=row["class_name"], subject_name=row["subject_name"])]
    
    db.execute("""
        SELECT c.name as class_name, s.name as name, s.roll_no, p.date, p.day, sub.name as subject, COALESCE(a.status, 'absent') as status
        FROM students s
        JOIN teacherSubjects ts ON s.class_id = ts.class_id
        JOIN periods p ON ts.id = p.teacher_subject_id
        JOIN subjects sub ON ts.subject_id = sub.id
        JOIN classes c ON s.class_id = c.id
        LEFT JOIN attendance a ON p.id = a.period_id AND a.student_id = s.id
        ORDER BY p.date DESC 
        """)
    rows = db.fetchall()
    attendance = [{"class_name": row["class_name"], "name": row["name"], "roll_no": row["roll_no"], "date": row["date"], "day": DAY_MAP[f"{row['day']}"], "subject": row["subject"], "status": row["status"]} for row in rows]
    
    db.execute("SELECT c.id, c.name as class_name from classes c")
    rows = db.fetchall()
    class_list = []
    for row in rows:
        class_list.append(dict(id=row["id"], class_name=row["class_name"]))
        
    db.connection.close()
    return render_template("admin_dashboard.html", classes=classes, timetables=timetables, students=students, pending_students=pending_students, teachers=teachers, attendance=serialize_rows(attendance), class_list=class_list, pending_teachers=pending_teachers)

# ---------- Student's List ------------------
@app.route("/api/classes/<ts_id>/students", methods=["GET"])
def get_students(ts_id):
    db = get_db()
    if session.get("role") != "teacher" and session.get("role") != "admin":
        flash("Unauthorized", "error")
        return jsonify({"error": "Unauthorized"}), 403
    db.execute("""
        SELECT 
            s.id,
            s.roll_no,
            s.name,
            COUNT(DISTINCT p.id) AS total_classes,
            SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) AS attended,
            ROUND(
                (
                    SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END)::numeric
                    / NULLIF(COUNT(DISTINCT a.period_id), 0)::numeric
                    * 100
                )::numeric, 1
            ) AS percentage
        FROM students s
        LEFT JOIN teacherSubjects ts ON ts.class_id = s.class_id
        LEFT JOIN periods p ON ts.id = p.teacher_subject_id
        LEFT JOIN attendance a ON a.period_id = p.id AND a.student_id = s.id
        WHERE ts.id = %s
        GROUP BY s.id
        ORDER BY s.roll_no
        """, (ts_id,))
    students = db.fetchall()
    db.connection.close()
    return jsonify([dict(row) for row in students])

# ------------API to Get Today's Periods ------------
@app.route("/api/periods/today", methods=["GET"])
def get_periods_today():
    if session.get("role") == "student":
        db = get_db()
        db.execute("""
            SELECT sub.name as subject_name, p.start_time, p.end_time, p.status FROM periods p
            JOIN teacherSubjects ts ON p.teacher_subject_id = ts.id
            JOIN subjects sub ON ts.subject_id = sub.id
            WHERE ts.class_id = %s AND p.date = %s
        """, (session["class_id"], datetime.now().strftime("%Y-%m-%d")))
        today_periods = db.fetchall()
        db.connection.close()
        return jsonify(serialize_rows(today_periods))
    
    elif session.get("role") == "teacher":
        db = get_db()
        db.execute("""
            SELECT p.id, c.name as class_name, sub.name as subject_name, p.start_time, p.end_time, p.status FROM periods p
            JOIN teacherSubjects ts ON p.teacher_subject_id = ts.id
            JOIN subjects sub ON ts.subject_id = sub.id
            JOIN classes c ON ts.class_id = c.id
            WHERE ts.teacher_id = (SELECT id FROM teachers WHERE user_id=%s) AND p.date = %s
        """, (session["user_id"], datetime.now().strftime("%Y-%m-%d")))
        today_periods = db.fetchall()
        db.connection.close()
        return jsonify(serialize_rows(today_periods))
    elif session.get("role") == "admin":
        db = get_db()
        db.execute("""
            SELECT p.id, c.name as class_name, sub.name as subject_name, t.name as teacher_name, p.start_time, p.end_time, p.status FROM periods p
            JOIN teacherSubjects ts ON p.teacher_subject_id = ts.id
            JOIN subjects sub ON ts.subject_id = sub.id
            JOIN classes c ON ts.class_id = c.id
            JOIN teachers t ON ts.teacher_id = t.id
            WHERE p.date = %s
        """, (datetime.now().strftime("%Y-%m-%d"),))
        today_periods = db.fetchall()
        db.connection.close()
        return jsonify(serialize_rows(today_periods))
    
# ---------------- API to Add Class ----------------
@app.route("/api/classes", methods=["POST"])
def add_class():
    if session.get("role") != "teacher" and session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403
    if not request.json:
        return jsonify({"error": "No data provided"}), 400

    teacher_subject_id = request.json.get("ts_id")
    start_time = request.json.get("start_time")
    start_time = datetime.strptime(start_time, "%H:%M").strftime("%H:%M:%S") if start_time else None    
    end_time = request.json.get("end_time")
    end_time = datetime.strptime(end_time, "%H:%M").strftime("%H:%M:%S") if end_time else None
    date = datetime.strptime(request.json.get("date"), "%d/%m/%Y").strftime("%Y-%m-%d") if request.json.get("date") else None
    day = datetime.strptime(date, "%Y-%m-%d").strftime("%w") if date else datetime.now().strftime("%w")
    
    status = request.json.get("status", "scheduled")

    if not teacher_subject_id or not day or not start_time or not end_time:
        return jsonify({"error": "Missing required fields"}), 400    

    db = get_db()
    db.execute("INSERT INTO periods (teacher_subject_id, day, start_time, end_time, date, status) VALUES (%s, %s, %s, %s, %s, %s)",
               (teacher_subject_id, day, start_time, end_time, date, status))
    db.connection.commit()
    db.connection.close()
    return jsonify({"message": "Class added successfully"}), 201


# ---------------- API to Update Period Status ----------------
@app.route("/api/periods/<int:period_id>/status", methods=["POST"])
def update_period_status_api(period_id):
    if session.get("role") != "teacher" and session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403
    if not request.json or "status" not in request.json:
        return jsonify({"error": "No status provided"}), 400

    new_status = request.json["status"]
    if new_status not in ["scheduled", "running", "completed", "cancelled"]:
        return jsonify({"error": "Invalid status"}), 400

    db = get_db()
    db.execute("UPDATE periods SET status = %s WHERE id = %s", (new_status, period_id))
    db.connection.commit()
    db.connection.close()
    return jsonify({"message": "Status updated successfully"}), 200

# ----------------- API to Get Period Students ----------------
@app.route("/api/periods/<int:period_id>/students", methods=["GET"])
def get_period_students_api(period_id):
    if session.get("role") != "teacher" and session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403
    db = get_db()
    db.execute("SELECT s.id, s.roll_no, s.name, a.status FROM periods p JOIN teacherSubjects ts ON p.teacher_subject_id = ts.id JOIN students s ON ts.class_id = s.class_id LEFT JOIN attendance a ON p.id = a.period_id WHERE p.id = %s", (period_id,))
    students = db.fetchall()
    db.connection.close()
    return jsonify([dict(row) for row in students])

# ---------------- API to Add Attendance ----------------
@app.route("/api/periods/<int:period_id>/students/<int:student_id>", methods=["POST"])
def add_attendance_api(period_id, student_id):
    if session.get("role") != "teacher" and session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403
    db = get_db()
    db.execute("INSERT INTO attendance (period_id, student_id, status) VALUES (%s, %s, %s)", (period_id, student_id, "present"))
    db.connection.commit()
    db.connection.close()
    return jsonify({"message": "Attendance added successfully"}), 201

# ---------------- API to Remove Attendance ----------------
@app.route("/api/periods/<int:period_id>/students/<int:student_id>", methods=["DELETE"])
def remove_attendance_api(period_id, student_id):
    if session.get("role") != "teacher" and session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403
    db = get_db()
    db.execute("DELETE FROM attendance WHERE period_id = %s AND student_id = %s", (period_id, student_id))
    db.connection.commit()
    db.connection.close()
    return jsonify({"message": "Attendance removed successfully"}), 200

# ------------------ API to update Student's Class -----------------
@app.route("/api/students/<int:student_id>/class", methods=["POST"])
def update_student_class_api(student_id):
    if session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403
    if not request.json or "class_id" not in request.json:
        return jsonify({"error": "No class_id provided"}), 400
    class_id = request.json["class_id"]
    db = get_db()
    db.execute("UPDATE students SET class_id = %s WHERE id = %s", (class_id, student_id))
    db.connection.commit()
    db.connection.close()
    return jsonify({"message": "Class updated successfully"}), 200

# ----------------- API to get currently running Class ------------------
@app.route("/api/classes/<int:class_id>", methods=["GET"])
def get_current_class_api(class_id):
    if session.get("role") != "teacher" and session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403
    db = get_db()
    db.execute("SELECT p.status, p.id FROM periods p JOIN teacherSubjects ts ON p.teacher_subject_id = ts.id WHERE ts.class_id = %s AND p.status = 'running'", (class_id,))
    current_class = db.fetchone()
    db.connection.close()
    return jsonify(dict(current_class) if current_class else {})

# ----------------- API to enroll Student -----------------
@app.route("/api/students/<int:student_id>/enroll", methods=["POST"])
def enroll_student_api(student_id):
    if session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    class_id = data.get("class_id")
    db = get_db()
    db.execute("UPDATE students SET class_id = %s WHERE id = %s", (class_id, student_id))
    db.connection.commit()
    db.connection.close()
    return jsonify({"message": "Student enrolled successfully"}), 200

# --------------- API to reject Student ----------------
@app.route("/api/students/<int:student_id>/reject", methods=["POST"])
def reject_student_api(student_id):
    if session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403
    db = get_db()
    db.execute("DELETE FROM students WHERE id = %s", (student_id,))
    db.connection.commit()
    db.connection.close()
    return jsonify({"message": "Student rejected successfully"}), 200

# ---------------- API to Upload File ----------------
@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    student_id = request.form.get("student_id")
    files = request.files.getlist("images")

    if not student_id:
        print("student_id is required")
        return jsonify({"error": "student_id is required"}), 400
    if not files:
        print("no images uploaded")
        return jsonify({"error": "no images uploaded"}), 400

    DRIVE_FOLDER_ID = get_students_folder_id(student_id)
    
    if not DRIVE_FOLDER_ID:
        print("Student's Drive folder not found")
        return jsonify({"error": "Student's Drive folder not found"}), 400
    
    uploaded = []

    for file in files:
        filename = file.filename
        local_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(local_path)


        # Upload to Google Drive
        drive_file_id = upload_to_drive(local_path, filename, DRIVE_FOLDER_ID)

        # Save DB reference
        save_drive_file(student_id, drive_file_id, filename)

        uploaded.append({
            "filename": filename,
            "drive_file_id": drive_file_id
        })
        os.remove(local_path)
    return redirect("/admin")

# ----------------- API to Generate Embeddings -----------------
@app.route("/api/generate_embeddings", methods=["POST"])
async def generate_embeddings_api():
    if session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403
    data = request.json
    
    student_id = data.get("student_id")
    db = get_db()
    db.execute("SELECT drive_file_id, file_name FROM students_images WHERE student_id = %s", (student_id,))
    file_ids = [{"file_id": row["drive_file_id"]} for row in db.fetchall()]
    
    response = await requests.post(
        os.getenv("FACE_SERVICE_URL") + "/generate_embeddings",
        json={"file_ids": file_ids}
    )
    for embedding in response.json():
        file_id = embedding["file_id"]
        vector = embedding["embedding"]
        db.execute("INSERT INTO embeddings (image_id, vector) VALUES (SELECT id from students_images WHERE drive_file_id = %s, %s)", ( file_id, vector))
    return jsonify({"message": "Embeddings generated and saved successfully"}), 200

if __name__ == "__main__":  
    scheduler.start()
    app.run(host="0.0.0.0", port=5000, debug=True)
