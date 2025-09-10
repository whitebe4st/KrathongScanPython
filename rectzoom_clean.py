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
        self.root.title("Document Scanner")
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
        ttk.Button(toolbar, text="Auto Scan", command=self.auto_scan_document).pack(
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
        right_frame = ttk.LabelFrame(main_frame, text="Scanned Document", padding=10)
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

        # Manual crop button for when auto-detection fails
        ttk.Button(
            options_frame, text="Manual Crop", command=self.manual_crop_mode
        ).grid(row=0, column=2, padx=20)

        # Debug button to show edge detection
        ttk.Button(
            options_frame, text="Show Edges", command=self.show_edge_detection
        ).grid(row=0, column=3, padx=5)

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

    def find_document_contour(self, image):
        """Simplified automatic document detection - no manual mode"""

        # Try the most reliable automatic method
        contour = self.find_paper_boundary_simple(image)
        if contour is not None:
            print("✓ Document found using simplified boundary detection")
            return contour

        # Fallback: use the largest rectangular region
        contour = self.find_largest_rectangle(image)
        if contour is not None:
            print("✓ Document found using largest rectangle fallback")
            return contour

        # Final fallback: create a reasonable document boundary (80% of image)
        height, width = image.shape[:2]
        margin_x = int(width * 0.1)
        margin_y = int(height * 0.1)

        fallback_contour = np.array(
            [
                [margin_x, margin_y],
                [width - margin_x, margin_y],
                [width - margin_x, height - margin_y],
                [margin_x, height - margin_y],
            ]
        ).reshape(-1, 1, 2)

        print("✓ Using fallback document boundary (80% of image)")
        return fallback_contour

    def find_paper_boundary_simple(self, image):
        """Simplified paper boundary detection focusing on reliability"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            height, width = image.shape[:2]
            image_area = height * width

            # Method 1: Heavy blur + Otsu thresholding (most reliable for paper detection)
            heavily_blurred = cv2.GaussianBlur(gray, (51, 51), 0)  # Very heavy blur

            # Use Otsu thresholding to separate paper from background
            _, binary = cv2.threshold(
                heavily_blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )

            # Find the largest contour (should be the paper)
            contours, _ = cv2.findContours(
                binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                area = cv2.contourArea(largest_contour)

                # Paper should be at least 20% of the image
                if area > image_area * 0.2:
                    # Use convex hull and then minimum area rectangle for clean boundaries
                    hull = cv2.convexHull(largest_contour)
                    rect = cv2.minAreaRect(hull)
                    box = cv2.boxPoints(rect)
                    contour = np.array(box, dtype=np.int32).reshape(-1, 1, 2)

                    # Make sure it's not the entire image
                    if not self.is_full_image(contour, width, height):
                        return contour

            # Method 2: Edge detection with very low thresholds
            blurred = cv2.GaussianBlur(gray, (9, 9), 0)
            edges = cv2.Canny(blurred, 10, 50, apertureSize=3)

            # Dilate edges to connect paper boundaries
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
            dilated = cv2.dilate(edges, kernel, iterations=3)

            # Find contours
            contours, _ = cv2.findContours(
                dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            # Look for rectangular contours
            for contour in sorted(contours, key=cv2.contourArea, reverse=True)[:5]:
                area = cv2.contourArea(contour)

                if area > image_area * 0.15:  # At least 15% of image
                    # Try to approximate as rectangle
                    perimeter = cv2.arcLength(contour, True)
                    epsilon = 0.02 * perimeter
                    approx = cv2.approxPolyDP(contour, epsilon, True)

                    if len(approx) >= 4:
                        if len(approx) > 4:
                            # Convert to minimum area rectangle
                            rect = cv2.minAreaRect(contour)
                            box = cv2.boxPoints(rect)
                            approx = np.array(box, dtype=np.int32).reshape(-1, 1, 2)

                        if not self.is_full_image(approx, width, height):
                            return approx

            return None

        except Exception as e:
            print(f"Error in simplified paper boundary detection: {e}")
            return None

    def find_largest_rectangle(self, image):
        """Find the largest reasonable rectangle in the image"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            height, width = image.shape[:2]
            image_area = height * width

            # Apply adaptive threshold
            adaptive = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )

            # Find contours
            contours, _ = cv2.findContours(
                adaptive, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
            )

            best_contour = None
            best_area = 0

            for contour in contours:
                area = cv2.contourArea(contour)

                # Must be substantial but not the whole image
                if image_area * 0.1 < area < image_area * 0.95:
                    perimeter = cv2.arcLength(contour, True)
                    epsilon = 0.02 * perimeter
                    approx = cv2.approxPolyDP(contour, epsilon, True)

                    if len(approx) == 4:
                        if not self.is_full_image(approx, width, height):
                            if area > best_area:
                                best_area = area
                                best_contour = approx

                    elif len(approx) > 4:
                        # Convert to rectangle
                        rect = cv2.minAreaRect(contour)
                        box = cv2.boxPoints(rect)
                        rect_approx = np.array(box, dtype=np.int32).reshape(-1, 1, 2)

                        if not self.is_full_image(rect_approx, width, height):
                            if area > best_area:
                                best_area = area
                                best_contour = rect_approx

            return best_contour

        except Exception as e:
            print(f"Error in largest rectangle detection: {e}")
            return None

    def is_full_image(self, contour, width, height):
        """Check if contour covers almost the entire image"""
        pts = contour.reshape(4, 2)

        # Calculate bounding box
        min_x, min_y = np.min(pts, axis=0)
        max_x, max_y = np.max(pts, axis=0)

        # Check margins from edges
        margin_threshold = 30  # pixels

        return (
            min_x < margin_threshold
            and min_y < margin_threshold
            and max_x > width - margin_threshold
            and max_y > height - margin_threshold
        )

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
        """Apply perspective transformation to get a bird's eye view"""
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
        if self.original_cv is None:
            messagebox.showwarning("No Image", "Please open an image first.")
            return

        try:
            self.status_var.set("Detecting document edges...")
            self.root.update()

            # Find document contour
            contour = self.find_document_contour(self.original_cv)

            if contour is not None:
                # Apply perspective transformation
                self.status_var.set("Applying perspective correction...")
                self.root.update()

                # Reshape contour for processing
                pts = contour.reshape(4, 2)
                print(f"Points before transformation: {pts}")

                # Apply perspective transform to zoom in on the paper area
                warped = self.four_point_transform(self.original_cv, pts)

                # Convert back to PIL Image
                self.processed_cv = warped
                processed_rgb = cv2.cvtColor(warped, cv2.COLOR_BGR2RGB)
                self.processed_image = Image.fromarray(processed_rgb)

                # Apply enhancement based on selected option
                self.enhance_document()

                self.status_var.set("Document scanned successfully!")

            else:
                # If no document contour found, use the original image
                messagebox.showinfo(
                    "Info",
                    "Could not detect document edges automatically. Using original image.",
                )
                processed_rgb = cv2.cvtColor(self.original_cv, cv2.COLOR_BGR2RGB)
                self.processed_image = Image.fromarray(processed_rgb)
                self.processed_cv = self.original_cv.copy()
                self.enhance_document()

        except Exception as e:
            messagebox.showerror("Error", f"Could not scan document: {str(e)}")
            self.status_var.set("Error during scanning")

    def enhance_document(self):
        if not self.processed_image:
            self.auto_scan_document()
            return

        try:
            enhancement_type = self.enhancement_var.get()

            if enhancement_type == "auto":
                # Auto enhancement: increase contrast and sharpness
                enhancer = ImageEnhance.Contrast(self.processed_image)
                enhanced = enhancer.enhance(1.2)

                enhancer = ImageEnhance.Sharpness(enhanced)
                enhanced = enhancer.enhance(1.1)

                enhancer = ImageEnhance.Brightness(enhanced)
                self.processed_image = enhancer.enhance(1.05)

            elif enhancement_type == "contrast":
                # High contrast black and white
                gray = self.processed_image.convert("L")
                enhancer = ImageEnhance.Contrast(gray)
                self.processed_image = enhancer.enhance(2.0)

            elif enhancement_type == "grayscale":
                # Simple grayscale
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
            title="Save Scanned Document",
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
                    # Save as PDF
                    self.processed_image.save(file_path, "PDF", resolution=100.0)
                else:
                    # Save as image
                    self.processed_image.save(file_path)

                self.status_var.set(f"Document saved: {os.path.basename(file_path)}")
                messagebox.showinfo(
                    "Success",
                    f"Document saved successfully as {os.path.basename(file_path)}",
                )
            except Exception as e:
                messagebox.showerror("Error", f"Could not save document: {str(e)}")

    def manual_crop_mode(self):
        """Enable manual cropping when auto-detection fails"""
        if self.original_cv is None:
            messagebox.showwarning("No Image", "Please open an image first.")
            return

        messagebox.showinfo(
            "Manual Crop",
            "Auto-detection failed. Using the full image.\n"
            + "For manual cropping, you can:\n"
            + "1. Use an image editing tool to crop first, or\n"
            + "2. Try adjusting the image (better lighting, higher contrast)",
        )

        # Use the original image as-is
        processed_rgb = cv2.cvtColor(self.original_cv, cv2.COLOR_BGR2RGB)
        self.processed_image = Image.fromarray(processed_rgb)
        self.processed_cv = self.original_cv.copy()
        self.enhance_document()

    def show_edge_detection(self):
        """Show edge detection results for debugging"""
        if self.original_cv is None:
            messagebox.showwarning("No Image", "Please open an image first.")
            return

        try:
            # Create edge detection visualization
            gray = cv2.cvtColor(self.original_cv, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)

            # Try multiple edge detection methods
            edges1 = cv2.Canny(blurred, 50, 150)
            edges2 = cv2.Canny(blurred, 75, 200)
            edges3 = cv2.Canny(blurred, 100, 250)

            # Combine edges
            combined_edges = cv2.bitwise_or(cv2.bitwise_or(edges1, edges2), edges3)

            # Convert to RGB and display
            edges_rgb = cv2.cvtColor(combined_edges, cv2.COLOR_GRAY2RGB)
            self.processed_cv = cv2.cvtColor(edges_rgb, cv2.COLOR_RGB2BGR)
            self.processed_image = Image.fromarray(edges_rgb)

            self.display_processed_image()
            self.status_var.set("Showing edge detection results")

        except Exception as e:
            messagebox.showerror("Error", f"Could not show edges: {str(e)}")


def main():
    print("Starting Document Scanner...")

    try:
        root = tk.Tk()
        print("✓ Tkinter window created")

        app = DocumentScanner(root)
        print("✓ Document scanner initialized")

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
    print("Document Scanner - Starting up...")
    main()
    print("Document Scanner - Shutting down...")
