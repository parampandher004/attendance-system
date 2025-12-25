import os
import requests
import numpy as np
import threading
import time

embeddings = []

def load_embeddings():
    """Load embeddings from web service public API with error handling"""
    global embeddings
    
    try:
        web_service_url = os.getenv("WEB_SERVICE_URL")
        api_key = os.getenv("PUBLIC_API_KEY", "default-insecure-key")
        
        if not web_service_url:
            print("Warning: WEB_SERVICE_URL not set, skipping embeddings load")
            embeddings = []
            return
        
        headers = {
            "X-API-Key": api_key
        }
        
        resp = requests.get(
            f"{web_service_url}/public/api/get-embeddings",
            headers=headers,
            timeout=10
        )
        resp.raise_for_status()
        
        data = resp.json()
        if data and "embeddings" in data:
            embeddings_list = data["embeddings"]
            embeddings = [{
                "student_id": item["student_id"],
                "student_name": item["student_name"],
                "roll_no": item["roll_no"],
                "embedding": np.array(item["embedding"], dtype=np.float32)
            } for item in embeddings_list]
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
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
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