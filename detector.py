import os
from pathlib import Path

import cv2
from ultralytics import YOLO


DEFAULT_MODEL_PATH = "models/LessAccurate Model.pt"


class HazardDetector:
    def __init__(self, model_path=DEFAULT_MODEL_PATH):
        os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
        self.model_path = model_path
        self.model = YOLO(model_path, task="detect")
        self.labels = self.model.names
        self.bbox_colors = [
            (164, 120, 87),
            (68, 148, 228),
            (93, 97, 209),
            (178, 182, 133),
            (88, 159, 106),
            (96, 202, 231),
            (159, 124, 168),
            (169, 162, 241),
            (98, 118, 150),
            (172, 176, 184),
        ]

    def detect_frame(self, frame, confidence=0.4):
        results = self.model(frame, conf=confidence, verbose=False)
        detections = []

        for detection in results[0].boxes:
            xyxy = detection.xyxy.cpu().numpy().squeeze()
            if xyxy.size == 0:
                continue

            xmin, ymin, xmax, ymax = xyxy.astype(int)
            class_index = int(detection.cls.item())
            score = float(detection.conf.item())
            detections.append(
                {
                    "label": self.labels[class_index],
                    "confidence": round(score, 4),
                    "box": [int(xmin), int(ymin), int(xmax), int(ymax)],
                    "color": self.bbox_colors[class_index % len(self.bbox_colors)],
                }
            )

        return detections

    def annotate_frame(self, frame, detections):
        annotated = frame.copy()

        for detection in detections:
            xmin, ymin, xmax, ymax = detection["box"]
            color = detection["color"]
            label = f'{detection["label"]}: {int(detection["confidence"] * 100)}%'

            cv2.rectangle(annotated, (xmin, ymin), (xmax, ymax), color, 2)
            label_size, baseline = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
            )
            label_y = max(ymin, label_size[1] + 10)
            cv2.rectangle(
                annotated,
                (xmin, label_y - label_size[1] - 10),
                (xmin + label_size[0], label_y + baseline - 10),
                color,
                cv2.FILLED,
            )
            cv2.putText(
                annotated,
                label,
                (xmin, label_y - 7),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 0),
                1,
            )

        return annotated

    def detect_image_file(self, image_path, confidence=0.4):
        frame = cv2.imread(str(image_path))
        if frame is None:
            raise ValueError("Could not read the uploaded image.")

        detections = self.detect_frame(frame, confidence=confidence)
        annotated = self.annotate_frame(frame, detections)
        return annotated, detections


def ensure_directory(path):
    Path(path).mkdir(parents=True, exist_ok=True)
