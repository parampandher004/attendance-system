import uuid
import os

def get_temp_image_path():
    temp_folder = "temp_images"
    os.makedirs(temp_folder, exist_ok=True)
    return os.path.join(temp_folder, f"{uuid.uuid4().hex}.jpg")
