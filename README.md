<h1 align="center">Face Recognition Attendance System (Web Interface)</h1>

<p> A web-based attendance management system built to run on **Raspberry Pi**, integrating with an AI-powered face recognition module.  
This system records attendance automatically through facial recognition, while also providing a web interface for <b> students</b> and <b>teachers</b> to view and manage attendance data. </p>

## 🚀 Features

### 👩‍🎓 For Students

- View daily attendance records.
- Check subject-wise attendance.
- Calculate and view overall attendance percentage.

### 👩‍🏫 For Teachers

- View attendance of students in each subject.
- Manually add or edit attendance when required.
- Manage subject/period information for accurate tracking.

### 🔹 General

- Lightweight Flask-based web interface.
- Stores data in a database (SQLite/MySQL/Postgres — depending on configuration).
- Designed to run efficiently on Raspberry Pi.

---

## 🛠️ Tech Stack

- **Backend**: Python (Flask)
- **Frontend**: HTML, CSS (optionally Bootstrap/Tailwind)
- **Database**: SQLite (default), can be extended to MySQL/Postgres
- **Hardware**: Raspberry Pi + Camera Module for face detection
- **AI Module**: Face recognition system (integrated separately)

---

## ⚡ Installation & Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/parampandher004/attendance-system.git
   cd attendance-system
   ```
2. **Create and activate a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # On Linux/Mac
   venv\Scripts\activate      # On Windows
   ```
3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
4. **Run the Flask app**
   ```bash
   python app.py
   ```
   The server will start at [http://localhost:5000](http://localhost:5000).
