import streamlit as st
import os
import cv2
import numpy as np
import time
from ultralytics import YOLO
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

BBOX_COLORS = [(164,120,87), (68,148,228), (93,97,209), (178,182,133), (88,159,106), 
               (96,202,231), (159,124,168), (169,162,241), (98,118,150), (172,176,184)]

@st.cache_resource
def load_yolo_model(model_path):
    try:
        model = YOLO(model_path, task='detect')
        return model
    except Exception as e:
        st.error(f"Error loading model: {e}")
        return None

class YOLOVideoTransformer(VideoTransformerBase):
    def __init__(self, model, labels, min_thresh):
        self.model = model
        self.labels = labels
        self.min_thresh = min_thresh
        self.frame_rate_buffer = []
        self.fps_avg_len = 30

    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        
        t_start = time.perf_counter()

        results = self.model(img, verbose=False)
        detections = results[0].boxes
        object_count = 0

        for i in range(len(detections)):
            xyxy_tensor = detections[i].xyxy.cpu() 
            xyxy = xyxy_tensor.numpy().squeeze() 
            xmin, ymin, xmax, ymax = xyxy.astype(int) 

            classidx = int(detections[i].cls.item())
            conf = detections[i].conf.item()
            classname = self.labels[classidx]

            if conf > self.min_thresh:
                object_count += 1
                color = BBOX_COLORS[classidx % len(BBOX_COLORS)]
                
                cv2.rectangle(img, (xmin, ymin), (xmax, ymax), color, 2)

                label = f'{classname}: {int(conf*100)}%'
                labelSize, baseLine = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                label_ymin = max(ymin, labelSize[1] + 10)
                
                cv2.rectangle(img, (xmin, label_ymin - labelSize[1] - 10), 
                              (xmin + labelSize[0], label_ymin + baseLine - 10), color, cv2.FILLED) 
                cv2.putText(img, label, (xmin, label_ymin - 7), cv2.FONT_HERSHEY_SIMPLEX, 
                            0.5, (0, 0, 0), 1)

        t_stop = time.perf_counter()
        frame_rate_calc = float(1/(t_stop - t_start))

        self.frame_rate_buffer.append(frame_rate_calc)
        if len(self.frame_rate_buffer) > self.fps_avg_len:
            self.frame_rate_buffer.pop(0)
        
        avg_frame_rate = np.mean(self.frame_rate_buffer)
        
        cv2.putText(img, f'FPS: {avg_frame_rate:0.2f}', (10, 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(img, f'Objects: {object_count}', (10, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        return img

def main():
    st.title("🤖 YOLOv8 Based Real-Time Cam PotHole Detection System")
    st.markdown("Use the sidebar to load your model, then press START to begin the live feed.")

    st.sidebar.header("Model and Configuration")

    model_file = st.sidebar.file_uploader("Upload YOLO Model (`.pt` file)", type=['pt'])
    
    min_thresh = st.sidebar.slider("Confidence Threshold", 0.0, 1.0, 0.5)

    if model_file is not None:
        temp_model_path = os.path.join("./temp", model_file.name)
        os.makedirs("./temp", exist_ok=True)
        with open(temp_model_path, "wb") as f:
            f.write(model_file.getbuffer())
        
        model = load_yolo_model(temp_model_path)
        
        if model:
            labels = model.names
            st.sidebar.success(f"Model loaded successfully! Detected {len(labels)} classes.")

            st.subheader("Live Webcam Feed")
            
            webrtc_streamer(
                key="yolo-detector",
                video_transformer_factory=lambda: YOLOVideoTransformer(model, labels, min_thresh),
                rtc_configuration={
                    "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
                },
                media_stream_constraints={"video": True, "audio": False},
            )

    else:
        st.warning("Please upload your YOLO model (`.pt` file) to begin.")


if __name__ == '__main__':
    main()