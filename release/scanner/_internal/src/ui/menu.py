"""
Modern UI Menu for KrathongScanner.

This module provides a clean, user-friendly interface for:
- Import krathong from picture (file browser)
- Use webcam for real-time scanning
"""

import os
import subprocess
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Callable, Optional

import cv2
import numpy as np

# Import requests for API calls
try:
    import requests
except ImportError:
    requests = None
from PIL import Image, ImageTk

from aruco_detector import ArUcoDetector
from auto_directory_detector import AutoDirectoryDetector
from webcam_detector_with_paper import WebcamDetectorWithPaper


class ImagePreviewWindow:
    """Enhanced window for previewing and adjusting processed images with visual mask controls."""

    def __init__(
        self,
        parent,
        original_image_path: str,
        processed_image: np.ndarray,
        detector,
        output_directory: Path,
    ):
        self.parent = parent
        self.original_image_path = original_image_path
        self.processed_image = processed_image.copy()
        self.detector = detector
        self.output_directory = output_directory
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

            # Resize to fit canvas while maintaining aspect ratios
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

            # Use the output directory passed to this window
            output_dir = self.output_directory
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
    """

    def __init__(self):
        """Initialize the UI."""
        self.root = None

        # Output directory
        self.output_directory = Path("data/processed_images")
        self.output_directory.mkdir(parents=True, exist_ok=True)

        # Initialize detector
        self.aruco_detector = ArUcoDetector()

    def run(self):
        """Start the UI application."""
        self.root = tk.Tk()
        self.root.title("KrathongScanner")

        # Set application icon
        try:
            icon_path = Path("krathong.ico")
            if icon_path.exists():
                self.root.iconbitmap(icon_path)
        except Exception as e:
            # Silently fail if icon can't be loaded
            pass

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
            text="📁 Import from Picture",
            style="Large.TButton",
            command=self.import_from_picture,
        )
        import_btn.grid(row=0, column=0, padx=10, pady=10, sticky=(tk.W, tk.E))

        # Webcam button
        webcam_btn = ttk.Button(
            button_frame,
            text="📷 Use Webcam",
            style="Large.TButton",
            command=self.use_webcam,
        )
        webcam_btn.grid(row=1, column=0, padx=10, pady=10, sticky=(tk.W, tk.E))

        # Auto-directory button
        auto_dir_btn = ttk.Button(
            button_frame,
            text="🔄 Auto-Directory Monitor",
            style="Large.TButton",
            command=self.auto_directory_monitor,
        )
        auto_dir_btn.grid(row=2, column=0, padx=10, pady=10, sticky=(tk.W, tk.E))

        # Web server button
        web_server_btn = ttk.Button(
            button_frame,
            text="🌐 Start Web Server",
            style="Large.TButton",
            command=self.start_web_server,
        )
        web_server_btn.grid(row=3, column=0, padx=10, pady=10, sticky=(tk.W, tk.E))

        # QR Link button
        qr_link_btn = ttk.Button(
            button_frame,
            text="📱 Generate QR Link",
            style="Large.TButton",
            command=self.generate_qr_link,
        )
        qr_link_btn.grid(row=4, column=0, padx=10, pady=10, sticky=(tk.W, tk.E))

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

    def create_status_area(self, parent):
        """Create the status display area."""
        # Status frame
        status_frame = ttk.LabelFrame(parent, text="Status", padding="10")
        status_frame.grid(
            row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20)
        )

        # Status label
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(
            status_frame, textvariable=self.status_var, foreground="green"
        )
        self.status_label.grid(row=0, column=0, sticky=tk.W)

    def show_status(self, message: str, color: str = "blue"):
        """
        Update the status display.

        Args:
            message: Status message to display
            color: Color for the status text (green, blue, red, orange)
        """
        if hasattr(self, "status_var"):
            self.status_var.set(message)
            if hasattr(self, "status_label"):
                self.status_label.configure(foreground=color)

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
                self.root,
                file_path,
                processed_image,
                self.aruco_detector,
                self.output_directory,
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

    def auto_directory_monitor(self):
        """Handle auto-directory monitoring mode."""
        try:
            # Ask user for input directory
            input_directory = filedialog.askdirectory(
                title="Select Directory to Monitor for New Krathong Images",
                initialdir=str(Path.home()),
            )

            if not input_directory:
                return  # User cancelled

            # Confirm directories with user
            result = messagebox.askyesno(
                "Auto-Directory Monitor",
                f"Monitor Directory: {input_directory}\n"
                f"Output Directory: {self.output_directory}\n\n"
                f"Start monitoring for new krathong images?\n\n"
                f"The system will automatically process any new image files\n"
                f"dropped into the monitor directory.",
            )

            if not result:
                return

            # Show status and start monitoring
            self.show_status("Starting auto-directory monitor...")

            # Start auto-directory monitor in background thread
            thread = threading.Thread(
                target=self.start_auto_directory_monitor,
                args=(input_directory,),
                daemon=True,
            )
            thread.start()

            # Show instruction dialog
            messagebox.showinfo(
                "Auto-Directory Monitor Started",
                f"✅ Monitoring: {input_directory}\n"
                f"📤 Output to: {self.output_directory}\n\n"
                f"💡 Drop krathong images into the monitor folder and they will be\n"
                f"    automatically processed!\n\n"
                f"🛑 Close this application to stop monitoring.",
            )

        except Exception as e:
            messagebox.showerror(
                "Error", f"Error starting auto-directory monitor: {str(e)}"
            )

    def generate_qr_link(self):
        """Generate QR code for public tunnel link."""
        try:
            self.show_status("Checking for InstaTunnel connection...")

            # Check if InstaTunnel is running
            tunnel_url = self.detect_tunnel_url()

            if tunnel_url:
                # Generate QR code
                qr_file = self.create_qr_code(tunnel_url)
                if qr_file:
                    # Show success dialog with options
                    result = messagebox.askyesno(
                        "QR Code Generated",
                        f"QR code generated successfully!\n\n"
                        f"Public URL: {tunnel_url}\n"
                        f"QR file: {qr_file}\n\n"
                        f"Would you like to open the QR code file?",
                        icon="question",
                    )

                    if result:
                        # Open QR code file
                        try:
                            if os.name == "nt":  # Windows
                                os.startfile(qr_file)
                            else:  # macOS/Linux
                                subprocess.run(
                                    [
                                        "open"
                                        if sys.platform == "darwin"
                                        else "xdg-open",
                                        qr_file,
                                    ]
                                )
                        except Exception as e:
                            messagebox.showwarning(
                                "Warning", f"Could not open file automatically: {e}"
                            )

                    self.show_status(f"QR code ready: {tunnel_url}")
                else:
                    messagebox.showerror("Error", "Failed to generate QR code")
                    self.show_status("QR generation failed")
            else:
                # InstaTunnel not detected, offer to start it
                result = messagebox.askyesno(
                    "InstaTunnel Not Found",
                    "No InstaTunnel connection detected.\n\n"
                    "InstaTunnel is required for public QR links.\n"
                    "Would you like to learn how to start it?",
                    icon="question",
                )

                if result:
                    self.show_tunnel_instructions()

                self.show_status("InstaTunnel required for QR generation")

        except Exception as e:
            messagebox.showerror("Error", f"QR Link generation error: {str(e)}")
            self.show_status("QR generation error")

    def detect_tunnel_url(self):
        """Detect active InstaTunnel URL or start web server with tunnel."""
        try:
            # First, check if web server is already running locally
            try:
                import requests

                response = requests.get("http://localhost:5000", timeout=2)
                if response.status_code == 200:
                    print("🌐 Local web server is running")

                    # Try to get tunnel URL from server status endpoint
                    try:
                        status_response = requests.get(
                            "http://localhost:5000/api/status", timeout=2
                        )
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            public_url = status_data.get("public_url")
                            if public_url:
                                print(f"✅ Found existing tunnel URL: {public_url}")

                                # Verify tunnel is still working
                                try:
                                    tunnel_response = requests.get(
                                        public_url, timeout=10
                                    )
                                    if tunnel_response.status_code == 200:
                                        print(
                                            f"✅ Tunnel verified working: {public_url}"
                                        )
                                        return public_url
                                    else:
                                        print(f"⚠️ Tunnel not responding, will restart")
                                except:
                                    print(f"⚠️ Tunnel connection failed, will restart")
                            else:
                                print("⚠️ No tunnel URL found, will start one")
                    except:
                        print("⚠️ Could not get server status, will restart")

            except requests.exceptions.RequestException:
                print("🔄 Web server not running, will start it")
                pass

            # If no web server or tunnel not working, start the web server with InstaTunnel
            print("🚀 Starting web server with InstaTunnel...")
            return self.start_web_server_with_tunnel()

        except Exception as e:
            print(f"❌ Tunnel detection error: {e}")
            return None

    def start_web_server_with_tunnel(self):
        """Start the web server with InstaTunnel support - only if not already running."""
        try:
            # Check one more time if server is already running with tunnel
            try:
                import requests

                response = requests.get("http://localhost:5000/api/status", timeout=2)
                if response.status_code == 200:
                    status_data = response.json()
                    public_url = status_data.get("public_url")
                    if public_url:
                        print(f"✅ Server already running with tunnel: {public_url}")
                        return public_url
            except:
                pass

            # Import and start the web server
            from pathlib import Path

            # Add web directory to path
            web_path = Path(__file__).parent.parent.parent / "web"
            sys.path.insert(0, str(web_path))

            # Import server
            import server

            # Setup the server with the current output directory
            server.RESULTS_FOLDER = str(self.output_directory)
            server.setup_auto_detector()

            # IMPORTANT: Start Flask server FIRST, then tunnel
            # Check if Flask server is already running
            flask_running = False
            try:
                test_response = requests.get("http://localhost:5000", timeout=2)
                if test_response.status_code == 200:
                    print("✅ Flask server already running")
                    flask_running = True
            except:
                print("🚀 Starting Flask server first...")

            # Start Flask server if not running
            if not flask_running:

                def run_server():
                    try:
                        server.app.run(
                            host="0.0.0.0", port=5000, debug=False, use_reloader=False
                        )
                    except Exception as e:
                        print(f"Server error: {e}")

                server_thread = threading.Thread(target=run_server, daemon=True)
                server_thread.start()

                # Wait for Flask to be ready
                flask_ready = False
                for attempt in range(10):
                    try:
                        test_response = requests.get("http://localhost:5000", timeout=2)
                        if test_response.status_code == 200:
                            flask_ready = True
                            print(f"✅ Flask server ready (attempt {attempt + 1})")
                            break
                    except:
                        print(f"⏳ Waiting for Flask... (attempt {attempt + 1}/10)")
                        time.sleep(1)

                if not flask_ready:
                    print("❌ Flask server failed to start")
                    return None

            # NOW start InstaTunnel since Flask is ready
            print("🚇 Starting InstaTunnel now that Flask is ready...")
            public_url = server.start_instatunnel(5000)

            if public_url:
                print(f"✅ InstaTunnel connected to running Flask server: {public_url}")
                return public_url
            else:
                print("⚠️ InstaTunnel failed to start, but Flask is running locally")
                # Return local network URL as fallback
                return "http://10.11.0.39:5000"

        except Exception as e:
            print(f"❌ Server start error: {e}")
            return None

    def basic_tunnel_detection(self):
        """Basic tunnel detection fallback."""
        try:
            # Check if InstaTunnel is running by listing active tunnels
            result = subprocess.run(
                ["instatunnel", "--list"],
                capture_output=True,
                text=True,
                timeout=3,
            )

            if result.returncode == 0 and "https://" in result.stdout:
                import re

                # Look for InstaTunnel URL patterns
                url_match = re.search(r"https://[^\s]+", result.stdout)
                if url_match:
                    return url_match.group(0)

            return None

        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return None

    def show_nodejs_installation_dialog(self):
        """Show Node.js installation dialog with options."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Node.js Required")
        dialog.geometry("500x400")
        dialog.resizable(False, False)

        # Center the dialog
        dialog.transient(self.root)
        dialog.grab_set()

        # Main frame
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="Node.js Required for QR Links",
            font=("Segoe UI", 14, "bold"),
        )
        title_label.pack(pady=(0, 20))

        # Explanation
        explanation = (
            "The QR Link feature requires Node.js and InstaTunnel to create "
            "public URLs that work from anywhere.\n\n"
            "Node.js is not detected on your system."
        )
        explanation_label = ttk.Label(main_frame, text=explanation, wraplength=450)
        explanation_label.pack(pady=(0, 20))

        # Options frame
        options_frame = ttk.LabelFrame(
            main_frame, text="Installation Options", padding="10"
        )
        options_frame.pack(fill=tk.X, pady=(0, 20))

        # Option 1: Download Node.js
        option1_btn = ttk.Button(
            options_frame,
            text="📥 Download Node.js (Recommended)",
            command=lambda: self.open_nodejs_download(),
            width=40,
        )
        option1_btn.pack(pady=5)

        # Option 2: Alternative instructions
        option2_btn = ttk.Button(
            options_frame,
            text="📋 Show Manual Installation Steps",
            command=lambda: self.show_manual_install_steps(),
            width=40,
        )
        option2_btn.pack(pady=5)

        # Option 3: Use local network only
        option3_btn = ttk.Button(
            options_frame,
            text="🏠 Use Local Network Only",
            command=lambda: self.show_local_network_info(),
            width=40,
        )
        option3_btn.pack(pady=5)

        # Close button
        close_btn = ttk.Button(main_frame, text="Close", command=dialog.destroy)
        close_btn.pack(pady=(10, 0))

    def open_nodejs_download(self):
        """Open Node.js download page."""
        import webbrowser

        try:
            webbrowser.open("https://nodejs.org/en/download/")
            messagebox.showinfo(
                "Node.js Download",
                "Node.js download page opened in your browser.\n\n"
                "After installation:\n"
                "1. Restart KrathongScanner\n"
                "2. Try 'Generate QR Link' again",
            )
        except Exception:
            messagebox.showinfo(
                "Manual Download",
                "Please visit: https://nodejs.org/en/download/\n"
                "Download and install Node.js, then restart KrathongScanner.",
            )

    def show_manual_install_steps(self):
        """Show manual installation steps."""
        steps = (
            "Manual Installation Steps:\n\n"
            "1. Visit: https://nodejs.org/en/download/\n"
            "2. Download the LTS version for Windows\n"
            "3. Run the installer with default settings\n"
            "4. Restart your computer\n"
            "5. Restart KrathongScanner\n"
            "6. Try 'Generate QR Link' again\n\n"
            "Node.js includes NPM and InstaTunnel capability."
        )
        messagebox.showinfo("Installation Steps", steps)

    def show_local_network_info(self):
        """Show local network alternative."""
        info = (
            "Local Network Alternative:\n\n"
            "Without Node.js, you can still use the web server locally:\n\n"
            "1. Click 'Start Web Server'\n"
            "2. Connect your phone to the same Wi-Fi\n"
            "3. Visit: http://10.11.0.39:5000\n\n"
            "Note: This only works on the same network, not from anywhere."
        )
        messagebox.showinfo("Local Network Option", info)

    def create_qr_code(self, url):
        """Create QR code for the given URL."""
        try:
            import qrcode

            # Create high-quality QR code
            qr = qrcode.QRCode(
                version=2,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=12,
                border=6,
            )
            qr.add_data(url)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            # Save QR code
            qr_filename = f"qr_mall_link.png"
            qr_filepath = os.path.join(self.output_directory, qr_filename)
            img.save(qr_filepath)

            return qr_filepath

        except ImportError:
            messagebox.showerror(
                "Missing Dependency",
                "QR code generation requires the 'qrcode' package.\n\n"
                "Please install it with:\npip install qrcode[pil]",
            )
            return None
        except Exception as e:
            print(f"QR code generation error: {e}")
            return None

    def show_tunnel_instructions(self):
        """Show instructions for starting InstaTunnel."""
        instructions = (
            "How to start InstaTunnel for public QR links:\n\n"
            "1. Open a command prompt or terminal\n"
            "2. Install InstaTunnel: npm install -g instatunnel\n"
            "3. Run: instatunnel 5000\n"
            "4. Keep that terminal window open\n"
            "5. Click 'Generate QR Link' again\n\n"
            "The QR code will work from anywhere in the world!\n\n"
            "InstaTunnel Features:\n"
            "• 24-hour sessions (vs LocalTunnel's 2 hours)\n"
            "• Custom subdomains included\n"
            "• Built-in password protection\n"
            "• Zero configuration required"
        )
        messagebox.showinfo("InstaTunnel Instructions", instructions)

    def start_web_server(self):
        """Handle web server mode."""
        try:
            # Confirm with user
            result = messagebox.askyesno(
                "Start Web Server",
                f"Start KrathongScanner Web Server?\n\n"
                f"📱 Mobile upload interface will be available at:\n"
                f"   • Local: http://localhost:5000\n"
                f"   • Network: http://[your-ip]:5000\n\n"
                f"📁 Uploaded files will be processed automatically\n"
                f"📤 Results will be saved to: {self.output_directory}\n\n"
                f"🌐 Public access available if ngrok is installed\n\n"
                f"Continue?",
            )

            if not result:
                return

            # Show status
            self.show_status("Starting web server...")

            # Start web server in background thread
            thread = threading.Thread(
                target=self.run_web_server_thread,
                daemon=True,
            )
            thread.start()

            # Show instruction dialog
            messagebox.showinfo(
                "Web Server Starting",
                f"🚀 KrathongScanner Web Server is starting...\n\n"
                f"📱 Access from mobile browser:\n"
                f"   • http://localhost:5000 (local)\n"
                f"   • http://[your-computer-ip]:5000 (network)\n\n"
                f"✨ Features:\n"
                f"   • Mobile-friendly upload interface\n"
                f"   • Real-time processing progress\n"
                f"   • Automatic file download\n"
                f"   • QR code for easy mobile access\n\n"
                f"📊 Check server status at: http://localhost:5000/status\n\n"
                f"🛑 Close this application to stop the server.",
            )

        except Exception as e:
            messagebox.showerror("Error", f"Error starting web server: {str(e)}")

    def run_web_server_thread(self):
        """Run the web server in a separate thread."""
        try:
            import sys
            from pathlib import Path

            # Add web directory to path
            web_path = Path(__file__).parent.parent.parent / "web"
            sys.path.insert(0, str(web_path))

            # Import and run server
            import server

            # Update server output directory to match UI setting
            server.RESULTS_FOLDER = str(self.output_directory)

            # Setup auto detector
            server.setup_auto_detector()

            # Update status
            self.show_status("Web server running on http://localhost:5000")

            # Start InstaTunnel if available
            public_url = server.start_instatunnel(5000)
            if public_url:
                self.show_status(f"Public URL: {public_url}")

            # Start Flask server
            server.app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

        except ImportError as e:
            error_msg = (
                f"Web server dependencies not found: {e}\n\n"
                f"Please install required packages:\n"
                f"pip install flask werkzeug requests qrcode pillow"
            )
            messagebox.showerror("Missing Dependencies", error_msg)
            self.show_status("Web server failed - missing dependencies")
        except Exception as e:
            error_msg = f"Web server error: {str(e)}"
            messagebox.showerror("Web Server Error", error_msg)
            self.show_status("Web server stopped due to error")

    def start_auto_directory_monitor(self, input_directory: str):
        """Start the auto-directory detector."""
        try:
            # Create auto-directory detector with same settings as import mode
            detector = AutoDirectoryDetector(
                input_directory=input_directory,
                output_directory=str(self.output_directory),
                check_interval=2.0,
                use_homography=self.default_homography_var.get(),  # Use UI setting
            )

            # Update status
            self.show_status(f"Monitoring: {input_directory}")

            # Run the detector (this will block until stopped)
            detector.run()

        except Exception as e:
            messagebox.showerror("Error", f"Auto-directory monitor error: {str(e)}")
            self.show_status("Auto-directory monitor stopped due to error")


def main():
    """Main function to run the UI."""
    app = KrathongScannerUI()
    app.run()


if __name__ == "__main__":
    main()
