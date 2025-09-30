from datetime import date, datetime
from apscheduler.schedulers.background import BackgroundScheduler
import os, sqlite3, pickle, hashlib
from flask import Flask, jsonify, render_template, request, redirect, session
from werkzeug.utils import secure_filename
# from deepface import DeepFace

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
    conn = sqlite3.connect("attendance.db", timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

# --------- Generate Today's periods ----------
def generate_today_periods():
    today = date.today()
    db = get_db()
    
    db.execute("""
        INSERT INTO periods (teacher_subject_id, day, start_time, end_time, date, is_manual, status)
        SELECT teacher_subject_id, day, start_time, end_time, ?, 0, 'scheduled' FROM weekly_periods
        WHERE day = ?
        """, (today.strftime("%d/%m/%Y"), today.strftime("%w")))
    print(f"Generated periods for {today.strftime('%w')}")
    db.commit()
    
# --- Update period statuses automatically ----
def update_period_status():
    now = datetime.now()
    today = date.today()
    db = get_db()
    db.execute("""
        UPDATE periods
        SET status = 'running'
        WHERE date = ? AND start_time <= ? AND end_time >= ? AND status = 'scheduled'
        """, (today.strftime("%d/%m/%Y"), now.strftime("%H:%M:%S"), now.strftime("%H:%M:%S")))
    
    db.execute("""
        UPDATE periods
        SET status = 'completed'
        WHERE date = ? AND end_time < ? AND status IN ('scheduled', 'running')
        """, (today.strftime("%d/%m/%Y"), now.strftime("%H:%M:%S")))
    print(f"Updated period statuses at {datetime.now().strftime('%H:%M:%S')}")
    db.commit()
    db.close()
 
# ---------------- Scheduler Setup ----------------   
scheduler = BackgroundScheduler()
scheduler.add_job(generate_today_periods, 'cron', hour=15, minute=33)
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
            # Insert into users
            cursor = db.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                                (username, hashed_password, role))
            db.commit()
            user_id = cursor.lastrowid

            # If student, insert into students table
            if role == "student" and name and roll_no:
                db.execute("INSERT INTO students (name, roll_no, user_id) VALUES (?, ?, ?)",
                           (name, roll_no, user_id))
                db.commit()
            
            elif role == "teacher" and name:
                db.execute("INSERT INTO teachers (name, user_id) VALUES (?, ?)",
                           (name, user_id))
                db.commit()

            return redirect("/")  # After signup, go to login
        except sqlite3.IntegrityError:
            return "Username or Roll Number already exists!"

    return render_template("signup.html")

# ---------------- Login ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        db = sqlite3.connect("attendance.db")
        db.row_factory = sqlite3.Row
        user = db.execute("SELECT * FROM users WHERE username=? AND password=?", 
                          (username, hashed_password)).fetchone()
        user_name = db.execute("SELECT name FROM students WHERE user_id=?",
                          (user["id"],)).fetchone()
        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            session["name"] = user_name["name"] if user_name else "Teacher"
            if user["role"] == "student":
                student = db.execute("SELECT id, class_id FROM students Where user_id=?",
                          (user["id"],)).fetchone()
                session["class_id"] = student["class_id"]
                
                return redirect("/student")
            else:
                return redirect("/teacher")
        else:
            return "Invalid credentials"
        db.close()
    return render_template("login.html")

# ---------------- Logout ----------------
@app.route("/logout")
def logout():
    session.clear()  # Clears all session data
    return redirect("/")  # Redirect to login page


# ---------------- Student Dashboard ----------------
@app.route("/student")
def student_dashboard():
    if session.get("role") != "student":
        return redirect("/")
    db = get_db()
    subjects = db.execute("""
        SELECT sub.code as subject_code, sub.name as subject, t.name as teacher, c.name as class_name, c.id as class_id FROM students s
        JOIN classes c ON s.class_id = c.id
        JOIN teacherSubjects ts ON c.id = ts.class_id
        JOIN subjects sub ON ts.subject_id = sub.id
        JOIN teachers t ON ts.teacher_id = t.id
        WHERE s.user_id=?
    """, (session["user_id"],)).fetchall()

    session["class_name"] = subjects[0]["class_name"] if subjects else None
    session["class_id"] = subjects[0]["class_id"] if subjects else None

    rows = db.execute("""
        SELECT sub.name as subject_name, p.day, p.start_time, p.end_time FROM weekly_periods p
        JOIN teacherSubjects ts ON p.teacher_subject_id = ts.id
        JOIN subjects sub ON ts.subject_id = sub.id
        WHERE ts.class_id = ?
    """, (session["class_id"],)).fetchall()
    timetables = [
        {"subject_name": row["subject_name"], "day": DAY_MAP[f"{row["day"]}"], "start_time": row["start_time"], "end_time": row["end_time"]}
        for row in rows
    ]
    
    today_periods = db.execute("""
        SELECT sub.name as subject_name, p.start_time, p.end_time, p.status FROM periods p
        JOIN teacherSubjects ts ON p.teacher_subject_id = ts.id
        JOIN subjects sub ON ts.subject_id = sub.id
        WHERE ts.class_id = ? AND p.date = ?
    """, (session["class_id"], datetime.now().strftime("%d/%m/%Y"))).fetchall()

    rows = db.execute("""
        SELECT p.date, a.status, sub.name as subject, p.day as day FROM attendance a 
        JOIN periods p ON a.period_id = p.id
        JOIN teacherSubjects ts ON p.teacher_subject_id = ts.id
        JOIN subjects sub ON ts.subject_id = sub.id
        WHERE a.student_id=(SELECT id FROM students WHERE user_id=?)
    """, (session["user_id"],)).fetchall()

    attendance = [{"date": row["date"], "status": row["status"], "subject": row["subject"], "day": DAY_MAP[f"{row["day"]}"]} for row in rows]

    return render_template("student_dashboard.html", subjects=subjects, attendance=attendance, timetables=timetables, today_periods=today_periods)

# ---------------- Teacher Dashboard ----------------
@app.route("/teacher")
def teacher_dashboard():
    if session.get("role") != "teacher":
        return redirect("/")
    db = get_db()
    classes = db.execute("""
        SELECT DISTINCT c.name as class_name, sub.code as subject_code, sub.name as subject FROM classes c
        JOIN teacherSubjects ts ON c.id = ts.class_id
        JOIN subjects sub ON ts.subject_id = sub.id
        JOIN teachers t ON ts.teacher_id = t.id
        WHERE t.user_id=?
    """, (session["user_id"],)).fetchall()
    
    today_periods = db.execute("""
        SELECT c.name as class_name, sub.name as subject_name, p.start_time, p.end_time, p.status FROM periods p
        JOIN teacherSubjects ts ON p.teacher_subject_id = ts.id
        JOIN subjects sub ON ts.subject_id = sub.id
        JOIN classes c ON ts.class_id = c.id
        WHERE ts.teacher_id = (SELECT id FROM teachers WHERE user_id=?) AND p.date = ?
    """, (session["user_id"], datetime.now().strftime("%d/%m/%Y"))).fetchall()
    
    rows = db.execute("""
        SELECT c.name as class_name, sub.name as subject_name, p.day, p.start_time, p.end_time FROM weekly_periods p
        JOIN teacherSubjects ts ON p.teacher_subject_id = ts.id
        JOIN subjects sub ON ts.subject_id = sub.id
        JOIN classes c ON ts.class_id = c.id
        WHERE ts.teacher_id = (SELECT id FROM teachers WHERE user_id=?)
    """, (session["user_id"],)).fetchall()
    
    timetables = [
        {"class_name": row["class_name"], "subject_name": row["subject_name"], "day": DAY_MAP[f"{row["day"]}"], "start_time": row["start_time"], "end_time": row["end_time"]}
        for row in rows
    ]
    
    rows = db.execute("""
        SELECT s.name as name, s.roll_no, p.date, p.day, sub.name as subject, a.status
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        JOIN periods p ON a.period_id = p.id
        JOIN teacherSubjects ts ON p.teacher_subject_id = ts.id
        JOIN subjects sub ON ts.subject_id = sub.id
        WHERE ts.teacher_id = (SELECT id FROM teachers WHERE user_id=?)
        ORDER BY p.date DESC 
        """, (session["user_id"],)).fetchall()

    attendance = [{"name": row["name"], "roll_no": row["roll_no"], "date": row["date"], "day": DAY_MAP[f"{row["day"]}"], "subject": row["subject"], "status": row["status"]} for row in rows]

    return render_template("teacher_dashboard.html", attendance=attendance, classes=classes, timetables=timetables, today_periods=today_periods)


# ---------------- Upload Images for Encoding ----------------
# @app.route("/upload", methods=["GET", "POST"])
# def upload_images():
#     if session.get("role") != "teacher":
#         return redirect("/")
#     if request.method == "POST":
#         student_id = request.form["student_id"]
#         files = request.files.getlist("images")
#         student_folder = os.path.join(app.config["UPLOAD_FOLDER"], student_id)
#         os.makedirs(student_folder, exist_ok=True)

#         encodings = []
#         for file in files:
#             filename = secure_filename(file.filename)
#             filepath = os.path.join(student_folder, filename)
#             file.save(filepath)

#             # Generate embedding
#             try:
#                 embedding = DeepFace.represent(img_path=filepath, model_name="Facenet")[0]["embedding"]
#                 encodings.append(embedding)
#             except:
#                 print(f"Face not detected in {filename}")

#         if encodings:
#             db = get_db()
#             db.execute("INSERT INTO face_encodings (student_id, encoding) VALUES (?, ?)",
#                        (student_id, pickle.dumps(encodings)))
#             db.commit()
#             return f"Uploaded {len(encodings)} face images for student {student_id}"
#         return "No valid faces detected!"
#     return render_template("upload.html")


# ------------API to Get Today's Periods ------------
@app.route("/api/periods/today", methods=["GET"])
def get_periods_today():
    if session.get("role") == "student":
        db = get_db()
        today_periods = db.execute("""
            SELECT sub.name as subject_name, p.start_time, p.end_time, p.status FROM periods p
            JOIN teacherSubjects ts ON p.teacher_subject_id = ts.id
            JOIN subjects sub ON ts.subject_id = sub.id
            WHERE ts.class_id = ? AND p.date = ?
        """, (session["class_id"], datetime.now().strftime("%d/%m/%Y"))).fetchall()
        return jsonify([dict(row) for row in today_periods])
    
    elif session.get("role") == "teacher":
        db = get_db()
        today_periods = db.execute("""
            SELECT c.name as class_name, sub.name as subject_name, p.start_time, p.end_time, p.status FROM periods p
            JOIN teacherSubjects ts ON p.teacher_subject_id = ts.id
            JOIN subjects sub ON ts.subject_id = sub.id
            JOIN classes c ON ts.class_id = c.id
            WHERE ts.teacher_id = (SELECT id FROM teachers WHERE user_id=?) AND p.date = ?
        """, (session["user_id"], datetime.now().strftime("%d/%m/%Y"))).fetchall()
        return jsonify([dict(row) for row in today_periods])

# ---------------- API to Add Attendance ----------------
@app.route("/api/attendance", methods=["POST"])
def add_attendance():
    if not request.json:
        return jsonify({"error": "No data provided"}), 400

    student_id = request.json.get("student_id")
    status = request.json.get("status", "present")
    date = request.json.get("date")  # optional, default to today

    if not student_id:
        return jsonify({"error": "student_id is required"}), 400

    db = get_db()
    db.execute("INSERT INTO attendance (student_id, date, status) VALUES (?, ?, ?)",
               (student_id, date, status))
    db.commit()
    return jsonify({"message": "Attendance added successfully"}), 200


if __name__ == "__main__":
    scheduler.start()
    app.run(host="0.0.0.0", port=5000)
