from datetime import datetime
from pathlib import Path
from uuid import uuid4

import cv2
from flask import Flask, jsonify, render_template, request, url_for
from werkzeug.utils import secure_filename

from detector import DEFAULT_MODEL_PATH, HazardDetector, ensure_directory


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
RESULT_DIR = BASE_DIR / "static" / "results"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}

ensure_directory(UPLOAD_DIR)
ensure_directory(RESULT_DIR)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

detector = HazardDetector(DEFAULT_MODEL_PATH)


def allowed_file(filename):
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def save_upload(file_storage):
    original_name = secure_filename(file_storage.filename or "")
    if not original_name:
        raise ValueError("Please choose an image file.")

    if not allowed_file(original_name):
        raise ValueError("Unsupported file type. Upload JPG, PNG, or BMP.")

    unique_name = f"{uuid4().hex}_{original_name}"
    upload_path = UPLOAD_DIR / unique_name
    file_storage.save(upload_path)
    return upload_path, unique_name


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/detect", methods=["POST"])
def detect():
    uploaded_file = request.files.get("image")
    confidence = float(request.form.get("confidence", 0.4))

    if uploaded_file is None:
        return render_template(
            "index.html",
            error="Please upload an image before running detection.",
        ), 400

    try:
        upload_path, unique_name = save_upload(uploaded_file)
        annotated_frame, detections = detector.detect_image_file(
            upload_path, confidence=confidence
        )

        result_name = f"result_{unique_name}"
        result_path = RESULT_DIR / result_name
        cv2.imwrite(str(result_path), annotated_frame)

        hazard_counts = {}
        for item in detections:
            hazard_counts[item["label"]] = hazard_counts.get(item["label"], 0) + 1

        return render_template(
            "index.html",
            uploaded_image=url_for("static", filename=f"uploads/{unique_name}"),
            result_image=url_for("static", filename=f"results/{result_name}"),
            detections=detections,
            hazard_counts=hazard_counts,
            confidence=confidence,
            processed_at=datetime.now().strftime("%d %b %Y, %I:%M %p"),
        )
    except ValueError as exc:
        return render_template("index.html", error=str(exc)), 400


@app.route("/api/detect", methods=["POST"])
def api_detect():
    uploaded_file = request.files.get("image")
    confidence = float(request.form.get("confidence", 0.4))

    if uploaded_file is None:
        return jsonify({"error": "Missing image file."}), 400

    try:
        upload_path, unique_name = save_upload(uploaded_file)
        annotated_frame, detections = detector.detect_image_file(
            upload_path, confidence=confidence
        )

        result_name = f"result_{unique_name}"
        result_path = RESULT_DIR / result_name
        cv2.imwrite(str(result_path), annotated_frame)

        return jsonify(
            {
                "message": "Detection completed successfully.",
                "uploaded_image": url_for(
                    "static", filename=f"uploads/{unique_name}", _external=True
                ),
                "result_image": url_for(
                    "static", filename=f"results/{result_name}", _external=True
                ),
                "detections": [
                    {
                        "label": item["label"],
                        "confidence": item["confidence"],
                        "box": item["box"],
                    }
                    for item in detections
                ],
            }
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


if __name__ == "__main__":
    app.run(debug=True)
