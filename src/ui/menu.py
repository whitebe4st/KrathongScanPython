"""
Modern UI Menu for KrathongScanner.

This module provides a clean, user-friendly interface for:
- Import krathong from picture (file browser)
- Use webcam for real-time scanning
- Auto directory monitoring mode
"""

import logging
import os
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Callable, Optional

import cv2
import numpy as np
from PIL import Image, ImageTk

from aruco_detector import ArUcoDetector
from webcam_detector_with_paper import WebcamDetectorWithPaper


class ImagePreviewWindow:
    """Window for previewing and adjusting processed images."""

    def __init__(
        self, parent, original_image_path: str, processed_image: np.ndarray, detector
    ):
        self.parent = parent
        self.original_image_path = original_image_path
        self.processed_image = processed_image.copy()
        self.detector = detector
        self.result = None

        # Create preview window
        self.window = tk.Toplevel(parent)
        self.window.title("Image Preview & Mask Alignment")
        self.window.geometry("800x700")
        self.window.resizable(True, True)

        # Center the window
        self.center_window()

        # Create interface
        self.create_interface()

        # Make window modal
        self.window.transient(parent)
        self.window.grab_set()
        self.window.wait_window()

    def center_window(self):
        """Center the window on screen."""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")

    def create_interface(self):
        """Create the preview interface."""
        # Main container
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Title
        title_label = ttk.Label(
            main_frame,
            text="Image Preview & Mask Alignment",
            font=("Segoe UI", 16, "bold"),
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # Image preview area
        self.create_image_preview(main_frame)

        # Controls area
        self.create_controls(main_frame)

        # Action buttons
        self.create_action_buttons(main_frame)

        # Configure grid weights
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)

    def create_image_preview(self, parent):
        """Create the image preview area."""
        # Preview frame
        preview_frame = ttk.LabelFrame(parent, text="Preview", padding="10")
        preview_frame.grid(
            row=1, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 20)
        )

        # Canvas for image display
        self.canvas = tk.Canvas(preview_frame, bg="white", width=600, height=400)
        self.canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(
            preview_frame, orient=tk.VERTICAL, command=self.canvas.yview
        )
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar = ttk.Scrollbar(
            preview_frame, orient=tk.HORIZONTAL, command=self.canvas.xview
        )
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))

        self.canvas.configure(
            yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set
        )

        # Configure preview frame
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)

        # Display the processed image
        self.display_image()

    def create_controls(self, parent):
        """Create the control panel."""
        # Controls frame
        controls_frame = ttk.LabelFrame(
            parent, text="Processing Controls", padding="10"
        )
        controls_frame.grid(
            row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20)
        )

        # Homography toggle
        homography_frame = ttk.Frame(controls_frame)
        homography_frame.grid(
            row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15)
        )

        ttk.Label(homography_frame, text="Perspective Correction:").grid(
            row=0, column=0, padx=(0, 10)
        )
        self.use_homography_var = tk.BooleanVar(value=True)
        homography_check = ttk.Checkbutton(
            homography_frame,
            text="Use Homography",
            variable=self.use_homography_var,
            command=self.on_processing_change,
        )
        homography_check.grid(row=0, column=1, padx=(0, 10))
        ttk.Label(homography_frame, text="(Straightens warped images)").grid(
            row=0, column=2
        )

        # Mask adjustment controls
        mask_frame = ttk.LabelFrame(controls_frame, text="Mask Alignment", padding="5")
        mask_frame.grid(
            row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10)
        )

        ttk.Label(mask_frame, text="Mask Scale:").grid(row=0, column=0, padx=(0, 10))
        self.scale_var = tk.DoubleVar(value=1.0)
        scale_scale = ttk.Scale(
            mask_frame,
            from_=0.5,
            to=2.0,
            variable=self.scale_var,
            orient=tk.HORIZONTAL,
            length=200,
            command=self.on_mask_adjust,
        )
        scale_scale.grid(row=0, column=1, padx=(0, 20))
        ttk.Label(mask_frame, textvariable=self.scale_var).grid(row=0, column=2)

        ttk.Label(mask_frame, text="X Offset:").grid(row=1, column=0, padx=(0, 10))
        self.x_offset_var = tk.IntVar(value=0)
        x_offset_scale = ttk.Scale(
            mask_frame,
            from_=-100,
            to=100,
            variable=self.x_offset_var,
            orient=tk.HORIZONTAL,
            length=200,
            command=self.on_mask_adjust,
        )
        x_offset_scale.grid(row=1, column=1, padx=(0, 20))
        ttk.Label(mask_frame, textvariable=self.x_offset_var).grid(row=1, column=2)

        ttk.Label(mask_frame, text="Y Offset:").grid(row=2, column=0, padx=(0, 10))
        self.y_offset_var = tk.IntVar(value=0)
        y_offset_scale = ttk.Scale(
            mask_frame,
            from_=-100,
            to=100,
            variable=self.y_offset_var,
            orient=tk.HORIZONTAL,
            length=200,
            command=self.on_mask_adjust,
        )
        y_offset_scale.grid(row=2, column=1, padx=(0, 20))
        ttk.Label(mask_frame, textvariable=self.y_offset_var).grid(row=2, column=2)

        # Reset button
        reset_btn = ttk.Button(
            mask_frame, text="Reset Adjustments", command=self.reset_adjustments
        )
        reset_btn.grid(row=3, column=0, columnspan=3, pady=(10, 0))

    def create_action_buttons(self, parent):
        """Create the action buttons."""
        # Button frame
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=3, column=0, columnspan=3, pady=(0, 10))

        # Save button
        save_btn = ttk.Button(
            button_frame,
            text="save image",
            command=self.save_image,
            style="Large.TButton",
        )
        save_btn.grid(row=0, column=0, padx=(0, 10))

        # Cancel button
        cancel_btn = ttk.Button(button_frame, text="cancel", command=self.cancel)
        cancel_btn.grid(row=0, column=1, padx=(0, 10))

        # Re-process button
        reprocess_btn = ttk.Button(
            button_frame, text=" reprocess", command=self.reprocess_image
        )
        reprocess_btn.grid(row=0, column=2)

    def display_image(self):
        """Display the processed image on the canvas."""
        try:
            # Convert BGR to RGB
            rgb_image = cv2.cvtColor(self.processed_image, cv2.COLOR_BGR2RGB)

            # Convert to PIL Image
            pil_image = Image.fromarray(rgb_image)

            # Resize to fit canvas while maintaining aspect ratio
            canvas_width = 600
            canvas_height = 400

            # Calculate scaling
            img_width, img_height = pil_image.size
            scale = min(canvas_width / img_width, canvas_height / img_height)

            if scale < 1:
                new_width = int(img_width * scale)
                new_height = int(img_height * scale)
                pil_image = pil_image.resize(
                    (new_width, new_height), Image.Resampling.LANCZOS
                )

            # Convert to PhotoImage
            self.photo_image = ImageTk.PhotoImage(pil_image)

            # Clear canvas and display image
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo_image)

            # Update scroll region
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        except Exception as e:
            messagebox.showerror("Error", f"Failed to display image: {str(e)}")

    def on_processing_change(self):
        """Handle processing method changes (homography toggle)."""
        try:
            # Re-process with current settings
            self.reprocess_with_current_settings()
        except Exception as e:
            messagebox.showerror(
                "Error", f"Failed to change processing method: {str(e)}"
            )

    def on_mask_adjust(self, *args):
        """Handle mask adjustment changes."""
        try:
            # Re-process with current settings
            self.reprocess_with_current_settings()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to adjust mask: {str(e)}")

    def reprocess_with_current_settings(self):
        """Re-process the image with current settings (homography + mask adjustments)."""
        try:
            # Get current settings
            use_homography = self.use_homography_var.get()
            scale = self.scale_var.get()
            x_offset = self.x_offset_var.get()
            y_offset = self.y_offset_var.get()

            # Load original image
            original_image = cv2.imread(self.original_image_path)
            if original_image is None:
                raise ValueError("Could not load original image")

            # Detect markers
            markers = self.detector.detect_markers(original_image)
            if not markers:
                raise ValueError("No markers detected")

            # Get template mask path first
            marker_ids = [marker.id for marker in markers]
            template_id = self.detector.detect_template(marker_ids)

            # Get corner markers (now template-aware)
            corner_markers = self.detector.get_corner_markers(markers)
            if corner_markers is None:
                raise ValueError("Could not find corner markers")

            # Apply cropping based on homography setting
            if use_homography:
                # Apply homography for perspective correction, then crop
                cropped = self.detector._apply_homography_and_crop(
                    original_image, corner_markers
                )
            else:
                # Use simple cropping
                cropped = self.detector._crop_marker_area(
                    original_image, corner_markers
                )

            # Get template mask path
            template_mask_path = self.detector.get_template_mask_path()

            if template_mask_path:
                # Apply mask with adjustments
                adjusted_image = self.apply_adjusted_mask(
                    cropped, template_mask_path, scale, x_offset, y_offset
                )
                self.processed_image = self.detector._crop_masked_area(adjusted_image)
            else:
                self.processed_image = cropped

            # Update display
            self.display_image()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to re-process: {str(e)}")

    def reprocess_with_adjustments(self, scale, x_offset, y_offset):
        """Re-process the image with mask adjustments (legacy method)."""
        self.reprocess_with_current_settings()

    def apply_adjusted_mask(self, image, mask_path, scale, x_offset, y_offset):
        """Apply mask with manual adjustments."""
        try:
            # Load mask
            mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
            if mask is None:
                raise ValueError("Could not load mask")

            # Resize mask to match image
            mask_resized = cv2.resize(mask, (image.shape[1], image.shape[0]))

            # Apply scaling
            if scale != 1.0:
                # Calculate new size
                new_width = int(mask_resized.shape[1] * scale)
                new_height = int(mask_resized.shape[0] * scale)

                # Resize mask
                mask_resized = cv2.resize(mask_resized, (new_width, new_height))

                # Create new mask of original size
                new_mask = np.zeros((image.shape[0], image.shape[1]), dtype=np.uint8)

                # Calculate position
                y_start = max(0, (image.shape[0] - new_height) // 2 + y_offset)
                x_start = max(0, (image.shape[1] - new_width) // 2 + x_offset)

                # Ensure we don't go out of bounds
                y_end = min(image.shape[0], y_start + new_height)
                x_end = min(image.shape[1], x_start + new_width)

                # Copy resized mask to new mask
                mask_height = y_end - y_start
                mask_width = x_end - x_start
                new_mask[y_start:y_end, x_start:x_end] = mask_resized[
                    :mask_height, :mask_width
                ]

                mask_resized = new_mask

            # Apply offset
            if x_offset != 0 or y_offset != 0:
                # Create transformation matrix
                M = np.float32([[1, 0, x_offset], [0, 1, y_offset]])
                mask_resized = cv2.warpAffine(
                    mask_resized, M, (image.shape[1], image.shape[0])
                )

            # Create BGRA image
            bgra_image = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)

            # Apply mask
            _, binary_mask = cv2.threshold(mask_resized, 128, 255, cv2.THRESH_BINARY)
            bgra_image[:, :, 3] = binary_mask
            masked_bgr = cv2.bitwise_and(
                bgra_image[:, :, :3], bgra_image[:, :, :3], mask=binary_mask
            )
            bgra_image[:, :, :3] = masked_bgr

            return bgra_image

        except Exception as e:
            raise ValueError(f"Failed to apply adjusted mask: {str(e)}")

    def reset_adjustments(self):
        """Reset all adjustments to default values."""
        self.use_homography_var.set(True)  # Default to homography
        self.scale_var.set(1.0)
        self.x_offset_var.set(0)
        self.y_offset_var.set(0)
        self.reprocess_with_current_settings()

    def save_image(self):
        """Save the processed image."""
        try:
            # Generate output path
            input_path = Path(self.original_image_path)
            output_dir = Path("data/processed_images")
            output_dir.mkdir(parents=True, exist_ok=True)

            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_filename = f"{input_path.stem}_{timestamp}_processed.png"
            output_path = output_dir / output_filename

            # Save the image
            cv2.imwrite(str(output_path), self.processed_image)

            # Set result and close window
            self.result = str(output_path)
            self.window.destroy()

            messagebox.showinfo(
                "Success", f"Image saved successfully!\nSaved to: {output_path}"
            )

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save image: {str(e)}")

    def cancel(self):
        """Cancel the operation."""
        self.result = None
        self.window.destroy()

    def reprocess_image(self):
        """Re-process the image from scratch."""
        try:
            # Reset adjustments
            self.reset_adjustments()

            # Re-process with original settings
            self.reprocess_with_adjustments(1.0, 0, 0)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to re-process: {str(e)}")


class KrathongScannerUI:
    """
    Modern UI for KrathongScanner application.

    Features:
    - Clean, modern interface
    - File browser for image import
    - Webcam integration
    - Auto directory monitoring
    """

    def __init__(self):
        """Initialize the UI."""
        self.logger = self._setup_logger()
        self.root = None
        self.auto_monitor_thread = None
        self.auto_monitor_running = False
        self.monitored_directory = None
        self.processed_files = set()

        # Initialize detector
        self.aruco_detector = ArUcoDetector()

    def _setup_logger(self) -> logging.Logger:
        """Setup logger for the UI."""
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def run(self):
        """Start the UI application."""
        self.root = tk.Tk()
        self.root.title("KrathongScanner")
        self.root.geometry("600x500")
        self.root.resizable(False, False)

        # Center the window
        self.center_window()

        # Configure style
        self.setup_styles()

        # Create main interface
        self.create_main_interface()

        # Start the main loop
        self.root.mainloop()

    def center_window(self):
        """Center the window on screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def setup_styles(self):
        """Setup modern styles for the UI."""
        style = ttk.Style()
        style.theme_use("clam")

        # Configure styles
        style.configure("Title.TLabel", font=("Segoe UI", 24, "bold"))
        style.configure("Subtitle.TLabel", font=("Segoe UI", 12))
        style.configure("Button.TButton", font=("Segoe UI", 11))
        style.configure("Large.TButton", font=("Segoe UI", 12, "bold"))

    def create_main_interface(self):
        """Create the main interface."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="40")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Title
        title_label = ttk.Label(
            main_frame, text="KrathongScanner", style="Title.TLabel"
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        subtitle_label = ttk.Label(
            main_frame,
            text=" krathong detection and processing",
            style="Subtitle.TLabel",
        )
        subtitle_label.grid(row=1, column=0, columnspan=2, pady=(0, 40))

        # Mode selection buttons
        self.create_mode_buttons(main_frame)

        # Status area
        self.create_status_area(main_frame)

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

    def create_mode_buttons(self, parent):
        """Create the mode selection buttons."""
        # Button container
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(0, 30))

        # Import from picture button
        import_btn = ttk.Button(
            button_frame,
            text="import from picture",
            style="Large.TButton",
            command=self.import_from_picture,
        )
        import_btn.grid(row=0, column=0, padx=10, pady=10, sticky=(tk.W, tk.E))

        # Webcam button
        webcam_btn = ttk.Button(
            button_frame,
            text="use webcam",
            style="Large.TButton",
            command=self.use_webcam,
        )
        webcam_btn.grid(row=1, column=0, padx=10, pady=10, sticky=(tk.W, tk.E))

        # Auto directory button
        auto_btn = ttk.Button(
            button_frame,
            text="auto directory mode",
            style="Large.TButton",
            command=self.auto_directory_mode,
        )
        auto_btn.grid(row=2, column=0, padx=10, pady=10, sticky=(tk.W, tk.E))

        # Configure button frame
        button_frame.columnconfigure(0, weight=1)

    def create_status_area(self, parent):
        """Create the status display area."""
        # Settings frame
        settings_frame = ttk.LabelFrame(parent, text="Settings", padding="10")
        settings_frame.grid(
            row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10)
        )

        # Homography toggle for initial processing
        ttk.Label(settings_frame, text="Default Perspective Correction:").grid(
            row=0, column=0, padx=(0, 10)
        )
        self.default_homography_var = tk.BooleanVar(value=True)
        homography_check = ttk.Checkbutton(
            settings_frame, text="Use Homography", variable=self.default_homography_var
        )
        homography_check.grid(row=0, column=1, padx=(0, 10))
        ttk.Label(settings_frame, text="(For imported images)").grid(row=0, column=2)

        # Status frame
        status_frame = ttk.LabelFrame(parent, text="Status", padding="10")
        status_frame.grid(
            row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20)
        )

        # Status text
        self.status_text = tk.Text(status_frame, height=8, width=60, wrap=tk.WORD)
        self.status_text.grid(row=0, column=0, sticky=(tk.W, tk.E))

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            status_frame, orient=tk.VERTICAL, command=self.status_text.yview
        )
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.status_text.configure(yscrollcommand=scrollbar.set)

        # Configure status frame
        status_frame.columnconfigure(0, weight=1)
        status_frame.rowconfigure(0, weight=1)

        # Initial status
        self.update_status("ready!")

    def update_status(self, message: str):
        """Update the status display."""
        timestamp = time.strftime("%H:%M:%S")
        status_line = f"[{timestamp}] {message}\n"

        self.status_text.insert(tk.END, status_line)
        self.status_text.see(tk.END)

        # Keep only last 50 lines
        lines = self.status_text.get("1.0", tk.END).split("\n")
        if len(lines) > 50:
            self.status_text.delete("1.0", f"{len(lines) - 50}.0")

    def import_from_picture(self):
        """Handle import from picture mode."""
        try:
            # Open file dialog
            file_path = filedialog.askopenfilename(
                title="Select Krathong Image",
                filetypes=[
                    ("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff"),
                    ("All files", "*.*"),
                ],
            )

            if not file_path:
                return

            self.update_status(f"Processing image: {os.path.basename(file_path)}")

            # Process in background thread
            thread = threading.Thread(
                target=self.process_image_with_preview, args=(file_path,), daemon=True
            )
            thread.start()

        except Exception as e:
            self.logger.error(f"Error in import from picture: {e}")
            self.update_status(f"❌ Error: {str(e)}")

    def process_image_with_preview(self, file_path: str):
        """Process an image file with preview functionality."""
        try:
            # Load and process the image
            image = cv2.imread(file_path)
            if image is None:
                raise ValueError("Could not load image")

            # Detect markers
            markers = self.aruco_detector.detect_markers(image)
            if not markers:
                raise ValueError("No markers detected")

            # Get template mask path first
            marker_ids = [marker.id for marker in markers]
            template_id = self.aruco_detector.detect_template(marker_ids)

            # Get corner markers (now template-aware)
            corner_markers = self.aruco_detector.get_corner_markers(markers)
            if corner_markers is None:
                raise ValueError("Could not find corner markers")

            # Apply cropping based on default homography setting
            use_homography = self.default_homography_var.get()
            if use_homography:
                # Apply homography for perspective correction, then crop
                cropped = self.aruco_detector._apply_homography_and_crop(
                    image, corner_markers
                )
            else:
                # Use simple cropping
                cropped = self.aruco_detector._crop_marker_area(image, corner_markers)

            # Get template mask path
            template_mask_path = self.aruco_detector.get_template_mask_path()

            if template_mask_path:
                # Apply template mask
                masked = self.aruco_detector.apply_template_mask(
                    cropped, template_mask_path
                )
                processed_image = self.aruco_detector._crop_masked_area(masked)
            else:
                processed_image = cropped

            # Show preview window
            self.root.after(
                0, lambda: self.show_preview_window(file_path, processed_image)
            )

        except Exception as e:
            self.logger.error(f"Error processing image: {e}")
            error_msg = str(e)
            self.root.after(
                0, lambda: self.update_status(f"❌ Error processing image: {error_msg}")
            )

    def show_preview_window(self, file_path: str, processed_image: np.ndarray):
        """Show the preview window."""
        try:
            preview_window = ImagePreviewWindow(
                self.root, file_path, processed_image, self.aruco_detector
            )
            # Set the initial homography setting to match the default
            preview_window.use_homography_var.set(self.default_homography_var.get())

            if preview_window.result:
                # Image was saved
                self.update_status(
                    f"✅ Successfully processed and saved: {os.path.basename(preview_window.result)}"
                )
            else:
                # User cancelled
                self.update_status("❌ Image processing cancelled by user")

        except Exception as e:
            self.logger.error(f"Error showing preview: {e}")
            self.update_status(f"❌ Error showing preview: {str(e)}")

    def process_image_file(self, file_path: str):
        """Process an image file (legacy method for auto directory mode)."""
        try:
            # Generate output path
            input_path = Path(file_path)
            output_dir = Path("data/processed_images")
            output_dir.mkdir(parents=True, exist_ok=True)

            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_filename = f"{input_path.stem}_{timestamp}_processed.png"
            output_path = output_dir / output_filename

            # Process the image - use a default mask path since we'll detect the template automatically
            default_mask_path = (
                "data/markers/templates/mask1_final.png"  # Default fallback
            )
            success = self.aruco_detector.process_image(
                str(input_path), default_mask_path, str(output_path)
            )

            if success:
                self.update_status(f"✅ Successfully processed: {output_filename}")
            else:
                self.update_status(f"❌ Failed to process image")

        except Exception as e:
            self.logger.error(f"Error processing image: {e}")
            self.update_status(f"❌ Error processing image: {str(e)}")

    def use_webcam(self):
        """Handle webcam mode."""
        try:
            self.update_status("Starting webcam mode...")

            # Start webcam in background thread
            thread = threading.Thread(target=self.start_webcam_detector, daemon=True)
            thread.start()

        except Exception as e:
            self.logger.error(f"Error starting webcam: {e}")
            self.update_status(f"❌ Error starting webcam: {str(e)}")

    def start_webcam_detector(self):
        """Start the webcam detector."""
        try:
            detector = WebcamDetectorWithPaper()
            self.update_status("📷 Webcam mode started - Press 'q' to quit")
            detector.run()
            self.update_status("📷 Webcam mode stopped")

        except Exception as e:
            self.logger.error(f"Error in webcam detector: {e}")
            self.update_status(f"❌ Webcam error: {str(e)}")

    def auto_directory_mode(self):
        """Handle auto directory mode."""
        try:
            # Select directory
            directory = filedialog.askdirectory(title="Select Directory to Monitor")

            if not directory:
                return

            self.monitored_directory = Path(directory)
            self.update_status(f"📂 Monitoring directory: {self.monitored_directory}")

            # Start monitoring in background
            if not self.auto_monitor_running:
                self.auto_monitor_running = True
                self.auto_monitor_thread = threading.Thread(
                    target=self.monitor_directory, daemon=True
                )
                self.auto_monitor_thread.start()

                # Update button to show stop option
                self.update_status(
                    "🔄 Auto monitoring started - New files will be processed automatically"
                )

        except Exception as e:
            self.logger.error(f"Error in auto directory mode: {e}")
            self.update_status(f"❌ Error: {str(e)}")

    def monitor_directory(self):
        """Monitor directory for new files."""
        try:
            while self.auto_monitor_running:
                # Check for new image files
                image_extensions = {".png", ".jpg", ".jpeg", ".bmp", ".tiff"}

                for file_path in self.monitored_directory.iterdir():
                    if (
                        file_path.is_file()
                        and file_path.suffix.lower() in image_extensions
                        and str(file_path) not in self.processed_files
                    ):
                        # Process the new file
                        self.processed_files.add(str(file_path))
                        self.update_status(f"🔄 Processing new file: {file_path.name}")

                        # Process in separate thread to avoid blocking
                        thread = threading.Thread(
                            target=self.process_image_file,
                            args=(str(file_path),),
                            daemon=True,
                        )
                        thread.start()

                        # Wait a bit to avoid processing too many files at once
                        time.sleep(2)

                # Check every 5 seconds
                time.sleep(5)

        except Exception as e:
            self.logger.error(f"Error in directory monitoring: {e}")
            self.update_status(f"❌ Monitoring error: {str(e)}")
            self.auto_monitor_running = False


def main():
    """Main function to run the UI."""
    app = KrathongScannerUI()
    app.run()


if __name__ == "__main__":
    main()
