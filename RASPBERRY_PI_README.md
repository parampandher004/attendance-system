# Raspberry Pi Attendance System

Automated attendance system that captures images periodically during running classes and marks attendance using face recognition.

## Features

- ✅ Works on both **Raspberry Pi** and **Windows**
- ✅ Uses USB webcam for image capture
- ✅ Polls web service every 30 seconds to check for running periods
- ✅ Captures images every 5 minutes when a class is running
- ✅ Sends images to face_service for student identification
- ✅ Automatically marks attendance for identified students
- ✅ API key authentication for secure communication
- ✅ Comprehensive logging with timestamps

## Requirements

### Raspberry Pi

```bash
pip install opencv-python requests numpy
```

### Windows

```bash
pip install opencv-python requests numpy
```

## Setup

### 1. Environment Variables

Set these environment variables before running:

```bash
# Web service configuration
export WEB_SERVICE_URL=http://localhost:5000
export FACE_SERVICE_URL=http://localhost:8000
export PUBLIC_API_KEY=your-secret-api-key

# Attendance capture configuration
export CLASS_ID=1                    # ID of the class to track
export CAPTURE_INTERVAL=300          # Capture every 5 minutes (300 seconds)
export POLL_INTERVAL=30              # Check for running period every 30 seconds
export CAMERA_INDEX=0                # USB camera index (0 for first camera)
```

### 2. Configure for Your Environment

#### Windows

```batch
set WEB_SERVICE_URL=http://127.0.0.1:5000
set FACE_SERVICE_URL=http://127.0.0.1:8000
set PUBLIC_API_KEY=your-secret-key
set CLASS_ID=1
python raspberry_pi.py
```

#### Raspberry Pi

```bash
export WEB_SERVICE_URL=http://web:5000  # Docker service name
export FACE_SERVICE_URL=http://face_service:8000
export PUBLIC_API_KEY=your-secret-key
export CLASS_ID=1
python3 raspberry_pi.py
```

### 3. USB Camera Detection

On Raspberry Pi with USB webcam, find the camera index:

```bash
# List all video devices
ls -la /dev/video*

# Test camera capture
python3 -c "import cv2; cap = cv2.VideoCapture(0); print(cap.isOpened())"
```

If using `/dev/video1` instead of `/dev/video0`:

```bash
export CAMERA_INDEX=1
python3 raspberry_pi.py
```

## How It Works

### Flow Diagram

```
┌─────────────────────────────────────────┐
│   Raspberry Pi Script (raspberry_pi.py) │
└────────────────┬────────────────────────┘
                 │
         Every 30 seconds
                 ▼
    ┌──────────────────────────┐
    │ Check running period API │ (/public/api/get-running-period)
    └────────┬─────────────────┘
             │
     ┌───────┴────────┐
     │                │
  Period        No Period
  Running       Running
     │                │
     ▼                ▼
 Every 5 min    Wait for period
 Capture Image
     │
     ▼
 Send to Face Service
     │
     ▼
┌────────────────────────────────┐
│ Face Service Processing        │
│ (/process_with_attendance)     │
│ 1. Detect faces               │
│ 2. Identify students          │
│ 3. Mark attendance via API    │
└────────────────────────────────┘
```

### Step-by-Step Process

1. **Check Running Period**: Polls `/public/api/get-running-period` to see if a class is currently running
2. **Capture Image**: If running, captures an image from USB webcam every 5 minutes
3. **Send to Face Service**: Sends the captured image to face_service with the period_id
4. **Process Image**: Face service detects faces and identifies students using embeddings
5. **Mark Attendance**: For each identified student, calls `/public/api/mark-attendance` to record attendance

## Log Output Example

```
[2025-12-25 09:30:00] Starting Attendance Capture System
[2025-12-25 09:30:00] Web Service: http://localhost:5000
[2025-12-25 09:30:00] Face Service: http://localhost:8000
[2025-12-25 09:30:00] Class ID: 1
[2025-12-25 09:30:00] Capture Interval: 300 seconds
[2025-12-25 09:30:00] Platform: Windows
[2025-12-25 09:30:00] Camera initialized successfully (Index: 0)

[2025-12-25 09:30:15] Running period detected: Mathematics (Period ID: 5)
[2025-12-25 09:35:00] Image captured successfully
[2025-12-25 09:35:02] Sending image to face service: http://localhost:8000/process_with_attendance
[2025-12-25 09:35:05] Face service processed image: 2 students identified

[2025-12-25 09:40:00] Image captured successfully
[2025-12-25 09:40:05] Face service processed image: 3 students identified
```

## API Endpoints Used

### 1. Check Running Period

```http
GET /public/api/get-running-period?class_id=1
Headers: X-API-Key: your-secret-key

Response:
{
  "running": true,
  "count": 1,
  "periods": [{
    "id": 5,
    "class_id": 1,
    "subject_name": "Mathematics",
    "status": "running"
  }]
}
```

### 2. Process Image with Attendance

```http
POST /process_with_attendance
Headers: X-API-Key: your-secret-key
Content-Type: multipart/form-data

Fields:
- image: (binary image file)
- period_id: 5
- class_id: 1
- timestamp: 2025-12-25T09:35:00

Response:
{
  "message": "Processed image: 3 students identified",
  "predicted_students": [1, 2, 3],
  "marked_attendance": [
    {"student_id": 1, "status": "marked", "period_id": 5},
    {"student_id": 2, "status": "marked", "period_id": 5}
  ]
}
```

### 3. Mark Attendance

```http
POST /public/api/mark-attendance
Headers: X-API-Key: your-secret-key
Content-Type: application/json

Body:
{
  "student_id": 1,
  "period_id": 5,
  "status": "present"
}
```

## Troubleshooting

### Camera Not Detected

```bash
# Check available cameras
python -c "import cv2; print([cv2.VideoCapture(i).isOpened() for i in range(5)])"

# Update CAMERA_INDEX if needed
export CAMERA_INDEX=1
```

### Connection Refused

- Ensure web service is running on the configured URL
- Check firewall settings
- Verify API_KEY matches in all services

### Images Not Being Processed

- Check if period status is "running" in the database
- Verify embeddings are loaded in face_service
- Check face_service logs for processing errors

## Running as a Service (Raspberry Pi)

Create `/etc/systemd/system/attendance-capture.service`:

```ini
[Unit]
Description=Attendance Capture System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/attendance_system
Environment="WEB_SERVICE_URL=http://web:5000"
Environment="FACE_SERVICE_URL=http://face_service:8000"
Environment="PUBLIC_API_KEY=your-secret-key"
Environment="CLASS_ID=1"
ExecStart=/usr/bin/python3 /home/pi/attendance_system/raspberry_pi.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable attendance-capture
sudo systemctl start attendance-capture
sudo systemctl status attendance-capture
```

## Docker Deployment

Add to `compose.yml`:

```yaml
raspberry_pi:
  build: .
  container_name: raspberry_pi
  depends_on:
    - web
    - face_service
  environment:
    WEB_SERVICE_URL: http://web:5000
    FACE_SERVICE_URL: http://face_service:8000
    PUBLIC_API_KEY: ${PUBLIC_API_KEY}
    CLASS_ID: 1
    CAPTURE_INTERVAL: 300
  volumes:
    - /dev/video0:/dev/video0 # For USB camera on Raspberry Pi
  command: python3 /app/raspberry_pi.py
```

## Security Notes

1. **API Key**: Always set a strong `PUBLIC_API_KEY` in production
2. **Network**: Keep the system on a private network or behind a firewall
3. **Image Storage**: Images are processed in memory and not permanently stored
4. **SSL/TLS**: Consider using HTTPS in production environments

## Performance Tips

- Adjust `CAPTURE_INTERVAL` based on class size (larger classes may need more frequent captures)
- Adjust `POLL_INTERVAL` based on server load
- Consider running on Raspberry Pi 4 or newer for better performance
- Use a high-quality USB webcam for better face detection
