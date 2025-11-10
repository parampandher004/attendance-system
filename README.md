<h1 align="center">Face Recognition Attendance System</h1>

<p> A web-based attendance management system built to run on <b>Raspberry Pi</b>, integrating with an AI-powered face recognition module.  
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
- Stores data in a database (Postgres).

---

## 🛠️ Tech Stack

- **Backend**: Python (Flask)
- **Frontend**: HTML, CSS
- **Database**: Postgres
- **Hardware**: Raspberry Pi + Camera Module for face detection
- **AI Module**: Face recognition system

---

## ⚡ Installation & Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/parampandher004/attendance-system.git
   cd attendance-system
   ```
2. **create a directory models**
   ```bash
   mkdir models
   ```
3. **Move your model in models directory**

4. **Start Docker Containers**
   ```bash
   docker compose up -d
   ```
5. **Stop Docker Containers**
   ```bash
   docker compose down
   ```
   The server will start at [http://localhost:5000](http://localhost:5000).
