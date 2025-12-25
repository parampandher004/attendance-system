import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = "secret_key" # Change in production
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = "temp_uploads"
    FACE_SERVICE_URL = os.getenv("FACE_SERVICE_URL")
    
    # Ensure upload folder exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)