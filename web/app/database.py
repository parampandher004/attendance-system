import psycopg2
import psycopg2.extras
from flask import current_app

def get_db():
    conn = psycopg2.connect(current_app.config["DATABASE_URL"])
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    return cur