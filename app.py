from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

import cv2
from flask import Flask, abort, jsonify, render_template, request, url_for
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

STATUS_FLOW = ["pending", "acknowledged", "in progress", "resolved"]
STATUS_COLORS = {
    "pending": "orange",
    "acknowledged": "blue",
    "in progress": "purple",
    "resolved": "green",
}
SEVERITY_COLORS = {
    "critical": "red",
    "high": "orange",
    "medium": "blue",
    "low": "green",
}
SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def seed_detection_records():
    now = datetime.now()
    base_records = [
        {
            "hazard_type": "Pothole",
            "location": "Ring Road, Sector 21",
            "lat": 28.4595,
            "lng": 77.0266,
            "severity": "critical",
            "confidence": 0.97,
            "status": "pending",
            "device_id": "CAM-201",
            "team": "Rapid Fix North",
            "notes": "Lane collapse risk near divider.",
            "days_ago": 0,
            "hours_ago": 2,
            "address": "Sector 21, Gurugram, Haryana",
            "image": "results/demo-critical-pothole.jpg",
        },
        {
            "hazard_type": "Longitudinal Crack",
            "location": "NH-48 Service Lane",
            "lat": 28.4721,
            "lng": 77.0723,
            "severity": "high",
            "confidence": 0.91,
            "status": "in progress",
            "device_id": "CAM-114",
            "team": "Corridor Team A",
            "notes": "Needs resurfacing before monsoon.",
            "days_ago": 1,
            "hours_ago": 5,
            "address": "NH-48 Service Lane, Gurugram",
            "image": "uploads/demo-crack.jpg",
        },
        {
            "hazard_type": "Pothole",
            "location": "MG Road Metro Stretch",
            "lat": 28.4799,
            "lng": 77.0802,
            "severity": "medium",
            "confidence": 0.88,
            "status": "pending",
            "device_id": "CAM-143",
            "team": "Metro Response",
            "notes": "Recurring cavity near bus stop.",
            "days_ago": 1,
            "hours_ago": 9,
            "address": "MG Road, Gurugram",
            "image": "results/demo-metro-pothole.jpg",
        },
        {
            "hazard_type": "Alligator Crack",
            "location": "Golf Course Road",
            "lat": 28.4378,
            "lng": 77.1012,
            "severity": "critical",
            "confidence": 0.95,
            "status": "acknowledged",
            "device_id": "CAM-155",
            "team": "Rapid Fix South",
            "notes": "Patch failure spreading across outer lane.",
            "days_ago": 2,
            "hours_ago": 11,
            "address": "Golf Course Road, DLF Phase 5",
            "image": "uploads/demo-alligator.jpg",
        },
        {
            "hazard_type": "Edge Break",
            "location": "Old Delhi Road",
            "lat": 28.5005,
            "lng": 77.0322,
            "severity": "low",
            "confidence": 0.76,
            "status": "resolved",
            "device_id": "CAM-178",
            "team": "Perimeter Crew",
            "notes": "Resolved during shoulder repair.",
            "days_ago": 3,
            "hours_ago": 3,
            "address": "Old Delhi Road, Gurugram",
            "image": "results/demo-edge-break.jpg",
        },
        {
            "hazard_type": "Pothole",
            "location": "Hero Honda Chowk",
            "lat": 28.4228,
            "lng": 76.9718,
            "severity": "high",
            "confidence": 0.93,
            "status": "pending",
            "device_id": "CAM-132",
            "team": "Junction Squad",
            "notes": "Heavy truck corridor, rapid deterioration.",
            "days_ago": 4,
            "hours_ago": 7,
            "address": "Hero Honda Chowk, Gurugram",
            "image": "uploads/demo-junction-pothole.jpg",
        },
        {
            "hazard_type": "Transverse Crack",
            "location": "Cyber City Loop",
            "lat": 28.4942,
            "lng": 77.0894,
            "severity": "medium",
            "confidence": 0.83,
            "status": "resolved",
            "device_id": "CAM-166",
            "team": "CBD Maintenance",
            "notes": "Monitored for 24h before closure.",
            "days_ago": 5,
            "hours_ago": 6,
            "address": "Cyber City Loop, Gurugram",
            "image": "results/demo-loop-crack.jpg",
        },
        {
            "hazard_type": "Pothole",
            "location": "Dwarka Expressway Ramp",
            "lat": 28.5289,
            "lng": 76.9892,
            "severity": "critical",
            "confidence": 0.98,
            "status": "pending",
            "device_id": "CAM-121",
            "team": "Expressway Unit",
            "notes": "Deep cavity at merge point.",
            "days_ago": 6,
            "hours_ago": 10,
            "address": "Dwarka Expressway Ramp, Gurugram",
            "image": "uploads/demo-ramp-pothole.jpg",
        },
        {
            "hazard_type": "Rut",
            "location": "Sohna Road",
            "lat": 28.4089,
            "lng": 77.0405,
            "severity": "high",
            "confidence": 0.89,
            "status": "in progress",
            "device_id": "CAM-188",
            "team": "South Arterial Crew",
            "notes": "Requires milling and compaction.",
            "days_ago": 8,
            "hours_ago": 4,
            "address": "Sohna Road, Gurugram",
            "image": "results/demo-rut.jpg",
        },
        {
            "hazard_type": "Pothole",
            "location": "IFFCO Chowk Underpass",
            "lat": 28.4683,
            "lng": 77.0715,
            "severity": "medium",
            "confidence": 0.81,
            "status": "acknowledged",
            "device_id": "CAM-193",
            "team": "Underpass Unit",
            "notes": "Waterlogging worsens surface damage.",
            "days_ago": 11,
            "hours_ago": 8,
            "address": "IFFCO Chowk Underpass, Gurugram",
            "image": "uploads/demo-underpass-pothole.jpg",
        },
        {
            "hazard_type": "Depression",
            "location": "Sector 56 Connector",
            "lat": 28.4201,
            "lng": 77.1108,
            "severity": "low",
            "confidence": 0.72,
            "status": "pending",
            "device_id": "CAM-204",
            "team": "Connector Cell",
            "notes": "Monitor before full patch work.",
            "days_ago": 14,
            "hours_ago": 1,
            "address": "Sector 56 Connector, Gurugram",
            "image": "results/demo-depression.jpg",
        },
        {
            "hazard_type": "Pothole",
            "location": "Udyog Vihar Phase 3",
            "lat": 28.5038,
            "lng": 77.0731,
            "severity": "high",
            "confidence": 0.9,
            "status": "resolved",
            "device_id": "CAM-211",
            "team": "Industrial Belt Crew",
            "notes": "Resolved after overnight closure.",
            "days_ago": 18,
            "hours_ago": 2,
            "address": "Udyog Vihar Phase 3, Gurugram",
            "image": "uploads/demo-udyog-pothole.jpg",
        },
    ]

    records = []
    for index, item in enumerate(base_records, start=1001):
        reported_at = now - timedelta(days=item.pop("days_ago"), hours=item.pop("hours_ago"))
        resolved_at = None
        if item["status"] == "resolved":
            resolved_at = reported_at + timedelta(days=1, hours=6)

        activity_log = [
            {
                "status": "pending",
                "timestamp": reported_at.isoformat(),
                "updated_by": "Detection Engine",
                "note": "Automatic hazard detection created the report.",
            }
        ]

        if item["status"] in {"acknowledged", "in progress", "resolved"}:
            activity_log.append(
                {
                    "status": "acknowledged",
                    "timestamp": (reported_at + timedelta(hours=3)).isoformat(),
                    "updated_by": "Control Room",
                    "note": "Flagged for authority review.",
                }
            )
        if item["status"] in {"in progress", "resolved"}:
            activity_log.append(
                {
                    "status": "in progress",
                    "timestamp": (reported_at + timedelta(hours=12)).isoformat(),
                    "updated_by": item["team"],
                    "note": "Repair crew dispatched to site.",
                }
            )
        if item["status"] == "resolved":
            activity_log.append(
                {
                    "status": "resolved",
                    "timestamp": resolved_at.isoformat(),
                    "updated_by": item["team"],
                    "note": "Hazard repaired and marked closed.",
                }
            )

        records.append(
            {
                "id": index,
                "hazard_type": item["hazard_type"],
                "location": item["location"],
                "lat": item["lat"],
                "lng": item["lng"],
                "severity": item["severity"],
                "severity_color": SEVERITY_COLORS[item["severity"]],
                "confidence": item["confidence"],
                "status": item["status"],
                "status_color": STATUS_COLORS[item["status"]],
                "device_id": item["device_id"],
                "assigned_team": item["team"],
                "notes": item["notes"],
                "reported_at": reported_at.isoformat(),
                "resolved_at": resolved_at.isoformat() if resolved_at else None,
                "address": item["address"],
                "image_url": "/static/admin-hazard-placeholder.svg",
                "activity_log": activity_log,
            }
        )

    return records


with app.app_context():
    DETECTION_RECORDS = seed_detection_records()


def parse_iso_datetime(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def serialize_record(record):
    return {
        "id": record["id"],
        "hazard_type": record["hazard_type"],
        "location": record["location"],
        "lat": record["lat"],
        "lng": record["lng"],
        "severity": record["severity"],
        "severity_color": record["severity_color"],
        "confidence": record["confidence"],
        "status": record["status"],
        "status_color": record["status_color"],
        "reported_at": record["reported_at"],
        "resolved_at": record["resolved_at"],
        "address": record["address"],
        "device_id": record["device_id"],
        "assigned_team": record["assigned_team"],
        "notes": record["notes"],
        "image_url": record["image_url"],
        "activity_log": record["activity_log"],
    }


def get_record_or_404(detection_id):
    for record in DETECTION_RECORDS:
        if record["id"] == detection_id:
            return record
    abort(404, description="Detection not found.")


def filter_records(records, args):
    filtered = list(records)
    hazard_type = args.get("hazard_type")
    severity = args.get("severity")
    status = args.get("status")
    search = args.get("search", "").strip().lower()
    start_date = args.get("start_date")
    end_date = args.get("end_date")

    if hazard_type:
        filtered = [
            record for record in filtered if record["hazard_type"].lower() == hazard_type.lower()
        ]
    if severity:
        filtered = [record for record in filtered if record["severity"] == severity.lower()]
    if status:
        filtered = [record for record in filtered if record["status"] == status.lower()]
    if search:
        filtered = [
            record
            for record in filtered
            if search in record["location"].lower()
            or search in record["hazard_type"].lower()
        ]

    if start_date:
        start_dt = parse_iso_datetime(f"{start_date}T00:00:00")
        if start_dt:
            filtered = [
                record
                for record in filtered
                if parse_iso_datetime(record["reported_at"]) >= start_dt
            ]
    if end_date:
        end_dt = parse_iso_datetime(f"{end_date}T23:59:59")
        if end_dt:
            filtered = [
                record
                for record in filtered
                if parse_iso_datetime(record["reported_at"]) <= end_dt
            ]

    return filtered


def build_dashboard_summary(records):
    now = datetime.now()
    start_of_day = datetime(now.year, now.month, now.day)
    return {
        "total_detections": len(records),
        "pending_repairs": sum(1 for record in records if record["status"] != "resolved"),
        "critical_unresolved": sum(
            1
            for record in records
            if record["severity"] == "critical" and record["status"] != "resolved"
        ),
        "reported_today": sum(
            1
            for record in records
            if parse_iso_datetime(record["reported_at"]) >= start_of_day
        ),
    }


def build_trend(records, days):
    labels = []
    detections = []
    resolved = []
    today = datetime.now()
    for offset in range(days - 1, -1, -1):
        start = datetime(today.year, today.month, today.day) - timedelta(days=offset)
        end = start + timedelta(days=1)
        labels.append(start.strftime("%d %b"))
        detections.append(
            sum(
                1
                for record in records
                if start <= parse_iso_datetime(record["reported_at"]) < end
            )
        )
        resolved.append(
            sum(
                1
                for record in records
                if record["resolved_at"]
                and start <= parse_iso_datetime(record["resolved_at"]) < end
            )
        )
    return {"labels": labels, "detections": detections, "resolved": resolved}


def aggregate_counts(records, field_name):
    counts = {}
    for record in records:
        key = record[field_name]
        counts[key] = counts.get(key, 0) + 1
    return [{"label": label, "count": count} for label, count in sorted(counts.items())]


def build_priority_queue(records):
    unresolved = [record for record in records if record["status"] != "resolved"]
    unresolved.sort(
        key=lambda item: (
            SEVERITY_RANK[item["severity"]],
            parse_iso_datetime(item["reported_at"]),
        )
    )
    return [serialize_record(record) for record in unresolved]


def build_hotspots(records):
    hotspots = {}
    for record in records:
        key = (record["location"], record["lat"], record["lng"])
        if key not in hotspots:
            hotspots[key] = {
                "location": record["location"],
                "lat": record["lat"],
                "lng": record["lng"],
                "count": 0,
                "worst_severity": record["severity"],
            }
        hotspots[key]["count"] += 1
        if SEVERITY_RANK[record["severity"]] < SEVERITY_RANK[hotspots[key]["worst_severity"]]:
            hotspots[key]["worst_severity"] = record["severity"]

    ordered = sorted(
        hotspots.values(),
        key=lambda item: (-item["count"], SEVERITY_RANK[item["worst_severity"]], item["location"]),
    )
    return ordered[:10]


def build_resolution_stats(records):
    resolved_records = [record for record in records if record["resolved_at"]]
    if not resolved_records:
        return {"average_days": 0}
    total_days = sum(
        (
            parse_iso_datetime(record["resolved_at"]) - parse_iso_datetime(record["reported_at"])
        ).total_seconds()
        / 86400
        for record in resolved_records
    )
    return {"average_days": round(total_days / len(resolved_records), 2)}


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


@app.route("/admin", methods=["GET"])
def admin_dashboard():
    return render_template("admin_dashboard.html")


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


@app.route("/api/dashboard/summary", methods=["GET"])
def api_dashboard_summary():
    return jsonify(build_dashboard_summary(DETECTION_RECORDS))


@app.route("/api/dashboard/trend", methods=["GET"])
def api_dashboard_trend():
    days = request.args.get("days", default=7, type=int)
    days = max(1, min(days, 30))
    return jsonify(build_trend(DETECTION_RECORDS, days))


@app.route("/api/dashboard/by-hazard", methods=["GET"])
def api_dashboard_by_hazard():
    return jsonify({"items": aggregate_counts(DETECTION_RECORDS, "hazard_type")})


@app.route("/api/dashboard/by-severity", methods=["GET"])
def api_dashboard_by_severity():
    return jsonify({"items": aggregate_counts(DETECTION_RECORDS, "severity")})


@app.route("/api/dashboard/priority-queue", methods=["GET"])
def api_dashboard_priority_queue():
    return jsonify({"items": build_priority_queue(DETECTION_RECORDS)})


@app.route("/api/dashboard/hotspots", methods=["GET"])
def api_dashboard_hotspots():
    return jsonify({"items": build_hotspots(DETECTION_RECORDS)})


@app.route("/api/detections/", methods=["GET"])
def api_detections():
    filtered = filter_records(DETECTION_RECORDS, request.args)
    filtered.sort(key=lambda item: parse_iso_datetime(item["reported_at"]), reverse=True)

    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=20, type=int)
    page = max(1, page)
    per_page = max(1, min(per_page, 50))
    start_index = (page - 1) * per_page
    end_index = start_index + per_page

    return jsonify(
        {
            "items": [serialize_record(record) for record in filtered[start_index:end_index]],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": len(filtered),
                "total_pages": max(1, (len(filtered) + per_page - 1) // per_page),
            },
        }
    )


@app.route("/api/detections/<int:detection_id>", methods=["GET"])
def api_detection_detail(detection_id):
    return jsonify(serialize_record(get_record_or_404(detection_id)))


@app.route("/api/detections/<int:detection_id>/status", methods=["PATCH"])
def api_detection_status(detection_id):
    record = get_record_or_404(detection_id)
    payload = request.get_json(silent=True) or {}
    status = str(payload.get("status", record["status"])).strip().lower()
    assigned_team = str(payload.get("assigned_team", record["assigned_team"])).strip()
    notes = str(payload.get("notes", record["notes"])).strip()
    updated_by = str(payload.get("updated_by", "Admin Authority")).strip() or "Admin Authority"

    if status not in STATUS_FLOW:
        return jsonify({"error": "Invalid status value."}), 400

    record["status"] = status
    record["status_color"] = STATUS_COLORS[status]
    record["assigned_team"] = assigned_team or record["assigned_team"]
    record["notes"] = notes

    if status == "resolved" and not record["resolved_at"]:
        record["resolved_at"] = datetime.now().isoformat()
    if status != "resolved":
        record["resolved_at"] = None

    record["activity_log"].append(
        {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "updated_by": updated_by,
            "note": notes or f"Status changed to {status}.",
        }
    )

    return jsonify(
        {
            "message": "Detection updated successfully.",
            "item": serialize_record(record),
        }
    )


if __name__ == "__main__":
    app.run(debug=True)
