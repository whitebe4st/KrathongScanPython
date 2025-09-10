import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk


class ImageCropEditor:
    def __init__(self, root):
        print("Initializing ImageCropEditor...")

        self.root = root
        self.root.title("Simple Image Crop Editor")
        self.root.geometry("800x600")

        # Variables
        self.original_image = None
        self.display_image = None
        self.photo_image = None
        self.canvas_image_id = None
        self.scale_factor = 1.0

        # Crop selection variables
        self.start_x = 0
        self.start_y = 0
        self.end_x = 0
        self.end_y = 0
        self.rect_id = None
        self.is_selecting = False

        print("Setting up UI...")
        self.setup_ui()
        print("✓ ImageCropEditor initialized successfully")

    def setup_ui(self):
        # Create menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Image", command=self.open_image)
        file_menu.add_command(
            label="Save Cropped Image", command=self.save_cropped_image
        )
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Create toolbar
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        ttk.Button(toolbar, text="Open Image", command=self.open_image).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(toolbar, text="Crop Selection", command=self.crop_image).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(toolbar, text="Clear Selection", command=self.clear_selection).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(toolbar, text="Save Cropped", command=self.save_cropped_image).pack(
            side=tk.LEFT, padx=5
        )

        # Create main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create canvas with scrollbars
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg="gray90", cursor="crosshair")

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(
            canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview
        )
        h_scrollbar = ttk.Scrollbar(
            canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview
        )

        self.canvas.configure(
            yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set
        )

        # Grid layout for canvas and scrollbars
        self.canvas.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)

        # Bind mouse events for crop selection
        self.canvas.bind("<Button-1>", self.start_selection)
        self.canvas.bind("<B1-Motion>", self.update_selection)
        self.canvas.bind("<ButtonRelease-1>", self.end_selection)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready - Open an image to start cropping")
        status_bar = ttk.Label(
            self.root, textvariable=self.status_var, relief=tk.SUNKEN
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Variables for cropped image
        self.cropped_image = None

    def open_image(self):
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff"),
                ("JPEG files", "*.jpg *.jpeg"),
                ("PNG files", "*.png"),
                ("All files", "*.*"),
            ],
        )

        if file_path:
            try:
                self.original_image = Image.open(file_path)
                self.display_image_on_canvas()
                self.status_var.set(
                    f"Loaded: {os.path.basename(file_path)} ({self.original_image.size[0]}x{self.original_image.size[1]})"
                )
                self.clear_selection()
            except Exception as e:
                messagebox.showerror("Error", f"Could not open image: {str(e)}")

    def display_image_on_canvas(self):
        if not self.original_image:
            return

        # Calculate scale to fit image in canvas while maintaining aspect ratio
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1:  # Canvas not yet initialized
            self.root.after(100, self.display_image_on_canvas)
            return

        img_width, img_height = self.original_image.size

        # Calculate scale factor to fit image in canvas
        scale_x = canvas_width / img_width
        scale_y = canvas_height / img_height
        self.scale_factor = min(scale_x, scale_y, 1.0)  # Don't scale up

        # Resize image for display
        display_width = int(img_width * self.scale_factor)
        display_height = int(img_height * self.scale_factor)

        self.display_image = self.original_image.resize(
            (display_width, display_height), Image.Resampling.LANCZOS
        )
        self.photo_image = ImageTk.PhotoImage(self.display_image)

        # Clear canvas and add image
        self.canvas.delete("all")
        self.canvas_image_id = self.canvas.create_image(
            0, 0, anchor=tk.NW, image=self.photo_image
        )

        # Update canvas scroll region
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def start_selection(self, event):
        if not self.original_image:
            return

        self.is_selecting = True
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        self.end_x = self.start_x
        self.end_y = self.start_y

        # Clear previous selection
        if self.rect_id:
            self.canvas.delete(self.rect_id)

    def update_selection(self, event):
        if not self.is_selecting or not self.original_image:
            return

        self.end_x = self.canvas.canvasx(event.x)
        self.end_y = self.canvas.canvasy(event.y)

        # Update selection rectangle
        if self.rect_id:
            self.canvas.delete(self.rect_id)

        self.rect_id = self.canvas.create_rectangle(
            self.start_x,
            self.start_y,
            self.end_x,
            self.end_y,
            outline="red",
            width=2,
            dash=(5, 5),
        )

        # Update status with selection size
        width = abs(self.end_x - self.start_x) / self.scale_factor
        height = abs(self.end_y - self.start_y) / self.scale_factor
        self.status_var.set(f"Selection: {int(width)}x{int(height)} pixels")

    def end_selection(self, event):
        self.is_selecting = False

        if not self.original_image:
            return

        # Ensure we have a valid selection
        if abs(self.end_x - self.start_x) < 5 or abs(self.end_y - self.start_y) < 5:
            self.clear_selection()
            return

        # Final update of selection
        self.end_x = self.canvas.canvasx(event.x)
        self.end_y = self.canvas.canvasy(event.y)

        if self.rect_id:
            self.canvas.delete(self.rect_id)

        self.rect_id = self.canvas.create_rectangle(
            self.start_x,
            self.start_y,
            self.end_x,
            self.end_y,
            outline="red",
            width=2,
            dash=(5, 5),
        )

        width = abs(self.end_x - self.start_x) / self.scale_factor
        height = abs(self.end_y - self.start_y) / self.scale_factor
        self.status_var.set(
            f"Selection ready: {int(width)}x{int(height)} pixels - Click 'Crop Selection' to crop"
        )

    def clear_selection(self):
        if self.rect_id:
            self.canvas.delete(self.rect_id)
            self.rect_id = None
        self.cropped_image = None
        if self.original_image:
            self.status_var.set(
                "Selection cleared - Draw a rectangle to select crop area"
            )
        else:
            self.status_var.set("Ready - Open an image to start cropping")

    def crop_image(self):
        if not self.original_image or not self.rect_id:
            messagebox.showwarning(
                "No Selection",
                "Please make a selection first by dragging on the image.",
            )
            return

        try:
            # Convert canvas coordinates to image coordinates
            left = min(self.start_x, self.end_x) / self.scale_factor
            top = min(self.start_y, self.end_y) / self.scale_factor
            right = max(self.start_x, self.end_x) / self.scale_factor
            bottom = max(self.start_y, self.end_y) / self.scale_factor

            # Ensure coordinates are within image bounds
            left = max(0, min(left, self.original_image.size[0]))
            top = max(0, min(top, self.original_image.size[1]))
            right = max(0, min(right, self.original_image.size[0]))
            bottom = max(0, min(bottom, self.original_image.size[1]))

            # Crop the original image
            crop_box = (int(left), int(top), int(right), int(bottom))
            self.cropped_image = self.original_image.crop(crop_box)

            # Update display with cropped image
            self.original_image = self.cropped_image.copy()
            self.display_image_on_canvas()

            crop_width = int(right - left)
            crop_height = int(bottom - top)
            self.status_var.set(f"Image cropped to {crop_width}x{crop_height} pixels")

            messagebox.showinfo(
                "Success",
                f"Image cropped successfully!\nNew size: {crop_width}x{crop_height} pixels",
            )

        except Exception as e:
            messagebox.showerror("Error", f"Could not crop image: {str(e)}")

    def save_cropped_image(self):
        if not self.original_image:
            messagebox.showwarning("No Image", "Please open and crop an image first.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Save Cropped Image",
            defaultextension=".png",
            filetypes=[
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg"),
                ("All files", "*.*"),
            ],
        )

        if file_path:
            try:
                # Save the current image (which is the cropped version)
                self.original_image.save(file_path)
                self.status_var.set(f"Image saved: {os.path.basename(file_path)}")
                messagebox.showinfo(
                    "Success",
                    f"Image saved successfully as {os.path.basename(file_path)}",
                )
            except Exception as e:
                messagebox.showerror("Error", f"Could not save image: {str(e)}")


def main():
    root = tk.Tk()
    app = ImageCropEditor(root)

    # Bind window resize event to redraw image
    def on_canvas_configure(event):
        if app.original_image:
            app.display_image_on_canvas()

    app.canvas.bind("<Configure>", on_canvas_configure)

    root.mainloop()


if __name__ == "__main__":
    main()
