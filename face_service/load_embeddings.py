import os
import requests
import numpy as np
import threading
import time

embeddings = []

def load_embeddings():

    resp = requests.get(os.getenv("WEB_SERVICE_URL") + "/api/get_embeddings")
    data = resp.json()

    global embeddings
    embeddings = [{
        "student_id": item["student_id"],
        "embedding": np.array(item["embedding"], dtype=np.float32)
    } for item in data]

t = threading.Timer(
    3600, 
    load_embeddings , 
    args=() 
)
t.start()
t.join(1)
load_embeddings()