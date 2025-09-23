import os, sqlite3, pickle, hashlib
from flask import Flask, jsonify, render_template, request, redirect, session
from werkzeug.utils import secure_filename
# from deepface import DeepFace

app = Flask(__name__)
app.secret_key = "secret_key"  # change in production
UPLOAD_FOLDER = "dataset/"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ---------------- DB Helper ----------------
def get_db():
    conn = sqlite3.connect("attendance.db")
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

# ---------------- Sign Up Page ----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]  # "student" or "teacher"
        name = request.form.get("name")  # Only for student
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
        db.close()
        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            if user["role"] == "student":
                return redirect("/student")
            else:
                return redirect("/teacher")
        else:
            return "Invalid credentials"
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
    attendance = db.execute("""
        SELECT date, status FROM attendance
        WHERE student_id=(SELECT id FROM students WHERE user_id=?)
    """, (session["user_id"],)).fetchall()
    return render_template("student_dashboard.html", attendance=attendance)

# ---------------- Teacher Dashboard ----------------
@app.route("/teacher")
def teacher_dashboard():
    if session.get("role") != "teacher":
        return redirect("/")
    db = get_db()
    attendance = db.execute("""
        SELECT s.name, s.roll_no, a.date, a.status
        FROM attendance a
        JOIN students s ON a.student_id = s.id
    """).fetchall()
    return render_template("teacher_dashboard.html", attendance=attendance)

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
    app.run(host="0.0.0.0", port=5000, debug=True)
