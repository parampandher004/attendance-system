from flask import Flask, request, jsonify
import cv2
import numpy as np
from detector import detect_faces  

app = Flask(__name__)

@app.route('/process', methods=['POST'])
def process():
    file = request.files['image']
    npimg = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

    res = detect_faces(img)
    
    for i, face_img in enumerate(res.get("faces", [])):
        # Here you can integrate your face recognition logic
        recog_result = "recognized_person"  # Placeholder for actual recognition result
        res["faces"][i] = {
            "box": res["boxes"][i],
            "confidence": res["confs"][i],
            "recognition": recog_result
        }

    result = res
    return jsonify(result)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000)