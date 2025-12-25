import cv2

image = cv2.imread('goru.png')
height, width, _ = image.shape

# Define your grid (e.g., 30x30)
rows = 6
cols = 5

step_h = height // rows
step_w = width // cols

for r in range(rows):
    for c in range(cols):
        # Slice the array
        crop = image[r*step_h:(r+1)*step_h, c*step_w:(c+1)*step_w]
        cv2.imwrite(f'face_{r}_{c}.jpg', crop)