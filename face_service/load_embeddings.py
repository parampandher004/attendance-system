import os
import requests
import numpy as np
import threading
import time

embeddings = []

def load_embeddings():
    """Load embeddings from web service with error handling"""
    global embeddings
    
    try:
        web_service_url = os.getenv("WEB_SERVICE_URL")
        if not web_service_url:
            print("Warning: WEB_SERVICE_URL not set, skipping embeddings load")
            embeddings = []
            return
        
        resp = requests.get(
            f"{web_service_url}/api/get_embeddings",
            timeout=10
        )
        resp.raise_for_status()
        
        data = resp.json()
        if data:
            embeddings = [{
                "student_id": item["student_id"],
                "embedding": np.array(item["embedding"], dtype=np.float32)
            } for item in data]
            print(f"Successfully loaded {len(embeddings)} embeddings from web service")
        else:
            print("No embeddings found from web service")
            embeddings = []
    
    except requests.exceptions.Timeout:
        print("Timeout while loading embeddings from web service")
        embeddings = []
    except requests.exceptions.ConnectionError:
        print("Failed to connect to web service for embeddings")
        embeddings = []
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error while loading embeddings: {e}")
        embeddings = []
    except ValueError as e:
        print(f"Invalid JSON response from web service: {e}")
        embeddings = []
    except Exception as e:
        print(f"Error loading embeddings: {e}")
        embeddings = []

# Schedule periodic reload
t = threading.Timer(
    3600, 
    load_embeddings , 
    args=() 
)
t.daemon = True  # Make thread daemon so it doesn't block shutdown
t.start()

# Initial load with timeout to not block startup
try:
    t.join(1)  # Wait max 1 second for initial load
    load_embeddings()
except Exception as e:
    print(f"Error during initial embeddings load: {e}")
    embeddings = []