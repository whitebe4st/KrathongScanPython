import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import numpy as np

# Check for required libraries
missing_libs = []
try:
    from PIL import Image, ImageEnhance, ImageTk

    print("✓ PIL/Pillow imported successfully")
except ImportError:
    missing_libs.append("Pillow")

try:
    import cv2

    print("✓ OpenCV imported successfully")
except ImportError:
    missing_libs.append("opencv-python")

if missing_libs:
    print("❌ Missing required libraries:")
    for lib in missing_libs:
        print(f"   - {lib}")
    print("\nInstall with:")
    print(f"pip install {' '.join(missing_libs)}")
    sys.exit(1)


class DocumentScanner:
    def __init__(self, root):
        print("Initializing Document Scanner...")

        self.root = root
        self.root.title("Document Scanner - Rectangle Zoom")
        self.root.geometry("1200x800")

        # Variables
        self.original_image = None
        self.processed_image = None
        self.original_cv = None
        self.processed_cv = None

        # UI variables
        self.original_photo = None
        self.processed_photo = None

        print("Setting up UI...")
        self.setup_ui()
        print("✓ Document Scanner initialized successfully")

    def setup_ui(self):
        # Create menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Image", command=self.open_image)
        file_menu.add_command(
            label="Save Scanned Document", command=self.save_processed_image
        )
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Create toolbar
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        ttk.Button(toolbar, text="Open Image", command=self.open_image).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(toolbar, text="Zoom Into Box", command=self.auto_scan_document).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(toolbar, text="Enhance", command=self.enhance_document).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(toolbar, text="Save Result", command=self.save_processed_image).pack(
            side=tk.LEFT, padx=5
        )

        # Create main frame with two panels
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left panel - Original image
        left_frame = ttk.LabelFrame(main_frame, text="Original Image", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        self.original_canvas = tk.Canvas(left_frame, bg="gray90")
        self.original_canvas.pack(fill=tk.BOTH, expand=True)

        # Right panel - Processed image
        right_frame = ttk.LabelFrame(main_frame, text="Zoomed Rectangle", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        self.processed_canvas = tk.Canvas(right_frame, bg="gray90")
        self.processed_canvas.pack(fill=tk.BOTH, expand=True)

        # Processing options frame
        options_frame = ttk.LabelFrame(self.root, text="Processing Options", padding=10)
        options_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

        # Enhancement options
        ttk.Label(options_frame, text="Enhancement:").grid(
            row=0, column=0, padx=5, sticky="w"
        )

        self.enhancement_var = tk.StringVar(value="auto")
        enhancement_frame = ttk.Frame(options_frame)
        enhancement_frame.grid(row=0, column=1, padx=5, sticky="w")

        ttk.Radiobutton(
            enhancement_frame, text="Auto", variable=self.enhancement_var, value="auto"
        ).pack(side=tk.LEFT)
        ttk.Radiobutton(
            enhancement_frame,
            text="High Contrast",
            variable=self.enhancement_var,
            value="contrast",
        ).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(
            enhancement_frame,
            text="Grayscale",
            variable=self.enhancement_var,
            value="grayscale",
        ).pack(side=tk.LEFT, padx=5)

        # Debug button to show edge detection
        ttk.Button(
            options_frame, text="Show Edges", command=self.show_edge_detection
        ).grid(row=0, column=2, padx=20)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready - Open an image to start scanning")
        status_bar = ttk.Label(
            self.root, textvariable=self.status_var, relief=tk.SUNKEN
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def open_image(self):
        file_path = filedialog.askopenfilename(
            title="Select Document Image",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff"),
                ("JPEG files", "*.jpg *.jpeg"),
                ("PNG files", "*.png"),
                ("All files", "*.*"),
            ],
        )

        if file_path:
            try:
                # Load with PIL for display
                self.original_image = Image.open(file_path)

                # Load with OpenCV for processing
                self.original_cv = cv2.imread(file_path)

                self.display_original_image()
                self.status_var.set(
                    f"Loaded: {os.path.basename(file_path)} ({self.original_image.size[0]}x{self.original_image.size[1]})"
                )

                # Clear processed image
                self.processed_canvas.delete("all")
                self.processed_image = None
                self.processed_cv = None

            except Exception as e:
                messagebox.showerror("Error", f"Could not open image: {str(e)}")

    def display_original_image(self):
        if not self.original_image:
            return

        # Get canvas dimensions
        self.original_canvas.update()
        canvas_width = self.original_canvas.winfo_width()
        canvas_height = self.original_canvas.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1:
            self.root.after(100, self.display_original_image)
            return

        # Calculate scale to fit image in canvas
        img_width, img_height = self.original_image.size
        scale_x = canvas_width / img_width
        scale_y = canvas_height / img_height
        scale = min(scale_x, scale_y, 1.0)

        # Resize image for display
        display_width = int(img_width * scale)
        display_height = int(img_height * scale)

        display_image = self.original_image.resize(
            (display_width, display_height), Image.Resampling.LANCZOS
        )
        self.original_photo = ImageTk.PhotoImage(display_image)

        # Clear canvas and add image
        self.original_canvas.delete("all")
        self.original_canvas.create_image(
            canvas_width // 2,
            canvas_height // 2,
            anchor=tk.CENTER,
            image=self.original_photo,
        )

    def display_processed_image(self):
        if not self.processed_image:
            return

        # Get canvas dimensions
        self.processed_canvas.update()
        canvas_width = self.processed_canvas.winfo_width()
        canvas_height = self.processed_canvas.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1:
            self.root.after(100, self.display_processed_image)
            return

        # Calculate scale to fit image in canvas
        img_width, img_height = self.processed_image.size
        scale_x = canvas_width / img_width
        scale_y = canvas_height / img_height
        scale = min(scale_x, scale_y, 1.0)

        # Resize image for display
        display_width = int(img_width * scale)
        display_height = int(img_height * scale)

        display_image = self.processed_image.resize(
            (display_width, display_height), Image.Resampling.LANCZOS
        )
        self.processed_photo = ImageTk.PhotoImage(display_image)

        # Clear canvas and add image
        self.processed_canvas.delete("all")
        self.processed_canvas.create_image(
            canvas_width // 2,
            canvas_height // 2,
            anchor=tk.CENTER,
            image=self.processed_photo,
        )

    def find_rectangle_contour(self, image):
        """Find any rectangular contour in the image"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)

            # Try multiple edge detection approaches
            threshold_pairs = [(50, 150), (75, 200), (30, 100), (100, 250)]

            for low, high in threshold_pairs:
                edged = cv2.Canny(blurred, low, high)

                # Find contours
                contours, _ = cv2.findContours(
                    edged, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
                )
                contours = sorted(contours, key=cv2.contourArea, reverse=True)

                # Look for rectangular contours
                for contour in contours:
                    epsilon = 0.02 * cv2.arcLength(contour, True)
                    approx = cv2.approxPolyDP(contour, epsilon, True)

                    # Check if it's a rectangle with reasonable area
                    if len(approx) == 4:
                        area = cv2.contourArea(approx)
                        if area > 5000:  # Minimum area threshold
                            print(f"Found rectangle with area: {area}")
                            return approx

            # If no rectangles found with edge detection, try adaptive threshold
            adaptive = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )

            contours, _ = cv2.findContours(
                adaptive, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
            )
            contours = sorted(contours, key=cv2.contourArea, reverse=True)

            for contour in contours:
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)

                if len(approx) == 4:
                    area = cv2.contourArea(approx)
                    if area > 5000:
                        print(f"Found rectangle (adaptive) with area: {area}")
                        return approx

            print("❌ No rectangular contours found")
            return None

        except Exception as e:
            print(f"Error finding rectangle: {e}")
            return None

    def order_points(self, pts):
        """Order points in the order: top-left, top-right, bottom-right, bottom-left"""
        rect = np.zeros((4, 2), dtype="float32")

        # Sum and difference to find corners
        s = pts.sum(axis=1)
        diff = np.diff(pts, axis=1)

        rect[0] = pts[np.argmin(s)]  # top-left
        rect[2] = pts[np.argmax(s)]  # bottom-right
        rect[1] = pts[np.argmin(diff)]  # top-right
        rect[3] = pts[np.argmax(diff)]  # bottom-left

        return rect

    def four_point_transform(self, image, pts):
        """Apply perspective transformation to zoom into the rectangle"""
        # Order the points
        rect = self.order_points(pts)
        (tl, tr, br, bl) = rect

        # Calculate the width and height of the new image
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))

        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB))

        # Define the destination points
        dst = np.array(
            [
                [0, 0],
                [maxWidth - 1, 0],
                [maxWidth - 1, maxHeight - 1],
                [0, maxHeight - 1],
            ],
            dtype="float32",
        )

        # Calculate the perspective transform matrix and apply it
        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))

        return warped

    def auto_scan_document(self):
        """Find and zoom into any rectangular region in the image"""
        if self.original_cv is None:
            messagebox.showwarning("No Image", "Please open an image first.")
            return

        try:
            self.status_var.set("Looking for rectangular regions...")
            self.root.update()

            # Find rectangular contour
            contour = self.find_rectangle_contour(self.original_cv)

            if contour is not None:
                # Show the detected rectangle briefly
                self.show_detected_rectangle(contour)

                # Apply perspective transformation to zoom into the rectangle
                self.status_var.set("Zooming into detected rectangle...")
                self.root.update()

                # Reshape contour for processing
                pts = contour.reshape(4, 2)
                print(f"Rectangle corners: {pts}")

                # Apply perspective transform
                warped = self.four_point_transform(self.original_cv, pts)

                # Convert back to PIL Image
                self.processed_cv = warped
                processed_rgb = cv2.cvtColor(warped, cv2.COLOR_BGR2RGB)
                self.processed_image = Image.fromarray(processed_rgb)

                # Apply enhancement
                self.enhance_document()

                # Calculate zoom info
                original_area = self.original_cv.shape[0] * self.original_cv.shape[1]
                rect_area = cv2.contourArea(contour)
                zoom_factor = original_area / rect_area if rect_area > 0 else 1

                self.status_var.set(
                    f"Rectangle zoomed! Zoom factor: {zoom_factor:.1f}x"
                )

            else:
                messagebox.showinfo(
                    "No Rectangle Found",
                    "Could not detect any rectangular region to zoom into.\n"
                    + "Try an image with clear rectangular shapes or text boxes.",
                )
                self.status_var.set("No rectangle detected")

        except Exception as e:
            messagebox.showerror("Error", f"Could not scan document: {str(e)}")
            self.status_var.set("Error during rectangle detection")

    def show_detected_rectangle(self, contour):
        """Briefly show the detected rectangle on the original image"""
        try:
            # Create a copy with the rectangle highlighted
            vis_image = self.original_cv.copy()

            # Draw the rectangle in thick red
            cv2.drawContours(vis_image, [contour], -1, (0, 0, 255), 5)

            # Draw corner points
            pts = contour.reshape(4, 2)
            for i, point in enumerate(pts):
                cv2.circle(vis_image, tuple(point.astype(int)), 10, (0, 255, 0), -1)
                cv2.putText(
                    vis_image,
                    str(i + 1),
                    (point[0] - 5, point[1] + 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (255, 255, 255),
                    2,
                )

            # Convert and show
            vis_rgb = cv2.cvtColor(vis_image, cv2.COLOR_BGR2RGB)
            temp_image = Image.fromarray(vis_rgb)

            # Temporarily show
            original_processed = self.processed_image
            self.processed_image = temp_image
            self.display_processed_image()
            self.root.update()

            import time

            time.sleep(1)  # Show for 1 second

            # Restore
            self.processed_image = original_processed

        except Exception as e:
            print(f"Error showing rectangle: {e}")

    def enhance_document(self):
        if not self.processed_image:
            return

        try:
            enhancement_type = self.enhancement_var.get()

            if enhancement_type == "auto":
                # Auto enhancement
                enhancer = ImageEnhance.Contrast(self.processed_image)
                enhanced = enhancer.enhance(1.2)

                enhancer = ImageEnhance.Sharpness(enhanced)
                enhanced = enhancer.enhance(1.1)

                enhancer = ImageEnhance.Brightness(enhanced)
                self.processed_image = enhancer.enhance(1.05)

            elif enhancement_type == "contrast":
                # High contrast
                gray = self.processed_image.convert("L")
                enhancer = ImageEnhance.Contrast(gray)
                self.processed_image = enhancer.enhance(2.0)

            elif enhancement_type == "grayscale":
                # Grayscale
                self.processed_image = self.processed_image.convert("L")

            self.display_processed_image()
            self.status_var.set(f"Enhancement applied: {enhancement_type}")

        except Exception as e:
            messagebox.showerror("Error", f"Could not enhance document: {str(e)}")

    def save_processed_image(self):
        if not self.processed_image:
            messagebox.showwarning(
                "No Processed Image", "Please scan a document first."
            )
            return

        file_path = filedialog.asksaveasfilename(
            title="Save Zoomed Rectangle",
            defaultextension=".png",
            filetypes=[
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg"),
                ("PDF files", "*.pdf"),
                ("All files", "*.*"),
            ],
        )

        if file_path:
            try:
                if file_path.lower().endswith(".pdf"):
                    self.processed_image.save(file_path, "PDF", resolution=100.0)
                else:
                    self.processed_image.save(file_path)

                self.status_var.set(f"Saved: {os.path.basename(file_path)}")
                messagebox.showinfo(
                    "Success", f"Rectangle saved as {os.path.basename(file_path)}"
                )
            except Exception as e:
                messagebox.showerror("Error", f"Could not save: {str(e)}")

    def show_edge_detection(self):
        """Show edge detection for debugging"""
        if self.original_cv is None:
            messagebox.showwarning("No Image", "Please open an image first.")
            return

        try:
            gray = cv2.cvtColor(self.original_cv, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Canny(blurred, 75, 200)

            # Convert to RGB and display
            edges_rgb = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
            self.processed_cv = cv2.cvtColor(edges_rgb, cv2.COLOR_RGB2BGR)
            self.processed_image = Image.fromarray(edges_rgb)

            self.display_processed_image()
            self.status_var.set("Showing edge detection")

        except Exception as e:
            messagebox.showerror("Error", f"Could not show edges: {str(e)}")


def main():
    print("Starting Rectangle Zoom Scanner...")

    try:
        root = tk.Tk()
        print("✓ Tkinter window created")

        app = DocumentScanner(root)
        print("✓ Rectangle zoom scanner initialized")

        # Bind window resize events
        def on_canvas_configure(event=None):
            if app.original_image:
                app.display_original_image()
            if app.processed_image:
                app.display_processed_image()

        app.original_canvas.bind("<Configure>", on_canvas_configure)
        app.processed_canvas.bind("<Configure>", on_canvas_configure)

        print("✓ Starting GUI...")
        root.mainloop()

    except Exception as e:
        print(f"❌ Error starting application: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print("Rectangle Zoom Scanner - Starting up...")
    main()
    print("Rectangle Zoom Scanner - Shutting down...")
