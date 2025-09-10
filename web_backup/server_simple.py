"""
KrathongScanner Web Server - Simplified Version
Fast and reliable mobile upload interface
"""

import base64
import io
import os
import signal
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime

import qrcode
from flask import Flask, jsonify, redirect, render_template, request, send_file, url_for
from werkzeug.utils import secure_filename

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from auto_directory_detector import AutoDirectoryDetector

app = Flask(__name__)
app.config["SECRET_KEY"] = "krathong-scanner-2024"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
RESULTS_FOLDER = os.path.join(os.path.dirname(__file__), "results")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp"}

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

# Global variables
auto_detector = None
auto_detector_thread = None
public_url = None
processing_jobs = {}
stop_monitoring = False


def allowed_file(filename):
    """Check if file extension is allowed"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


class ProcessingJob:
    """Track individual file processing jobs"""

    def __init__(self, job_id, filename):
        self.job_id = job_id
        self.filename = filename
        self.status = "pending"
        self.result_file = None
        self.error_message = None
        self.created_at = datetime.now()


def generate_qr_code(url):
    """Generate QR code for the given URL"""
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64 for web display
        img_buffer = io.BytesIO()
        img.save(img_buffer, format="PNG")
        img_buffer.seek(0)
        img_b64 = base64.b64encode(img_buffer.getvalue()).decode()

        return f"data:image/png;base64,{img_b64}"

    except Exception as e:
        print(f"❌ Failed to generate QR code: {e}")
        return None


def generate_and_save_qr_codes():
    """Generate and save QR codes as files"""
    try:
        # Generate local QR code
        local_url = "http://127.0.0.1:5000"
        local_qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        local_qr.add_data(local_url)
        local_qr.make(fit=True)
        local_img = local_qr.make_image(fill_color="black", back_color="white")

        # Save to static folder
        static_dir = os.path.join(os.path.dirname(__file__), "static")
        os.makedirs(static_dir, exist_ok=True)

        # Save local QR code
        local_path = os.path.join(static_dir, "qr_local.png")
        local_img.save(local_path)
        print(f"📱 Local QR code saved: {local_path}")

        # Generate and save public QR code if available
        if public_url:
            public_qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            public_qr.add_data(public_url)
            public_qr.make(fit=True)
            public_img = public_qr.make_image(fill_color="black", back_color="white")

            public_path = os.path.join(static_dir, "qr_public.png")
            public_img.save(public_path)
            print(f"🌍 Public QR code saved: {public_path}")

    except Exception as e:
        print(f"❌ Failed to generate QR code files: {e}")


def monitor_directory():
    """Monitor directory for new files"""
    global stop_monitoring

    if auto_detector is None:
        return

    try:
        # Initial scan
        auto_detector.scan_and_process()

        # Continuous monitoring
        while not stop_monitoring:
            time.sleep(auto_detector.check_interval)
            if not stop_monitoring:
                auto_detector.scan_and_process()

    except Exception as e:
        print(f"❌ Auto-detector monitoring error: {e}")


def setup_auto_detector():
    """Initialize the auto directory detector"""
    global auto_detector, auto_detector_thread, stop_monitoring

    if auto_detector is None:
        auto_detector = AutoDirectoryDetector(
            input_directory=UPLOAD_FOLDER,
            output_directory=RESULTS_FOLDER,
            use_homography=True,
        )

        # Start monitoring in a separate thread
        stop_monitoring = False
        auto_detector_thread = threading.Thread(target=monitor_directory, daemon=True)
        auto_detector_thread.start()
        print("✅ Auto-directory detector started")


def process_uploaded_file(job_id, filepath):
    """Process uploaded file and update job status"""
    global processing_jobs

    job = processing_jobs.get(job_id)
    if not job:
        return

    try:
        job.status = "processing"
        print(f"🔄 Processing {job.filename}...")

        filename_base = os.path.splitext(job.filename)[0]
        expected_result = os.path.join(RESULTS_FOLDER, f"processed_{filename_base}.png")

        # Wait for processing (max 30 seconds)
        wait_time = 0
        while wait_time < 30:
            if os.path.exists(expected_result):
                job.status = "completed"
                job.result_file = f"processed_{filename_base}.png"
                print(f"✅ Processing completed: {job.result_file}")
                return

            time.sleep(1)
            wait_time += 1

        # Timeout
        job.status = "error"
        job.error_message = "Processing timeout"
        print(f"⏰ Processing timeout for {job.filename}")

    except Exception as e:
        job.status = "error"
        job.error_message = str(e)
        print(f"❌ Processing error for {job.filename}: {e}")


@app.route("/")
def index():
    """Main upload page"""
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload_file():
    """Handle file upload"""
    if "file" not in request.files:
        return jsonify({"error": "No file selected"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if file and allowed_file(file.filename):
        # Generate unique job ID
        job_id = str(uuid.uuid4())

        # Secure filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        filename = f"{timestamp}_{name}{ext}"

        # Save file
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        # Create processing job
        job = ProcessingJob(job_id, filename)
        processing_jobs[job_id] = job

        # Start processing in background thread
        processing_thread = threading.Thread(
            target=process_uploaded_file, args=(job_id, filepath), daemon=True
        )
        processing_thread.start()

        return jsonify(
            {
                "success": True,
                "job_id": job_id,
                "filename": filename,
                "message": "File uploaded successfully, processing started",
            }
        )
    else:
        return jsonify({"error": "Invalid file type"}), 400


@app.route("/status/<job_id>")
def check_status(job_id):
    """Check processing status"""
    job = processing_jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    response = {
        "job_id": job_id,
        "status": job.status,
        "filename": job.filename,
        "created_at": job.created_at.isoformat(),
    }

    if job.status == "completed" and job.result_file:
        response["download_url"] = url_for("download_result", filename=job.result_file)
        response["preview_url"] = url_for("preview_result", filename=job.result_file)

    if job.status == "error" and job.error_message:
        response["error"] = job.error_message

    return jsonify(response)


@app.route("/download/<filename>")
def download_result(filename):
    """Download processed result"""
    try:
        filepath = os.path.join(RESULTS_FOLDER, filename)
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True)
        else:
            return jsonify({"error": "File not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/preview/<filename>")
def preview_result(filename):
    """Preview processed result"""
    try:
        filepath = os.path.join(RESULTS_FOLDER, filename)
        if os.path.exists(filepath):
            return send_file(filepath)
        else:
            return jsonify({"error": "File not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/status")
def server_status():
    """Server status and info page"""
    global public_url

    status_info = {
        "server_running": True,
        "public_url": public_url,
        "active_jobs": len(
            [
                j
                for j in processing_jobs.values()
                if j.status in ["pending", "processing"]
            ]
        ),
        "completed_jobs": len(
            [j for j in processing_jobs.values() if j.status == "completed"]
        ),
        "total_jobs": len(processing_jobs),
        "auto_detector_running": auto_detector is not None,
    }

    # Generate QR code if we have public URL
    qr_code = None
    if public_url:
        qr_code = generate_qr_code(public_url)

    return render_template("status.html", status=status_info, qr_code=qr_code)


@app.route("/jobs")
def list_jobs():
    """List all processing jobs"""
    jobs_list = []
    for job in processing_jobs.values():
        job_data = {
            "job_id": job.job_id,
            "filename": job.filename,
            "status": job.status,
            "created_at": job.created_at.isoformat(),
        }

        if job.status == "completed" and job.result_file:
            job_data["download_url"] = url_for(
                "download_result", filename=job.result_file
            )

        if job.status == "error" and job.error_message:
            job_data["error"] = job.error_message

        jobs_list.append(job_data)

    # Sort by creation time (newest first)
    jobs_list.sort(key=lambda x: x["created_at"], reverse=True)

    return jsonify(jobs_list)


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    global stop_monitoring
    print("\n🔄 Shutting down server...")
    stop_monitoring = True
    print("✅ Server shutdown complete")
    sys.exit(0)


if __name__ == "__main__":
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)

    try:
        print("🚀 Starting KrathongScanner Web Server (Simple Version)...")

        # Setup auto detector
        setup_auto_detector()

        # Simple tunnel check (optional)
        print("🚇 Checking for public tunnel...")
        try:
            result = subprocess.run(
                ["npx", "localtunnel", "--port", "5000"],
                capture_output=True,
                text=True,
                timeout=3,
            )
            if result.returncode == 0 and "your url is:" in result.stdout:
                import re

                url_match = re.search(r"https://[^\s]+\.loca\.lt", result.stdout)
                if url_match:
                    public_url = url_match.group(0)
                    print(f"✅ Public URL available: {public_url}")
            else:
                print("💡 For public access, run: npx localtunnel --port 5000")
        except:
            print(
                "💡 For public access, install Node.js and run: npx localtunnel --port 5000"
            )

        # Generate QR codes
        generate_and_save_qr_codes()

        print("📂 Upload folder:", UPLOAD_FOLDER)
        print("📁 Results folder:", RESULTS_FOLDER)
        print("\n" + "=" * 50)
        print("🎯 Server Ready! Upload images to process them automatically")
        if public_url:
            print(f"🌐 Public URL: {public_url}")
        print("=" * 50 + "\n")

        # Start Flask server
        app.run(host="0.0.0.0", port=5000, debug=False)

    except KeyboardInterrupt:
        signal_handler(None, None)
    except Exception as e:
        print(f"❌ Server error: {e}")
        signal_handler(None, None)
