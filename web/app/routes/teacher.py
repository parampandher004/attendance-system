from flask import Blueprint, flash, render_template, session, jsonify, request, redirect, url_for
from app.extensions import db
from app.models import Teacher, Period, Attendance, Student, TeacherSubject, Class, WeeklyPeriod, Subject
from app.utils.helpers import format_time, serialize_model, DAY_MAP
from datetime import date, datetime
from sqlalchemy import desc, func, join

teacher_bp = Blueprint('teacher', __name__)

@teacher_bp.before_request
def check_role():
    if session.get('role') != 'teacher':
        return redirect(url_for('auth.login'))

@teacher_bp.route('/dashboard')
def dashboard():
    teacher = Teacher.query.filter_by(user_id=session['user_id']).first()
    
    # Get Classes
    my_classes = []
    for ts in teacher.teacher_subjects:
        my_classes.append({
            "id": ts.id, # This is the teacher_subject_id
            "class_name": ts.class_.name,
            "subject": ts.subject.name,
            "subject_code": ts.subject.code
        })
   
    weekly_rows = db.session.query(WeeklyPeriod, Class.name, Subject.name).\
            join(TeacherSubject, WeeklyPeriod.teacher_subject_id == TeacherSubject.id).\
            join(Class, TeacherSubject.class_id == Class.id).\
            join(Subject, TeacherSubject.subject_id == Subject.id).\
            filter(TeacherSubject.teacher_id == teacher.id).all()

    timetables = []
    for wp, class_name, subject_name in weekly_rows:
        timetables.append({
            "class_name": class_name,
            "subject_name": subject_name,
            "day": DAY_MAP.get(str(wp.day), "Unknown"),
            "start_time": format_time(wp.start_time),
            "end_time": format_time(wp.end_time)
        })
        
    distinct_classes_subq = (
    db.session.query(TeacherSubject.class_id)
    .filter(TeacherSubject.teacher_id == teacher.id)
    .distinct()
    .subquery()
    )
    
    total_students = (
    db.session.query(func.count(Student.id))
    .filter(Student.class_id.in_(distinct_classes_subq))
    .scalar()
    )
        
    results = db.session.query(
        Student.name,
        Student.roll_no,
        Period.date,
        Period.day,
        Subject.name,
        func.coalesce(Attendance.status, 'absent').label('status')
    ).select_from(Student)\
    .join(TeacherSubject, Student.class_id == TeacherSubject.class_id)\
    .join(Period, TeacherSubject.id == Period.teacher_subject_id)\
    .join(Subject, TeacherSubject.subject_id == Subject.id)\
    .outerjoin(Attendance, (Attendance.period_id == Period.id) & (Attendance.student_id == Student.id))\
    .filter(TeacherSubject.teacher_id == teacher.id)\
    .order_by(desc(Period.date)).all()

    attendance_data = []
    for row in results:
        attendance_data.append({
            "name": row[0],   # Student.name
            "roll_no": row[1],# Student.roll_no
            "date": row[2].strftime("%d/%m/%Y") if row[2] else "",
            "day": DAY_MAP.get(str(row[3]), "Unknown"),
            "subject": row[4],# Subject.name
            "status": row[5].capitalize() # The status string
        })
    
        
    return render_template('teacher/dashboard.html', classes=my_classes, total_students=total_students, timetables=timetables, attendance=attendance_data)

# --- APIs ---

@teacher_bp.route('/api/periods', methods=['POST'])
def schedule_period():
    data = request.get_json()
    teacher = Teacher.query.filter_by(user_id=session['user_id']).first()
    teacher_subject = TeacherSubject.query.filter_by(id=data['teacher_subject_id']).first()
    date = datetime.strptime(data['date'], "%d/%m/%Y").date()
    day = date.weekday()
    period = Period(date=date, day=day, start_time=data['start_time'], end_time=data['end_time'], teacher_subject=teacher_subject)
    db.session.add(period)
    db.session.commit()
    flash("Period scheduled successfully", "success")
    return jsonify({"message": "Period scheduled", "success": True})

@teacher_bp.route('/api/periods/today', methods=['GET'])
def get_today_schedule():
    teacher = Teacher.query.filter_by(user_id=session['user_id']).first()
    today = date.today()
    
    periods = Period.query.join(TeacherSubject).\
        filter(TeacherSubject.teacher_id == teacher.id, Period.date == today).\
        order_by(Period.start_time).all()
        
    data = []
    for p in periods:
        p_dict = serialize_model(p)
        p_dict['class_name'] = p.teacher_subject.class_.name
        p_dict['subject'] = p.teacher_subject.subject.name
        data.append(p_dict)
    return jsonify(data)

@teacher_bp.route('/api/periods/<int:period_id>/status', methods=['POST'])
def update_period_status(period_id):
    data = request.json
    period = Period.query.get_or_404(period_id)
    period.status = data.get('status')
    db.session.commit()
    return jsonify({"message": "Status updated"})

@teacher_bp.route('/api/periods/<int:period_id>/students', methods=['GET'])
def get_class_students(period_id):
    period = Period.query.get_or_404(period_id)
    class_students = period.teacher_subject.class_.students
    
    # Map existing attendance
    attendance_map = {a.student_id: a.status for a in period.attendance_records}
    
    data = []
    for s in class_students:
        data.append({
            "id": s.id,
            "roll_no": s.roll_no,
            "name": s.name,
            "status": attendance_map.get(s.id, None) 
        })
    return jsonify(data)

@teacher_bp.route('/api/classes/<int:ts_id>/students', methods=['GET'])
def get_teacher_subject_students(ts_id):
    """Get students in a teacher's class (by teacher_subject_id)"""
    teacher_subject = TeacherSubject.query.get_or_404(ts_id)
    class_students = teacher_subject.class_.students
    
    # Calculate attendance stats for each student
    data = []
    for s in class_students:
        # Count total periods and attended periods for this student in this class
        total_periods = db.session.query(func.count(Period.id)).\
            filter(Period.teacher_subject_id == ts_id).scalar() or 0
        attended_periods = db.session.query(func.count(Attendance.id)).\
            filter(Attendance.student_id == s.id, 
                   Attendance.period_id.in_(
                       db.session.query(Period.id).filter(Period.teacher_subject_id == ts_id)
                   ),
                   Attendance.status == 'present').scalar() or 0
        
        data.append({
            "id": s.id,
            "roll_no": s.roll_no,
            "name": s.name,
            "total_classes": total_periods,
            "attended": attended_periods,
            "percentage": (attended_periods / total_periods * 100) if total_periods > 0 else 0
        })
    return jsonify(data)

@teacher_bp.route('/api/attendance', methods=['POST'])
def mark_attendance():
    """Handles both Add and Remove via 'action' field"""
    data = request.json
    period_id = data.get('period_id')
    student_id = data.get('student_id')
    action = data.get('action') # 'present' or 'remove'
    
    if action == 'present':
        exists = Attendance.query.filter_by(period_id=period_id, student_id=student_id).first()
        if not exists:
            db.session.add(Attendance(period_id=period_id, student_id=student_id, status='present'))
    elif action == 'remove':
        Attendance.query.filter_by(period_id=period_id, student_id=student_id).delete()
        
    db.session.commit()
    return jsonify({"message": "Success"})