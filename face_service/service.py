import os
from embeddings_comparator import match_students
from flask import Flask, request, jsonify
import cv2
import numpy as np
from detector import detect_faces  
from utilities.image_path import get_temp_image_path
from drive_downloader import download_image
from embeddings_generator import generate_bulk_embeddings
import load_embeddings


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
    data = request.json
    image_paths = []
    
    for file_id in data['file_ids']:
        image_path = get_temp_image_path()
        download_image(file_id, image_path)
        image_paths.append({"image_path": image_path, "file_id": file_id})
    
    embeddings = generate_bulk_embeddings(image_paths)
    
    for path in image_paths:
        os.remove(path["image_path"])
    
    return jsonify(embeddings)
   

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000)