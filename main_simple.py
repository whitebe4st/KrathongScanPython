#!/usr/bin/env python3
"""
KrathongScanner - Simplified User-Friendly Main Application

A clean, simple interface for KrathongScanner without complex modals.
Everything is accessible from one main window.
"""

import os
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

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from aruco_detector.detector import ArUcoDetector
from utils.logger import setup_logger


class SimplifiedKrathongScannerUI:
    """Simplified, user-friendly UI for KrathongScanner."""

    def __init__(self):
        """Initialize the simplified UI."""
        self.root = tk.Tk()
        self.root.title("🌸 KrathongScanner - Easy Photo Processing")
        self.root.geometry("900x700")
        self.root.configure(bg="#f0f0f0")

        # Initialize detector
        self.detector = None
        self.current_image = None
        self.processed_image = None

        # Setup logger
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
        x = (screen_width - 900) // 2
        y = (screen_height - 700) // 2
        self.root.geometry(f"900x700+{x}+{y}")

    def create_interface(self):
        """Create the main interface."""
        # Main container with padding
        main_frame = tk.Frame(self.root, bg="#f0f0f0", padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title section
        self.create_title_section(main_frame)

        # Action buttons section
        self.create_action_section(main_frame)

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
        action_frame.pack(fill=tk.X, pady=(0, 20))

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

        # Start Webcam button
        self.webcam_btn = tk.Button(
            button_frame,
            text="📹 Start Webcam",
            font=("Arial", 14, "bold"),
            bg="#2ecc71",
            fg="white",
            relief=tk.RAISED,
            borderwidth=2,
            padx=30,
            pady=15,
            command=self.start_webcam,
            cursor="hand2",
        )
        self.webcam_btn.grid(row=0, column=1, padx=15)

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
        self.server_btn.grid(row=0, column=2, padx=(15, 0))

    def create_preview_section(self, parent):
        """Create the image preview section."""
        preview_frame = tk.LabelFrame(
            parent,
            text="Image Preview",
            font=("Arial", 12, "bold"),
            bg="#f0f0f0",
            fg="#2c3e50",
            padx=10,
            pady=10,
        )
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        # Create canvas for image display
        self.canvas = tk.Canvas(
            preview_frame, bg="white", relief=tk.SUNKEN, borderwidth=2, height=350
        )
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Initial message
        self.canvas.create_text(
            450,
            175,
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

    def update_status(self, message: str, show_progress: bool = False):
        """Update status message and progress bar."""

        def update():
            self.status_label.config(text=message)
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
        try:
            self.update_status("Loading image...", True)

            # Load image
            image = cv2.imread(file_path)
            if image is None:
                raise ValueError("Could not load image")

            self.current_image = image.copy()

            self.update_status("Processing with ArUco detector...", True)

            # Process with detector
            result = self.detector.process_image(image)

            if result and "processed_image" in result:
                self.processed_image = result["processed_image"]
                self.root.after(0, self._display_result, result)
                self.update_status(
                    "Processing complete - Image ready for review", False
                )
            else:
                self.update_status("No ArUco markers found in image", False)
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

    def start_webcam(self):
        """Start webcam detection."""
        try:
            self.update_status("Starting webcam...", True)

            # Import webcam detector
            from webcam_detector_with_paper import WebcamDetectorWithPaper

            # Start webcam in separate process to avoid blocking
            def run_webcam():
                try:
                    detector = WebcamDetectorWithPaper(camera_id=0)
                    detector.run()
                except Exception as e:
                    self.logger.error(f"Webcam error: {e}")

            threading.Thread(target=run_webcam, daemon=True).start()
            self.update_status("Webcam started - Check camera window", False)

        except Exception as e:
            self.update_status(f"Error starting webcam: {str(e)}", False)
            messagebox.showerror("Error", f"Failed to start webcam: {str(e)}")

    def start_web_server(self):
        """Start the web server."""
        try:
            self.update_status("Starting web server...", True)

            def run_server():
                try:
                    # Import and run web server
                    import subprocess

                    # Run the web server script
                    server_path = Path(__file__).parent / "web" / "server.py"
                    subprocess.Popen(
                        [sys.executable, str(server_path), "--port", "5000"]
                    )

                except Exception as e:
                    self.logger.error(f"Web server error: {e}")

            threading.Thread(target=run_server, daemon=True).start()
            self.update_status("Web server starting - Check console for URL", False)

            # Show info dialog
            messagebox.showinfo(
                "Web Server",
                "Web server is starting!\n\n"
                "Check the console window for:\n"
                "• Local URL (usually http://localhost:5000)\n"
                "• Public URL for mobile access\n"
                "• QR code for easy mobile scanning\n\n"
                "You can upload photos from your phone!",
            )

        except Exception as e:
            self.update_status(f"Error starting web server: {str(e)}", False)
            messagebox.showerror("Error", f"Failed to start web server: {str(e)}")

    def run(self):
        """Run the application."""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.logger.info("Application closed by user")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            messagebox.showerror("Error", f"Unexpected error: {str(e)}")


def main():
    """Main entry point for simplified UI."""
    try:
        app = SimplifiedKrathongScannerUI()
        app.run()
    except Exception as e:
        print(f"Failed to start application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
