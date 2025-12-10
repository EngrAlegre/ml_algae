"""
AMLAC Robot - Simple Web Interface (Polling-based)

Provides a lightweight Flask server to:
 - Serve a dashboard (auto-refreshing every few seconds)
 - Expose JSON endpoints for current status, logs, and statistics

Design choices:
 - Uses CSV logs already produced by the robot (no extra DB)
 - Simple polling from the browser (easy and reliable)
 - No external services required (no Firebase)
"""

import os
import csv
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, jsonify

# Ensure imports work when running from web/ or repo root
import sys
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from config import LOGS_DIR, ROBOT_NAME, ROBOT_VERSION  # noqa: E402

app = Flask(__name__)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def get_latest_log_file():
    """Return the most recent CSV log file path, or None if none exist."""
    log_files = sorted(Path(LOGS_DIR).glob("amlac_log_*.csv"))
    return log_files[-1] if log_files else None


def read_latest_logs(limit=100):
    """Read latest rows from the newest log file."""
    log_file = get_latest_log_file()
    if not log_file:
        return []

    rows = []
    try:
        with open(log_file, newline="", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            rows = reader[-limit:] if reader else []
    except Exception as e:
        print(f"[web] Error reading log file: {e}")
    return rows[::-1]  # newest first


def current_status():
    """Return the most recent status snapshot."""
    logs = read_latest_logs(limit=1)
    latest = logs[0] if logs else {}

    return {
        "timestamp": latest.get("timestamp", "N/A"),
        "system_status": latest.get("system_status", "No data"),
        "gps": {
            "lat": latest.get("gps_latitude", "N/A"),
            "lon": latest.get("gps_longitude", "N/A"),
            "alt": latest.get("gps_altitude", "N/A"),
        },
        "sensors": {
            "color": {
                "r": latest.get("color_r", "N/A"),
                "g": latest.get("color_g", "N/A"),
                "b": latest.get("color_b", "N/A"),
            },
            "distance_cm": latest.get("distance_cm", "N/A"),
            "weight_kg": latest.get("weight_kg", "N/A"),
            "water_level": latest.get("water_level", "N/A"),
        },
        "ml": {
            "result": latest.get("ml_result", "N/A"),
            "confidence": latest.get("ml_confidence", "N/A"),
        },
        "motor_state": latest.get("motor_state", "N/A"),
    }


def summary_stats(limit=500):
    """Compute simple statistics from recent logs."""
    logs = read_latest_logs(limit=limit)
    if not logs:
        return {
            "total_logs": 0,
            "algae_detections": 0,
            "max_weight_kg": 0,
            "collection_events": 0,
            "success_rate": 0,
        }

    algae_detections = sum(
        1 for row in logs if str(row.get("ml_result", "")).lower() == "algae"
    )

    weights = []
    for row in logs:
        try:
            weights.append(float(row.get("weight_kg", 0) or 0))
        except ValueError:
            continue

    collection_events = 0
    prev_state = None
    for row in logs:
        state = row.get("motor_state", "")
        if prev_state and "forward" in prev_state and state == "stopped":
            collection_events += 1
        prev_state = state

    total = len(logs)
    return {
        "total_logs": total,
        "algae_detections": algae_detections,
        "max_weight_kg": round(max(weights) if weights else 0, 2),
        "collection_events": collection_events,
        "success_rate": round((algae_detections / total * 100), 1) if total else 0,
    }


# --------------------------------------------------------------------------- #
# Routes
# --------------------------------------------------------------------------- #
@app.route("/")
def index():
    return render_template(
        "index.html",
        robot_name=ROBOT_NAME,
        robot_version=ROBOT_VERSION,
    )


@app.route("/logs")
def logs_page():
    return render_template(
        "logs.html",
        robot_name=ROBOT_NAME,
        robot_version=ROBOT_VERSION,
    )


@app.route("/api/status")
def api_status():
    return jsonify(current_status())


@app.route("/api/logs")
def api_logs():
    limit = int(os.environ.get("LOG_LIMIT", 100))
    return jsonify(read_latest_logs(limit=limit))


@app.route("/api/stats")
def api_stats():
    return jsonify(summary_stats())


if __name__ == "__main__":
    # Run on all interfaces so you can view from your LAN
    # Access from another device: http://<pi-ip>:5000
    app.run(host="0.0.0.0", port=5000, debug=False)

