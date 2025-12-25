import os
from embeddings_comparator import match_students
from flask import Flask, request, jsonify
import cv2
import numpy as np
from detector import detect_faces  
from utilities.image_path import get_temp_image_path
from drive_downloader import download_image
from embeddings_generator import generate_bulk_embeddings

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