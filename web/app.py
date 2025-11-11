from datetime import date, datetime
from apscheduler.schedulers.background import BackgroundScheduler
import os, pickle, hashlib
from flask import Flask, jsonify, render_template, request, redirect, session, flash
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

DAY_MAP = {
    "0": "Sunday",
    "1": "Monday",
    "2": "Tuesday",
    "3": "Wednesday",
    "4": "Thursday",
    "5": "Friday",
    "6": "Saturday",
}

# ---------------- DB Helper ----------------
def get_db():
    DATABASE_URL = os.getenv("DATABASE_URL")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    return cur

def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

def serialize_rows(rows):
    out = []
    for r in rows:
        row = dict(r)
        for k, v in row.items():
            # convert date / datetime / time (and any object with isoformat) to string
            if hasattr(v, "isoformat") and not isinstance(v, str):
                try:
                    row[k] = v.isoformat()
                except Exception:
                    row[k] = str(v)
        out.append(row)
    return out

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
            db.execute("SELECT name FROM students WHERE user_id=%s", (user["id"],))
            user_name = db.fetchone()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            session["name"] = user_name["name"] if user_name else "Teacher"
            if user["role"] == "student":
                db.execute("SELECT id, class_id FROM students Where user_id=%s", (user["id"],))
                student = db.fetchone()
                session["class_id"] = student["class_id"]
               
                flash(f"Welcome, {session['name']}! You are logged in as a {session['role']}.", "success")
                db.connection.close()
                return redirect("/student")
            else:
                flash(f"Welcome, {session['name']}! You are logged in as a {session['role']}.", "success")
                db.connection.close()
                return redirect("/teacher")
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
        LEFT JOIN attendance a ON p.id = a.period_id
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
        {"subject_name": row["subject_name"], "day": DAY_MAP[f"{row['day']}"], "start_time": row["start_time"], "end_time": row["end_time"]}
        for row in rows
    ]

    db.execute("""
        SELECT p.date, a.status, sub.name as subject, p.day as day FROM attendance a 
        JOIN periods p ON a.period_id = p.id
        JOIN teacherSubjects ts ON p.teacher_subject_id = ts.id
        JOIN subjects sub ON ts.subject_id = sub.id
        WHERE a.student_id=(SELECT id FROM students WHERE user_id=%s)
    """, (session["user_id"],))
    rows = db.fetchall()

    attendance = [{"date": row["date"], "status": row["status"], "subject": row["subject"], "day": DAY_MAP[f"{row['day']}"]} for row in rows]
    db.connection.close()
    return render_template("student_dashboard.html", subjects=subjects, attendance=attendance, timetables=timetables)

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
        {"class_name": row["class_name"], "subject_name": row["subject_name"], "day": DAY_MAP[f"{row['day']}"], "start_time": row["start_time"], "end_time": row["end_time"]}
        for row in rows
    ]
    
    db.execute("""
        SELECT s.name as name, s.roll_no, p.date, p.day, sub.name as subject, a.status
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        JOIN periods p ON a.period_id = p.id
        JOIN teacherSubjects ts ON p.teacher_subject_id = ts.id
        JOIN subjects sub ON ts.subject_id = sub.id
        WHERE ts.teacher_id = (SELECT id FROM teachers WHERE user_id=%s)
        ORDER BY p.date DESC 
        """, (session["user_id"],))
    rows = db.fetchall()

    attendance = [{"name": row["name"], "roll_no": row["roll_no"], "date": row["date"], "day": DAY_MAP[f"{row['day']}"], "subject": row["subject"], "status": row["status"]} for row in rows]
    db.connection.close()
    return render_template("teacher_dashboard.html", attendance=attendance, classes=classes, timetables=timetables)

# ---------- Student's List ------------------
@app.route("/api/classes/<ts_id>/students", methods=["GET"])
def get_students(ts_id):
    db = get_db()
    if session.get("role") != "teacher":
        flash("Unauthorized", "error")
        return jsonify({"error": "Unauthorized"}), 403
    db.execute("""
        SELECT 
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
        LEFT JOIN attendance a ON a.period_id = p.id
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
    
# ---------------- API to Add Class ----------------
@app.route("/api/classes", methods=["POST"])
def add_class():
    if session.get("role") != "teacher":
        return jsonify({"error": "Unauthorized"}), 403
    if not request.json:
        return jsonify({"error": "No data provided"}), 400

    teacher_subject_id = request.json.get("ts_id")
    start_time = request.json.get("start_time")
    start_time = datetime.strptime(start_time, "%H:%M").strftime("%H:%M:%S") if start_time else None    
    end_time = request.json.get("end_time")
    end_time = datetime.strptime(end_time, "%H:%M").strftime("%H:%M:%S") if end_time else None
    date = request.json.get("date")  # optional, default to today
    day = datetime.strptime(date, "%d/%m/%Y").strftime("%w") if date else datetime.now().strftime("%w")
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
    if session.get("role") != "teacher":
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
    if session.get("role") != "teacher":
        return jsonify({"error": "Unauthorized"}), 403
    db = get_db()
    db.execute("SELECT s.id, s.roll_no, s.name, a.status FROM periods p JOIN teacherSubjects ts ON p.teacher_subject_id = ts.id JOIN students s ON ts.class_id = s.class_id LEFT JOIN attendance a ON p.id = a.period_id WHERE p.id = %s", (period_id,))
    students = db.fetchall()
    db.connection.close()
    return jsonify([dict(row) for row in students])

# ---------------- API to Add Attendance ----------------
@app.route("/api/periods/<int:period_id>/students/<int:student_id>", methods=["POST"])
def add_attendance_api(period_id, student_id):
    if session.get("role") != "teacher":
        return jsonify({"error": "Unauthorized"}), 403
    db = get_db()
    db.execute("INSERT INTO attendance (period_id, student_id, status) VALUES (%s, %s, %s)", (period_id, student_id, "present"))
    db.connection.commit()
    db.connection.close()
    return jsonify({"message": "Attendance added successfully"}), 201

# ---------------- API to Remove Attendance ----------------
@app.route("/api/periods/<int:period_id>/students/<int:student_id>", methods=["DELETE"])
def remove_attendance_api(period_id, student_id):
    if session.get("role") != "teacher":
        return jsonify({"error": "Unauthorized"}), 403
    db = get_db()
    db.execute("DELETE FROM attendance WHERE period_id = %s AND student_id = %s", (period_id, student_id))
    db.connection.commit()
    db.connection.close()
    return jsonify({"message": "Attendance removed successfully"}), 200

# ----------------- API to get currently running Class ------------------
@app.route("/api/classes/<int:class_id>", methods=["GET"])
def get_current_class_api(class_id):
    if session.get("role") != "teacher":
        return jsonify({"error": "Unauthorized"}), 403
    db = get_db()
    db.execute("SELECT p.status, p.id FROM periods p JOIN teacherSubjects ts ON p.teacher_subject_id = ts.id WHERE ts.class_id = %s AND p.status = 'running'", (class_id,))
    current_class = db.fetchone()
    db.connection.close()
    return jsonify(dict(current_class) if current_class else {})

# -------------------API to get Section -----------------------
@app.route("/api/<section>", methods=["GET"])
def get_section(section):
    db = get_db()
    if section == "st-periods":
        return render_template("partials/st-periods.html")

if __name__ == "__main__":
    scheduler.start()
    app.run(host="0.0.0.0", port=5000)
