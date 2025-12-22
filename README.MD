# 🚔 YOLOv8 Pothole Detection System

>A computer vision project designed to identify road hazards (potholes) in real-time from video files, images, or live camera feeds.

---

## 🛠️ Features

- Three Interaction Modes:
  1. Direct Script: Quick execution for specific test videos (app.py).
  2. Flexible CLI: Command-line tool for images, videos, or USB cameras with custom resolutions (yolo_detect.py).
  3. Web Dashboard: Real-time browser-based detection using Streamlit and WebRTC (LiveCamera.py).
- Performance Toggling: Adjust confidence thresholds on the fly via the web UI or CLI arguments.
- Multi-Source Support: Handles .mp4, .avi, .jpg, .png, and live USB streams.

## How To Run
 
 - Clone The Repo

```bash

# Create Conda environment
conda create -n YOLOv8PotholeDetection python=3.13.5 -y

# Activate environment
conda activate YOLOv8PotholeDetection

# Install dependencies
pip install -r requirements.txt

```
---

## 💻 Usage

- 1. Command Line Tool
    ```bash

# For Video Files:
python yolo_detect.py --model "models/LessAccurate Model.pt" --source "Test/Pothole Exp1.mp4"

# For USB Camera:
python yolo_detect.py --model "models/LessAccurate Model.pt" --source "usb0" --resolution 640x480

# For Single Images:
python yolo_detect.py --model "models/LessAccurate Model.pt" --source "Test/1.png"

```


- 2. Streamlit Web Interface

```bash
# Run the live web dashboard for a user-friendly experience with a confidence slider:
streamlit run LiveCamera.py

```

-3 Basic Test Script
```bash
python app.py
```

---

