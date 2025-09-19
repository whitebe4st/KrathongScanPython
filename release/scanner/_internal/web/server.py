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
from enhanced_auto_directory_detector import EnhancedAutoDirectoryDetector
from tunneling.bundled_instatunnel import (
    get_bundled_tunnel_url,
    is_bundled_tunnel_available,
    is_bundled_tunnel_running,
    start_bundled_tunnel,
    stop_bundled_tunnel,
    test_bundled_tunnel_connection,
)

# Ensure console can print Unicode on Windows (avoid cp1252 errors)
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

app = Flask(__name__)
app.config["SECRET_KEY"] = "krathong-scanner-2024"
app.config["MAX_CONTENT_LENGTH"] = (
    50 * 1024 * 1024
)  # 50MB max file size for large photos


# LocalTunnel bypass middleware
@app.before_request
def bypass_localtunnel_warning():
    """Add headers to bypass LocalTunnel warning page"""
    from flask import request

    # Check if this is coming through LocalTunnel
    if "loca.lt" in request.host or "localtunnel" in request.headers.get("host", ""):
        # Add bypass headers
        request.environ["HTTP_X_FORWARDED_PROTO"] = "https"
        request.environ["HTTP_X_REAL_IP"] = request.remote_addr


@app.after_request
def add_bypass_headers(response):
    """Add headers to help bypass LocalTunnel warnings"""
    if "loca.lt" in request.host or "localtunnel" in request.headers.get("host", ""):
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


@app.errorhandler(413)
def file_too_large(error):
    """Handle file too large errors"""
    return (
        jsonify(
            {
                "success": False,
                "error": "File too large",
                "message": "The uploaded file is too large. Please use a smaller image (max 50MB) or compress your photo.",
                "code": 413,
            }
        ),
        413,
    )


@app.errorhandler(400)
def bad_request(error):
    """Handle bad request errors"""
    return (
        jsonify(
            {
                "success": False,
                "error": "Bad request",
                "message": "Invalid request. Please check your file and try again.",
                "code": 400,
            }
        ),
        400,
    )


# Configuration
UPLOAD_FOLDER = os.environ.get(
    "KRATHONG_UPLOAD_FOLDER", os.path.join(os.path.dirname(__file__), "uploads")
)
RESULTS_FOLDER = os.environ.get(
    "KRATHONG_RESULTS_FOLDER", os.path.join(os.path.dirname(__file__), "results")
)
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
        self.cropped_file = None
        self.masked_file = None
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

    # COMMENTED OUT: Auto-detector creates duplicate files
    # Only use manual processing pipeline to avoid duplicate outputs
    print("🚫 Auto-directory detector disabled to prevent duplicate file creation")

    # if auto_detector is None:
    #     # Prefer enhanced pipeline: detect paper -> detect aruco -> apply mask
    #     try:
    #         auto_detector = EnhancedAutoDirectoryDetector(
    #             input_directory=UPLOAD_FOLDER,
    #             output_directory=RESULTS_FOLDER,
    #             check_interval=2.0,
    #             use_document_detection=True,
    #         )
    #         print("✅ Enhanced auto-directory detector initialized")
    #     except Exception as e:
    #         print(
    #             f"⚠️ Enhanced detector unavailable ({e}), falling back to legacy detector"
    #         )
    #         auto_detector = AutoDirectoryDetector(
    #             input_directory=UPLOAD_FOLDER,
    #             output_directory=RESULTS_FOLDER,
    #             use_homography=True,
    #         )

    #     # Start monitoring in a separate thread
    #     stop_monitoring = False
    #     auto_detector_thread = threading.Thread(target=monitor_directory, daemon=True)
    #     auto_detector_thread.start()
    #     print("✅ Auto-directory detector started")


def process_uploaded_file(job_id, filepath):
    """Process uploaded file and update job status"""
    global processing_jobs

    job = processing_jobs.get(job_id)
    if not job:
        return

    try:
        job.status = "processing"
        print(f"🔄 Processing {job.filename}...")

        # Import ArUco detector
        import os
        import sys
        from pathlib import Path

        # Add src directory to path more reliably
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        src_path = os.path.join(project_root, "src")

        # FIXED: Also add project root for database imports
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
            print(f"🔧 Added project root: {project_root}")

        if src_path not in sys.path:
            sys.path.insert(0, src_path)
            print(f"🔧 Added src path: {src_path}")

        # Try importing with error handling
        try:
            from aruco_detector.detector import ArUcoDetector

            print("✅ ArUcoDetector imported successfully")
        except ImportError as e:
            print(f"❌ Failed to import ArUcoDetector: {e}")
            # Try alternative import path
            sys.path.insert(0, project_root)
            from src.aruco_detector.detector import ArUcoDetector

            print("✅ ArUcoDetector imported with alternative path")

        try:
            from enhanced_rectangle_cropper import detect_and_crop_rectangle_enhanced

            print("✅ Enhanced rectangle cropper imported successfully")
        except ImportError as e:
            print(f"❌ Failed to import enhanced_rectangle_cropper: {e}")
            from src.enhanced_rectangle_cropper import (
                detect_and_crop_rectangle_enhanced,
            )

            print("✅ Enhanced rectangle cropper imported with alternative path")

        try:
            from paper_detector import PaperDetector

            print("✅ PaperDetector imported successfully")
        except ImportError as e:
            print(f"❌ Failed to import PaperDetector: {e}")
            from src.paper_detector import PaperDetector

            print("✅ PaperDetector imported with alternative path")

        # Initialize detectors
        detector = ArUcoDetector()
        paper_detector = PaperDetector(target_size=(1280, 720))

        # Load and process the image
        import cv2

        image = cv2.imread(filepath)
        if image is None:
            job.status = "error"
            job.error_message = "Could not load image file"
            print(f"❌ Could not load image: {filepath}")
            return

        # 1) First try paper detection to get perspective-corrected document
        processing_image, paper_ok = paper_detector.process_with_auto_zoom(image)
        if paper_ok:
            print(f"� Paper detector succeeded for {job.filename}")
        else:
            print(f"⚠️ Paper detector failed; using original image for {job.filename}")
            processing_image = image

        # 2) Try ArUco marker detection first (most precise for templates with markers)
        markers = detector.detect_markers(processing_image)
        marker_ids = [m.id for m in markers] if markers else []
        template_id = detector.detect_template(marker_ids) if marker_ids else None

        if markers and template_id:
            print(f"🎯 Found ArUco template: {template_id}")
            corner_markers = detector.get_corner_markers(markers)
            if corner_markers is not None:
                print("🎯 Using ArUco-based cropping")
                cropped = detector._apply_homography_and_crop(
                    processing_image, corner_markers
                )
            else:
                job.status = "error"
                job.error_message = "Could not find all corner markers"
                print(f"❌ Missing corner markers in {job.filename}")
                return
        else:
            print("🔍 No ArUco markers found, trying rectangle detection...")
            # 3) Fallback to rectangle detection for non-ArUco templates
            rect_cropped, rect_contour = detect_and_crop_rectangle_enhanced(
                processing_image
            )
            if rect_cropped is not None:
                print("🟩 Rectangle area detected; using rectangle-cropped image")
                cropped = rect_cropped
                # Normalize to target canvas to align with template masks
                try:
                    TARGET_W, TARGET_H = 779, 457
                    if cropped.shape[1] != TARGET_W or cropped.shape[0] != TARGET_H:
                        cropped = cv2.resize(
                            cropped,
                            (TARGET_W, TARGET_H),
                            interpolation=cv2.INTER_LANCZOS4,
                        )
                        print(
                            f"📏 Resized rectangle crop to {TARGET_W}x{TARGET_H} for mask alignment"
                        )
                except Exception as _e:
                    pass
                # Re-detect on cropped image for template identification
                markers = detector.detect_markers(cropped)
                marker_ids = [m.id for m in markers] if markers else []
                template_id = (
                    detector.detect_template(marker_ids) if marker_ids else None
                )
            else:
                print("❌ Rectangle detection also failed")
                job.status = "error"
                job.error_message = (
                    "Could not detect document boundary or ArUco markers"
                )
                print(f"❌ No detection method succeeded for {job.filename}")
                return

        # Get template mask path (mask1-4_final.png mapping)
        template_mask_path = None
        try:
            template_mask_path = detector.get_template_mask_path()
        except Exception:
            pass

        if not template_mask_path and template_id:
            import re

            m = re.search(r"(\d+)$", template_id)
            num = m.group(1) if m else None
            if num:
                for candidate in [
                    f"data/markers/templates/mask{num}_final.png",
                    f"data/markers/templates/mask{num}.png",
                    f"data/templates/mask{num}_final.png",
                    f"data/templates/mask{num}.png",
                ]:
                    if os.path.exists(candidate):
                        template_mask_path = candidate
                        break

        if template_mask_path:
            # Apply template mask and keep full 779x457 canvas (match webcam behavior)
            masked = detector.apply_template_mask(cropped, template_mask_path)

            # Content-crop the masked image to krathong only (this is the perfect aligned version)
            final_masked = detector._crop_masked_area(masked)
            print(
                f"🎯 Content-cropped masked image to: {final_masked.shape[1]}x{final_masked.shape[0]}"
            )
        else:
            print("⚠️ No template mask available, using cropped image")
            final_masked = None
            processed_image = cropped

        # Save only the masked (content-cropped) image as the main result
        filename_base = os.path.splitext(job.filename)[0]
        masked_filename = f"processed_{filename_base}_masked.png"
        masked_path = os.path.join(RESULTS_FOLDER, masked_filename)

        if final_masked is not None:
            print(f"🔧 Saving masked result to: {masked_path}")
            print(f"🔧 Results folder: {RESULTS_FOLDER}")
            print(f"🔧 Image shape: {final_masked.shape}")
            print(f"🔧 Image dtype: {final_masked.dtype}")

            success = cv2.imwrite(masked_path, final_masked)

            print(f"🔧 cv2.imwrite returned: {success}")
            file_exists = os.path.exists(masked_path)
            print(f"🔧 File exists after save: {file_exists}")

            if file_exists:
                file_size = os.path.getsize(masked_path)
                print(f"🔧 File size: {file_size} bytes")

            if success:
                job.status = "completed"
                job.result_file = (
                    masked_filename  # Use the masked file as the main result
                )
                print(f"✅ Processing completed: {job.result_file}")

                # Log template info if available
                if template_id:
                    print(f"📋 Detected template: {template_id}")
            else:
                job.status = "error"
                job.error_message = "Failed to save processed image"
                print(f"❌ Failed to save processed image: {masked_path}")
        else:
            job.status = "error"
            job.error_message = "No template mask available"
            print("❌ Processing failed: No template mask available")

    except Exception as e:
        job.status = "error"
        job.error_message = str(e)
        print(f"❌ Processing error for {job.filename}: {e}")
        import traceback

        traceback.print_exc()


@app.route("/")
def index():
    """Main upload page"""
    return render_template("index.html")


@app.route("/bypass")
@app.route("/continue")
@app.route("/direct")
def bypass_warning():
    """Direct bypass route for LocalTunnel warning page"""
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
        # Convert to absolute path to handle relative path issues
        filepath = os.path.abspath(filepath)

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
        # Ensure we're looking for the PNG file, not JSON
        if filename.endswith(".json"):
            # If someone is trying to preview JSON, redirect to the PNG
            png_filename = filename.replace(".json", ".png")
            filepath = os.path.join(RESULTS_FOLDER, png_filename)
        else:
            filepath = os.path.join(RESULTS_FOLDER, filename)

        # Convert to absolute path to handle relative path issues
        filepath = os.path.abspath(filepath)

        print(f"🔍 Preview request for: {filename}")
        print(f"🔍 Looking for file at: {filepath}")
        print(f"🔍 File exists: {os.path.exists(filepath)}")

        if os.path.exists(filepath):
            print(f"✅ Serving preview file: {filepath}")
            # Explicitly set content type for images
            if filepath.lower().endswith((".png", ".jpg", ".jpeg")):
                return send_file(
                    filepath,
                    mimetype="image/png" if filepath.endswith(".png") else "image/jpeg",
                )
            else:
                return send_file(filepath)
        else:
            print(f"❌ Preview file not found: {filepath}")
            return jsonify({"error": "File not found"}), 404
    except Exception as e:
        print(f"❌ Preview error: {e}")
        import traceback

        traceback.print_exc()
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


@app.route("/api/status")
def api_status():
    """API endpoint for server status - returns JSON"""
    global public_url

    # Check tunnel status
    tunnel_running = (
        is_bundled_tunnel_running() if is_bundled_tunnel_available() else False
    )
    tunnel_connected = test_bundled_tunnel_connection() if tunnel_running else False

    status_info = {
        "server_running": True,
        "public_url": public_url,
        "tunnel_running": tunnel_running,
        "tunnel_connected": tunnel_connected,
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

    return jsonify(status_info)


@app.route("/update_tunnel_url", methods=["POST"])
def update_tunnel_url():
    """Update the public tunnel URL and generate QR codes"""
    global public_url

    data = request.get_json()
    if not data or "url" not in data:
        return jsonify({"error": "URL is required"}), 400

    new_url = data["url"]

    # Validate URL format
    if not new_url.startswith("https://") or ".loca.lt" not in new_url:
        return jsonify({"error": "Invalid LocalTunnel URL format"}), 400

    # Update global URL
    old_url = public_url
    public_url = new_url

    try:
        # Generate new QR codes
        generate_and_save_qr_codes()

        # Generate high-quality mall QR code
        qr = qrcode.QRCode(
            version=2,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=12,
            border=6,
        )
        qr.add_data(public_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        mall_qr_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "mall_public_qr_auto.png"
        )
        img.save(mall_qr_path)

        return jsonify(
            {
                "success": True,
                "old_url": old_url,
                "new_url": public_url,
                "qr_generated": True,
                "mall_qr_path": mall_qr_path,
                "message": "Tunnel URL updated and QR codes generated successfully",
            }
        )

    except Exception as e:
        # Rollback on error
        public_url = old_url
        return jsonify({"error": f"Failed to generate QR codes: {str(e)}"}), 500


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


@app.route("/api/tunnel/status")
def tunnel_status():
    """Get detailed tunnel status for diagnostics"""
    try:
        from tunneling.bundled_instatunnel import bundled_tunnel

        if bundled_tunnel.is_available():
            status = bundled_tunnel.get_tunnel_status()

            # Add timestamp
            import datetime

            status["timestamp"] = datetime.datetime.now().isoformat()
            status["available"] = True

            return jsonify(status)
        else:
            return jsonify(
                {
                    "available": False,
                    "error_message": "Bundled InstaTunnel not available",
                    "timestamp": datetime.datetime.now().isoformat(),
                }
            )

    except Exception as e:
        return (
            jsonify(
                {
                    "available": False,
                    "error_message": f"Status check failed: {e}",
                    "timestamp": datetime.datetime.now().isoformat(),
                }
            ),
            500,
        )


def start_localtunnel(port):
    """Start LocalTunnel for public access"""
    global public_url

    try:
        print(f"🚇 Starting LocalTunnel on port {port}...")

        # Find the correct npx executable for Windows
        npx_cmd = "npx"
        possible_paths = [
            r"C:\Program Files\nodejs\npx.cmd",
            r"C:\Program Files (x86)\nodejs\npx.cmd",
            "npx.cmd",
            "npx",
        ]

        # Try to find a working npx command
        npx_found = False
        for npx_path in possible_paths:
            try:
                check_result = subprocess.run(
                    [npx_path, "--version"], capture_output=True, text=True, timeout=3
                )
                if check_result.returncode == 0:
                    npx_cmd = npx_path
                    npx_found = True
                    print(f"✅ Found npx at: {npx_cmd}")
                    break
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue

        if not npx_found:
            print("❌ NPX not found. Make sure Node.js is installed")
            return None

        # Try to start LocalTunnel with the working npx command
        env = os.environ.copy()

        # Generate a custom subdomain to reduce warning pages
        import random
        import string

        custom_subdomain = "krathong-" + "".join(
            random.choices(string.ascii_lowercase + string.digits, k=8)
        )

        # Start LocalTunnel as a background process with bypass reminder and print URL
        print("🚇 Starting LocalTunnel as background process...")
        process = subprocess.Popen(
            [
                npx_cmd,
                "localtunnel",
                "--port",
                str(port),
                "--print-requests",
                "--bypass-tunnel-reminder",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )

        # Give it a few seconds to start and capture initial output
        try:
            stdout, stderr = process.communicate(timeout=5)
            print(f"🔍 LocalTunnel stdout: {stdout}")
            print(f"🔍 LocalTunnel stderr: {stderr}")
            print(f"🔍 LocalTunnel return code: {process.returncode}")

            if "your url is:" in stdout:
                import re

                url_match = re.search(r"https://[^\s]+\.loca\.lt", stdout)
                if url_match:
                    public_url = url_match.group(0)
                    print(f"✅ LocalTunnel started: {public_url}")

                    # Generate QR code after tunnel is ready
                    threading.Thread(
                        target=auto_detect_tunnel_and_generate_qr, daemon=True
                    ).start()

                    return public_url
            else:
                print("⚠️ LocalTunnel failed to start properly")
                if stderr:
                    print(f"Error details: {stderr}")
                return None

        except subprocess.TimeoutExpired:
            # LocalTunnel is still running, try to read the output differently
            print("🔍 LocalTunnel is running, trying to detect URL...")

            # Kill the process since we can't get the URL this way
            process.terminate()

            # Alternative approach: start LocalTunnel and parse output in real-time
            return start_localtunnel_realtime(npx_cmd, port, env)

    except subprocess.TimeoutExpired:
        print("⚠️ LocalTunnel startup timeout (10 seconds)")
        return None
    except Exception as e:
        print(f"❌ LocalTunnel error: {e}")
        return None


def start_localtunnel_realtime(npx_cmd, port, env):
    """Start LocalTunnel and parse output in real-time"""
    global public_url

    try:
        print("🚇 Starting LocalTunnel with real-time output parsing...")

        # Generate a custom subdomain to reduce warning pages
        import random
        import string

        custom_subdomain = "krathong-" + "".join(
            random.choices(string.ascii_lowercase + string.digits, k=8)
        )

        # Start the process with bypass reminder and print requests
        process = subprocess.Popen(
            [
                npx_cmd,
                "localtunnel",
                "--port",
                str(port),
                "--print-requests",
                "--bypass-tunnel-reminder",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env,
            bufsize=1,
            universal_newlines=True,
        )

        # Read output line by line with timeout
        import select
        import time

        start_time = time.time()
        timeout = 10  # 10 seconds timeout

        while time.time() - start_time < timeout:
            if process.poll() is not None:
                # Process has terminated
                break

            # Try to read a line with a short timeout
            try:
                line = process.stdout.readline()
                if line:
                    print(f"🔍 LocalTunnel output: {line.strip()}")

                    if "your url is:" in line:
                        import re

                        url_match = re.search(r"https://[^\s]+\.loca\.lt", line)
                        if url_match:
                            public_url = url_match.group(0)
                            print(f"✅ LocalTunnel started: {public_url}")

                            # Don't terminate the process, let it keep running
                            # Generate QR code after tunnel is ready
                            threading.Thread(
                                target=auto_detect_tunnel_and_generate_qr, daemon=True
                            ).start()

                            return public_url
            except:
                pass

            time.sleep(0.1)  # Small delay

        print("⚠️ LocalTunnel URL not detected within timeout")
        return None

    except Exception as e:
        print(f"❌ LocalTunnel real-time error: {e}")
        return None

    except subprocess.TimeoutExpired:
        print("⚠️ LocalTunnel startup timeout (10 seconds)")
        return None
    except Exception as e:
        print(f"❌ LocalTunnel error: {e}")
        return None


def start_instatunnel(port):
    """Start InstaTunnel for public access using bundled Node.js"""
    global public_url

    try:
        print(f"🚀 Starting bundled InstaTunnel on port {port}...")

        # Check if we already have a working tunnel
        if public_url:
            print(f"🔍 Checking existing tunnel: {public_url}")
            try:
                import urllib.request

                with urllib.request.urlopen(public_url, timeout=5) as response:
                    if response.status == 200:
                        print(f"✅ Existing tunnel still working: {public_url}")
                        return public_url
                    else:
                        print(f"⚠️ Existing tunnel not responding, will restart")
            except Exception as e:
                print(f"⚠️ Existing tunnel failed ({e}), will restart")

        # Try bundled InstaTunnel first
        if is_bundled_tunnel_available():
            url = start_bundled_tunnel(port)
            if url:
                public_url = url
                print(f"✅ Tunnel started successfully: {url}")

                # Extended wait for tunnel stabilization with loading indicator
                print("⏱️ Stabilizing tunnel connection...")

                # Show loading progress for stabilization
                import threading

                stabilizing = True

                def show_stabilizing():
                    chars = "🔄🔃🔄🔃"
                    i = 0
                    while stabilizing:
                        print(
                            f"\r{chars[i % len(chars)]} Checking tunnel stability...",
                            end="",
                            flush=True,
                        )
                        time.sleep(0.5)
                        i += 1

                stabilizing_thread = threading.Thread(
                    target=show_stabilizing, daemon=True
                )
                stabilizing_thread.start()

                time.sleep(5)

                # Multiple status checks to ensure stability
                stable_checks = 0
                max_checks = 3

                for check in range(max_checks):
                    # Get comprehensive status
                    try:
                        from tunneling.bundled_instatunnel import bundled_tunnel

                        status = bundled_tunnel.get_tunnel_status()

                        if (
                            status["is_running"]
                            and status["process_alive"]
                            and status["connection_test"]
                        ):
                            stable_checks += 1
                        else:
                            pass  # Status check failed
                    except Exception as e:
                        pass  # Import or status check failed

                    if check < max_checks - 1:  # Don't wait after last check
                        time.sleep(2)

                stabilizing = False  # Stop the loading animation
                print("\r" + " " * 50 + "\r", end="")  # Clear loading line

                if stable_checks >= 2:  # At least 2 out of 3 checks should pass
                    print(
                        f"✅ Tunnel is stable ({stable_checks}/{max_checks} checks passed)"
                    )
                    return url
                else:
                    print(
                        f"⚠️ Tunnel stability checks: ({stable_checks}/{max_checks} passed)"
                    )
                    print("🔄 Continuing anyway - tunnel should work for basic usage")
                    return url
            else:
                print("⚠️ Bundled InstaTunnel failed, trying system InstaTunnel...")
        else:
            print("⚠️ Bundled InstaTunnel not available, trying system InstaTunnel...")

        # Fallback to system InstaTunnel if bundled version fails
        return _start_system_instatunnel(port)

    except Exception as e:
        print(f"❌ InstaTunnel error: {e}")
        import traceback

        traceback.print_exc()
        return None


def _start_system_instatunnel(port):
    """Fallback: Start system InstaTunnel if bundled version is not available"""
    global public_url

    try:
        print(f"🚀 Starting system InstaTunnel on port {port}...")

        # Find the correct InstaTunnel executable for Windows
        instatunnel_cmd = "instatunnel"
        possible_paths = [
            r"C:\Users\white\AppData\Roaming\npm\instatunnel.cmd",
            "instatunnel.cmd",
            "instatunnel",
        ]

        # Try to find a working InstaTunnel command
        instatunnel_found = False
        for tunnel_path in possible_paths:
            try:
                check_result = subprocess.run(
                    [tunnel_path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=3,
                )
                if check_result.returncode == 0:
                    instatunnel_cmd = tunnel_path
                    instatunnel_found = True
                    print(f"✅ Found system InstaTunnel at: {instatunnel_cmd}")
                    break
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue

        if not instatunnel_found:
            print("❌ InstaTunnel not found. Install with: npm install -g instatunnel")
            return None

        # Generate a custom subdomain (optional)
        import random
        import string

        custom_subdomain = "krathong-" + "".join(
            random.choices(string.ascii_lowercase + string.digits, k=6)
        )

        # Start InstaTunnel as a background process - try without custom subdomain first
        print("🚀 Starting InstaTunnel with real-time output parsing...")

        # Try without custom subdomain first for better compatibility
        try:
            process = subprocess.Popen(
                [instatunnel_cmd, str(port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )
        except Exception as e:
            print(f"⚠️ Failed to start InstaTunnel without subdomain: {e}")
            # Fallback to custom subdomain
            process = subprocess.Popen(
                [
                    instatunnel_cmd,
                    str(port),
                    "--subdomain",
                    custom_subdomain,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )

        # Read output line by line with timeout
        import time

        start_time = time.time()
        timeout = 25  # Increased to 25 seconds timeout for InstaTunnel

        while time.time() - start_time < timeout:
            if process.poll() is not None:
                # Process has terminated, read remaining output
                remaining_output = process.stdout.read()
                if remaining_output:
                    print(f"🚀 InstaTunnel final output: {remaining_output.strip()}")

                    # Check for URL in final output
                    if (
                        "Your app is now live at" in remaining_output
                        and "https://" in remaining_output
                    ):
                        import re

                        url_match = re.search(r"https://[^\s]+", remaining_output)
                        if url_match:
                            tunnel_url = url_match.group(0)
                            public_url = tunnel_url
                            print(f"✅ InstaTunnel started: {tunnel_url}")
                            return tunnel_url
                break

            # Try to read a line with a short timeout
            try:
                line = process.stdout.readline()
                if line:
                    line_clean = line.strip()
                    print(f"🚀 InstaTunnel: {line_clean}")

                    # Look for the main InstaTunnel URL output: "Your app is now live at https://..."
                    if (
                        "Your app is now live at" in line_clean
                        and "https://" in line_clean
                    ):
                        import re

                        url_match = re.search(r"https://[^\s]+", line_clean)
                        if url_match:
                            tunnel_url = url_match.group(0)
                            public_url = tunnel_url
                            print(f"✅ InstaTunnel started: {tunnel_url}")

                            # Generate QR code after tunnel is ready
                            threading.Thread(
                                target=auto_detect_tunnel_and_generate_qr, daemon=True
                            ).start()

                            return tunnel_url

                    # Alternative detection: Look for "Forwarding" line
                    if (
                        "Forwarding" in line_clean
                        and "https://" in line_clean
                        and "->" in line_clean
                    ):
                        import re

                        url_match = re.search(r"https://[^\s]+", line_clean)
                        if url_match:
                            tunnel_url = url_match.group(0)
                            public_url = tunnel_url
                            print(f"✅ InstaTunnel started: {tunnel_url}")

                            # Generate QR code after tunnel is ready
                            threading.Thread(
                                target=auto_detect_tunnel_and_generate_qr, daemon=True
                            ).start()

                            return tunnel_url

                    # Fallback: Any line with instatunnel domain
                    if "https://" in line_clean and "instatunnel.my" in line_clean:
                        import re

                        url_match = re.search(
                            r"https://[^\s]+\.instatunnel\.my", line_clean
                        )
                        if url_match:
                            tunnel_url = url_match.group(0)
                            public_url = tunnel_url
                            print(f"✅ InstaTunnel started: {tunnel_url}")

                            # Generate QR code after tunnel is ready
                            threading.Thread(
                                target=auto_detect_tunnel_and_generate_qr, daemon=True
                            ).start()

                            return tunnel_url

            except:
                pass

            time.sleep(0.1)  # Small delay

        print("⚠️ InstaTunnel URL not detected within timeout")
        return None

    except subprocess.TimeoutExpired:
        print("⚠️ InstaTunnel startup timeout (15 seconds)")
        return None
    except Exception as e:
        print(f"❌ InstaTunnel error: {e}")
        return None


def auto_detect_tunnel_and_generate_qr():
    """Automatically detect tunnel URL and generate QR codes"""
    global public_url

    print("🔍 Auto-detecting tunnel URL...")

    # Check multiple times for tunnel URL
    for attempt in range(10):
        try:
            # Check if there's already a tunnel URL from startup
            if public_url:
                print(f"🌐 Using existing tunnel URL: {public_url}")
                return public_url

            # Try to detect LocalTunnel process output
            # Check for active LocalTunnel processes
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq node.exe"],
                capture_output=True,
                text=True,
            )
            if "node.exe" in result.stdout:
                # LocalTunnel is running, try to get the URL
                # This is a simplified detection - in practice, the tunnel URL
                # is usually passed from the startup or external process
                print("🔍 LocalTunnel process detected...")

                # For now, we'll rely on the manual tunnel startup
                # The public_url will be set when tunnel is manually started

        except Exception as e:
            pass

        time.sleep(3)  # Wait 3 seconds between attempts

    print("⚠️ No new tunnel URL detected - use manual tunnel startup")
    return None


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    global stop_monitoring, auto_detector
    print("\n🔄 Shutting down server...")
    stop_monitoring = True

    # Clean up auto detector
    if auto_detector:
        try:
            auto_detector.cleanup_on_exit()
            print("✅ Auto-directory detector cleanup completed")
        except Exception as e:
            print(f"⚠️ Auto-directory detector cleanup error: {e}")

    print("✅ Server shutdown complete")
    sys.exit(0)


if __name__ == "__main__":
    import argparse

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="KrathongScanner Web Server")
    parser.add_argument(
        "--upload-folder",
        default=None,
        help="Directory for uploaded images (default: web/uploads)",
    )
    parser.add_argument(
        "--results-folder",
        default=None,
        help="Directory for processed images (default: web/results)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port to run the web server on (default: 5000)",
    )

    args = parser.parse_args()

    # Override directories if specified via command line
    if args.upload_folder:
        globals()["UPLOAD_FOLDER"] = os.path.abspath(args.upload_folder)
    if args.results_folder:
        globals()["RESULTS_FOLDER"] = os.path.abspath(args.results_folder)

    # Ensure directories exist with updated paths
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(RESULTS_FOLDER, exist_ok=True)

    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)

    try:
        print("🚀 Starting KrathongScanner Web Server...")
        print("=" * 50)

        # Setup auto detector
        print("� Setting up auto-directory processing...")
        # COMMENTED OUT: Auto-detector creates duplicate files
        # setup_auto_detector()
        print("🚫 Auto-directory detector disabled to prevent duplicate file creation")

        # Start Flask server first (local server only)
        print("🌐 Starting local web server...")
        print("📂 Upload folder:", UPLOAD_FOLDER)
        print("📁 Results folder:", RESULTS_FOLDER)

        def start_server():
            app.run(host="0.0.0.0", port=args.port, debug=False, use_reloader=False)

        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()

        # Wait for local server to be ready
        server_ready = False
        max_attempts = 10

        for attempt in range(max_attempts):
            try:
                import urllib.request

                urllib.request.urlopen(f"http://localhost:{args.port}", timeout=2)
                server_ready = True
                print(f"✅ Local server ready at http://localhost:{args.port}")
                break
            except:
                print(f"⏳ Starting local server... ({attempt + 1}/{max_attempts})")
                time.sleep(1)

        if not server_ready:
            print("❌ Local server failed to start")
            exit(1)

        print("=" * 50)
        print("🎯 LOCAL SERVER READY!")
        print(f"💻 You can use the app locally at: http://localhost:{args.port}")
        print("=" * 50)

        # Now optionally create public tunnel
        print("\n🌐 Creating public tunnel for mobile access...")
        print("⏳ This may take 10-30 seconds - please wait...")

        # Show loading progress for tunnel creation
        import threading
        import time

        loading_active = True

        def show_loading():
            chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
            i = 0
            while loading_active:
                print(
                    f"\r{chars[i % len(chars)]} Creating tunnel connection...",
                    end="",
                    flush=True,
                )
                time.sleep(0.1)
                i += 1

        loading_thread = threading.Thread(target=show_loading, daemon=True)
        loading_thread.start()

        public_url = start_instatunnel(args.port)
        loading_active = False
        print("\r" + " " * 50 + "\r", end="")  # Clear loading line

        print("\n" + "=" * 50)
        if public_url:
            print("🎯 TUNNEL READY!")
            print(f"🌐 Public URL: {public_url}")
            print("📱 Scan QR code with your phone to upload photos")
        else:
            print("⚠️ Tunnel creation failed - using local server only")
            print("💻 Access locally at: http://localhost:5000")
        print("=" * 50 + "\n")

        # Generate QR codes with loading indicator
        if public_url:
            print("📱 Generating QR codes...")
            loading_active = True

            def show_qr_loading():
                chars = "📱📲📱📲"
                i = 0
                while loading_active:
                    print(
                        f"\r{chars[i % len(chars)]} Generating QR codes for mobile access...",
                        end="",
                        flush=True,
                    )
                    time.sleep(0.3)
                    i += 1

            qr_loading_thread = threading.Thread(target=show_qr_loading, daemon=True)
            qr_loading_thread.start()

            generate_and_save_qr_codes()
            loading_active = False
            print("\r" + " " * 60 + "\r", end="")  # Clear loading line
            print("✅ QR codes generated successfully!")
        else:
            print("⚠️ Skipping QR code generation (no public URL)")

        # Start automated tunnel detection and QR generation in background
        qr_monitor_thread = threading.Thread(
            target=auto_detect_tunnel_and_generate_qr, daemon=True
        )
        qr_monitor_thread.start()

        # If we already have a public URL, create a high-quality mall QR code
        if public_url:
            try:
                print("🏬 Creating high-quality mall display QR code...")
                qr = qrcode.QRCode(
                    version=2,
                    error_correction=qrcode.constants.ERROR_CORRECT_H,
                    box_size=12,
                    border=6,
                )
                qr.add_data(public_url)
                qr.make(fit=True)

                img = qr.make_image(fill_color="black", back_color="white")
                mall_qr_path = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)), "mall_public_qr.png"
                )
                img.save(mall_qr_path)
                print(f"✅ Mall QR code saved: {mall_qr_path}")
                print("💡 Print this QR code for customer displays!")
            except Exception as e:
                print(f"❌ Failed to generate mall QR code: {e}")

        print("\n" + "🎉" * 20)
        print("🎉 ALL SYSTEMS READY! 🎉")
        print("🎉" * 20)

        if public_url:
            print(f"📱 Mobile URL: {public_url}")
        print(f"💻 Local URL: http://localhost:{args.port}")
        print("🔍 Auto QR monitor active - will detect new tunnel URLs automatically!")
        print("📁 Auto-processing: Drop images in data folder for automatic processing")
        print("🛑 Press Ctrl+C to stop")
        print("=" * 60)

        # Keep the main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            signal_handler(None, None)

    except KeyboardInterrupt:
        signal_handler(None, None)
    except Exception as e:
        print(f"❌ Server error: {e}")
        signal_handler(None, None)


def run_web_server(host="0.0.0.0", port=5000, results_folder=None):
    """Run the KrathongScanner web server - function for GUI integration."""
    import logging

    logger = logging.getLogger("krathong_scanner")

    try:
        logger.info("Starting KrathongScanner Web Server...")
        logger.info(f"Server will be available at http://localhost:{port}")
        logger.info("🔥 Running in frozen mode, starting web server in-process")

        # Set Flask configuration
        app.config["HOST"] = host
        app.config["PORT"] = port

        logger.info(f"Upload folder: {UPLOAD_FOLDER}")
        logger.info(f"Results folder: {RESULTS_FOLDER}")
        logger.info("=" * 50)
        logger.info("🎯 Web Server Ready! Upload images to process them automatically")
        logger.info("=" * 50)

        # Start Flask server in a separate thread
        def start_flask_server():
            app.run(host=host, port=port, debug=False, use_reloader=False)

        flask_thread = threading.Thread(target=start_flask_server, daemon=True)
        flask_thread.start()

        # Wait a moment for Flask server to start
        time.sleep(3)

        # Now start InstaTunnel for public access
        logger.info("Starting InstaTunnel for public access...")
        public_url = start_instatunnel(port)

        if public_url:
            logger.info(f"Public URL: {public_url}")
            qr_code = generate_qr_code(public_url)
            if qr_code:
                logger.info("QR code generated for mobile access")

        # Keep the main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            logger.info("Shutdown complete")

    except Exception as e:
        logger.error(f"Failed to start web server: {e}")
        raise
