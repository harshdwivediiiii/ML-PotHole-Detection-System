import streamlit as st
import os
import av
from ultralytics import YOLO
from streamlit_webrtc import webrtc_streamer, WebRtcMode

# Load Model

MODEL_PATH = "models/LessAccurate Model.pt"
@st.cache_resource
def get_model():
    return YOLO(MODEL_PATH) if os.path.exists(MODEL_PATH) else None

model = get_model()

def video_frame_callback(frame):
    img = frame.to_ndarray(format="bgr24")
    
    results = model(img, conf=st.session_state.get("conf", 0.4), verbose=False)
    annotated_img = results[0].plot()
    
    return av.VideoFrame.from_ndarray(annotated_img, format="bgr24")

def main():
    st.title("🚔 YOLOv8 Real-Time PotHole Detection")
    st.session_state["conf"] = st.sidebar.slider("Confidence", 0.0, 1.0, 0.4)

    if model:
        webrtc_streamer(
            key="yolo-720p",
            mode=WebRtcMode.SENDRECV,
            video_frame_callback=video_frame_callback,
            async_processing=True,
            
            media_stream_constraints={
                "video": {
                    "width": {"ideal": 1280},
                    "height": {"ideal": 720},
                    "frameRate": {"ideal": 60} 
                },
                "audio": False
            },
            rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
        )

if __name__ == "__main__":
    main()