from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models import Student, Period, Attendance, TeacherSubject, Subject, StudentEmbedding, StudentImage
from functools import wraps
import os
from datetime import date
import traceback

public_bp = Blueprint('public', __name__)

# Get API key from environment
API_KEY = os.getenv('PUBLIC_API_KEY', 'default-insecure-key')

def require_api_key(f):
    """Decorator to validate API key in request headers"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({"error": "Missing API key"}), 401
        
        if api_key != API_KEY:
            return jsonify({"error": "Invalid API key"}), 403
        
        return f(*args, **kwargs)
    return decorated_function


@public_bp.route('/api/mark-attendance', methods=['POST'])
@require_api_key
def mark_attendance():
    """
    Mark attendance for a student in a period.
    
    Expected JSON:
    {
        "student_id": 1,
        "period_id": 1,
        "status": "present"  # or "absent", "late"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        student_id = data.get('student_id')
        period_id = data.get('period_id')
        status = data.get('status', 'present').lower()
        
        # Validate required fields
        if not student_id or not period_id:
            return jsonify({"error": "student_id and period_id are required"}), 400
        
        # Validate status
        valid_statuses = ['present', 'absent', 'late']
        if status not in valid_statuses:
            return jsonify({"error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}), 400
        
        # Check if student exists
        student = Student.query.get(student_id)
        if not student:
            return jsonify({"error": "Student not found"}), 404
        
        # Check if period exists
        period = Period.query.get(period_id)
        if not period:
            return jsonify({"error": "Period not found"}), 404
        
        # Check if attendance record already exists
        existing_attendance = Attendance.query.filter_by(
            student_id=student_id,
            period_id=period_id
        ).first()
        
        if existing_attendance:
            # Update existing record
            existing_attendance.status = status
        else:
            # Create new attendance record
            attendance = Attendance(
                student_id=student_id,
                period_id=period_id,
                status=status
            )
            db.session.add(attendance)
        
        db.session.commit()
        
        return jsonify({
            "message": "Attendance marked successfully",
            "student_id": student_id,
            "period_id": period_id,
            "status": status
        }), 201
    
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@public_bp.route('/api/get-period-by-date', methods=['GET'])
@require_api_key
def get_period_by_date():
    """
    Get periods for a specific class and date.
    
    Query parameters:
    - class_id: ID of the class
    - date: Date in YYYY-MM-DD format (optional, defaults to today)
    """
    try:
        class_id = request.args.get('class_id')
        date_str = request.args.get('date')
        
        if not class_id:
            return jsonify({"error": "class_id is required"}), 400
        
        # Parse date (default to today)
        if date_str:
            try:
                period_date = date.fromisoformat(date_str)
            except ValueError:
                return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
        else:
            period_date = date.today()
        
        # Get periods for the class on the given date
        periods = db.session.query(
            Period.id,
            Period.date,
            Period.day,
            Period.start_time,
            Period.end_time,
            Subject.name.label('subject_name'),
            Subject.code.label('subject_code')
        ).join(
            TeacherSubject, Period.teacher_subject_id == TeacherSubject.id
        ).join(
            Subject, TeacherSubject.subject_id == Subject.id
        ).filter(
            TeacherSubject.class_id == class_id,
            Period.date == period_date
        ).all()
        
        periods_data = [
            {
                "id": p.id,
                "date": p.date.isoformat(),
                "day": p.day,
                "subject_name": p.subject_name,
                "subject_code": p.subject_code,
                "start_time": p.start_time.isoformat() if p.start_time else None,
                "end_time": p.end_time.isoformat() if p.end_time else None
            }
            for p in periods
        ]
        
        return jsonify({
            "class_id": int(class_id),
            "date": period_date.isoformat(),
            "periods": periods_data
        }), 200
    
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@public_bp.route('/api/get-student-by-id', methods=['GET'])
@require_api_key
def get_student_by_id():
    """
    Get student information by ID.
    
    Query parameters:
    - student_id: ID of the student
    """
    try:
        student_id = request.args.get('student_id')
        
        if not student_id:
            return jsonify({"error": "student_id is required"}), 400
        
        student = Student.query.get(student_id)
        
        if not student:
            return jsonify({"error": "Student not found"}), 404
        
        return jsonify({
            "id": student.id,
            "name": student.name,
            "roll_no": student.roll_no,
            "class_id": student.class_id,
            "gender": student.gender
        }), 200
    
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@public_bp.route('/api/get-class-students', methods=['GET'])
@require_api_key
def get_class_students():
    """
    Get all students in a class.
    
    Query parameters:
    - class_id: ID of the class
    """
    try:
        class_id = request.args.get('class_id')
        
        if not class_id:
            return jsonify({"error": "class_id is required"}), 400
        
        students = Student.query.filter_by(class_id=class_id).all()
        
        students_data = [
            {
                "id": s.id,
                "name": s.name,
                "roll_no": s.roll_no,
                "gender": s.gender
            }
            for s in students
        ]
        
        return jsonify({
            "class_id": int(class_id),
            "students": students_data,
            "count": len(students_data)
        }), 200
    
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@public_bp.route('/api/get-attendance-status', methods=['GET'])
@require_api_key
def get_attendance_status():
    """
    Get attendance status for a student in a period.
    
    Query parameters:
    - student_id: ID of the student
    - period_id: ID of the period
    """
    try:
        student_id = request.args.get('student_id')
        period_id = request.args.get('period_id')
        
        if not student_id or not period_id:
            return jsonify({"error": "student_id and period_id are required"}), 400
        
        attendance = Attendance.query.filter_by(
            student_id=student_id,
            period_id=period_id
        ).first()
        
        if not attendance:
            return jsonify({
                "marked": False,
                "status": None
            }), 200
        
        return jsonify({
            "marked": True,
            "status": attendance.status
        }), 200
    
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@public_bp.route('/api/get-running-period', methods=['GET'])
@require_api_key
def get_running_period():
    try:
        class_id = request.args.get('class_id')
        
        # Start a single query with all necessary joins
        query = db.session.query(
            Period.id,
            Period.date,
            Period.day,
            Period.start_time,
            Period.end_time,
            Period.status,
            Subject.name.label('subject_name'),
            Subject.code.label('subject_code'),
            TeacherSubject.class_id
        ).join(
            TeacherSubject, Period.teacher_subject_id == TeacherSubject.id
        ).join(
            Subject, TeacherSubject.subject_id == Subject.id
        ).filter(Period.status == 'running') # Only fetch running periods

        # Apply class filter if provided
        if class_id:
            query = query.filter(TeacherSubject.class_id == class_id)
        
        periods = query.all()
        
        if not periods:
            return jsonify({
                "running": False,
                "message": "No running periods at this time",
                "periods": []
            }), 200
        
        periods_data = [
            {
                "id": p.id,
                "class_id": p.class_id,
                "date": p.date.isoformat() if p.date else None,
                "day": p.day,
                "subject_name": p.subject_name,
                "subject_code": p.subject_code,
                "start_time": p.start_time.isoformat() if p.start_time else None,
                "end_time": p.end_time.isoformat() if p.end_time else None,
                "status": p.status
            }
            for p in periods
        ]
        
        return jsonify({
            "running": True,
            "count": len(periods_data),
            "periods": periods_data
        }), 200
    
    except Exception as e:
        traceback.print_exc() # Check your console for the specific error details
        return jsonify({"error": str(e)}), 500


@public_bp.route('/api/update-period-status', methods=['POST'])
@require_api_key
def update_period_status():
    """
    Update the status of a period.
    Used by Raspberry Pi or teacher to change period status.
    
    Expected JSON:
    {
        "period_id": 1,
        "status": "running"  # or "scheduled", "completed", "cancelled"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        period_id = data.get('period_id')
        status = data.get('status', '').lower()
        
        if not period_id:
            return jsonify({"error": "period_id is required"}), 400
        
        valid_statuses = ['scheduled', 'running', 'completed', 'cancelled']
        if status not in valid_statuses:
            return jsonify({"error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}), 400
        
        period = Period.query.get(period_id)
        
        if not period:
            return jsonify({"error": "Period not found"}), 404
        
        old_status = period.status
        period.status = status
        db.session.commit()
        
        return jsonify({
            "message": "Period status updated successfully",
            "period_id": period_id,
            "old_status": old_status,
            "new_status": status
        }), 200
    
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@public_bp.route('/api/get-embeddings', methods=['GET'])
@require_api_key
def get_embeddings():
    """
    Get all student embeddings for face recognition.
    Used by face_service to load embeddings for student matching.
    
    Returns list of students with their embeddings.
    """
    try:
        # Get all students with their embeddings
        embeddings_data = []
        
        students = Student.query.all()
        
        for student in students:
            # Get all embeddings for this student across all their images
            student_embeddings = db.session.query(StudentEmbedding).join(
                StudentImage, StudentEmbedding.image_id == StudentImage.id
            ).filter(
                StudentImage.student_id == student.id
            ).all()
            
            # Aggregate embeddings for the student
            if student_embeddings:
                for emb in student_embeddings:
                    embeddings_data.append({
                        "student_id": student.id,
                        "student_name": student.name,
                        "roll_no": student.roll_no,
                        "embedding": emb.vector,  # PostgreSQL ARRAY will be converted to list
                        "embedding_id": emb.id
                    })
        
        return jsonify({
            "count": len(embeddings_data),
            "embeddings": embeddings_data
        }), 200
    
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@public_bp.route('/api/health', methods=['GET'])
@require_api_key
def health_check():
    """Health check endpoint for face service and Raspberry Pi"""
    return jsonify({
        "status": "healthy",
        "message": "Web service is running"
    }), 200
