import cv2
import numpy as np
import onnxruntime as ort
from insightface.app import FaceAnalysis


# -------------------------------------------
# Load InsightFace ArcFace Model (once)
# -------------------------------------------
def load_model():
    app = FaceAnalysis(name="buffalo_l")     # ArcFace 100k model
    app.prepare(ctx_id=0, det_size=(640, 640))
    return app


# ---------------------------------------------------
# Generate embedding for one image
# ---------------------------------------------------
def generate_embedding(model, image_path):
    img = cv2.imread(image_path)
    faces = model.get(img)

    if len(faces) == 0:
        print(f"No face found in {image_path}")
        return None

    return faces[0].embedding.tolist()


# ---------------------------------------------------
# BULK embedding generation
# ---------------------------------------------------
def generate_bulk_embeddings(image_paths):

    model = load_model()
    embeddings = {}

    for path in image_paths:
        print(f"Processing: {path.get('image_path')}")
        emb = generate_embedding(model, path.get("image_path"))
        if emb is not None:
            embeddings[path.get("file_id")] = emb

    return embeddings
