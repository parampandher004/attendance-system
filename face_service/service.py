import os
from embeddings_comparator import match_students
from flask import Flask, request, jsonify
import cv2
import numpy as np
from detector import detect_faces  
from utilities.image_path import get_temp_image_path
from drive_downloader import download_image
from embeddings_generator import generate_bulk_embeddings
import requests
from functools import wraps

# Import load_embeddings but handle errors gracefully
try:
    import load_embeddings
except Exception as e:
    print(f"Warning: Failed to load embeddings on startup: {e}")
    # Create a mock load_embeddings module if import fails
    class MockLoadEmbeddings:
        embeddings = []
    load_embeddings = MockLoadEmbeddings()


app = Flask(__name__)

# Get API key from environment
API_KEY = os.getenv('PUBLIC_API_KEY', 'default-insecure-key')
WEB_SERVICE_URL = os.getenv('WEB_SERVICE_URL', 'http://web:5000')

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

@app.route('/process', methods=['POST'])
def process():
    file = request.files['image']
    npimg = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

    faces = detect_faces(img)
    
    embeddings = generate_bulk_embeddings(faces)
    
    student_embeddings = load_embeddings.embeddings
    
    predicted_students, similar_students_all = match_students(
        list(embeddings.values()),
        student_embeddings
    )
    
    return jsonify({
        "predicted_students": predicted_students,
        "similar_students_all": similar_students_all
    })


@app.route('/process_with_attendance', methods=['POST'])
@require_api_key
def process_with_attendance():
    """
    Process image from Raspberry Pi and mark attendance for identified students.
    
    Expects:
    - image: image file (multipart)
    - period_id: ID of the period
    - class_id: ID of the class
    - timestamp: timestamp of capture (optional)
    """
    try:
        # Check if image file is present
        if 'image' not in request.files:
            return jsonify({"error": "Missing image file"}), 400
        
        period_id = request.form.get('period_id')
        class_id = request.form.get('class_id')
        
        if not period_id or not class_id:
            return jsonify({"error": "period_id and class_id are required"}), 400
        
        # Decode image
        file = request.files['image']
        npimg = np.frombuffer(file.read(), np.uint8)
        img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
        
        if img is None:
            return jsonify({"error": "Failed to decode image"}), 400
        
        # Detect faces and generate embeddings
        faces = detect_faces(img)
        
        if not faces:
            return jsonify({
                "message": "No faces detected in image",
                "predicted_students": [],
                "marked_attendance": []
            }), 200
        
        embeddings = generate_bulk_embeddings(faces)
        
        student_embeddings = load_embeddings.embeddings
        
        if not student_embeddings:
            return jsonify({
                "message": "No reference embeddings loaded",
                "predicted_students": [],
                "marked_attendance": []
            }), 200
        
        predicted_students, similar_students_all = match_students(
            list(embeddings.values()),
            student_embeddings
        )
        
        # Mark attendance for predicted students
        marked_attendance = []
        headers = {"X-API-Key": API_KEY}
        
        for student_id in predicted_students:
            try:
                # Call web service API to mark attendance
                attendance_url = f"{WEB_SERVICE_URL}/public/api/mark-attendance"
                attendance_data = {
                    "student_id": int(student_id),
                    "period_id": int(period_id),
                    "status": "present"
                }
                
                response = requests.post(
                    attendance_url,
                    json=attendance_data,
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 201:
                    marked_attendance.append({
                        "student_id": student_id,
                        "status": "marked",
                        "period_id": int(period_id)
                    })
                    print(f"Attendance marked for student {student_id} in period {period_id}")
                else:
                    marked_attendance.append({
                        "student_id": student_id,
                        "status": "failed",
                        "error": response.text
                    })
                    print(f"Failed to mark attendance for student {student_id}: {response.text}")
            
            except Exception as e:
                marked_attendance.append({
                    "student_id": student_id,
                    "status": "error",
                    "error": str(e)
                })
                print(f"Error marking attendance for student {student_id}: {e}")
        
        return jsonify({
            "message": f"Processed image: {len(predicted_students)} students identified",
            "predicted_students": predicted_students,
            "marked_attendance": marked_attendance,
            "similar_students_all": similar_students_all
        }), 200
    
    except Exception as e:
        print(f"Error in process_with_attendance: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    

@app.route('/generate_embeddings', methods=['POST'])
def generate_embeddings():
    """Generate face embeddings from image file IDs"""
    try:
        data = request.json
        if not data or 'file_ids' not in data:
            return jsonify({"error": "Missing file_ids in request"}), 400
        
        image_paths = []
        embeddings_result = {}
        
        try:
            for file_id in data['file_ids']:
                try:
                    image_path = get_temp_image_path()
                    download_image(file_id, image_path)
                    image_paths.append({"image_path": image_path, "file_id": file_id})
                except Exception as e:
                    print(f"Error processing file {file_id}: {e}")
                    # Continue processing other files
            
            if image_paths:
                embeddings_result = generate_bulk_embeddings(image_paths)
        
        finally:
            # Clean up temp files
            for path_info in image_paths:
                try:
                    if os.path.exists(path_info["image_path"]):
                        os.remove(path_info["image_path"])
                except Exception as e:
                    print(f"Error cleaning up {path_info['image_path']}: {e}")
        
        return jsonify(embeddings_result)
    
    except Exception as e:
        print(f"Error in generate_embeddings: {e}")
        return jsonify({"error": str(e)}), 500
   

if __name__ == '__main__':
    print("Starting face_service on port 8000...")
    app.run(host="0.0.0.0", port=8000, debug=True)