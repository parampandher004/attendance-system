import cv2
import os
import numpy as np
from datetime import datetime

# ============ CONFIG ============
PERSON_ID = "person_01"
DATASET_ROOT = "face_service/dataset"
IMG_SIZE = 200
MAX_IMAGES = 70
CAMERA_INDEX = 0
# =================================

SAVE_DIR = os.path.join(DATASET_ROOT, PERSON_ID)
os.makedirs(SAVE_DIR, exist_ok=True)

cap = cv2.VideoCapture(CAMERA_INDEX)

counts = {"front":0, "side":0}

def gamma(img, g):
    table = np.array([(i/255.0)**g * 255 for i in range(256)]).astype("uint8")
    return cv2.LUT(img, table)

def add_noise(img):
    noise = np.random.normal(0, 10, img.shape).astype(np.uint8)
    return cv2.add(img, noise)

def motion_blur(img):
    k = np.zeros((5,5))
    k[2,:] = np.ones(5)
    k /= 5
    return cv2.filter2D(img, -1, k)

def random_crop(img):
    h, w = img.shape
    dx = np.random.randint(0, 10)
    dy = np.random.randint(0, 10)
    cropped = img[dy:h-dy, dx:w-dx]
    return cv2.resize(cropped, (IMG_SIZE, IMG_SIZE))

def save(img, label):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    cv2.imwrite(f"{SAVE_DIR}/{label}_{ts}.jpg", img)

print("[INFO] Webcam augmentation running")
print("[INFO] Move face naturally")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    h, w = frame.shape[:2]
    face = frame[h//4:3*h//4, w//4:3*w//4]  # simple central crop

    face = cv2.resize(face, (IMG_SIZE, IMG_SIZE))
    gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)

    label = "front" if counts["front"] < MAX_IMAGES//2 else "side"

    if counts[label] < MAX_IMAGES//2:
        # ---- Original ----
        save(gray, label)

        # ---- Augmentations ----
        save(gamma(gray, 0.7), label)
        save(gamma(gray, 1.3), label)
        save(add_noise(gray), label)
        save(motion_blur(gray), label)
        save(random_crop(gray), label)
        save(cv2.flip(gray, 1), label)

        counts[label] += 6

    # SHOW ORIGINAL + AUGMENTED PREVIEW
    preview = np.hstack([
        gray,
        gamma(gray, 0.7),
        motion_blur(gray)
    ])
    cv2.imshow("Augmentation Preview", preview)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    if sum(counts.values()) >= MAX_IMAGES:
        break

cap.release()
cv2.destroyAllWindows()

print("[DONE] Strong augmented dataset created at:", SAVE_DIR)
