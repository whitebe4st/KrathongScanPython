#!/usr/bin/env python3
"""
KrathongScanner - Simplified User-Friendly Main Application

A clean, simple interface for KrathongScanner without complex modals.
Everything is accessible from one main window.
"""

import argparse
import os
import subprocess
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Optional

import cv2
import numpy as np
from PIL import Image, ImageTk

# add src to py path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from aruco_detector.detector import ArUcoDetector
from utils.logger import setup_logger


class SimplifiedKrathongScannerUI:
    """Simplified, user-friendly UI for KrathongScanner."""

    def __init__(self):
        """Initialize the simplified UI."""
        self.root = tk.Tk()
        self.root.title("KrathongScanner")
        self.root.geometry("1100x900")
        self.root.configure(bg="#f0f0f0")

        # detector inti
        self.detector = None
        self.current_image = None
        self.processed_image = None

        # Configuration settings
        self.web_output_dir = str(Path(__file__).parent / "web" / "results")
        self.webcam_output_dir = str(Path(__file__).parent / "data" / "webcam_captures")
        self.auto_input_dir = str(Path(__file__).parent / "data" / "auto_input")
        self.auto_output_dir = str(Path(__file__).parent / "data" / "auto_output")

        # Auto directory state
        self.auto_directory_running = False
        self.auto_directory_thread = None
        self.auto_directory_stop_flag = threading.Event()  # For stopping auto directory

        # Web server state
        self.web_server_running = False
        self.web_server_process = None  # Setup logger
        self.logger = setup_logger()

        # Center window
        self.center_window()

        # Create UI
        self.create_interface()

        # Initialize detector in background
        self.init_detector()

    def center_window(self):
        """Center the window on screen."""
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 1100) // 2
        y = (screen_height - 900) // 2
        self.root.geometry(f"1100x900+{x}+{y}")

    def create_interface(self):
        """Create the main interface."""
        # Main container with padding
        main_frame = tk.Frame(self.root, bg="#f0f0f0", padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title section
        self.create_title_section(main_frame)

        # Action buttons section
        self.create_action_section(main_frame)

        # Configuration section
        self.create_config_section(main_frame)

        # Image preview section
        self.create_preview_section(main_frame)

        # Status section
        self.create_status_section(main_frame)

    def create_title_section(self, parent):
        """Create the title section."""
        title_frame = tk.Frame(parent, bg="#f0f0f0")
        title_frame.pack(fill=tk.X, pady=(0, 20))

        # Main title
        title_label = tk.Label(
            title_frame,
            text="🌸 KrathongScanner",
            font=("Arial", 24, "bold"),
            bg="#f0f0f0",
            fg="#2c3e50",
        )
        title_label.pack()

        # Subtitle
        subtitle_label = tk.Label(
            title_frame,
            text="Simple Photo Processing for Krathong Templates",
            font=("Arial", 12),
            bg="#f0f0f0",
            fg="#7f8c8d",
        )
        subtitle_label.pack(pady=(5, 0))

    def create_action_section(self, parent):
        """Create the action buttons section."""
        action_frame = tk.Frame(parent, bg="#f0f0f0")
        action_frame.pack(fill=tk.X, pady=(0, 15))

        # Action buttons in a clean grid
        button_frame = tk.Frame(action_frame, bg="#f0f0f0")
        button_frame.pack()

        # Process Photo button
        self.process_btn = tk.Button(
            button_frame,
            text="📷 Process Photo",
            font=("Arial", 14, "bold"),
            bg="#3498db",
            fg="white",
            relief=tk.RAISED,
            borderwidth=2,
            padx=30,
            pady=15,
            command=self.process_photo,
            cursor="hand2",
        )
        self.process_btn.grid(row=0, column=0, padx=(0, 15))

        # Start Webcam button - COMMENTED OUT
        # self.webcam_btn = tk.Button(
        #     button_frame,
        #     text="📹 Start Webcam",
        #     font=("Arial", 14, "bold"),
        #     bg="#2ecc71",
        #     fg="white",
        #     relief=tk.RAISED,
        #     borderwidth=2,
        #     padx=30,
        #     pady=15,
        #     command=self.start_webcam,
        #     cursor="hand2",
        # )
        # self.webcam_btn.grid(row=0, column=1, padx=15)

        # Web Server button
        self.server_btn = tk.Button(
            button_frame,
            text="🌐 Start Web Server",
            font=("Arial", 14, "bold"),
            bg="#e74c3c",
            fg="white",
            relief=tk.RAISED,
            borderwidth=2,
            padx=30,
            pady=15,
            command=self.start_web_server,
            cursor="hand2",
        )
        self.server_btn.grid(row=0, column=1, padx=(15, 0))

        # Auto Directory button
        self.auto_dir_btn = tk.Button(
            button_frame,
            text="📁 Auto Directory",
            font=("Arial", 14, "bold"),
            bg="#9b59b6",
            fg="white",
            relief=tk.RAISED,
            borderwidth=2,
            padx=30,
            pady=15,
            command=self.start_auto_directory,
            cursor="hand2",
        )
        self.auto_dir_btn.grid(row=1, column=0, columnspan=2, pady=(15, 0))

    def create_config_section(self, parent):
        """Create the configuration section."""
        config_frame = tk.LabelFrame(
            parent,
            text="⚙️ Configuration",
            font=("Arial", 10, "bold"),
            bg="#f0f0f0",
            fg="#2c3e50",
            padx=8,
            pady=3,
        )
        config_frame.pack(fill=tk.X, pady=(0, 10))

        # Web output directory setting
        web_dir_frame = tk.Frame(config_frame, bg="#f0f0f0")
        web_dir_frame.pack(fill=tk.X, pady=2)

        tk.Label(
            web_dir_frame,
            text="🌐 Web Server Output:",
            font=("Arial", 9),
            bg="#f0f0f0",
            fg="#2c3e50",
        ).pack(side=tk.LEFT)

        self.web_dir_var = tk.StringVar(value=self.web_output_dir)
        self.web_dir_entry = tk.Entry(
            web_dir_frame,
            textvariable=self.web_dir_var,
            font=("Arial", 9),
            width=50,
            state="readonly",
        )
        self.web_dir_entry.pack(side=tk.LEFT, padx=(10, 5), fill=tk.X, expand=True)

        tk.Button(
            web_dir_frame,
            text="📁 Choose",
            font=("Arial", 8),
            bg="#3498db",
            fg="white",
            padx=10,
            pady=2,
            command=self.choose_web_output_dir,
            cursor="hand2",
        ).pack(side=tk.RIGHT)

        # Auto Directory input setting
        auto_input_dir_frame = tk.Frame(config_frame, bg="#f0f0f0")
        auto_input_dir_frame.pack(fill=tk.X, pady=2)

        tk.Label(
            auto_input_dir_frame,
            text="📂 Auto Input Dir:",
            font=("Arial", 9),
            bg="#f0f0f0",
            fg="#2c3e50",
        ).pack(side=tk.LEFT)

        self.auto_input_dir_var = tk.StringVar(value=self.auto_input_dir)
        self.auto_input_dir_entry = tk.Entry(
            auto_input_dir_frame,
            textvariable=self.auto_input_dir_var,
            font=("Arial", 9),
            width=50,
            state="readonly",
        )
        self.auto_input_dir_entry.pack(
            side=tk.LEFT, padx=(10, 5), fill=tk.X, expand=True
        )

        tk.Button(
            auto_input_dir_frame,
            text="📁 Choose",
            font=("Arial", 8),
            bg="#9b59b6",
            fg="white",
            padx=10,
            pady=2,
            command=self.choose_auto_input_dir,
            cursor="hand2",
        ).pack(side=tk.RIGHT)

        # Auto Directory output setting
        auto_output_dir_frame = tk.Frame(config_frame, bg="#f0f0f0")
        auto_output_dir_frame.pack(fill=tk.X, pady=2)

        tk.Label(
            auto_output_dir_frame,
            text="📤 Auto Output Dir:",
            font=("Arial", 9),
            bg="#f0f0f0",
            fg="#2c3e50",
        ).pack(side=tk.LEFT)

        self.auto_output_dir_var = tk.StringVar(value=self.auto_output_dir)
        self.auto_output_dir_entry = tk.Entry(
            auto_output_dir_frame,
            textvariable=self.auto_output_dir_var,
            font=("Arial", 9),
            width=50,
            state="readonly",
        )
        self.auto_output_dir_entry.pack(
            side=tk.LEFT, padx=(10, 5), fill=tk.X, expand=True
        )

        tk.Button(
            auto_output_dir_frame,
            text="📁 Choose",
            font=("Arial", 8),
            bg="#9b59b6",
            fg="white",
            padx=10,
            pady=2,
            command=self.choose_auto_output_dir,
            cursor="hand2",
        ).pack(side=tk.RIGHT)

        # Webcam output directory setting - COMMENTED OUT
        # webcam_dir_frame = tk.Frame(config_frame, bg="#f0f0f0")
        # webcam_dir_frame.pack(fill=tk.X, pady=2)

        # tk.Label(
        #     webcam_dir_frame,
        #     text="📹 Webcam Output:",
        #     font=("Arial", 9),
        #     bg="#f0f0f0",
        #     fg="#2c3e50",
        # ).pack(side=tk.LEFT)

        # self.webcam_dir_var = tk.StringVar(value=self.webcam_output_dir)
        # self.webcam_dir_entry = tk.Entry(
        #     webcam_dir_frame,
        #     textvariable=self.webcam_dir_var,
        #     font=("Arial", 9),
        #     width=50,
        #     state="readonly",
        # )
        # self.webcam_dir_entry.pack(side=tk.LEFT, padx=(10, 5), fill=tk.X, expand=True)

        # tk.Button(
        #     webcam_dir_frame,
        #     text="📁 Choose",
        #     font=("Arial", 8),
        #     bg="#2ecc71",
        #     fg="white",
        #     padx=10,
        #     pady=2,
        #     command=self.choose_webcam_output_dir,
        #     cursor="hand2",
        # ).pack(side=tk.RIGHT)

    def create_preview_section(self, parent):
        """Create the image preview section."""
        preview_frame = tk.LabelFrame(
            parent,
            text="Image Preview",
            font=("Arial", 12, "bold"),
            bg="#f0f0f0",
            fg="#2c3e50",
            padx=8,
            pady=5,
        )
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # Create canvas for image display
        self.canvas = tk.Canvas(
            preview_frame, bg="white", relief=tk.SUNKEN, borderwidth=2, height=280
        )
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Initial message
        self.canvas.create_text(
            550,
            140,
            text="Select 'Process Photo' to load and process an image\nor use 'Start Webcam' for real-time processing",
            font=("Arial", 12),
            fill="#7f8c8d",
            justify=tk.CENTER,
        )

        # Processing controls (initially hidden)
        self.controls_frame = tk.Frame(preview_frame, bg="#f0f0f0")

        # Save button
        self.save_btn = tk.Button(
            self.controls_frame,
            text="💾 Save Result",
            font=("Arial", 11, "bold"),
            bg="#27ae60",
            fg="white",
            relief=tk.RAISED,
            borderwidth=1,
            padx=20,
            pady=8,
            command=self.save_result,
            cursor="hand2",
        )
        self.save_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Clear button
        self.clear_btn = tk.Button(
            self.controls_frame,
            text="🗑️ Clear",
            font=("Arial", 11, "bold"),
            bg="#95a5a6",
            fg="white",
            relief=tk.RAISED,
            borderwidth=1,
            padx=20,
            pady=8,
            command=self.clear_preview,
            cursor="hand2",
        )
        self.clear_btn.pack(side=tk.LEFT)

    def create_status_section(self, parent):
        """Create the status section."""
        status_frame = tk.Frame(parent, bg="#f0f0f0")
        status_frame.pack(fill=tk.X)

        # Status label
        self.status_label = tk.Label(
            status_frame,
            text="Ready - Select an action to begin",
            font=("Arial", 10),
            bg="#f0f0f0",
            fg="#27ae60",
        )
        self.status_label.pack(side=tk.LEFT)

        # Progress bar
        self.progress = ttk.Progressbar(status_frame, mode="indeterminate", length=200)
        self.progress.pack(side=tk.RIGHT)

    def init_detector(self):
        """Initialize the ArUco detector in background."""

        def init_in_background():
            try:
                self.update_status("Initializing detector...", True)
                self.detector = ArUcoDetector()
                self.update_status("Ready - Select an action to begin", False)
                self.logger.info("ArUco detector initialized successfully")
            except Exception as e:
                self.update_status(f"Error initializing detector: {str(e)}", False)
                self.logger.error(f"Failed to initialize detector: {e}")

        threading.Thread(target=init_in_background, daemon=True).start()

    def check_directory_conflicts(self):
        """Check for directory conflicts between different modes."""
        conflicts = []

        # Check if web and auto output directories are the same
        if os.path.normpath(self.web_output_dir) == os.path.normpath(
            self.auto_output_dir
        ):
            conflicts.append(
                "Web Server and Auto Directory have the same output directory"
            )

        # Check if auto input and output directories are the same
        if os.path.normpath(self.auto_input_dir) == os.path.normpath(
            self.auto_output_dir
        ):
            conflicts.append("Auto Directory input and output directories are the same")

        return conflicts

    def get_active_modes_status(self):
        """Get status of all active modes."""
        active_modes = []
        if self.web_server_running:
            active_modes.append("🌐 Web Server")
        if self.auto_directory_running:
            active_modes.append("📁 Auto Directory")

        if not active_modes:
            return "Ready"
        elif len(active_modes) == 1:
            return f"{active_modes[0]} running"
        else:
            return f"Multiple modes: {', '.join(active_modes)}"

    def update_status(self, message: str, show_progress: bool = False):
        """Update status message and progress bar."""

        def update():
            # Add multi-mode information if applicable
            full_message = message
            active_modes = self.get_active_modes_status()
            if active_modes != "Ready" and not show_progress:
                full_message = f"{message} | {active_modes}"

            self.status_label.config(text=full_message)
            if show_progress:
                self.progress.start(10)
            else:
                self.progress.stop()

        self.root.after(0, update)

    def process_photo(self):
        """Process a photo from file."""
        if not self.detector:
            messagebox.showerror(
                "Error", "Detector not initialized yet. Please wait a moment."
            )
            return

        # Open file dialog
        file_path = filedialog.askopenfilename(
            title="Select Krathong Photo",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff"),
                ("All files", "*.*"),
            ],
        )

        if not file_path:
            return

        # Process in background
        threading.Thread(
            target=self._process_photo_background, args=(file_path,), daemon=True
        ).start()

    def _process_photo_background(self, file_path: str):
        """Process photo in background thread."""
        import os
        import tempfile

        try:
            self.update_status("Loading image...", True)

            # Load image
            image = cv2.imread(file_path)
            if image is None:
                raise ValueError("Could not load image")

            self.current_image = image.copy()

            self.update_status("Processing with ArUco detector...", True)

            # Process similar to web server approach for proper masking
            try:
                # Debug logging
                self.logger.info(
                    f"🔍 GUI: Starting marker detection on image with shape: {image.shape}"
                )

                # Create fresh detector instance like web server does
                from aruco_detector.detector import ArUcoDetector

                detector = ArUcoDetector()
                self.logger.info("🔍 GUI: Created fresh ArUcoDetector instance")

                # Step 1: Detect markers
                markers = detector.detect_markers(image)
                self.logger.info(
                    f"🔍 GUI: Found {len(markers) if markers else 0} markers"
                )
                if markers:
                    marker_ids = [marker.id for marker in markers]
                    self.logger.info(f"🔍 GUI: Marker IDs: {marker_ids}")

                if not markers:
                    self.logger.warning("🔍 GUI: No ArUco markers found in image")
                    self.update_status("No ArUco markers found in image", False)
                    self.root.after(0, self._display_original)
                    return

                # Step 2: Detect template
                marker_ids = [marker.id for marker in markers]
                template_id = detector.detect_template(marker_ids)
                self.logger.info(f"🔍 GUI: Template detected: {template_id}")
                if not template_id:
                    self.update_status("No template detected", False)
                    self.root.after(0, self._display_original)
                    return

                # Step 3: Get corner markers
                corner_markers = detector.get_corner_markers(markers)
                if corner_markers is None:
                    self.update_status("Could not find all corner markers", False)
                    self.root.after(0, self._display_original)
                    return

                # Step 4: Apply homography correction
                homography = detector.create_perspective_transform(corner_markers)
                if homography is None:
                    self.update_status("Failed to create perspective transform", False)
                    self.root.after(0, self._display_original)
                    return

                corrected = detector.apply_perspective_correction(image, homography)

                # Step 5: Crop the corrected image
                cropped = detector._crop_perspective_corrected_area(
                    corrected, corner_markers
                )

                # Step 6: Apply template mask - use proper mask path resolution
                template_mask_path = detector.get_template_mask_path()
                self.logger.info(f"🔍 GUI: Template mask path: {template_mask_path}")
                if template_mask_path:
                    masked = detector.apply_template_mask(cropped, template_mask_path)

                    # Step 7: Crop to content area (this removes black background and adds transparency)
                    final_masked = detector._crop_masked_area(masked)

                    self.processed_image = final_masked

                    # Create result dict for compatibility
                    result = {
                        "processed_image": final_masked,
                        "success": True,
                        "template_name": template_id,
                    }
                    self.root.after(0, self._display_result, result)
                    self.update_status(
                        "Processing complete - Transparent masked image ready", False
                    )
                else:
                    self.update_status("No template mask found", False)
                    self.root.after(0, self._display_original)

            except Exception as processing_error:
                self.logger.error(f"Processing error: {processing_error}")
                self.update_status(
                    "Processing failed - No markers or template found", False
                )
                self.root.after(0, self._display_original)

        except Exception as e:
            self.update_status(f"Error processing image: {str(e)}", False)
            self.logger.error(f"Error processing image: {e}")

    def _display_result(self, result):
        """Display processing result."""
        if self.processed_image is not None:
            self._display_image(self.processed_image)
            self.controls_frame.pack(fill=tk.X, pady=(10, 0))

        # Show result info if available
        if "template_name" in result:
            self.update_status(f"Found template: {result['template_name']}", False)

    def _display_original(self):
        """Display original image when no processing result."""
        if self.current_image is not None:
            self._display_image(self.current_image)

    def _display_image(self, image):
        """Display image on canvas."""
        # Resize image to fit canvas
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1:
            # Canvas not ready yet, try again later
            self.root.after(100, lambda: self._display_image(image))
            return

        # Calculate scaling
        h, w = image.shape[:2]
        scale_w = (canvas_width - 20) / w
        scale_h = (canvas_height - 20) / h
        scale = min(scale_w, scale_h)

        new_w = int(w * scale)
        new_h = int(h * scale)

        # Resize image
        resized = cv2.resize(image, (new_w, new_h))

        # Convert to PIL format
        if len(resized.shape) == 3:
            resized_rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        else:
            resized_rgb = resized

        pil_image = Image.fromarray(resized_rgb)
        photo = ImageTk.PhotoImage(pil_image)

        # Clear canvas and display image
        self.canvas.delete("all")
        x = canvas_width // 2
        y = canvas_height // 2
        self.canvas.create_image(x, y, image=photo)

        # Keep reference to prevent garbage collection
        self.canvas.image = photo

    def save_result(self):
        """Save the processed result."""
        if self.processed_image is None:
            messagebox.showwarning("Warning", "No processed image to save.")
            return

        # Open save dialog
        file_path = filedialog.asksaveasfilename(
            title="Save Processed Image",
            defaultextension=".png",
            filetypes=[
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg"),
                ("All files", "*.*"),
            ],
        )

        if file_path:
            try:
                cv2.imwrite(file_path, self.processed_image)
                self.update_status(f"Image saved to: {file_path}", False)
                messagebox.showinfo(
                    "Success", f"Image saved successfully!\n{file_path}"
                )
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save image: {str(e)}")

    def clear_preview(self):
        """Clear the preview."""
        self.canvas.delete("all")
        self.canvas.create_text(
            450,
            175,
            text="Select 'Process Photo' to load and process an image\nor use 'Start Webcam' for real-time processing",
            font=("Arial", 12),
            fill="#7f8c8d",
            justify=tk.CENTER,
        )
        self.controls_frame.pack_forget()
        self.current_image = None
        self.processed_image = None
        self.update_status("Ready - Select an action to begin", False)

    def choose_web_output_dir(self):
        """Choose web server output directory."""
        directory = filedialog.askdirectory(
            title="Choose Web Server Output Directory", initialdir=self.web_output_dir
        )
        if directory:
            self.web_output_dir = directory
            self.web_dir_var.set(directory)
            self.logger.info(f"Web output directory set to: {directory}")
            self.update_status(f"Web output directory: {directory}", False)

    def choose_webcam_output_dir(self):
        """Choose webcam output directory."""
        directory = filedialog.askdirectory(
            title="Choose Webcam Output Directory", initialdir=self.webcam_output_dir
        )
        if directory:
            self.webcam_output_dir = directory
            self.webcam_dir_var.set(directory)
            self.logger.info(f"Webcam output directory set to: {directory}")
            self.update_status(f"Webcam output directory: {directory}", False)

    def choose_auto_input_dir(self):
        """Choose auto directory input directory."""
        directory = filedialog.askdirectory(
            title="Choose Auto Directory Input Directory",
            initialdir=self.auto_input_dir,
        )
        if directory:
            self.auto_input_dir = directory
            self.auto_input_dir_var.set(directory)
            self.logger.info(f"Auto input directory set to: {directory}")
            self.update_status(f"Auto input directory: {directory}", False)

    def choose_auto_output_dir(self):
        """Choose auto directory output directory."""
        directory = filedialog.askdirectory(
            title="Choose Auto Directory Output Directory",
            initialdir=self.auto_output_dir,
        )
        if directory:
            self.auto_output_dir = directory
            self.auto_output_dir_var.set(directory)
            self.logger.info(f"Auto output directory set to: {directory}")
            self.update_status(f"Auto output directory: {directory}", False)

    def start_webcam(self):
        """Start webcam detection."""
        try:
            self.update_status("Starting webcam...", True)

            # Import webcam detector
            from src.webcam_detector_with_paper import WebcamDetectorWithPaper

            # Start webcam in separate process to avoid blocking
            def run_webcam():
                try:
                    detector = WebcamDetectorWithPaper(
                        camera_id=0, capture_dir=self.webcam_output_dir
                    )
                    detector.run()
                except Exception as e:
                    self.logger.error(f"Webcam error: {e}")

            threading.Thread(target=run_webcam, daemon=True).start()
            self.update_status("Webcam started - Check camera window", False)

        except Exception as e:
            self.update_status(f"Error starting webcam: {str(e)}", False)
            messagebox.showerror("Error", f"Failed to start webcam: {str(e)}")

    def start_web_server(self):
        """Start or stop the web server."""
        if not self.web_server_running:
            # Start web server
            try:
                # Check for directory conflicts
                conflicts = self.check_directory_conflicts()
                if conflicts:
                    conflict_message = "Directory conflicts detected:\n\n" + "\n".join(
                        f"• {c}" for c in conflicts
                    )
                    conflict_message += (
                        "\n\nPlease choose different directories to avoid issues."
                    )
                    result = messagebox.askyesno(
                        "Directory Conflicts",
                        f"{conflict_message}\n\nDo you want to continue anyway?",
                    )
                    if not result:
                        return

                self.update_status("Starting web server...", True)

                def run_server():
                    try:
                        # Check if running in frozen mode (PyInstaller)
                        if getattr(sys, "frozen", False):
                            # Running in PyInstaller bundle - start server in-process
                            self.logger.info(
                                "🔥 Running in frozen mode, starting web server in-process"
                            )
                            from web.server import run_web_server

                            # Start server in background thread
                            threading.Thread(
                                target=lambda: run_web_server(
                                    port=5000, results_folder=self.web_output_dir
                                ),
                                daemon=True,
                            ).start()
                        else:
                            # Development mode - use subprocess
                            import subprocess

                            server_path = Path(__file__).parent / "web" / "server.py"
                            self.web_server_process = subprocess.Popen(
                                [
                                    sys.executable,
                                    str(server_path),
                                    "--port",
                                    "5000",
                                    "--results-folder",
                                    self.web_output_dir,
                                ]
                            )

                    except Exception as e:
                        self.logger.error(f"Web server error: {e}")
                        error_msg = str(e)  # Capture the error message
                        self.root.after(
                            0,
                            lambda msg=error_msg: self.update_status(
                                f"Web server error: {msg}", False
                            ),
                        )

                threading.Thread(target=run_server, daemon=True).start()

                self.web_server_running = True
                self.server_btn.config(text="⏹️ Stop Web Server", bg="#95a5a6")

                self.update_status("Web server starting - Check console for URL", False)

                # Wait a moment then open QR code
                def open_qr_code():
                    import time

                    time.sleep(5)  # Wait for web server to start and generate QR codes

                    # Look for the public QR code image
                    qr_files = [
                        Path(__file__).parent / "mall_public_qr.png",
                        Path(__file__).parent / "web" / "static" / "qr_public.png",
                        Path(__file__).parent / "web" / "static" / "qr_local.png",
                    ]

                    for qr_file in qr_files:
                        if qr_file.exists():
                            try:
                                # Open QR code in default image viewer
                                import subprocess

                                subprocess.run(
                                    ["start", str(qr_file)], shell=True, check=False
                                )
                                self.logger.info(f"Opened QR code: {qr_file}")
                                break
                            except Exception as e:
                                self.logger.error(
                                    f"Failed to open QR code {qr_file}: {e}"
                                )

                # Start QR opening in background
                threading.Thread(target=open_qr_code, daemon=True).start()

                # Show info dialog
                messagebox.showinfo(
                    "Web Server",
                    f"Web server is starting!\n\n"
                    f"Output Directory: {self.web_output_dir}\n\n"
                    "• QR code will open automatically in ~5 seconds\n"
                    "• Check the console window for URLs\n"
                    "• Local URL (usually http://localhost:5000)\n"
                    "• Public URL for mobile access\n\n"
                    "You can upload photos from your phone!",
                )

            except Exception as e:
                self.update_status(f"Error starting web server: {str(e)}", False)
                messagebox.showerror("Error", f"Failed to start web server: {str(e)}")
        else:
            # Stop web server
            try:
                if self.web_server_process:
                    self.logger.info(
                        "Terminating web server process and child processes..."
                    )

                    # Kill all related processes (Flask + InstaTunnel)
                    self._kill_web_server_processes()

                    self.web_server_process = None
                    self.logger.info("Web server and related processes terminated")

                self.web_server_running = False
                self.server_btn.config(text="🌐 Start Web Server", bg="#e74c3c")
                self.update_status("Web server stopped", False)
                messagebox.showinfo(
                    "Web Server Stopped", "Web server and tunnel have been stopped."
                )

            except Exception as e:
                self.logger.error(f"Error stopping web server: {e}")
                self.update_status(f"Error stopping web server: {str(e)}", False)

    def _kill_web_server_processes(self):
        """Kill all web server related processes including InstaTunnel."""
        try:
            # First, try to terminate the main process gracefully
            if self.web_server_process:
                self.web_server_process.terminate()
                try:
                    self.web_server_process.wait(timeout=3.0)
                except subprocess.TimeoutExpired:
                    self.web_server_process.kill()

            # On Windows, use taskkill to kill related processes
            if os.name == "nt":  # Windows
                self.logger.info("Killing web server related processes on Windows...")

                # Kill Python processes running server.py
                try:
                    subprocess.run(
                        [
                            "taskkill",
                            "/f",
                            "/im",
                            "python.exe",
                            "/fi",
                            "WINDOWTITLE eq *server.py*",
                        ],
                        capture_output=True,
                        timeout=5,
                    )
                except:
                    pass

                # Kill InstaTunnel processes (Node.js)
                try:
                    subprocess.run(
                        [
                            "taskkill",
                            "/f",
                            "/im",
                            "node.exe",
                            "/fi",
                            "WINDOWTITLE eq *instatunnel*",
                        ],
                        capture_output=True,
                        timeout=5,
                    )
                except:
                    pass

                # Kill any process listening on port 5000
                try:
                    # Find processes using port 5000
                    result = subprocess.run(
                        ["netstat", "-ano", "|", "findstr", ":5000"],
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )

                    if result.stdout:
                        lines = result.stdout.strip().split("\n")
                        pids = set()
                        for line in lines:
                            parts = line.split()
                            if len(parts) > 4 and parts[1].endswith(":5000"):
                                pid = parts[-1]
                                if pid.isdigit():
                                    pids.add(pid)

                        # Kill processes by PID
                        for pid in pids:
                            try:
                                subprocess.run(
                                    ["taskkill", "/f", "/pid", pid],
                                    capture_output=True,
                                    timeout=5,
                                )
                                self.logger.info(
                                    f"Killed process PID {pid} using port 5000"
                                )
                            except:
                                pass

                except Exception as e:
                    self.logger.warning(f"Could not kill port 5000 processes: {e}")

            else:
                # Unix/Linux fallback
                try:
                    subprocess.run(
                        ["pkill", "-f", "server.py"], capture_output=True, timeout=5
                    )
                    subprocess.run(
                        ["pkill", "-f", "instatunnel"], capture_output=True, timeout=5
                    )
                except:
                    pass

            self.logger.info("Web server process cleanup completed")

        except Exception as e:
            self.logger.error(f"Error killing web server processes: {e}")

    def start_auto_directory(self):
        """Start or stop auto directory monitoring."""
        if not self.auto_directory_running:
            # Start auto directory
            try:
                # Check for directory conflicts
                conflicts = self.check_directory_conflicts()
                if conflicts:
                    conflict_message = "Directory conflicts detected:\n\n" + "\n".join(
                        f"• {c}" for c in conflicts
                    )
                    conflict_message += (
                        "\n\nPlease choose different directories to avoid issues."
                    )
                    result = messagebox.askyesno(
                        "Directory Conflicts",
                        f"{conflict_message}\n\nDo you want to continue anyway?",
                    )
                    if not result:
                        return

                # Ensure directories exist
                Path(self.auto_input_dir).mkdir(parents=True, exist_ok=True)
                Path(self.auto_output_dir).mkdir(parents=True, exist_ok=True)

                self.update_status("Starting auto directory monitoring...", True)

                def run_auto_directory():
                    try:
                        from src.auto_directory_detector import AutoDirectoryDetector

                        self.logger.info(
                            f"Auto directory monitoring: {self.auto_input_dir} -> {self.auto_output_dir}"
                        )

                        # Create detector instance
                        detector = AutoDirectoryDetector(
                            input_directory=self.auto_input_dir,
                            output_directory=self.auto_output_dir,
                            check_interval=2.0,
                            use_homography=True,
                            use_rectangle_detection=False,
                        )

                        self.logger.info(
                            "Auto directory detector initialized, starting monitoring loop..."
                        )

                        # Custom monitoring loop that respects our stop flag
                        detector.stats["start_time"] = time.time()

                        # Initial scan
                        detector.scan_and_process()

                        # Continuous monitoring with stop flag checking
                        while not self.auto_directory_stop_flag.wait(
                            detector.check_interval
                        ):
                            if not self.auto_directory_running:
                                break
                            detector.scan_and_process()

                        self.logger.info("Auto directory monitoring stopped")

                    except Exception as e:
                        self.logger.error(f"Auto directory error: {e}")
                        self.root.after(
                            0,
                            lambda: self.update_status(
                                f"Auto directory error: {str(e)}", False
                            ),
                        )

                self.auto_directory_thread = threading.Thread(
                    target=run_auto_directory, daemon=True
                )
                self.auto_directory_thread.start()

                self.auto_directory_running = True
                self.auto_dir_btn.config(text="⏹️ Stop Auto Directory", bg="#e74c3c")

                self.update_status(
                    f"Auto directory monitoring started - Watching: {self.auto_input_dir}",
                    False,
                )

                # Show info dialog
                messagebox.showinfo(
                    "Auto Directory Started",
                    f"Auto Directory is now monitoring:\n\n"
                    f"Input Directory: {self.auto_input_dir}\n"
                    f"Output Directory: {self.auto_output_dir}\n\n"
                    "Place new images in the input directory and they will be automatically processed!\n\n"
                    "Supported formats: JPG, PNG, BMP, TIFF\n"
                    "Processing happens every 2 seconds.",
                )

            except Exception as e:
                self.update_status(f"Error starting auto directory: {str(e)}", False)
                messagebox.showerror(
                    "Error", f"Failed to start auto directory: {str(e)}"
                )
        else:
            # Stop auto directory
            self.auto_directory_running = False
            self.auto_directory_stop_flag.set()  # Signal the thread to stop

            # Wait a moment for the thread to stop gracefully
            if self.auto_directory_thread and self.auto_directory_thread.is_alive():
                self.auto_directory_thread.join(timeout=3.0)

            # Reset the stop flag for next time
            self.auto_directory_stop_flag.clear()

            self.auto_dir_btn.config(text="📁 Auto Directory", bg="#9b59b6")
            self.update_status("Auto directory monitoring stopped", False)
            messagebox.showinfo(
                "Auto Directory Stopped", "Auto directory monitoring has been stopped."
            )

    def run(self):
        """Run the application."""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.logger.info("Application closed by user")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            messagebox.showerror("Error", f"Unexpected error: {str(e)}")


# Keep the original command-line functionality for backward compatibility
def run_webcam_detection(mode="basic"):
    """Run webcam detection in specified mode."""
    logger = setup_logger()

    if mode == "basic":
        logger.info("Starting basic webcam detection...")
        from src.webcam_detector import WebcamDetector

        detector = WebcamDetector(
            camera_index=0, frame_width=1280, frame_height=720, fps=30
        )
    elif mode == "advanced":
        logger.info("Starting advanced webcam detection...")
        from src.webcam_detector_advanced import AdvancedWebcamDetector

        detector = AdvancedWebcamDetector(
            camera_index=0,
            frame_width=1280,
            frame_height=720,
            fps=30,
            auto_capture=True,
            capture_delay=2.0,
            min_markers=4,
        )
    elif mode == "enhanced":
        logger.info("Starting enhanced webcam detection with paper detection...")
        from src.webcam_detector_with_paper import WebcamDetectorWithPaper

        detector = WebcamDetectorWithPaper(camera_id=0)
    else:
        logger.error(f"Unknown webcam mode: {mode}")
        return

    try:
        detector.run()
    except KeyboardInterrupt:
        logger.info("Webcam detection stopped by user")
    except Exception as e:
        logger.error(f"Error in webcam detection: {e}")


def run_web_server(host="0.0.0.0", port=5000, results_folder=None):
    """Run the KrathongScanner web server."""
    logger = setup_logger()

    try:
        logger.info("Starting KrathongScanner Web Server...")
        logger.info(f"Server will be available at http://localhost:{port}")

        # Check if running in frozen mode (PyInstaller)
        if getattr(sys, "frozen", False):
            # Running in PyInstaller bundle - import and run in-process
            logger.info("🔥 Running in frozen mode, starting web server in-process")
            try:
                from web.server import (
                    RESULTS_FOLDER,
                    UPLOAD_FOLDER,
                    app,
                    generate_qr_code,
                    start_instatunnel,
                )

                # Set Flask configuration
                app.config["HOST"] = host
                app.config["PORT"] = port

                logger.info(f"Upload folder: {UPLOAD_FOLDER}")
                logger.info(f"Results folder: {RESULTS_FOLDER}")
                logger.info("=" * 50)
                logger.info(
                    "🎯 Web Server Ready! Upload images to process them automatically"
                )
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
                    # Cleanup if needed
                    try:
                        from web.server import cleanup_on_exit

                        cleanup_on_exit()
                    except ImportError:
                        pass
                    logger.info("Shutdown complete")

            except Exception as e:
                logger.error(f"Failed to start web server in frozen mode: {e}")
                raise
        else:
            # Development mode - use subprocess approach
            logger.info("🔧 Running in development mode, using subprocess")
            import subprocess

            # Import Flask server components
            sys.path.insert(0, str(Path(__file__).parent / "web"))

            # Import and run the server
            from web import server

            # Set Flask configuration
            server.app.config["HOST"] = host
            server.app.config["PORT"] = port

            logger.info(f"Upload folder: {server.UPLOAD_FOLDER}")
            logger.info(f"Results folder: {server.RESULTS_FOLDER}")
            logger.info("=" * 50)
            logger.info(
                "🎯 Web Server Ready! Upload images to process them automatically"
            )
            logger.info("=" * 50)

            # Start Flask server in a separate thread
            def start_flask_server():
                server.app.run(host=host, port=port, debug=False, use_reloader=False)

            flask_thread = threading.Thread(target=start_flask_server, daemon=True)
            flask_thread.start()

            # Wait a moment for Flask server to start
            time.sleep(3)

            # Now start InstaTunnel for public access
            logger.info("Starting InstaTunnel for public access...")
            public_url = server.start_instatunnel(port)

            if public_url:
                logger.info(f"Public URL: {public_url}")
                qr_code = server.generate_qr_code(public_url)
                if qr_code:
                    logger.info("QR code generated for mobile access")
            else:
                logger.warning("Server will only be available locally")

            # Keep the main thread alive
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Shutting down...")

    except ImportError as e:
        logger.error(f"Failed to import web server components: {e}")
        logger.error("Make sure Flask and other web dependencies are installed:")
        logger.error("pip install flask werkzeug requests qrcode pillow")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error starting web server: {e}")
        sys.exit(1)
    finally:
        # Cleanup
        try:
            from web import server

            server.cleanup_on_exit()
        except:
            pass


def main():
    """Main application function with both GUI and CLI support."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="KrathongScanner - ArUco Marker Detection System"
    )
    parser.add_argument(
        "--mode",
        choices=[
            "ui",
            "webcam",
            "webcam-advanced",
            "webcam-enhanced",
            "server",
            "auto-directory",
            "web-server",
        ],
        default="ui",
        help="Application mode: ui (simplified graphical interface), webcam (basic), webcam-advanced (auto-capture), webcam-enhanced (with paper detection), web-server (mobile upload interface), auto-directory (monitor folder for new images), or server (WebSocket API)",
    )
    parser.add_argument(
        "--camera", type=int, default=0, help="Camera device index (default: 0)"
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        help="Input directory to monitor for new images (auto-directory mode)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Output directory for processed images (auto-directory mode)",
    )
    parser.add_argument(
        "--check-interval",
        type=float,
        default=2.0,
        help="Interval in seconds to check for new files (default: 2.0)",
    )
    parser.add_argument(
        "--use-homography",
        action="store_true",
        default=True,
        help="Use homography/perspective correction (default: True)",
    )
    parser.add_argument(
        "--no-homography",
        action="store_true",
        help="Disable homography/perspective correction",
    )
    parser.add_argument(
        "--use-rectangle-detection",
        action="store_true",
        help="Use rectangle detection instead of ArUco markers (auto-directory mode)",
    )

    args = parser.parse_args()

    # Set up logging
    logger = setup_logger()

    try:
        logger.info("Starting KrathongScanner...")

        if args.mode == "ui":
            logger.info("Running in simplified UI mode")
            app = SimplifiedKrathongScannerUI()
            app.run()
        elif args.mode == "webcam":
            logger.info("Running in webcam detection mode")
            run_webcam_detection("basic")
        elif args.mode == "webcam-advanced":
            logger.info("Running in advanced webcam detection mode")
            run_webcam_detection("advanced")
        elif args.mode == "webcam-enhanced":
            logger.info(
                "Running in enhanced webcam detection mode with paper detection"
            )
            run_webcam_detection("enhanced")
        elif args.mode == "auto-directory":
            logger.info("Running in auto-directory mode")
            from src.auto_directory_detector import run_auto_directory_detection

            # Get directories from command line or prompt user
            input_dir = args.input_dir
            output_dir = args.output_dir

            if not input_dir:
                input_dir = input("Enter input directory to monitor: ").strip()
                if not input_dir:
                    logger.error("Input directory is required for auto-directory mode")
                    return

            if not output_dir:
                output_dir = input(
                    "Enter output directory for processed images: "
                ).strip()
                if not output_dir:
                    output_dir = "data/processed_images"
                    logger.info(f"Using default output directory: {output_dir}")

            # Determine homography setting
            use_homography = (
                not args.no_homography if args.no_homography else args.use_homography
            )

            logger.info(f"Input directory: {input_dir}")
            logger.info(f"Output directory: {output_dir}")
            logger.info(f"Check interval: {args.check_interval} seconds")
            logger.info(f"Use homography: {use_homography}")
            logger.info(f"Use rectangle detection: {args.use_rectangle_detection}")

            # Run auto-directory detection
            run_auto_directory_detection(
                input_dir,
                output_dir,
                args.check_interval,
                use_homography,
                args.use_rectangle_detection,
            )
        elif args.mode == "web-server":
            logger.info("Running in web server mode")
            # Run the web server (this will block)
            run_web_server()
        elif args.mode == "server":
            logger.info("Running in server mode")
            logger.info("Server mode not yet implemented")
            # TODO: Implement WebSocket server mode

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Shutdown complete")


if __name__ == "__main__":
    main()
