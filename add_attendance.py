import requests
from datetime import date

data = {
    "student_id": "1",
    "status": "present",
    "date": str(date.today())
}
response = requests.post("http://localhost:5000/api/attendance", json=data)
print(response.json())
