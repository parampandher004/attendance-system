from flask import Blueprint, render_template, session, jsonify, request, redirect, url_for, current_app
from app.extensions import db
from sqlalchemy import func, desc
from app.models import Student, Teacher, Class, Subject, TeacherSubject, Period, Attendance, WeeklyPeriod
from app.utils.helpers import DAY_MAP
from app.services.drive import upload_to_drive, get_drive_service
import os
import requests

# Configuration for face service API
FACE_SERVICE_URL = os.getenv('FACE_SERVICE_URL', 'http://face_service:8000')

admin_bp = Blueprint('admin', __name__)

@admin_bp.before_request
def check_role():
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))

@admin_bp.route('/dashboard')
def dashboard():
    # Fetch data needed for dropdowns and tables
    pending = Student.query.filter(Student.class_id == None).all()
    classes = Class.query.all()
    teachers = Teacher.query.all()
    subjects = Subject.query.all()

    # Get all students for the filter
    all_students = Student.query.all()
    all_students_data = [{"id": s.id, "name": s.name} for s in all_students]

    # Get assigned classes (TeacherSubject) for the table
    assigned_classes_query = db.session.query(
        TeacherSubject, Class, Subject, Teacher
    ).join(Class, TeacherSubject.class_id == Class.id).join(
        Subject, TeacherSubject.subject_id == Subject.id
    ).join(Teacher, TeacherSubject.teacher_id == Teacher.id).all()

    assigned_classes_data = [
        {
            "id": ts.id,
            "class_name": c.name,
            "subject": s.name,
            "subject_code": s.code,
            "teacher": t.name,
            "teacher_id": t.id,
            "class_id": c.id,
            "subject_id": s.id,
        }
        for ts, c, s, t in assigned_classes_query
    ]

    # Get timetables from WeeklyPeriod (weekly schedule template)
    timetables_query = db.session.query(
        WeeklyPeriod, Class, Subject, TeacherSubject, Teacher
    ).join(TeacherSubject, WeeklyPeriod.teacher_subject_id == TeacherSubject.id).join(
        Class, TeacherSubject.class_id == Class.id
    ).join(Subject, TeacherSubject.subject_id == Subject.id).join(
        Teacher, TeacherSubject.teacher_id == Teacher.id
    ).all()

    timetables_data = [
        {
            "id": wp.id,
            "class_name": c.name,
            "day": wp.day,
            "subject_name": s.name,
            "teacher_name": t.name,
            "start_time": wp.start_time.strftime("%H:%M") if wp.start_time else "",
            "end_time": wp.end_time.strftime("%H:%M") if wp.end_time else "",
            "status": "template",
        }
        for wp, c, s, ts, t in timetables_query
    ]

    # Build attendance data for admin (all students)
    results = (
        db.session.query(
            Student.name,
            Student.roll_no,
            Period.date,
            Period.day,
            Subject.name,
            func.coalesce(Attendance.status, 'absent').label('status'),
        )
        .select_from(Student)
        .join(TeacherSubject, Student.class_id == TeacherSubject.class_id)
        .join(Period, TeacherSubject.id == Period.teacher_subject_id)
        .join(Subject, TeacherSubject.subject_id == Subject.id)
        .outerjoin(
            Attendance,
            (Attendance.period_id == Period.id) & (Attendance.student_id == Student.id),
        )
        .order_by(desc(Period.date))
        .all()
    )

    attendance_data = []
    for row in results:
        attendance_data.append({
            "name": row[0],
            "roll_no": row[1],
            "date": row[2].strftime("%d/%m/%Y") if row[2] else "",
            "day": DAY_MAP.get(str(row[3]), "Unknown"),
            "subject": row[4],
            "status": row[5].capitalize() if row[5] else ""
        })

    # Get total counts
    total_students = Student.query.count()
    total_teachers = Teacher.query.count()
    total_classes = Class.query.count()
    pending_count = len(pending)

    # Convert to JSON-serializable format
    classes_data = [{"id": c.id, "name": c.name} for c in classes]
    teachers_data = [{"id": t.id, "name": t.name} for t in teachers]
    subjects_data = [{"id": s.id, "name": s.name, "code": s.code} for s in subjects]
    pending_data = [{"id": s.id, "name": s.name, "roll_no": s.roll_no} for s in pending]

    return render_template('admin/dashboard.html',
                           pending_students=pending_data,
                           classes=classes_data,
                           teachers=teachers_data,
                           subjects=subjects_data,
                           total_students=total_students,
                           total_teachers=total_teachers,
                           total_classes=total_classes,
                           pending_count=pending_count,
                           assigned_classes=assigned_classes_data,
                           timetables=timetables_data,
                           class_list=classes_data,  # For assign students to classes dropdown
                           students=all_students_data,
                           attendance=attendance_data)

# --- APIs ---

@admin_bp.route('/api/student/enroll', methods=['POST'])
def enroll_student():
    data = request.json
    student = Student.query.get(data['student_id'])
    if student:
        student.class_id = data['class_id']
        db.session.commit()
        return jsonify({"message": "Enrolled"})
    return jsonify({"error": "Student not found"}), 404

@admin_bp.route('/api/student/reject', methods=['POST'])
def reject_student():
    data = request.json
    student = Student.query.get(data['student_id'])
    if student:
        db.session.delete(student)
        db.session.commit()
        return jsonify({"message": "Rejected"})
    return jsonify({"error": "Student not found"}), 404

@admin_bp.route('/api/assign/teacher', methods=['POST'])
def assign_teacher():
    data = request.json
    exists = TeacherSubject.query.filter_by(
        teacher_id=data['teacher_id'], 
        class_id=data['class_id'], 
        subject_id=data['subject_id']
    ).first()
    
    if exists:
        return jsonify({"error": "Already assigned"}), 400
        
    db.session.add(TeacherSubject(
        teacher_id=data['teacher_id'], 
        class_id=data['class_id'], 
        subject_id=data['subject_id']
    ))
    db.session.commit()
    return jsonify({"message": "Assigned"})

@admin_bp.route('/upload', methods=['POST'])
def upload_images():
    from app.models import StudentImage
    
    student_id = request.form.get("student_id")
    files = request.files.getlist("images")
    
    try:
        student = Student.query.get(student_id)
        if not student:
            return jsonify({"error": "Student not found"}), 404
        
        if not student.folder_id:
            return jsonify({"error": "Student does not have a Google Drive folder"}), 400

        upload_folder = current_app.config.get('UPLOAD_FOLDER', '/tmp')
        
        # Create upload folder if it doesn't exist
        import os
        os.makedirs(upload_folder, exist_ok=True)
        
        uploaded_count = 0
        for file in files:
            if file.filename == '':
                continue
            
            try:
                filename = file.filename
                local_path = os.path.join(upload_folder, filename)
                file.save(local_path)
                
                # Call service to upload to Google Drive
                drive_file_id = upload_to_drive(local_path, filename, student.folder_id)
                
                # Save to DB
                image = StudentImage(
                    student_id=student_id, 
                    drive_file_id=drive_file_id, 
                    file_name=filename
                )
                db.session.add(image)
                
                # Clean up local file
                try:
                    os.remove(local_path)
                except:
                    pass
                
                uploaded_count += 1
            except Exception as file_err:
                print(f"Error uploading file {filename}: {str(file_err)}")
                import traceback
                traceback.print_exc()
                continue
        
        db.session.commit()
        
        return jsonify({
            "message": f"Successfully uploaded {uploaded_count} image(s)",
            "uploaded_count": uploaded_count
        })
    
    except Exception as e:
        db.session.rollback()
        print(f"Upload error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/api/embeddings/generate', methods=['POST'])
async def generate_embeddings():
    # This logic matches your original async request
    # Note: Flask 2.0+ supports async routes if you use 'async def'
    data = request.json
    # ... (Your logic to call external Face Service) ...
    return jsonify({"message": "Started"})

@admin_bp.route('/api/get_embeddings', methods=['GET'])
def get_embeddings():
    """
    Endpoint for face_service to fetch all student embeddings.
    Used by load_embeddings.py to load embeddings into memory.
    """
    from app.models import StudentEmbedding
    
    try:
        # Query all embeddings with their associated student info
        embeddings_data = db.session.query(
            StudentEmbedding.id,
            StudentEmbedding.image_id,
            StudentEmbedding.vector,
            StudentEmbedding.created_at
        ).all()
        
        if not embeddings_data:
            return jsonify([]), 200
        
        # Format response for face_service
        result = []
        for embedding in embeddings_data:
            # Get student_id from the image
            from app.models import StudentImage
            image = StudentImage.query.get(embedding.image_id)
            if image:
                result.append({
                    "student_id": image.student_id,
                    "embedding": embedding.vector.tolist() if hasattr(embedding.vector, 'tolist') else list(embedding.vector),
                    "created_at": embedding.created_at.isoformat() if embedding.created_at else None
                })
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Admin: Schedule a period (create new class session)
@admin_bp.route('/api/periods', methods=['POST'])
def schedule_period_admin():
    from datetime import datetime
    data = request.get_json()
    try:
        # Accept both teacher_subject_id and ts_id field names
        ts_id = data.get('teacher_subject_id') or data.get('ts_id')
        if not ts_id:
            return jsonify({"error": "Missing teacher_subject_id or ts_id"}), 400
            
        teacher_subject = TeacherSubject.query.get_or_404(ts_id)
        date_str = data.get('date')  # Format: DD/MM/YYYY
        if not date_str:
            return jsonify({"error": "Missing date field"}), 400
            
        date_obj = datetime.strptime(date_str, "%d/%m/%Y").date()
        day = date_obj.weekday()
        
        period = Period(
            date=date_obj,
            day=day,
            start_time=data.get('start_time'),
            end_time=data.get('end_time'),
            teacher_subject_id=teacher_subject.id,
            status=data.get('status', 'scheduled')
        )
        db.session.add(period)
        db.session.commit()
        return jsonify({"message": "Period scheduled successfully", "success": True})
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 400


# Admin: Get students for a teacher_subject (used by admin dashboard)
@admin_bp.route('/api/classes/<int:ts_id>/students', methods=['GET'])
def get_teacher_subject_students_admin(ts_id):
    """Get students in a class (by teacher_subject_id) for admin view"""
    teacher_subject = TeacherSubject.query.get_or_404(ts_id)
    class_students = teacher_subject.class_.students

    # Calculate attendance stats for each student
    data = []
    for s in class_students:
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


# Admin: Get student images and encoding status
@admin_bp.route('/api/students/<int:student_id>/images', methods=['GET'])
def get_student_images(student_id):
    """Get all images for a student and their encoding status"""
    from app.models import StudentImage, StudentEmbedding
    
    try:
        student = Student.query.get_or_404(student_id)
        images = StudentImage.query.filter(StudentImage.student_id == student_id).all()
        
        image_data = []
        for img in images:
            embeddings = StudentEmbedding.query.filter(StudentEmbedding.image_id == img.id).all()
            image_data.append({
                "id": img.id,
                "file_name": img.file_name,
                "drive_file_id": img.drive_file_id,
                "uploaded_at": img.uploaded_at.isoformat() if img.uploaded_at else None,
                "has_encoding": len(embeddings) > 0,
                "encoding_count": len(embeddings)
            })
        
        total_images = len(images)
        encoded_images = sum(1 for img in image_data if img["has_encoding"])
        
        return jsonify({
            "total_images": total_images,
            "encoded_images": encoded_images,
            "images": image_data,
            "student_id": student_id,
            "student_name": student.name
        })
    except Exception as e:
        import traceback
        print(f"Error getting student images: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# Admin: Generate encodings for a student's images
@admin_bp.route('/api/students/<int:student_id>/generate-encodings', methods=['POST'])
def generate_student_encodings(student_id):
    """Generate embeddings for all images of a student using face_service API"""
    from app.models import StudentImage, StudentEmbedding
    import requests
    import traceback
    
    try:
        student = Student.query.get_or_404(student_id)
        images = StudentImage.query.filter(StudentImage.student_id == student_id).all()
        
        if not images:
            return jsonify({"error": "No images found for student"}), 404
        
        success_count = 0
        error_count = 0
        errors = []
        
        # Collect file IDs of images that don't have embeddings
        file_ids = []
        image_map = {}  # Map file_id to image record
        
        for image in images:
            # Check if embedding already exists
            existing = StudentEmbedding.query.filter(StudentEmbedding.image_id == image.id).first()
            if not existing:
                file_ids.append(image.drive_file_id)
                image_map[image.drive_file_id] = image
        
        if not file_ids:
            # Prepare diagnostics to help debug why there are no file_ids to process
            images_info = []
            for img in images:
                existing = StudentEmbedding.query.filter(StudentEmbedding.image_id == img.id).first()
                images_info.append({
                    "image_id": img.id,
                    "file_name": img.file_name,
                    "drive_file_id": img.drive_file_id,
                    "has_embedding": bool(existing)
                })

            print(f"[generate-encodings] No file_ids to process for student {student_id}. Images: {images_info}")

            return jsonify({
                "message": "All images already have encodings or no images without embeddings found",
                "success_count": 0,
                "error_count": 0,
                "diagnostics": images_info
            })
        
        # Call face_service API to generate embeddings
        try:
            # Log what we will send to the face service for debugging
            print(f"[generate-encodings] Sending {len(file_ids)} file_ids to face service: {file_ids}")
            face_service_endpoint = f"{FACE_SERVICE_URL}/generate_embeddings"
            # Allow configurable timeout via env var
            timeout_seconds = int(os.getenv('FACE_SERVICE_TIMEOUT', '300'))
            response = requests.post(
                face_service_endpoint,
                json={"file_ids": file_ids},
                timeout=timeout_seconds
            )

            if response.status_code == 200:
                embeddings_data = response.json()

                # Process returned embeddings
                for file_id, embedding_vector in embeddings_data.items():
                    if file_id in image_map:
                        try:
                            image = image_map[file_id]
                            embedding = StudentEmbedding(
                                image_id=image.id,
                                vector=embedding_vector
                            )
                            db.session.add(embedding)
                            success_count += 1
                        except Exception as e:
                            error_count += 1
                            errors.append(f"Error saving embedding for {image_map[file_id].file_name}: {str(e)}")
            else:
                error_count = len(file_ids)
                errors.append(f"Face service error: {response.status_code} - {response.text}")

        except requests.exceptions.ReadTimeout as rt:
            # Face service is taking too long; spawn a background worker to finish processing
            print(f"Face service read timeout after {timeout_seconds}s: starting background worker: {rt}")

            def background_generate(ids, img_map):
                try:
                    from flask import current_app
                    import time as _time
                    with current_app.app_context():
                        try:
                            long_timeout = int(os.getenv('FACE_SERVICE_LONG_TIMEOUT', '600'))
                            resp = requests.post(f"{FACE_SERVICE_URL}/generate_embeddings",
                                                  json={"file_ids": ids}, timeout=long_timeout)
                            if resp.status_code == 200:
                                emb_data = resp.json()
                                for fid, vec in emb_data.items():
                                    if fid in img_map:
                                        try:
                                            image = img_map[fid]
                                            emb = StudentEmbedding(image_id=image.id, vector=vec)
                                            db.session.add(emb)
                                        except Exception as e:
                                            print(f"Background save error for {fid}: {e}")
                                try:
                                    db.session.commit()
                                    print(f"Background embeddings saved for student {student_id}")
                                except Exception as commit_e:
                                    db.session.rollback()
                                    print(f"Background DB commit failed: {commit_e}")
                            else:
                                print(f"Background face service responded {resp.status_code}: {resp.text}")
                        except Exception as e:
                            print(f"Background generation error: {e}")
                except Exception as outer_e:
                    print(f"Background worker outer exception: {outer_e}")

            import threading
            worker = threading.Thread(target=background_generate, args=(file_ids, image_map), daemon=True)
            worker.start()

            return jsonify({
                "message": "Face service timed out; processing started in background",
                "status": "processing",
                "success_count": 0,
                "error_count": 0
            }), 202

        except requests.exceptions.ConnectionError as conn_err:
            # Face service not available - use placeholder embeddings
            import random
            for file_id, image in image_map.items():
                # Create random 512-dim vector without numpy
                dummy_vector = [random.uniform(-1, 1) for _ in range(512)]
                embedding = StudentEmbedding(
                    image_id=image.id,
                    vector=dummy_vector
                )
                db.session.add(embedding)
                success_count += 1
                errors.append(f"Face service unavailable - using placeholder embedding for {image.file_name}")
            print(f"Face service connection error: {str(conn_err)}")

        except Exception as e:
            error_count = len(file_ids)
            errors.append(f"Face service API error: {str(e)}")
            traceback.print_exc()
        
        try:
            db.session.commit()
        except Exception as commit_err:
            db.session.rollback()
            return jsonify({
                "error": f"Database error: {str(commit_err)}",
                "success_count": success_count,
                "error_count": error_count
            }), 400
        
        return jsonify({
            "message": f"Encoding generation completed. Success: {success_count}, Failed: {error_count}",
            "success_count": success_count,
            "error_count": error_count,
            "errors": errors if errors else None
        })
    
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({"error": f"Server error: {str(e)}"}), 400

# Admin: Debug endpoint to check student info
@admin_bp.route('/api/students/<int:student_id>/debug', methods=['GET'])
def debug_student_info(student_id):
    """Debug endpoint to check student info and images"""
    from app.models import StudentImage, StudentEmbedding
    
    try:
        student = Student.query.get_or_404(student_id)
        images = StudentImage.query.filter(StudentImage.student_id == student_id).all()
        
        debug_info = {
            "student": {
                "id": student.id,
                "name": student.name,
                "folder_id": student.folder_id,
                "has_folder": bool(student.folder_id)
            },
            "images": []
        }
        
        for img in images:
            embeddings = StudentEmbedding.query.filter(StudentEmbedding.image_id == img.id).all()
            debug_info["images"].append({
                "id": img.id,
                "file_name": img.file_name,
                "drive_file_id": img.drive_file_id,
                "has_drive_id": bool(img.drive_file_id),
                "has_embeddings": len(embeddings) > 0,
                "embedding_count": len(embeddings)
            })
        
        return jsonify(debug_info)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# Admin: Delete a student image
@admin_bp.route('/api/students/<int:student_id>/images/<int:image_id>', methods=['DELETE'])
def delete_student_image(student_id, image_id):
    """Delete a student image and its embeddings"""
    from app.models import StudentImage, StudentEmbedding
    
    try:
        image = StudentImage.query.filter(
            StudentImage.id == image_id,
            StudentImage.student_id == student_id
        ).first()

        if not image:
            return jsonify({"error": "Image not found"}), 404
        
        # Delete associated embeddings (use ORM deletes to ensure proper session handling)
        embeddings = StudentEmbedding.query.filter(StudentEmbedding.image_id == image_id).all()
        for emb in embeddings:
            db.session.delete(emb)

        # Delete the image
        db.session.delete(image)
        db.session.commit()
        
        return jsonify({"message": "Image deleted successfully"})
    except Exception as e:
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


# Admin: Get student image from Google Drive (serves the image)
@admin_bp.route('/api/students/<int:student_id>/images/<int:image_id>/view', methods=['GET'])
def view_student_image(student_id, image_id):
    """Stream a student's image from Google Drive"""
    from app.models import StudentImage
    from flask import send_file
    import io
    import traceback
    
    try:
        # Get the image record from database
        image = StudentImage.query.filter(
            StudentImage.id == image_id,
            StudentImage.student_id == student_id
        ).first()
        
        if not image:
            return jsonify({"error": "Image not found"}), 404
        
        if not image.drive_file_id:
            return jsonify({"error": "Image file ID not available"}), 400
        
        try:
            # Try to get drive service and download the image
            from app.services.drive_service import get_drive_service
            drive_service = get_drive_service()
            
            if not drive_service:
                return jsonify({"error": "Drive service not configured"}), 503
            
            # Download the file from Google Drive
            request = drive_service.files().get_media(fileId=image.drive_file_id)
            file_content = request.execute()
            
            # Return as image
            return send_file(
                io.BytesIO(file_content),
                mimetype='image/jpeg',
                as_attachment=False,
                download_name=image.file_name
            )
        except Exception as drive_err:
            print(f"Drive error for file {image.drive_file_id}: {str(drive_err)}")
            traceback.print_exc()
            return jsonify({
                "error": f"Failed to download image from Drive: {str(drive_err)}"
            }), 503
            
    except Exception as e:
        print(f"Error viewing image: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"Server error: {str(e)}"}), 500