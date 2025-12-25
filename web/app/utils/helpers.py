import hashlib
from datetime import datetime, date, time

DAY_MAP = {
    "0": "Sunday",
    "1": "Monday",
    "2": "Tuesday",
    "3": "Wednesday",
    "4": "Thursday",
    "5": "Friday",
    "6": "Saturday",
}

def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

def format_time(v):
    """Formats time object to 12-hour string (e.g., 02:30 PM)"""
    try:
        s = v.strftime("%I:%M %p")
        return s.lstrip("0")
    except Exception:
        return v

def serialize_model(obj, many=False):
    """Converts a SQLAlchemy model instance to a dictionary"""
    if many:
        return [serialize_model(o) for o in obj]
    data = {}
    for column in obj.__table__.columns:
        value = getattr(obj, column.name)
        if isinstance(value, (datetime, date)):
            data[column.name] = value.strftime("%d/%m/%Y")
        elif isinstance(value, time):
            data[column.name] = format_time(value)
        else:
            data[column.name] = value
    return data