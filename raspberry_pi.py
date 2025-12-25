#!/usr/bin/env python3
"""
Raspberry Pi Attendance System - Image Capture and Processing
Works on both Windows and Raspberry Pi using USB webcam
"""

import os
import sys
import time
import requests
import cv2
from datetime import datetime
import json
import platform

# Configuration
WEB_SERVICE_URL = os.getenv('WEB_SERVICE_URL', 'http://localhost:5000')
FACE_SERVICE_URL = os.getenv('FACE_SERVICE_URL', 'http://localhost:8000')
PUBLIC_API_KEY = os.getenv('PUBLIC_API_KEY', 'default-insecure-key')
CLASS_ID = os.getenv('CLASS_ID', '1')  # Set class ID via environment variable
CAPTURE_INTERVAL = int(os.getenv('CAPTURE_INTERVAL', '300'))  # 5 minutes in seconds
POLL_INTERVAL = int(os.getenv('POLL_INTERVAL', '30'))  # Check for running period every 30 seconds

# Detect OS and camera index
IS_WINDOWS = platform.system() == 'Windows'
IS_RASPBERRY_PI = platform.machine().startswith('arm')

# USB camera index (0 for most USB webcams, adjust if needed)
CAMERA_INDEX = int(os.getenv('CAMERA_INDEX', '0'))


class AttendanceCapture:
    def __init__(self):
        self.running = False
        self.current_period_id = None
        self.camera = None
        self.last_capture_time = 0
        
    def log(self, message):
        """Print log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    def initialize_camera(self):
        """Initialize USB webcam"""
        try:
            self.camera = cv2.VideoCapture(CAMERA_INDEX)
            
            if not self.camera.isOpened():
                self.log(f"ERROR: Failed to open camera at index {CAMERA_INDEX}")
                return False
            
            # Set camera properties for better quality
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            
            self.log(f"Camera initialized successfully (Index: {CAMERA_INDEX})")
            return True
        except Exception as e:
            self.log(f"ERROR: Failed to initialize camera: {e}")
            return False
    
    def release_camera(self):
        """Release camera resources"""
        if self.camera:
            self.camera.release()
            self.log("Camera released")
    
    def check_running_period(self):
        """Check if there's a running period for the class"""
        try:
            headers = {"X-API-Key": PUBLIC_API_KEY}
            url = f"{WEB_SERVICE_URL}/public/api/get-running-period"
            params = {"class_id": CLASS_ID}
            
            response = requests.get(url, headers=headers, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("running") and data.get("periods"):
                period = data["periods"][0]  # Get first running period
                self.current_period_id = period["id"]
                subject = period.get("subject_name", "Unknown")
                self.log(f"Running period detected: {subject} (Period ID: {self.current_period_id})")
                return True
            else:
                if self.running:  # Only log if we were previously running
                    self.log("No running period detected")
                self.current_period_id = None
                return False
        
        except requests.exceptions.ConnectionError:
            self.log("WARNING: Cannot connect to web service")
            return False
        except Exception as e:
            self.log(f"ERROR: Failed to check running period: {e}")
            return False
    
    def capture_image(self):
        """Capture image from webcam"""
        try:
            if not self.camera or not self.camera.isOpened():
                self.log("ERROR: Camera not initialized")
                return None
            
            ret, frame = self.camera.read()
            
            if not ret:
                self.log("ERROR: Failed to capture frame")
                return None
            
            self.log("Image captured successfully")
            return frame
        except Exception as e:
            self.log(f"ERROR: Failed to capture image: {e}")
            return None
    
    def send_to_face_service(self, frame):
        """Send captured image to face service for processing"""
        try:
            if self.current_period_id is None:
                self.log("ERROR: No period ID available")
                return False
            
            # Encode frame to JPEG
            success, buffer = cv2.imencode('.jpg', frame)
            if not success:
                self.log("ERROR: Failed to encode image")
                return False
            
            # Prepare multipart form data
            files = {
                'image': ('captured_image.jpg', buffer.tobytes(), 'image/jpeg')
            }
            data = {
                'period_id': str(self.current_period_id),
                'class_id': str(CLASS_ID),
                'timestamp': datetime.now().isoformat()
            }
            
            headers = {"X-API-Key": PUBLIC_API_KEY}
            url = f"{FACE_SERVICE_URL}/process_with_attendance"
            
            self.log(f"Sending image to face service: {url}")
            response = requests.post(
                url,
                files=files,
                data=data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                predicted_count = len(result.get('predicted_students', []))
                self.log(f"Face service processed image: {predicted_count} students identified")
                return True
            else:
                self.log(f"ERROR: Face service returned status {response.status_code}: {response.text}")
                return False
        
        except requests.exceptions.ConnectionError:
            self.log("ERROR: Cannot connect to face service")
            return False
        except Exception as e:
            self.log(f"ERROR: Failed to send image to face service: {e}")
            return False
    
    def run(self):
        """Main run loop"""
        self.log("Starting Attendance Capture System")
        self.log(f"Web Service: {WEB_SERVICE_URL}")
        self.log(f"Face Service: {FACE_SERVICE_URL}")
        self.log(f"Class ID: {CLASS_ID}")
        self.log(f"Capture Interval: {CAPTURE_INTERVAL} seconds")
        self.log(f"Poll Interval: {POLL_INTERVAL} seconds")
        self.log(f"Platform: {'Windows' if IS_WINDOWS else 'Raspberry Pi' if IS_RASPBERRY_PI else 'Linux'}")
        
        if not self.initialize_camera():
            self.log("ERROR: Failed to initialize camera. Exiting.")
            return
        
        try:
            while True:
                # Check for running period
                period_running = self.check_running_period()
                
                if period_running:
                    if not self.running:
                        self.running = True
                        self.last_capture_time = 0  # Reset timer
                    
                    # Capture and send image at intervals
                    current_time = time.time()
                    if current_time - self.last_capture_time >= CAPTURE_INTERVAL:
                        frame = self.capture_image()
                        
                        if frame is not None:
                            self.send_to_face_service(frame)
                        
                        self.last_capture_time = current_time
                else:
                    if self.running:
                        self.running = False
                        self.log("Stopped image capture (period not running)")
                
                # Wait before next poll
                time.sleep(POLL_INTERVAL)
        
        except KeyboardInterrupt:
            self.log("\nShutting down...")
        except Exception as e:
            self.log(f"ERROR: Unexpected error in main loop: {e}")
        finally:
            self.release_camera()
            self.log("Attendance Capture System stopped")


if __name__ == '__main__':
    # Create and run the capture system
    system = AttendanceCapture()
    system.run()
