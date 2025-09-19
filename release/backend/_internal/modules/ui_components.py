"""
UI Components Module

Provides reusable UI components for template creation interface.
Extracted and modularized from template_maker_gui.py.

Key Features:
- Preview windows and dialogs
- Control panels and frames
- Interactive adjustment tools
- Canvas management
- File dialogs and selectors

Author: KrathongScanner Team
"""

import logging
import os
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any, Callable, Dict, List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image, ImageTk


class PreviewCanvas:
    """
    Enhanced canvas with image display and scrolling capabilities.

    Handles image scaling, coordinate conversion, and interactive feedback.
    """

    def __init__(self, parent, width: int = 640, height: int = 480, bg: str = "gray90"):
        """Initialize the preview canvas."""
        self.logger = logging.getLogger(__name__)

        # Create frame with scrollbars
        self.frame = ttk.Frame(parent)

        # Canvas setup
        self.canvas = tk.Canvas(
            self.frame, bg=bg, width=width, height=height, cursor="crosshair"
        )

        # Scrollbars
        self.v_scrollbar = ttk.Scrollbar(
            self.frame, orient=tk.VERTICAL, command=self.canvas.yview
        )
        self.h_scrollbar = ttk.Scrollbar(
            self.frame, orient=tk.HORIZONTAL, command=self.canvas.xview
        )

        self.canvas.configure(
            yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set
        )

        # Grid layout
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.v_scrollbar.grid(row=0, column=1, sticky="ns")
        self.h_scrollbar.grid(row=1, column=0, sticky="ew")

        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        # Image state
        self.current_image = None
        self.photo_image = None
        self.scale_factor = 1.0
        self.image_id = None

        # Interactive elements
        self.overlays = {}
        self.callbacks = {}

        self.logger.debug("PreviewCanvas initialized")

    def pack(self, **kwargs):
        """Pack the canvas frame."""
        self.frame.pack(**kwargs)

    def grid(self, **kwargs):
        """Grid the canvas frame."""
        self.frame.grid(**kwargs)

    def display_image(self, image: np.ndarray, fit_to_canvas: bool = True):
        """Display image on canvas with optional scaling."""
        try:
            if image is None:
                return

            # Store original image
            self.current_image = image.copy()

            # Convert BGR to RGB for Tkinter
            if len(image.shape) == 3:
                if image.shape[2] == 4:  # RGBA
                    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA)
                else:  # BGR
                    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:  # Grayscale
                image_rgb = image

            # Calculate scale factor if needed
            if fit_to_canvas:
                canvas_width = self.canvas.winfo_width()
                canvas_height = self.canvas.winfo_height()

                if canvas_width > 1 and canvas_height > 1:  # Canvas is realized
                    img_height, img_width = image.shape[:2]
                    scale_x = canvas_width / img_width
                    scale_y = canvas_height / img_height
                    self.scale_factor = min(scale_x, scale_y, 1.0)  # Don't scale up
                else:
                    self.scale_factor = 0.5  # Default scale

            # Resize image
            img_height, img_width = image.shape[:2]
            new_width = int(img_width * self.scale_factor)
            new_height = int(img_height * self.scale_factor)

            if new_width > 0 and new_height > 0:
                resized = cv2.resize(image_rgb, (new_width, new_height))

                # Convert to PIL and then PhotoImage
                pil_image = Image.fromarray(resized)
                self.photo_image = ImageTk.PhotoImage(pil_image)

                # Clear canvas and display image
                if self.image_id:
                    self.canvas.delete(self.image_id)

                self.image_id = self.canvas.create_image(
                    0, 0, anchor=tk.NW, image=self.photo_image
                )

                # Update scroll region
                self.canvas.configure(scrollregion=self.canvas.bbox("all"))

                self.logger.debug(
                    f"Image displayed: {new_width}x{new_height}, scale: {self.scale_factor:.3f}"
                )

        except Exception as e:
            self.logger.error(f"Failed to display image: {e}")

    def canvas_to_image_coords(
        self, canvas_x: float, canvas_y: float
    ) -> Tuple[int, int]:
        """Convert canvas coordinates to image coordinates."""
        if self.current_image is None:
            return 0, 0

        # Account for canvas scrolling
        canvas_x = self.canvas.canvasx(canvas_x)
        canvas_y = self.canvas.canvasy(canvas_y)

        # Convert to image coordinates
        img_x = int(canvas_x / self.scale_factor)
        img_y = int(canvas_y / self.scale_factor)

        # Clamp to image bounds
        img_height, img_width = self.current_image.shape[:2]
        img_x = max(0, min(img_x, img_width - 1))
        img_y = max(0, min(img_y, img_height - 1))

        return img_x, img_y

    def image_to_canvas_coords(self, img_x: int, img_y: int) -> Tuple[float, float]:
        """Convert image coordinates to canvas coordinates."""
        canvas_x = img_x * self.scale_factor
        canvas_y = img_y * self.scale_factor
        return canvas_x, canvas_y

    def add_overlay(self, name: str, overlay_type: str, coords: List[float], **kwargs):
        """Add overlay element to canvas."""
        if overlay_type == "rectangle":
            overlay_id = self.canvas.create_rectangle(*coords, **kwargs)
        elif overlay_type == "line":
            overlay_id = self.canvas.create_line(*coords, **kwargs)
        elif overlay_type == "oval":
            overlay_id = self.canvas.create_oval(*coords, **kwargs)
        elif overlay_type == "text":
            overlay_id = self.canvas.create_text(*coords, **kwargs)
        else:
            self.logger.warning(f"Unknown overlay type: {overlay_type}")
            return

        self.overlays[name] = overlay_id
        self.canvas.tag_raise(overlay_id)

    def remove_overlay(self, name: str):
        """Remove overlay element."""
        if name in self.overlays:
            self.canvas.delete(self.overlays[name])
            del self.overlays[name]

    def clear_overlays(self):
        """Clear all overlay elements."""
        for overlay_id in self.overlays.values():
            self.canvas.delete(overlay_id)
        self.overlays.clear()

    def bind_event(self, event: str, callback: Callable):
        """Bind event to canvas."""
        self.canvas.bind(event, callback)
        self.callbacks[event] = callback


class ControlPanel:
    """
    Reusable control panel with various input types.

    Supports sliders, entry fields, buttons, and checkboxes.
    """

    def __init__(self, parent, title: str = "Controls", padding: str = "10"):
        """Initialize the control panel."""
        self.logger = logging.getLogger(__name__)

        # Create labeled frame
        self.frame = ttk.LabelFrame(parent, text=title, padding=padding)
        self.controls = {}
        self.variables = {}
        self.callbacks = {}

        self.logger.debug(f"ControlPanel '{title}' initialized")

    def pack(self, **kwargs):
        """Pack the control panel."""
        self.frame.pack(**kwargs)

    def grid(self, **kwargs):
        """Grid the control panel."""
        self.frame.grid(**kwargs)

    def add_slider(
        self,
        name: str,
        label: str,
        from_: float,
        to: float,
        initial: float = 0.0,
        resolution: float = 0.01,
        callback: Optional[Callable] = None,
        orient: str = "horizontal",
    ):
        """Add a slider control."""
        container = ttk.Frame(self.frame)
        container.pack(fill=tk.X, pady=2)

        # Label
        ttk.Label(container, text=label).pack(side=tk.LEFT)

        # Variable
        var = tk.DoubleVar(value=initial)
        self.variables[name] = var

        # Slider
        slider = ttk.Scale(
            container, from_=from_, to=to, variable=var, orient=orient, length=200
        )
        slider.pack(side=tk.LEFT, padx=(10, 0))

        # Value label
        value_label = ttk.Label(container, text=f"{initial:.2f}")
        value_label.pack(side=tk.LEFT, padx=(10, 0))

        # Update callback
        def update_value(*args):
            value_label.config(text=f"{var.get():.2f}")
            if callback:
                callback(var.get())

        var.trace_add("write", update_value)
        if callback:
            self.callbacks[name] = callback

        self.controls[name] = {
            "type": "slider",
            "container": container,
            "variable": var,
            "widget": slider,
            "label": value_label,
        }

    def add_entry(
        self,
        name: str,
        label: str,
        initial: str = "",
        callback: Optional[Callable] = None,
        width: int = 10,
    ):
        """Add an entry field."""
        container = ttk.Frame(self.frame)
        container.pack(fill=tk.X, pady=2)

        # Label
        ttk.Label(container, text=label).pack(side=tk.LEFT)

        # Variable
        var = tk.StringVar(value=initial)
        self.variables[name] = var

        # Entry
        entry = ttk.Entry(container, textvariable=var, width=width)
        entry.pack(side=tk.LEFT, padx=(10, 0))

        # Callback
        if callback:
            var.trace_add("write", lambda *args: callback(var.get()))
            self.callbacks[name] = callback

        self.controls[name] = {
            "type": "entry",
            "container": container,
            "variable": var,
            "widget": entry,
        }

    def add_checkbox(
        self,
        name: str,
        label: str,
        initial: bool = False,
        callback: Optional[Callable] = None,
    ):
        """Add a checkbox."""
        container = ttk.Frame(self.frame)
        container.pack(fill=tk.X, pady=2)

        # Variable
        var = tk.BooleanVar(value=initial)
        self.variables[name] = var

        # Checkbox
        checkbox = ttk.Checkbutton(container, text=label, variable=var)
        checkbox.pack(side=tk.LEFT)

        # Callback
        if callback:
            var.trace_add("write", lambda *args: callback(var.get()))
            self.callbacks[name] = callback

        self.controls[name] = {
            "type": "checkbox",
            "container": container,
            "variable": var,
            "widget": checkbox,
        }

    def add_button_row(self, buttons: List[Dict[str, Any]]):
        """Add a row of buttons."""
        container = ttk.Frame(self.frame)
        container.pack(fill=tk.X, pady=5)

        for i, btn_config in enumerate(buttons):
            text = btn_config["text"]
            command = btn_config["command"]
            side = btn_config.get("side", tk.LEFT)
            padx = btn_config.get("padx", (0, 10) if side == tk.LEFT else (10, 0))

            button = ttk.Button(container, text=text, command=command)
            button.pack(side=side, padx=padx)

    def get_value(self, name: str):
        """Get current value of a control."""
        if name in self.variables:
            return self.variables[name].get()
        return None

    def set_value(self, name: str, value):
        """Set value of a control."""
        if name in self.variables:
            self.variables[name].set(value)

    def get_all_values(self) -> Dict[str, Any]:
        """Get all control values."""
        return {name: var.get() for name, var in self.variables.items()}

    def set_enabled(self, name: str, enabled: bool):
        """Enable or disable a control."""
        if name in self.controls:
            state = "normal" if enabled else "disabled"
            self.controls[name]["widget"].configure(state=state)


class CoordinateInput:
    """
    Coordinate input panel for crop selection and positioning.

    Provides entry fields for X1, Y1, X2, Y2 coordinates with validation.
    """

    def __init__(
        self, parent, title: str = "Coordinates", callback: Optional[Callable] = None
    ):
        """Initialize coordinate input."""
        self.logger = logging.getLogger(__name__)

        # Create frame
        self.frame = ttk.LabelFrame(parent, text=title, padding="10")

        # Variables
        self.x1_var = tk.IntVar(value=0)
        self.y1_var = tk.IntVar(value=0)
        self.x2_var = tk.IntVar(value=0)
        self.y2_var = tk.IntVar(value=0)

        self.callback = callback

        self._setup_ui()
        self._bind_callbacks()

        self.logger.debug("CoordinateInput initialized")

    def _setup_ui(self):
        """Set up the coordinate input UI."""
        coords_frame = ttk.Frame(self.frame)
        coords_frame.pack(fill=tk.X, pady=5)

        # X1
        ttk.Label(coords_frame, text="X1:").grid(row=0, column=0, padx=(0, 5))
        ttk.Entry(coords_frame, textvariable=self.x1_var, width=8).grid(
            row=0, column=1, padx=(0, 10)
        )

        # Y1
        ttk.Label(coords_frame, text="Y1:").grid(row=0, column=2, padx=(0, 5))
        ttk.Entry(coords_frame, textvariable=self.y1_var, width=8).grid(
            row=0, column=3, padx=(0, 10)
        )

        # X2
        ttk.Label(coords_frame, text="X2:").grid(row=0, column=4, padx=(0, 5))
        ttk.Entry(coords_frame, textvariable=self.x2_var, width=8).grid(
            row=0, column=5, padx=(0, 10)
        )

        # Y2
        ttk.Label(coords_frame, text="Y2:").grid(row=0, column=6, padx=(0, 5))
        ttk.Entry(coords_frame, textvariable=self.y2_var, width=8).grid(
            row=0, column=7, padx=(0, 10)
        )

    def _bind_callbacks(self):
        """Bind variable change callbacks."""
        if self.callback:
            for var in [self.x1_var, self.y1_var, self.x2_var, self.y2_var]:
                var.trace_add(
                    "write", lambda *args: self.callback(self.get_coordinates())
                )

    def pack(self, **kwargs):
        """Pack the coordinate input."""
        self.frame.pack(**kwargs)

    def grid(self, **kwargs):
        """Grid the coordinate input."""
        self.frame.grid(**kwargs)

    def get_coordinates(self) -> Tuple[int, int, int, int]:
        """Get current coordinates."""
        return (
            self.x1_var.get(),
            self.y1_var.get(),
            self.x2_var.get(),
            self.y2_var.get(),
        )

    def set_coordinates(self, x1: int, y1: int, x2: int, y2: int):
        """Set coordinates."""
        self.x1_var.set(x1)
        self.y1_var.set(y1)
        self.x2_var.set(x2)
        self.y2_var.set(y2)

    def clear(self):
        """Clear all coordinates."""
        self.set_coordinates(0, 0, 0, 0)


class TemplatePreviewWindow:
    """
    Template preview window with interactive adjustment controls.

    Shows template preview with krathong image and mask overlay.
    Provides controls for scale, offset, and mask adjustments.
    """

    def __init__(
        self, parent, template_data: Dict[str, Any], on_save: Optional[Callable] = None
    ):
        """Initialize template preview window."""
        self.logger = logging.getLogger(__name__)
        self.parent = parent
        self.template_data = template_data
        self.on_save = on_save

        # State variables
        self.scale_var = tk.DoubleVar(value=template_data.get("scale", 0.8))
        self.offset_x_var = tk.IntVar(value=template_data.get("offset_x", 0))
        self.offset_y_var = tk.IntVar(value=template_data.get("offset_y", 0))
        self.show_mask_var = tk.BooleanVar(value=True)

        # Create window
        self.window = tk.Toplevel(parent)
        self.window.title("Template Preview")
        self.window.geometry("1400x900")
        self.window.resizable(True, True)

        # Bind keyboard shortcuts
        self._bind_keyboard_shortcuts()

        self._setup_ui()
        self._update_preview()

        self.logger.info("Template preview window created")

    def _bind_keyboard_shortcuts(self):
        """Bind keyboard shortcuts for adjustment."""
        self.window.bind("<Left>", lambda e: self._adjust_offset_x(-1))
        self.window.bind("<Right>", lambda e: self._adjust_offset_x(1))
        self.window.bind("<Up>", lambda e: self._adjust_offset_y(-1))
        self.window.bind("<Down>", lambda e: self._adjust_offset_y(1))
        self.window.bind("<Shift-Left>", lambda e: self._adjust_offset_x(-10))
        self.window.bind("<Shift-Right>", lambda e: self._adjust_offset_x(10))
        self.window.bind("<Shift-Up>", lambda e: self._adjust_offset_y(-10))
        self.window.bind("<Shift-Down>", lambda e: self._adjust_offset_y(10))
        self.window.focus_set()

    def _setup_ui(self):
        """Set up the preview window UI."""
        # Main frame
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Preview canvas
        self.canvas = PreviewCanvas(main_frame, width=800, height=600)
        self.canvas.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Controls
        self.controls = ControlPanel(main_frame, "Adjust Template")
        self.controls.pack(fill=tk.X, pady=(0, 10))

        # Scale control
        self.controls.add_slider(
            "scale",
            "Scale:",
            0.1,
            1.5,
            initial=self.scale_var.get(),
            callback=self._on_scale_change,
        )

        # Offset controls
        self.controls.add_slider(
            "offset_x",
            "X Offset:",
            -200,
            200,
            initial=self.offset_x_var.get(),
            callback=self._on_offset_x_change,
        )

        self.controls.add_slider(
            "offset_y",
            "Y Offset:",
            -200,
            200,
            initial=self.offset_y_var.get(),
            callback=self._on_offset_y_change,
        )

        # Mask visibility
        self.controls.add_checkbox(
            "show_mask",
            "Show Mask Overlay",
            initial=self.show_mask_var.get(),
            callback=self._on_mask_toggle,
        )

        # Buttons
        self.controls.add_button_row(
            [
                {"text": "Reset", "command": self._reset_values},
                {"text": "Save Template", "command": self._save_template},
                {"text": "Cancel", "command": self.window.destroy, "side": tk.RIGHT},
            ]
        )

    def _adjust_offset_x(self, delta: int):
        """Adjust X offset by delta."""
        new_value = self.offset_x_var.get() + delta
        self.offset_x_var.set(new_value)
        self.controls.set_value("offset_x", new_value)
        self._update_preview()

    def _adjust_offset_y(self, delta: int):
        """Adjust Y offset by delta."""
        new_value = self.offset_y_var.get() + delta
        self.offset_y_var.set(new_value)
        self.controls.set_value("offset_y", new_value)
        self._update_preview()

    def _on_scale_change(self, value: float):
        """Handle scale change."""
        self.scale_var.set(value)
        self._update_preview()

    def _on_offset_x_change(self, value: float):
        """Handle X offset change."""
        self.offset_x_var.set(int(value))
        self._update_preview()

    def _on_offset_y_change(self, value: float):
        """Handle Y offset change."""
        self.offset_y_var.set(int(value))
        self._update_preview()

    def _on_mask_toggle(self, value: bool):
        """Handle mask visibility toggle."""
        self.show_mask_var.set(value)
        self._update_preview()

    def _update_preview(self):
        """Update the template preview."""
        try:
            # This would be implemented to generate and display the template
            # For now, just log the current settings
            self.logger.debug(
                f"Preview updated - Scale: {self.scale_var.get():.2f}, "
                f"Offset: ({self.offset_x_var.get()}, {self.offset_y_var.get()}), "
                f"Show mask: {self.show_mask_var.get()}"
            )
        except Exception as e:
            self.logger.error(f"Preview update failed: {e}")

    def _reset_values(self):
        """Reset all values to defaults."""
        self.scale_var.set(0.8)
        self.offset_x_var.set(0)
        self.offset_y_var.set(0)
        self.show_mask_var.set(True)

        # Update controls
        self.controls.set_value("scale", 0.8)
        self.controls.set_value("offset_x", 0)
        self.controls.set_value("offset_y", 0)
        self.controls.set_value("show_mask", True)

        self._update_preview()

    def _save_template(self):
        """Save template with current settings."""
        if self.on_save:
            settings = {
                "scale": self.scale_var.get(),
                "offset_x": self.offset_x_var.get(),
                "offset_y": self.offset_y_var.get(),
                "show_mask": self.show_mask_var.get(),
            }
            self.on_save(settings)
        self.window.destroy()


class FileSelector:
    """
    File selection component with preview and validation.

    Provides file dialog integration with format validation and preview.
    """

    def __init__(
        self,
        parent,
        title: str = "Select File",
        file_types: List[Tuple[str, str]] = None,
        callback: Optional[Callable] = None,
    ):
        """Initialize file selector."""
        self.logger = logging.getLogger(__name__)

        if file_types is None:
            file_types = [
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff"),
                ("All files", "*.*"),
            ]

        self.title = title
        self.file_types = file_types
        self.callback = callback

        # Create frame
        self.frame = ttk.Frame(parent)

        # Variables
        self.file_path_var = tk.StringVar()

        self._setup_ui()

        self.logger.debug("FileSelector initialized")

    def _setup_ui(self):
        """Set up file selector UI."""
        # File path display
        path_frame = ttk.Frame(self.frame)
        path_frame.pack(fill=tk.X, pady=2)

        ttk.Label(path_frame, text="File:").pack(side=tk.LEFT)

        self.path_entry = ttk.Entry(
            path_frame, textvariable=self.file_path_var, state="readonly"
        )
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))

        ttk.Button(path_frame, text="Browse...", command=self._browse_file).pack(
            side=tk.LEFT
        )
        ttk.Button(path_frame, text="Clear", command=self._clear_file).pack(
            side=tk.LEFT, padx=(5, 0)
        )

    def _browse_file(self):
        """Open file dialog."""
        file_path = filedialog.askopenfilename(
            title=self.title, filetypes=self.file_types
        )

        if file_path:
            self.file_path_var.set(file_path)
            if self.callback:
                self.callback(file_path)

    def _clear_file(self):
        """Clear selected file."""
        self.file_path_var.set("")
        if self.callback:
            self.callback("")

    def pack(self, **kwargs):
        """Pack the file selector."""
        self.frame.pack(**kwargs)

    def grid(self, **kwargs):
        """Grid the file selector."""
        self.frame.grid(**kwargs)

    def get_file_path(self) -> str:
        """Get selected file path."""
        return self.file_path_var.get()

    def set_file_path(self, path: str):
        """Set file path."""
        self.file_path_var.set(path)
        if self.callback:
            self.callback(path)


def show_info_dialog(parent, title: str, message: str):
    """Show information dialog."""
    messagebox.showinfo(title, message, parent=parent)


def show_error_dialog(parent, title: str, message: str):
    """Show error dialog."""
    messagebox.showerror(title, message, parent=parent)


def show_warning_dialog(parent, title: str, message: str):
    """Show warning dialog."""
    messagebox.showwarning(title, message, parent=parent)


def ask_yes_no(parent, title: str, message: str) -> bool:
    """Ask yes/no question."""
    return messagebox.askyesno(title, message, parent=parent)


def center_window(window, width: int = None, height: int = None):
    """Center window on screen."""
    window.update_idletasks()

    if width is None or height is None:
        window_width = window.winfo_width()
        window_height = window.winfo_height()
    else:
        window_width = width
        window_height = height

    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2

    window.geometry(f"{window_width}x{window_height}+{x}+{y}")


if __name__ == "__main__":
    # Test the UI components
    root = tk.Tk()
    root.title("UI Components Test")
    root.geometry("800x600")

    # Test PreviewCanvas
    canvas = PreviewCanvas(root, width=400, height=300)
    canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Test ControlPanel
    controls = ControlPanel(root, "Test Controls")
    controls.pack(fill=tk.X, padx=10, pady=5)

    controls.add_slider("scale", "Scale:", 0.1, 2.0, initial=1.0)
    controls.add_entry("name", "Name:", initial="test")
    controls.add_checkbox("enabled", "Enabled", initial=True)

    controls.add_button_row(
        [
            {"text": "Test", "command": lambda: print("Test clicked")},
            {"text": "Reset", "command": lambda: print("Reset clicked")},
            {"text": "Exit", "command": root.quit, "side": tk.RIGHT},
        ]
    )

    # Test FileSelector
    file_selector = FileSelector(root, "Select Image")
    file_selector.pack(fill=tk.X, padx=10, pady=5)

    center_window(root, 800, 600)

    print("UI Components test window created")
    root.mainloop()
