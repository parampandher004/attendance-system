# detect_yolov8_faces.py
# Path: detect_yolov8_faces.py
"""
YOLOv8 Face Detection with TTA (multi-scale + flip), confidence-weighted clustering and NMS.
- Install: pip install ultralytics opencv-python-headless numpy
- Recommended models (higher -> better accuracy):
    yolov8x-face.pt  (best, slowest)
    yolov8l-face.pt
    yolov8n-face.pt  (fastest, lower accuracy)
You must download a pretrained "face" YOLOv8 weight file and set MODEL_PATH below.
"""

from pathlib import Path
import sys
import cv2
import numpy as np

# Configuration (edit as needed)
IMAGE_PATH = "image.jpg"              # input image
MODEL_PATH = "models/yolov8x-face-lindevs.pt"        # set to your downloaded YOLOv8-face weights
OUTPUT_PATH = "detection_yolov8_faces.jpg"

SCALES = [1.0, 1.5, 2.0]              # TTA scales (1.0 = original). Add more for tiny faces.
USE_FLIP = True                       # horizontal flip TTA
CONF_THRESHOLD = 0.25                 # keep low to increase recall, then rely on clustering+NMS
NMS_IOU = 0.45                        # final NMS threshold
CLUSTER_IOU = 0.30                    # clustering IoU to merge many TTA boxes
IMG_MAX_SIDE = 1600                   # resize longer side to avoid huge inputs (keeps aspect ratio)

# ---------- Helpers ----------
def ensure_ultralytics():
    try:
        import ultralytics  # noqa: F401
    except Exception:
        raise ImportError(
            "Please install ultralytics package:\n\n"
            "    pip install ultralytics\n\n"
            "And download a YOLOv8-face weights file (e.g. yolov8x-face.pt) and place it next to this script.\n"
            "If you want, ask me for a direct download link for a recommended weight."
        )

def iou(a, b):
    x1 = max(a[0], b[0]); y1 = max(a[1], b[1])
    x2 = min(a[2], b[2]); y2 = min(a[3], b[3])
    w = max(0, x2 - x1 + 1); h = max(0, y2 - y1 + 1)
    inter = w * h
    area_a = (a[2] - a[0] + 1) * (a[3] - a[1] + 1)
    area_b = (b[2] - b[0] + 1) * (b[3] - b[1] + 1)
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0

def weighted_cluster(boxes, confs, iou_thresh=0.3):
    """
    Cluster boxes by IoU >= iou_thresh. For each cluster compute confidence-weighted average box.
    Returns merged_boxes (xyxy ints) and merged_confs (floats).
    """
    if not boxes:
        return [], []
    boxes = [list(b) for b in boxes]
    confs = [float(c) for c in confs]
    idxs = list(range(len(boxes)))
    merged_boxes = []
    merged_confs = []
    while idxs:
        # pick index of highest confidence remaining
        seed = max(idxs, key=lambda i: confs[i])
        cluster = [seed]
        others = [i for i in idxs if i != seed]
        for j in others:
            if iou(boxes[seed], boxes[j]) >= iou_thresh:
                cluster.append(j)
        # weighted average
        weights = np.array([confs[i] for i in cluster], dtype=float)
        coords = np.array([boxes[i] for i in cluster], dtype=float)
        wsum = weights.sum() if weights.sum() > 0 else 1.0
        avg = (weights[:, None] * coords).sum(axis=0) / wsum
        x1, y1, x2, y2 = avg
        merged_boxes.append([int(round(x1)), int(round(y1)), int(round(x2)), int(round(y2))])
        merged_confs.append(float(max(confs[i] for i in cluster)))
        # remove clustered indices
        idxs = [i for i in idxs if i not in cluster]
    return merged_boxes, merged_confs

# ---------- Detection pipeline ----------
def run_yolov8_face_detection(image_path: str, model_path: str, output_path: str):
    ensure_ultralytics()
    from ultralytics import YOLO
    import torch

    # choose device
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[INFO] Using device: {device}")

    # load model (will raise if file missing)
    if not Path(model_path).exists():
        raise FileNotFoundError(
            f"Model not found: {model_path}\n"
            "Download a YOLOv8-face weight (e.g. yolov8x-face.pt) and set MODEL_PATH accordingly."
        )
    model = YOLO(model_path)
    model.fuse()  # fuse conv+bn for faster inference

    # load image and keep original
    img_bgr = cv2.imread(image_path)
    if img_bgr is None:
        raise FileNotFoundError(f"Could not load image: {image_path}")
    orig_h, orig_w = img_bgr.shape[:2]
    long_side = max(orig_h, orig_w)
    # optionally resize to limit input size while keeping aspect ratio
    if long_side > IMG_MAX_SIDE:
        scale_small = IMG_MAX_SIDE / float(long_side)
        new_w = int(round(orig_w * scale_small))
        new_h = int(round(orig_h * scale_small))
        img_proc = cv2.resize(img_bgr, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        print(f"[INFO] Resized input from ({orig_w},{orig_h}) -> ({new_w},{new_h}) to limit max side to {IMG_MAX_SIDE}")
    else:
        img_proc = img_bgr.copy()

    all_boxes = []
    all_confs = []

    # TTA: scales and flips
    for scale in SCALES:
        if scale == 1.0:
            img_scale = img_proc
        else:
            sw = int(round(img_proc.shape[1] * scale))
            sh = int(round(img_proc.shape[0] * scale))
            img_scale = cv2.resize(img_proc, (sw, sh), interpolation=cv2.INTER_LINEAR)

        for flip in (False, True) if USE_FLIP else (False,):
            if flip:
                img_in = cv2.flip(img_scale, 1)
            else:
                img_in = img_scale

            # inference: use model.predict for more options; set conf and imgsz high enough
            # augment=False because we explicitly handle TTA
            results = model.predict(source=img_in, device=device, conf=CONF_THRESHOLD, imgsz=1280, verbose=False, augment=False)
            # results is a list; take first (single image)
            if not results:
                continue
            r = results[0]
            # r.boxes.xyxy -> tensor Nx4, r.boxes.conf -> Nx1
            boxes = r.boxes.xyxy.cpu().numpy() if r.boxes is not None else np.zeros((0,4))
            confs = r.boxes.conf.cpu().numpy().flatten() if r.boxes is not None else np.zeros((0,))

            # map boxes back to coordinates in img_proc (because we may have resized img_proc earlier)
            # and then back to original image coordinates if we resized for IMG_MAX_SIDE
            # Step 1: if flipped, unflip
            for (b, c) in zip(boxes, confs):
                x1, y1, x2, y2 = b.astype(float)
                if flip:
                    # unflip relative to img_scale width
                    w_img = img_in.shape[1]
                    x1n = w_img - x2
                    x2n = w_img - x1
                    x1, x2 = x1n, x2n
                # if img_scale != img_proc, scale coordinates back to img_proc
                if img_scale.shape[1] != img_proc.shape[1] or img_scale.shape[0] != img_proc.shape[0]:
                    sx = img_proc.shape[1] / float(img_scale.shape[1])
                    sy = img_proc.shape[0] / float(img_scale.shape[0])
                    x1 *= sx; x2 *= sx; y1 *= sy; y2 *= sy
                # if img_proc was resized from original due to IMG_MAX_SIDE, scale coords up
                if img_proc.shape[1] != orig_w or img_proc.shape[0] != orig_h:
                    sx2 = orig_w / float(img_proc.shape[1])
                    sy2 = orig_h / float(img_proc.shape[0])
                    x1 *= sx2; x2 *= sx2; y1 *= sy2; y2 *= sy2
                # clip
                x1c = max(0, min(orig_w - 1, int(round(x1))))
                y1c = max(0, min(orig_h - 1, int(round(y1))))
                x2c = max(0, min(orig_w - 1, int(round(x2))))
                y2c = max(0, min(orig_h - 1, int(round(y2))))
                if x2c <= x1c or y2c <= y1c:
                    continue
                all_boxes.append([x1c, y1c, x2c, y2c])
                all_confs.append(float(c))

    if not all_boxes:
        print("[INFO] No faces detected.")
        return

    # cluster and merge
    merged_boxes, merged_confs = weighted_cluster(all_boxes, all_confs, iou_thresh=CLUSTER_IOU)

    # final NMS (cv2.dnn.NMSBoxes expects boxes in x,y,w,h)
    boxes_xywh = [[b[0], b[1], b[2] - b[0] + 1, b[3] - b[1] + 1] for b in merged_boxes]
    indices = cv2.dnn.NMSBoxes(boxes_xywh, merged_confs, CONF_THRESHOLD, NMS_IOU)
    final_boxes = []
    final_confs = []
    if len(indices) > 0:
        # handle OpenCV return formats
        if isinstance(indices[0], (list, tuple, np.ndarray)):
            idxs = [int(i[0]) for i in indices]
        else:
            idxs = [int(i) for i in indices]
        for i in idxs:
            final_boxes.append(merged_boxes[i])
            final_confs.append(merged_confs[i])

    # draw results
    out = img_bgr.copy()
    for (box, conf) in zip(final_boxes, final_confs):
        x1, y1, x2, y2 = box
        label = f"{conf*100:.1f}%"
        cv2.rectangle(out, (x1, y1), (x2, y2), (0, 220, 0), 2)
        cv2.putText(out, label, (x1, max(15, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 220, 0), 2)

    print(f"[INFO] Final detections: {len(final_boxes)} faces")
    cv2.imwrite(output_path, out)
    print(f"[INFO] Saved visualization to: {output_path}")
    # show (optional)
    # cv2.imshow("YOLOv8 Face Detections", out); cv2.waitKey(0); cv2.destroyAllWindows()

# ---------- Main ----------
if __name__ == "__main__":
    try:
        run_yolov8_face_detection(IMAGE_PATH, MODEL_PATH, OUTPUT_PATH)
    except Exception as e:
        print("[ERROR]", e)
        sys.exit(1)
