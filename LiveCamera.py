import streamlit as st
import os
import cv2
import av
from ultralytics import YOLO
from streamlit_webrtc import webrtc_streamer

# Avoid library conflicts
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# 1. Load Model Automatically
MODEL_PATH = "models/LessAccurate Model.pt"

@st.cache_resource
def get_model():
    if not os.path.exists(MODEL_PATH):
        st.error(f"File not found: {MODEL_PATH}")
        return None
    return YOLO(MODEL_PATH)

model = get_model()

# 2. Simplified Frame Processing
def video_frame_callback(frame):
    img = frame.to_ndarray(format="bgr24")
    
    # Run detection
    results = model(img, conf=st.session_state.get("conf", 0.5), verbose=False)
    
    # Automatically draw all boxes and labels
    annotated_img = results[0].plot()
    
    return av.VideoFrame.from_ndarray(annotated_img, format="bgr24")

# 3. Streamlit UI
def main():
    st.title("🤖 YOLOv8 Real-Time PotHole Detection")
    
    # Store threshold in session state to access it inside the callback
    st.sidebar.header("Configuration")
    st.session_state["conf"] = st.sidebar.slider("Confidence Threshold", 0.0, 1.0, 0.5)
    
    if model:
        st.sidebar.success("Model Loaded Automatically")
        webrtc_streamer(
            key="yolo-streamer",
            video_frame_callback=video_frame_callback,
            rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
            media_stream_constraints={"video": True, "audio": False},
        )

if __name__ == "__main__":
    main()