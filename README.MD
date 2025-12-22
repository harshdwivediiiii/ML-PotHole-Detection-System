Here’s a **fixed, clean, and professional version** of your `README.md`, with corrected formatting, clearer structure, and consistent wording.
(Content is improved without changing your project logic.)

---

# 🚔 YOLOv8 Pothole Detection System

A computer vision–based system designed to detect road hazards (potholes) in **real time** from images, video files, or live camera feeds using **YOLOv8**.

---

## 🛠️ Features

* **Three Interaction Modes**

  1. **Direct Script** – Quick testing on predefined videos (`app.py`)
  2. **Flexible CLI Tool** – Detect potholes from images, videos, or USB cameras with custom resolution (`yolo_detect.py`)
  3. **Web Dashboard** – Real-time browser-based detection using **Streamlit + WebRTC** (`LiveCamera.py`)

* **Performance Control**

  * Adjustable confidence threshold via CLI arguments or web UI slider

* **Multi-Source Support**

  * Supports `.mp4`, `.avi`, `.jpg`, `.png`, and live USB camera streams

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/your-username/yolov8-pothole-detection.git
cd yolov8-pothole-detection
```

### 2️⃣ Create Conda Environment

```bash
conda create -n YOLOv8PotholeDetection python=3.10 -y
conda activate YOLOv8PotholeDetection
```

> ⚠️ **Note:** Python `3.10` is recommended for better compatibility with YOLOv8 and deep learning libraries.

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 💻 Usage

### 🔹 1. Command Line Tool (Flexible Detection)

#### Detect from Video

```bash
python yolo_detect.py --model "models/LessAccurate_Model.pt" --source "Test/Pothole_Exp1.mp4"
```

#### Detect from USB Camera

```bash
python yolo_detect.py --model "models/LessAccurate_Model.pt" --source usb0 --resolution 640x480
```

#### Detect from Single Image

```bash
python yolo_detect.py --model "models/LessAccurate_Model.pt" --source "Test/1.png"
```

---

### 🔹 2. Streamlit Web Interface (Recommended)

Run the real-time web dashboard with confidence slider control:

```bash
streamlit run LiveCamera.py
```

* Live camera detection
* Adjustable confidence threshold
* Browser-based UI

---

### 🔹 3. Basic Test Script

Quick test using default settings:

```bash
python app.py
```

---

## 📁 Project Structure

```
YOLOv8-Pothole-Detection/
│
├── models/
│   └── LessAccurate_Model.pt
│
├── Test/
│   ├── Pothole_Exp1.mp4
│   └── 1.png
│
├── app.py
├── yolo_detect.py
├── LiveCamera.py
├── requirements.txt
└── README.md
```

---

## 📌 Applications

* Smart city road monitoring
* Accident prevention systems
* Autonomous driving assistance
* Infrastructure maintenance

---

## 🔮 Future Enhancements

* Improve model accuracy with a larger dataset
* Add GPS-based pothole logging
* Deploy as a cloud-based service
* Mobile camera integration

---
