"""
Modern UI Menu for KrathongScanner.

This module provides a clean, user-friendly interface for:
- Import krathong from picture (file browser)
- Use webcam for real-time scanning
- Auto directory monitoring mode
"""

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
    """Enhanced window for previewing and adjusting processed images with visual mask controls."""

    def __init__(
        self, parent, original_image_path: str, processed_image: np.ndarray, detector
    ):
        self.parent = parent
        self.original_image_path = original_image_path
        self.processed_image = processed_image.copy()
        self.detector = detector
        self.result = None

        # Mask adjustment state
        self.mask_overlay_visible = True
        self.mask_scale = 1.0
        self.mask_x_offset = 0
        self.mask_y_offset = 0
        self.mask_rotation = 0.0

        # Interactive transform state
        self.dragging = False
        self.drag_start = None
        self.selected_handle = None
        self.dragging_box = False
        self.transform_handles = []  # [(x, y, handle_type), ...]
        self.mask_box = None  # (x, y, width, height)

        # Create preview window
        self.window = tk.Toplevel(parent)
        self.window.title("Enhanced Image Preview & Mask Adjustment")
        self.window.geometry("1400x1000")
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
        """Create the enhanced preview interface."""
        # Main container
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Title
        title_label = ttk.Label(
            main_frame,
            text="Enhanced Image Preview & Mask Adjustment",
            font=("Segoe UI", 16, "bold"),
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # Image preview area with mask overlay
        self.create_enhanced_image_preview(main_frame)

        # Enhanced controls area
        self.create_enhanced_controls(main_frame)

        # Action buttons
        self.create_action_buttons(main_frame)

        # Configure grid weights
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)

    def create_enhanced_image_preview(self, parent):
        """Create the enhanced image preview area with mask overlay."""
        # Preview frame
        preview_frame = ttk.LabelFrame(parent, text="Interactive Preview", padding="10")
        preview_frame.grid(
            row=1, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 20)
        )

        # Canvas for image display with mask overlay
        self.canvas = tk.Canvas(preview_frame, bg="white", width=1200, height=700)
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

        # Bind mouse events for interactive mask adjustment
        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.canvas.bind("<Motion>", self.on_mouse_move)

        # Initialize mask overlay variable before displaying
        self.mask_overlay_var = tk.BooleanVar(value=True)

        # Display the processed image with mask overlay
        self.display_image_with_mask()

    def create_enhanced_controls(self, parent):
        """Create the enhanced control panel."""
        # Controls frame
        controls_frame = ttk.LabelFrame(
            parent, text="Enhanced Processing Controls", padding="10"
        )
        controls_frame.grid(
            row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20)
        )

        # Processing method toggle
        processing_frame = ttk.Frame(controls_frame)
        processing_frame.grid(
            row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15)
        )

        ttk.Label(processing_frame, text="Perspective Correction:").grid(
            row=0, column=0, padx=(0, 10)
        )
        self.use_homography_var = tk.BooleanVar(value=True)
        homography_check = ttk.Checkbutton(
            processing_frame,
            text="Use Homography",
            variable=self.use_homography_var,
            command=self.on_processing_change,
        )
        homography_check.grid(row=0, column=1, padx=(0, 10))
        ttk.Label(processing_frame, text="(Straightens warped images)").grid(
            row=0, column=2
        )

        # Mask overlay toggle
        ttk.Label(processing_frame, text="Mask Overlay:").grid(
            row=1, column=0, padx=(0, 10)
        )
        overlay_check = ttk.Checkbutton(
            processing_frame,
            text="Show Mask Overlay",
            variable=self.mask_overlay_var,
            command=self.toggle_mask_overlay,
        )
        overlay_check.grid(row=1, column=1, padx=(0, 10))
        ttk.Label(processing_frame, text="(Visual mask preview)").grid(row=1, column=2)

        # Quick adjustment controls
        quick_frame = ttk.LabelFrame(
            controls_frame, text="Quick Adjustments", padding="5"
        )
        quick_frame.grid(
            row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10)
        )

        # Scale control
        ttk.Label(quick_frame, text="Scale:").grid(row=0, column=0, padx=(0, 10))
        self.scale_var = tk.DoubleVar(value=1.0)
        scale_scale = ttk.Scale(
            quick_frame,
            from_=0.5,
            to=2.0,
            variable=self.scale_var,
            orient=tk.HORIZONTAL,
            length=150,
            command=self.on_quick_adjust,
        )
        scale_scale.grid(row=0, column=1, padx=(0, 10))
        ttk.Label(quick_frame, textvariable=self.scale_var).grid(row=0, column=2)

        # X Offset control
        ttk.Label(quick_frame, text="X Offset:").grid(row=1, column=0, padx=(0, 10))
        self.x_offset_var = tk.IntVar(value=0)
        x_offset_scale = ttk.Scale(
            quick_frame,
            from_=-100,
            to=100,
            variable=self.x_offset_var,
            orient=tk.HORIZONTAL,
            length=150,
            command=self.on_quick_adjust,
        )
        x_offset_scale.grid(row=1, column=1, padx=(0, 10))
        ttk.Label(quick_frame, textvariable=self.x_offset_var).grid(row=1, column=2)

        # Y Offset control
        ttk.Label(quick_frame, text="Y Offset:").grid(row=2, column=0, padx=(0, 10))
        self.y_offset_var = tk.IntVar(value=0)
        y_offset_scale = ttk.Scale(
            quick_frame,
            from_=-100,
            to=100,
            variable=self.y_offset_var,
            orient=tk.HORIZONTAL,
            length=150,
            command=self.on_quick_adjust,
        )
        y_offset_scale.grid(row=2, column=1, padx=(0, 10))
        ttk.Label(quick_frame, textvariable=self.y_offset_var).grid(row=2, column=2)

        # Reset button
        reset_btn = ttk.Button(
            quick_frame, text="Reset All", command=self.reset_adjustments
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
            text="💾 Save Image",
            command=self.save_image,
            style="Large.TButton",
        )
        save_btn.grid(row=0, column=0, padx=(0, 10))

        # Cancel button
        cancel_btn = ttk.Button(button_frame, text="❌ Cancel", command=self.cancel)
        cancel_btn.grid(row=0, column=1, padx=(0, 10))

        # Re-process button
        reprocess_btn = ttk.Button(
            button_frame, text="🔄 Re-process", command=self.reprocess_image
        )
        reprocess_btn.grid(row=0, column=2)

    def display_image_with_mask(self):
        """Display the processed image with mask overlay."""
        try:
            # Convert BGR to RGB
            rgb_image = cv2.cvtColor(self.processed_image, cv2.COLOR_BGR2RGB)

            # Convert to PIL Image
            pil_image = Image.fromarray(rgb_image)

            # Resize to fit canvas while maintaining aspect ratio
            canvas_width = 1200
            canvas_height = 700

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

            # Add mask overlay if enabled
            if self.mask_overlay_var.get():
                self.draw_mask_overlay()

            # Update scroll region
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        except Exception as e:
            messagebox.showerror("Error", f"Failed to display image: {str(e)}")

    def draw_mask_overlay(self):
        """Draw the mask overlay on the canvas."""
        try:
            # Get the current mask parameters
            scale = self.scale_var.get()
            x_offset = self.x_offset_var.get()
            y_offset = self.y_offset_var.get()

            # Calculate mask bounds based on actual image dimensions
            img_width, img_height = self.photo_image.width(), self.photo_image.height()

            # Calculate mask rectangle (representing the actual mask area)
            # Use a reasonable default size that matches typical mask proportions
            base_width = int(img_width * 0.85)  # 85% of image width
            base_height = int(img_height * 0.85)  # 85% of image height

            # Apply scale
            mask_width = int(base_width * scale)
            mask_height = int(base_height * scale)

            # Center the mask and apply offsets
            mask_x = (img_width - mask_width) // 2 + x_offset
            mask_y = (img_height - mask_height) // 2 + y_offset

            # Store mask box coordinates for dragging
            self.mask_box = (mask_x, mask_y, mask_width, mask_height)

            # Draw semi-transparent mask overlay
            self.canvas.create_rectangle(
                mask_x,
                mask_y,
                mask_x + mask_width,
                mask_y + mask_height,
                outline="red",
                width=2,
                dash=(5, 5),
                fill="",
                stipple="gray50",
            )

            # Draw corner handles for interactive adjustment
            handle_size = 8
            handles = [
                (mask_x, mask_y, "top-left"),
                (mask_x + mask_width, mask_y, "top-right"),
                (mask_x, mask_y + mask_height, "bottom-left"),
                (mask_x + mask_width, mask_y + mask_height, "bottom-right"),
            ]

            self.transform_handles = []
            for x, y, handle_type in handles:
                self.canvas.create_rectangle(
                    x - handle_size // 2,
                    y - handle_size // 2,
                    x + handle_size // 2,
                    y + handle_size // 2,
                    fill="yellow",
                    outline="red",
                    width=2,
                )
                self.transform_handles.append((x, y, handle_type))

            # Add instruction text
            self.canvas.create_text(
                10,
                10,
                anchor=tk.NW,
                text="Drag box to move, handles to resize",
                fill="white",
                font=("Arial", 12, "bold"),
            )

            # Add current values display
            self.canvas.create_text(
                10,
                35,
                anchor=tk.NW,
                text=f"Scale: {scale:.2f}, X: {x_offset}, Y: {y_offset}",
                fill="white",
                font=("Arial", 10),
            )

        except Exception as e:
            pass  # Silently ignore mask overlay errors

    def toggle_mask_overlay(self):
        """Toggle the mask overlay visibility."""
        self.mask_overlay_visible = self.mask_overlay_var.get()
        self.display_image_with_mask()

    def on_mouse_down(self, event):
        """Handle mouse button press."""
        self.dragging = True
        self.drag_start = (event.x, event.y)

        # Check if clicking on a handle
        for i, (x, y, handle_type) in enumerate(self.transform_handles):
            if abs(event.x - x) <= 8 and abs(event.y - y) <= 8:
                self.selected_handle = i
                return

        # Check if clicking inside the mask box for dragging
        if self.mask_box:
            x, y, width, height = self.mask_box
            if x <= event.x <= x + width and y <= event.y <= y + height:
                self.dragging_box = True
                self.selected_handle = None

    def on_mouse_drag(self, event):
        """Handle mouse drag."""
        if not self.dragging:
            return

        # Calculate drag delta
        dx = event.x - self.drag_start[0]
        dy = event.y - self.drag_start[1]

        if self.dragging_box:
            # Dragging the entire mask box
            self.x_offset_var.set(self.x_offset_var.get() + dx)
            self.y_offset_var.set(self.y_offset_var.get() + dy)
        elif self.selected_handle is not None:
            # Dragging a corner handle
            handle_type = self.transform_handles[self.selected_handle][2]

            if "left" in handle_type:
                self.x_offset_var.set(self.x_offset_var.get() + dx)
            if "right" in handle_type:
                # Adjust scale for right handles
                scale_change = dx / 100.0
                new_scale = self.scale_var.get() + scale_change
                self.scale_var.set(max(0.5, min(2.0, new_scale)))
            if "top" in handle_type:
                self.y_offset_var.set(self.y_offset_var.get() + dy)
            if "bottom" in handle_type:
                # Adjust scale for bottom handles
                scale_change = dy / 100.0
                new_scale = self.scale_var.get() + scale_change
                self.scale_var.set(max(0.5, min(2.0, new_scale)))

        # Update drag start position
        self.drag_start = (event.x, event.y)

        # Re-process the image with new mask settings
        self.reprocess_with_current_settings()

    def on_mouse_up(self, event):
        """Handle mouse button release."""
        self.dragging = False
        self.dragging_box = False
        self.selected_handle = None
        self.drag_start = None

    def on_mouse_move(self, event):
        """Handle mouse movement for cursor changes."""
        # Change cursor when hovering over handles or mask box
        cursor = "arrow"

        # Check handles first
        for x, y, handle_type in self.transform_handles:
            if abs(event.x - x) <= 8 and abs(event.y - y) <= 8:
                cursor = "crosshair"
                break

        # Check if hovering over mask box
        if cursor == "arrow" and self.mask_box:
            x, y, width, height = self.mask_box
            if x <= event.x <= x + width and y <= event.y <= y + height:
                cursor = "fleur"  # Move cursor

        self.canvas.configure(cursor=cursor)

    def on_processing_change(self):
        """Handle processing method changes (homography toggle)."""
        try:
            self.reprocess_with_current_settings()
        except Exception as e:
            messagebox.showerror(
                "Error", f"Failed to change processing method: {str(e)}"
            )

    def on_quick_adjust(self, *args):
        """Handle quick adjustment changes."""
        try:
            # Update internal state
            self.mask_scale = self.scale_var.get()
            self.mask_x_offset = self.x_offset_var.get()
            self.mask_y_offset = self.y_offset_var.get()

            # Re-process the image with new mask settings
            self.reprocess_with_current_settings()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to adjust mask: {str(e)}")

    def reprocess_with_current_settings(self):
        """Re-process the image with current settings."""
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
            self.display_image_with_mask()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to re-process: {str(e)}")

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
        self.use_homography_var.set(True)
        self.scale_var.set(1.0)
        self.x_offset_var.set(0)
        self.y_offset_var.set(0)
        self.mask_overlay_var.set(True)
        self.reprocess_with_current_settings()

    def save_image(self):
        """Save the processed image."""
        try:
            # Generate output path using parent's output directory
            input_path = Path(self.original_image_path)
            timestamp = time.strftime("%Y%m%d_%H%M%S")

            # Get output directory from parent UI
            output_dir = (
                self.parent.output_directory
                if hasattr(self.parent, "output_directory")
                else Path("data/processed_images")
            )
            output_dir.mkdir(parents=True, exist_ok=True)

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
        self.root = None
        self.auto_monitor_thread = None
        self.auto_monitor_running = False
        self.monitored_directory = None
        self.processed_files = set()

        # Output directory
        self.output_directory = Path("data/processed_images")
        self.output_directory.mkdir(parents=True, exist_ok=True)

        # Initialize detector
        self.aruco_detector = ArUcoDetector()

    def run(self):
        """Start the UI application."""
        self.root = tk.Tk()
        self.root.title("KrathongScanner")
        self.root.geometry("700x650")  # Made taller for output directory section
        self.root.resizable(True, True)

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

        # Output directory section
        self.create_output_directory_section(main_frame)

        # Settings area
        self.create_settings_area(main_frame)

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

    def create_output_directory_section(self, parent):
        """Create the output directory selection section."""
        # Output directory frame
        output_frame = ttk.LabelFrame(parent, text="Output Directory", padding="10")
        output_frame.grid(
            row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20)
        )

        # Current directory display
        self.output_dir_var = tk.StringVar(value=str(self.output_directory))
        dir_label = ttk.Label(output_frame, text="Current output directory:")
        dir_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 10))

        dir_display = ttk.Entry(
            output_frame, textvariable=self.output_dir_var, state="readonly", width=50
        )
        dir_display.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))

        # Select directory button
        select_dir_btn = ttk.Button(
            output_frame,
            text="📁 Select Directory",
            command=self.select_output_directory,
        )
        select_dir_btn.grid(row=0, column=2, padx=(0, 10))

        # Reset to default button
        reset_dir_btn = ttk.Button(
            output_frame,
            text="🔄 Reset to Default",
            command=self.reset_output_directory,
        )
        reset_dir_btn.grid(row=0, column=3)

        # Configure grid weights
        output_frame.columnconfigure(1, weight=1)

    def select_output_directory(self):
        """Select a new output directory."""
        try:
            directory = filedialog.askdirectory(
                title="Select Output Directory for Processed Images",
                initialdir=str(self.output_directory),
            )

            if directory:
                self.output_directory = Path(directory)
                self.output_directory.mkdir(parents=True, exist_ok=True)
                self.output_dir_var.set(str(self.output_directory))
                messagebox.showinfo(
                    "Success", f"Output directory changed to:\n{self.output_directory}"
                )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to select directory: {str(e)}")

    def reset_output_directory(self):
        """Reset output directory to default."""
        try:
            default_dir = Path("data/processed_images")
            self.output_directory = default_dir
            self.output_directory.mkdir(parents=True, exist_ok=True)
            self.output_dir_var.set(str(self.output_directory))
            messagebox.showinfo(
                "Success",
                f"Output directory reset to default:\n{self.output_directory}",
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reset directory: {str(e)}")

    def create_settings_area(self, parent):
        """Create the settings area."""
        # Settings frame
        settings_frame = ttk.LabelFrame(parent, text="Settings", padding="10")
        settings_frame.grid(
            row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20)
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

            # Process in background thread
            thread = threading.Thread(
                target=self.process_image_with_preview, args=(file_path,), daemon=True
            )
            thread.start()

        except Exception as e:
            messagebox.showerror("Error", f"Error: {str(e)}")

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
            error_msg = str(e)
            self.root.after(
                0,
                lambda: messagebox.showerror(
                    "Error", f"Error processing image: {error_msg}"
                ),
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
                messagebox.showinfo(
                    "Success",
                    f"Successfully processed and saved: {os.path.basename(preview_window.result)}",
                )
            else:
                # User cancelled
                pass  # Silent cancellation

        except Exception as e:
            messagebox.showerror("Error", f"Error showing preview: {str(e)}")

    def process_image_file(self, file_path: str):
        """Process an image file (legacy method for auto directory mode)."""
        try:
            # Generate output path using selected output directory
            input_path = Path(file_path)
            output_dir = self.output_directory
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
                messagebox.showinfo(
                    "Success", f"Successfully processed: {output_filename}"
                )
            else:
                messagebox.showerror("Error", "Failed to process image")

        except Exception as e:
            messagebox.showerror("Error", f"Error processing image: {str(e)}")

    def use_webcam(self):
        """Handle webcam mode."""
        try:
            # Start webcam in background thread
            thread = threading.Thread(target=self.start_webcam_detector, daemon=True)
            thread.start()

        except Exception as e:
            messagebox.showerror("Error", f"Error starting webcam: {str(e)}")

    def start_webcam_detector(self):
        """Start the webcam detector."""
        try:
            # Create webcam detector with custom output directory
            detector = WebcamDetectorWithPaper(capture_dir=str(self.output_directory))
            detector.run()

        except Exception as e:
            messagebox.showerror("Error", f"Webcam error: {str(e)}")

    def auto_directory_mode(self):
        """Handle auto directory mode."""
        try:
            # Select directory
            directory = filedialog.askdirectory(title="Select Directory to Monitor")

            if not directory:
                return

            self.monitored_directory = Path(directory)

            # Start monitoring in background
            if not self.auto_monitor_running:
                self.auto_monitor_running = True
                self.auto_monitor_thread = threading.Thread(
                    target=self.monitor_directory, daemon=True
                )
                self.auto_monitor_thread.start()

                messagebox.showinfo(
                    "Auto Monitoring",
                    "Auto monitoring started - New files will be processed automatically",
                )

        except Exception as e:
            messagebox.showerror("Error", f"Error: {str(e)}")

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
            messagebox.showerror("Error", f"Monitoring error: {str(e)}")
            self.auto_monitor_running = False


def main():
    """Main function to run the UI."""
    app = KrathongScannerUI()
    app.run()


if __name__ == "__main__":
    main()
