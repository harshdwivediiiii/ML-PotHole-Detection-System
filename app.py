import cv2
from ultralytics import YOLO

model = YOLO('models/LessAccurate Model.pt')
names = model.names

cap = cv2.VideoCapture("Test/Pothole Exp1.mp4")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.resize(frame, (1600, 900))
    results = model.predict(frame)

    if results[0].boxes is not None:
        boxes = results[0].boxes.xyxy.cpu().numpy().astype(int)
        class_ids = results[0].boxes.cls.int().cpu().tolist()

        for box, class_id in zip(boxes, class_ids):
            x1, y1, x2, y2 = box
            label = names[class_id]
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(frame, label, (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    cv2.imshow("Pothole Detection", frame)
    
    key = cv2.waitKey(1) & 0xFF
    if key == 27:
        break

cap.release()
cv2.destroyAllWindows()