import requests
import os

# Configuration
FACE_SERVICE_URL = "http://localhost:8000/process_with_attendance"
API_KEY = "default-insecure-key"  # Must match PUBLIC_API_KEY in your .env or docker-compose.yml
IMAGE_PATH = "./student_image.jpg"

# Attendance metadata
PERIOD_ID = "17"  # The ID of the currently active/scheduled period
CLASS_ID = "1"   # The ID of the class for this period

def upload_and_mark_attendance():
    if not os.path.exists(IMAGE_PATH):
        print(f"Error: Image file not found at {IMAGE_PATH}")
        return

    # Headers for authentication
    headers = {
        "X-API-Key": API_KEY
    }

    # Data for the attendance marking
    data = {
        "period_id": PERIOD_ID,
        "class_id": CLASS_ID
    }

    # File to upload
    files = {
        "image": open(IMAGE_PATH, "rb")
    }

    try:
        print(f"Uploading {IMAGE_PATH} to face service...")
        response = requests.post(
            FACE_SERVICE_URL, 
            headers=headers, 
            data=data, 
            files=files,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            print("\n--- Success ---")
            print(f"Message: {result.get('message')}")
            print(f"Identified Student IDs: {result.get('predicted_students')}")
            
            print("\nAttendance Details:")
            for record in result.get('marked_attendance', []):
                status = record.get('status')
                s_id = record.get('student_id')
                if status == "marked":
                    print(f"  - Student {s_id}: Marked PRESENT")
                else:
                    print(f"  - Student {s_id}: Failed to mark ({record.get('error')})")
        else:
            print(f"Error: Server returned status code {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        files["image"].close()

if __name__ == "__main__":
    upload_and_mark_attendance()