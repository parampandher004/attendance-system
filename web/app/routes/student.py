from flask import Blueprint, render_template, session, jsonify, redirect, url_for, flash
from app.extensions import db
from app.models import Student, Period, Attendance, TeacherSubject, Subject, Class, Teacher, WeeklyPeriod
from app.utils.helpers import DAY_MAP, serialize_model, format_time
from app.services.drive import get_profile_image_bytes
import base64
from datetime import date
from sqlalchemy import func

student_bp = Blueprint('student', __name__)

@student_bp.before_request
def check_role():
    if session.get('role') != 'student':
        return redirect(url_for('auth.login'))

@student_bp.route('/dashboard')
def dashboard():
    user_id = session['user_id']
    student = Student.query.filter_by(user_id=user_id).first()
    
    if not student:
        flash("Student profile not found", "error")
        return redirect(url_for('auth.logout'))

    # 1. Fetch Profile Image
    img_data = get_profile_image_bytes(student.folder_id)
    encoded_img = base64.b64encode(img_data).decode() if img_data else None

    # 2. Fetch Subjects & Attendance Stats (Single optimized query)
    subjects_data = []
    if student.class_:
        # Get all stats in ONE query instead of N+1 queries
        subject_stats = db.session.query(
            TeacherSubject.id,
            Subject.name,
            Subject.code,
            Teacher.name.label("teacher_name"),
            func.count(Period.id).label("total_periods"),
            func.count(
                db.case(
                    (Attendance.status == 'present', 1),
                    else_=None
                )
            ).label("attended_count")
        ).join(Subject, TeacherSubject.subject_id == Subject.id)\
         .join(Teacher, TeacherSubject.teacher_id == Teacher.id)\
         .outerjoin(Period, TeacherSubject.id == Period.teacher_subject_id)\
         .outerjoin(Attendance, (Period.id == Attendance.period_id) & (Attendance.student_id == student.id))\
         .filter(TeacherSubject.class_id == student.class_id)\
         .group_by(TeacherSubject.id, Subject.name, Subject.code, Teacher.name)\
         .all()
        
        for ts_id, subject_name, subject_code, teacher_name, total_periods, attended_count in subject_stats:
            attended = attended_count or 0
            total = total_periods or 0
            percentage = round((attended / total * 100), 1) if total > 0 else 0
            
            subjects_data.append({
                "subject": subject_name,
                "subject_code": subject_code,
                "teacher": teacher_name,
                "total_classes": total,
                "attended": attended,
                "percentage": percentage
            })

    # 3. Fetch Recent Attendance History (with eager loading)
    recent_attendance = db.session.query(Period, Attendance.status, Subject.name, Subject.code, Period.day)\
        .outerjoin(Attendance, (Attendance.period_id == Period.id) & (Attendance.student_id == student.id))\
        .join(TeacherSubject, Period.teacher_subject_id == TeacherSubject.id)\
        .join(Subject, TeacherSubject.subject_id == Subject.id)\
        .filter(TeacherSubject.class_id == student.class_id)\
        .order_by(Period.date.desc()).limit(10).all()
        
    rows = db.session.query(
    Subject.name.label("subject_name"),
    WeeklyPeriod.day,
    WeeklyPeriod.start_time,
    WeeklyPeriod.end_time
    ).join(TeacherSubject, WeeklyPeriod.teacher_subject_id == TeacherSubject.id)\
    .join(Subject, TeacherSubject.subject_id == Subject.id)\
    .filter(TeacherSubject.class_id == student.class_id)\
    .all()

    timetables = [
        {
            "subject_name": row.subject_name,
            "day": DAY_MAP.get(str(row.day), "Unknown"),
            "start_time": format_time(row.start_time),
            "end_time": format_time(row.end_time)
        }
        for row in rows
    ]
        
    attendance_history = []
    
    for period, status, subject_name, subject_code, day in recent_attendance:
        attendance_history.append({
            "date": period.date.strftime("%d/%m/%Y"),
            "day": DAY_MAP.get(str(day), "Unknown"),
            "subject": subject_name,
            "subject_code": subject_code,
            "status": status if status else 'absent'
        })

    return render_template('student/dashboard.html', 
                           subjects=subjects_data, 
                           attendance=attendance_history, 
                           profile_picture=encoded_img, 
                           timetables=timetables)

@student_bp.route('/api/periods/today', methods=['GET'])
def get_periods_today():
    student = Student.query.filter_by(user_id=session['user_id']).first()
    today = date.today()
    
    periods = (
        db.session.query(
            Subject.name,
            Period.start_time,
            Period.end_time,
            Period.status
        )
        .select_from(TeacherSubject)  # <-- Required
        .join(Subject, Subject.id == TeacherSubject.subject_id)
        .join(Period, Period.teacher_subject_id == TeacherSubject.id)
        .filter(
            TeacherSubject.class_id == student.class_id,
            Period.date == today
        )
        .all()
    )
        
    return jsonify([
        {
            "subject_name": period.name,
            "start_time": format_time(period.start_time) if period.start_time else period.start_time,
            "end_time": format_time(period.end_time) if period.end_time else period.end_time,
            "status": period.status
        }
        for period in periods
    ])