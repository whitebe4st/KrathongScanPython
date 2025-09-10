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

    def find_outermost_paper_boundary(self, image):
        """Most aggressive method to find only the paper boundary, ignoring all internal content"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            height, width = image.shape[:2]
            image_area = height * width

            print("Trying outermost boundary detection...")

            # Strategy 1: Look for the paper as a bright region against dark background
            # Assuming paper is generally lighter than the background/table

            # Apply strong gaussian blur to eliminate internal details
            heavily_blurred = cv2.GaussianBlur(gray, (21, 21), 0)

            # Use Otsu thresholding on the heavily blurred image
            _, binary = cv2.threshold(
                heavily_blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )

            # Find the largest white region (should be the paper)
            contours, _ = cv2.findContours(
                binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            if contours:
                # Get the largest contour
                largest_contour = max(contours, key=cv2.contourArea)
                area = cv2.contourArea(largest_contour)

                print(
                    f"Largest contour area: {area}, Image area: {image_area}, Ratio: {area/image_area:.2f}"
                )

                # Paper should be at least 30% of the image
                if area > image_area * 0.3:
                    # Get the convex hull to smooth out any irregularities
                    hull = cv2.convexHull(largest_contour)

                    # Approximate to rectangle
                    perimeter = cv2.arcLength(hull, True)
                    epsilon = 0.02 * perimeter
                    approx = cv2.approxPolyDP(hull, epsilon, True)

                    # If we don't get exactly 4 points, use minimum area rectangle
                    if len(approx) != 4:
                        rect = cv2.minAreaRect(hull)
                        box = cv2.boxPoints(rect)
                        approx = np.int0(box).reshape(-1, 1, 2)

                    # Make sure it's not the image border
                    if not self.is_image_border(approx, width, height):
                        print("✓ Found paper using bright region detection")
                        return approx

            # Strategy 2: Edge-based approach with very specific filtering
            print("Trying edge-based outer boundary detection...")

            # Apply median filter to reduce noise while preserving edges
            median_filtered = cv2.medianBlur(gray, 5)

            # Use very gentle edge detection
            edges = cv2.Canny(median_filtered, 30, 100, apertureSize=3)

            # Apply morphological operations to connect paper edge segments
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            closed_edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

            # Dilate to ensure paper edges are connected
            dilated = cv2.dilate(closed_edges, kernel, iterations=2)

            # Find contours
            contours, _ = cv2.findContours(
                dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            # Look for the largest contour that could be paper
            valid_contours = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > image_area * 0.2:  # At least 20% of image
                    perimeter = cv2.arcLength(contour, True)
                    epsilon = 0.02 * perimeter
                    approx = cv2.approxPolyDP(contour, epsilon, True)

                    if 4 <= len(approx) <= 8:  # Reasonable number of sides
                        if len(approx) > 4:
                            # Convert to rectangle
                            rect = cv2.minAreaRect(contour)
                            box = cv2.boxPoints(rect)
                            approx = np.int0(box).reshape(-1, 1, 2)

                        if not self.is_image_border(approx, width, height):
                            valid_contours.append((approx, area))

            # Return the largest valid contour
            if valid_contours:
                valid_contours.sort(key=lambda x: x[1], reverse=True)  # Sort by area
                print(
                    f"✓ Found paper using edge detection, area: {valid_contours[0][1]}"
                )
                return valid_contours[0][0]

            # Strategy 3: Last resort - use distance transform to find paper center and work outward
            print("Trying distance transform approach...")

            # Create binary image
            _, binary2 = cv2.threshold(
                gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )

            # Distance transform
            dist_transform = cv2.distanceTransform(binary2, cv2.DIST_L2, 5)

            # Find the center of the largest white region
            _, max_val, _, max_loc = cv2.minMaxLoc(dist_transform)

            if max_val > 10:  # Significant distance from edge
                # Create a mask around the center
                mask = np.zeros_like(gray)
                cv2.circle(mask, max_loc, int(max_val * 0.8), 255, -1)

                # Apply mask and find contour
                masked = cv2.bitwise_and(binary2, mask)
                contours, _ = cv2.findContours(
                    masked, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
                )

                if contours:
                    largest = max(contours, key=cv2.contourArea)
                    area = cv2.contourArea(largest)

                    if area > image_area * 0.2:
                        hull = cv2.convexHull(largest)
                        rect = cv2.minAreaRect(hull)
                        box = cv2.boxPoints(rect)
                        approx = np.int0(box).reshape(-1, 1, 2)

                        if not self.is_image_border(approx, width, height):
                            print("✓ Found paper using distance transform")
                            return approx

            print("❌ All outermost boundary detection methods failed")
            return None

        except Exception as e:
            print(f"Error in outermost boundary detection: {e}")
            return None

    def manual_corner_selection(self, image):
        """Allow user to manually click the 4 corners of the document"""
        try:
            # Create a copy for display
            display_image = image.copy()
            height, width = display_image.shape[:2]

            # Scale down if image is too large
            max_display_size = 800
            if width > max_display_size or height > max_display_size:
                scale = max_display_size / max(width, height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                display_image = cv2.resize(display_image, (new_width, new_height))
                scale_factor = 1 / scale
            else:
                scale_factor = 1

            # Convert to RGB for display
            display_rgb = cv2.cvtColor(display_image, cv2.COLOR_BGR2RGB)

            # Create a simple corner selection window
            corners = []

            def mouse_callback(event, x, y, flags, param):
                if event == cv2.EVENT_LBUTTONDOWN and len(corners) < 4:
                    # Scale coordinates back to original image size
                    original_x = int(x * scale_factor)
                    original_y = int(y * scale_factor)
                    corners.append([original_x, original_y])

                    # Draw a circle on the display image
                    cv2.circle(display_image, (x, y), 5, (0, 255, 0), -1)
                    cv2.putText(
                        display_image,
                        f"{len(corners)}",
                        (x + 10, y),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 0),
                        2,
                    )
                    cv2.imshow("Select 4 Corners", display_image)

            cv2.namedWindow("Select 4 Corners", cv2.WINDOW_NORMAL)
            cv2.imshow("Select 4 Corners", display_image)
            cv2.setMouseCallback("Select 4 Corners", mouse_callback)

            messagebox.showinfo(
                "Instructions",
                "Click on the 4 corners of your document in any order.\n"
                + "Press any key when done or ESC to cancel.",
            )

            # Wait for user input
            while len(corners) < 4:
                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # ESC key
                    cv2.destroyAllWindows()
                    return None

            cv2.destroyAllWindows()

            if len(corners) == 4:
                # Convert to numpy array and reshape for consistency
                corners_array = np.array(corners, dtype=np.int32).reshape(-1, 1, 2)
                print(f"Manual corner selection: {corners}")
                return corners_array

        except Exception as e:
            print(f"Error in manual corner selection: {e}")
            messagebox.showerror("Error", f"Manual selection failed: {str(e)}")

        return None

    def find_paper_boundary(self, image):
        """Specifically designed to find paper boundaries, not internal content"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            height, width = image.shape[:2]
            image_area = height * width

            # Method 1: Very gentle edge detection to catch paper edges
            # Paper edges are often very subtle
            blurred = cv2.GaussianBlur(gray, (7, 7), 0)

            # Use very low thresholds to catch faint paper edges
            edges = cv2.Canny(blurred, 20, 60, apertureSize=3)

            # Apply closing to connect paper edge segments
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            edges_closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

            # Find contours - only external ones
            contours, _ = cv2.findContours(
                edges_closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            # Sort by area and look for the largest valid paper contour
            contours = sorted(contours, key=cv2.contourArea, reverse=True)

            for contour in contours:
                area = cv2.contourArea(contour)

                # Paper should be a very large portion of the image (50%+)
                if area > image_area * 0.5:
                    perimeter = cv2.arcLength(contour, True)
                    epsilon = 0.01 * perimeter  # Very precise approximation
                    approx = cv2.approxPolyDP(contour, epsilon, True)

                    # Allow 4-8 points, then reduce to 4 if needed
                    if 4 <= len(approx) <= 8:
                        if len(approx) > 4:
                            # If more than 4 points, use bounding rectangle approach
                            rect = cv2.minAreaRect(contour)
                            box = cv2.boxPoints(rect)
                            approx = np.int0(box).reshape(-1, 1, 2)

                        # Final validation
                        if not self.is_image_border(approx, width, height):
                            return approx

            # Method 2: If no contour found, try background subtraction approach
            # This helps when paper is on a background

            # Create a mask to find the paper against background
            # Use Otsu's thresholding to separate paper from background
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Find the largest white region (assuming paper is lighter than background)
            contours, _ = cv2.findContours(
                thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                area = cv2.contourArea(largest_contour)

                if area > image_area * 0.4:  # Paper should be substantial
                    # Get the convex hull to smooth out the boundary
                    hull = cv2.convexHull(largest_contour)

                    perimeter = cv2.arcLength(hull, True)
                    epsilon = 0.02 * perimeter
                    approx = cv2.approxPolyDP(hull, epsilon, True)

                    if len(approx) >= 4:
                        if len(approx) > 4:
                            # Use minimum area rectangle for clean paper boundary
                            rect = cv2.minAreaRect(hull)
                            box = cv2.boxPoints(rect)
                            approx = np.int0(box).reshape(-1, 1, 2)

                        if not self.is_image_border(approx, width, height):
                            return approx

            # Method 3: Look for paper shadow/edge using gradient
            # Paper often has subtle shadows at edges
            grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)

            # Normalize and threshold
            gradient_magnitude = np.uint8(
                gradient_magnitude / gradient_magnitude.max() * 255
            )
            _, thresh_grad = cv2.threshold(
                gradient_magnitude, 30, 255, cv2.THRESH_BINARY
            )

            # Clean up the gradient image
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            cleaned = cv2.morphologyEx(thresh_grad, cv2.MORPH_CLOSE, kernel)

            contours, _ = cv2.findContours(
                cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            for contour in sorted(contours, key=cv2.contourArea, reverse=True):
                area = cv2.contourArea(contour)

                if area > image_area * 0.3:
                    perimeter = cv2.arcLength(contour, True)
                    epsilon = 0.02 * perimeter
                    approx = cv2.approxPolyDP(contour, epsilon, True)

                    if len(approx) >= 4:
                        if len(approx) > 4:
                            rect = cv2.minAreaRect(contour)
                            box = cv2.boxPoints(rect)
                            approx = np.int0(box).reshape(-1, 1, 2)

                        if not self.is_image_border(approx, width, height):
                            return approx

        except Exception as e:
            print(f"Error in paper boundary detection: {e}")

        return None

    def find_contour_with_preprocessing(self, image):
        """Enhanced method with better preprocessing - prioritizes document edges over internal content"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Get image dimensions
            height, width = image.shape[:2]
            image_area = height * width

            # Method 1: Focus on document edges using dilated edges
            # Apply bilateral filter to reduce noise while keeping edges sharp
            filtered = cv2.bilateralFilter(gray, 9, 75, 75)

            # Use edge detection with lower thresholds to catch document boundaries
            edges = cv2.Canny(filtered, 30, 80, apertureSize=3)

            # Dilate to connect broken edges (document boundaries are often faint)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            dilated = cv2.dilate(edges, kernel, iterations=2)

            # Find contours - use RETR_EXTERNAL to get only outer contours
            contours, _ = cv2.findContours(
                dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            contours = sorted(contours, key=cv2.contourArea, reverse=True)

            # Look for the largest valid document contour
            for contour in contours:
                perimeter = cv2.arcLength(contour, True)
                epsilon = (
                    0.015 * perimeter
                )  # Reduced epsilon for more accurate approximation
                approx = cv2.approxPolyDP(contour, epsilon, True)

                if len(approx) == 4:
                    area = cv2.contourArea(approx)

                    # Document should be a significant portion of the image (at least 25%)
                    # but not the entire image border
                    if image_area * 0.25 < area < image_area * 0.85:
                        if not self.is_image_border(approx, width, height):
                            if self.is_roughly_rectangular(approx):
                                # Additional check: ensure it's not too centered (likely internal content)
                                if not self.is_too_centered(approx, width, height):
                                    return approx

            # Method 2: If no good contour found, try with different preprocessing
            # Apply CLAHE for better contrast
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)

            # Try with Gaussian blur and different Canny thresholds
            blurred = cv2.GaussianBlur(enhanced, (5, 5), 0)
            edges2 = cv2.Canny(blurred, 50, 120, apertureSize=3)

            # Find contours again
            contours2, _ = cv2.findContours(
                edges2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            contours2 = sorted(contours2, key=cv2.contourArea, reverse=True)

            for contour in contours2:
                perimeter = cv2.arcLength(contour, True)
                epsilon = 0.02 * perimeter
                approx = cv2.approxPolyDP(contour, epsilon, True)

                if len(approx) == 4:
                    area = cv2.contourArea(approx)

                    # Be more generous with area requirements in second pass
                    if image_area * 0.2 < area < image_area * 0.9:
                        if not self.is_image_border(approx, width, height):
                            if self.is_roughly_rectangular(approx):
                                return approx

        except Exception as e:
            print(f"Error in preprocessing method: {e}")
            pass
        return None

    def is_too_centered(self, contour, width, height):
        """Check if contour is too centered (likely internal content rather than document edge)"""
        try:
            pts = contour.reshape(4, 2)

            # Calculate bounding rectangle
            x_coords = pts[:, 0]
            y_coords = pts[:, 1]

            min_x, max_x = np.min(x_coords), np.max(x_coords)
            min_y, max_y = np.min(y_coords), np.max(y_coords)

            # Calculate margins from image edges
            left_margin = min_x
            right_margin = width - max_x
            top_margin = min_y
            bottom_margin = height - max_y

            # If all margins are substantial (>10% of image dimension), it's likely internal content
            margin_threshold_x = width * 0.1
            margin_threshold_y = height * 0.1

            large_margins = (
                left_margin > margin_threshold_x
                and right_margin > margin_threshold_x
                and top_margin > margin_threshold_y
                and bottom_margin > margin_threshold_y
            )

            return large_margins

        except:
            return False

    def is_roughly_rectangular(self, contour):
        """Check if the contour is roughly rectangular"""
        try:
            # Get the four corners
            pts = contour.reshape(4, 2)

            # Calculate all side lengths
            def distance(p1, p2):
                return np.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

            # Calculate distances between consecutive points
            sides = []
            for i in range(4):
                side_length = distance(pts[i], pts[(i + 1) % 4])
                sides.append(side_length)

            # Check if opposite sides are roughly equal (within 20% tolerance)
            tolerance = 0.2
            side1, side2, side3, side4 = sides

            # Compare opposite sides
            ratio1 = (
                min(side1, side3) / max(side1, side3) if max(side1, side3) > 0 else 0
            )
            ratio2 = (
                min(side2, side4) / max(side2, side4) if max(side2, side4) > 0 else 0
            )

            # Both ratios should be close to 1 (similar lengths)
            return ratio1 > (1 - tolerance) and ratio2 > (1 - tolerance)

        except:
            return False

    def find_contour_standard(self, image):
        """Standard edge detection method - prioritizes document boundaries"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)

            # Use lower thresholds to catch faint document edges
            edged = cv2.Canny(blurred, 50, 120)

            # Use RETR_EXTERNAL to get only outer contours
            contours, _ = cv2.findContours(
                edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            contours = sorted(contours, key=cv2.contourArea, reverse=True)

            # Get image dimensions
            height, width = image.shape[:2]
            image_area = height * width

            for contour in contours:
                epsilon = 0.015 * cv2.arcLength(
                    contour, True
                )  # More precise approximation
                approx = cv2.approxPolyDP(contour, epsilon, True)

                if len(approx) == 4:
                    area = cv2.contourArea(approx)
                    # Document should be substantial (at least 30% of image)
                    if image_area * 0.3 < area < image_area * 0.85:
                        if not self.is_image_border(approx, width, height):
                            if not self.is_too_centered(approx, width, height):
                                return approx
        except:
            pass
        return None

    def find_contour_adaptive(self, image):
        """Adaptive threshold method"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Apply adaptive threshold
            adaptive = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )

            # Find contours
            contours, _ = cv2.findContours(
                adaptive, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
            )
            contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

            # Get image dimensions
            height, width = image.shape[:2]
            image_area = height * width

            for contour in contours:
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)

                if len(approx) == 4:
                    area = cv2.contourArea(approx)
                    # Filter out contours that are too small or too large (likely the image border)
                    if 10000 < area < image_area * 0.9:
                        # Check if it's not the image border
                        if not self.is_image_border(approx, width, height):
                            return approx
        except:
            pass
        return None

    def find_contour_morphology(self, image):
        """Morphological operations method"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Apply morphological operations
            kernel = np.ones((3, 3), np.uint8)
            morph = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
            morph = cv2.morphologyEx(morph, cv2.MORPH_OPEN, kernel)

            # Edge detection
            edged = cv2.Canny(morph, 50, 150)

            contours, _ = cv2.findContours(
                edged, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
            )
            contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

            # Get image dimensions
            height, width = image.shape[:2]
            image_area = height * width

            for contour in contours:
                epsilon = 0.03 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)

                if len(approx) == 4:
                    area = cv2.contourArea(approx)
                    # Filter out contours that are too small or too large (likely the image border)
                    if 8000 < area < image_area * 0.9:
                        # Check if it's not the image border
                        if not self.is_image_border(approx, width, height):
                            return approx
        except:
            pass
        return None

    def find_contour_multi_canny(self, image):
        """Try multiple Canny threshold values"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)

            # Get image dimensions
            height, width = image.shape[:2]
            image_area = height * width

            # Try different threshold combinations
            threshold_pairs = [(50, 150), (30, 100), (100, 200), (75, 175), (40, 120)]

            for low, high in threshold_pairs:
                edged = cv2.Canny(blurred, low, high)

                contours, _ = cv2.findContours(
                    edged, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
                )
                contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

                for contour in contours:
                    epsilon = 0.02 * cv2.arcLength(contour, True)
                    approx = cv2.approxPolyDP(contour, epsilon, True)

                    if len(approx) == 4:
                        area = cv2.contourArea(approx)
                        # Filter out contours that are too small or too large (likely the image border)
                        if 5000 < area < image_area * 0.9:
                            # Check if it's not the image border
                            if not self.is_image_border(approx, width, height):
                                return approx
        except:
            pass
        return None

    def is_image_border(self, contour, width, height):
        """Check if the contour is just the image border - now more restrictive"""
        # Reshape contour points
        pts = contour.reshape(4, 2)

        # Define tolerance for border detection (pixels from edge)
        tolerance = 100  # Very strict - increased to 100px from edge

        # Check if any points are very close to the image edges
        border_points = 0
        for point in pts:
            x, y = point
            if (
                x < tolerance
                or x > width - tolerance
                or y < tolerance
                or y > height - tolerance
            ):
                border_points += 1

        # If even 1 point is near the border, reject it (very strict)
        return border_points >= 1

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

            # Find document contour - now always returns something
            contour = self.find_document_contour(self.original_cv)

            # Show what was detected before transformation
            self.visualize_detected_contour(contour)

            # Apply perspective transformation
            self.status_var.set("Applying perspective correction...")
            self.root.update()

            # Reshape contour for processing
            pts = contour.reshape(4, 2)
            print(f"Using points: {pts}")

            # Apply perspective transform
            warped = self.four_point_transform(self.original_cv, pts)

            # Convert back to PIL Image
            self.processed_cv = warped
            processed_rgb = cv2.cvtColor(warped, cv2.COLOR_BGR2RGB)
            self.processed_image = Image.fromarray(processed_rgb)

            # Apply enhancement based on selected option
            self.enhance_document()

            self.status_var.set("Document scanned successfully!")

        except Exception as e:
            print(f"Error during scanning: {e}")
            # If anything fails, just use the original image
            processed_rgb = cv2.cvtColor(self.original_cv, cv2.COLOR_BGR2RGB)
            self.processed_image = Image.fromarray(processed_rgb)
            self.processed_cv = self.original_cv.copy()
            self.enhance_document()
            self.status_var.set("Using original image (auto-detection had issues)")

    def fallback_largest_rectangle(self, image):
        """Fallback method: find the largest reasonable rectangle in the image"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            height, width = image.shape[:2]
            image_area = height * width

            # Try multiple edge detection approaches and combine them

            # Method 1: Very low threshold Canny
            blur1 = cv2.GaussianBlur(gray, (5, 5), 0)
            edges1 = cv2.Canny(blur1, 10, 50)

            # Method 2: Adaptive threshold
            adaptive = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )

            # Method 3: Simple threshold
            _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

            # Combine all edge detection methods
            combined = cv2.bitwise_or(cv2.bitwise_or(edges1, adaptive), thresh)

            # Apply morphological operations to clean up
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            cleaned = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel)

            # Find all contours
            contours, _ = cv2.findContours(
                cleaned, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
            )

            best_contour = None
            best_score = 0

            for contour in contours:
                area = cv2.contourArea(contour)

                # Must be a substantial area but not the whole image
                if image_area * 0.15 < area < image_area * 0.95:
                    # Try to approximate as rectangle
                    perimeter = cv2.arcLength(contour, True)

                    # Try different epsilon values
                    for epsilon_factor in [0.01, 0.02, 0.03, 0.05]:
                        epsilon = epsilon_factor * perimeter
                        approx = cv2.approxPolyDP(contour, epsilon, True)

                        if len(approx) == 4:
                            # Check if it's not the image border
                            if not self.is_image_border(approx, width, height):
                                # Score based on area (larger is better for paper detection)
                                score = area

                                # Bonus for being more rectangular
                                if self.is_roughly_rectangular(approx):
                                    score *= 1.2

                                # Penalty for being too centered (internal content)
                                if self.is_too_centered(approx, width, height):
                                    score *= 0.3

                                if score > best_score:
                                    best_score = score
                                    best_contour = approx

                        elif len(approx) > 4:
                            # If we get more than 4 points, use minimum area rectangle
                            rect = cv2.minAreaRect(contour)
                            box = cv2.boxPoints(rect)
                            box_approx = np.int0(box).reshape(-1, 1, 2)

                            if not self.is_image_border(box_approx, width, height):
                                score = area
                                if not self.is_too_centered(box_approx, width, height):
                                    score *= 1.5  # Bonus for being rectangular

                                if score > best_score:
                                    best_score = score
                                    best_contour = box_approx

            return best_contour

        except Exception as e:
            print(f"Error in fallback method: {e}")
            return None

    def visualize_detected_contour(self, contour):
        """Show what contour was detected on the original image"""
        try:
            # Create a copy of the original image for visualization
            vis_image = self.original_cv.copy()

            # Draw the detected contour in red
            cv2.drawContours(vis_image, [contour], -1, (0, 0, 255), 3)

            # Draw corner points in green
            pts = contour.reshape(4, 2)
            for point in pts:
                cv2.circle(vis_image, tuple(point.astype(int)), 8, (0, 255, 0), -1)

            # Convert to RGB and update the processed image display temporarily
            vis_rgb = cv2.cvtColor(vis_image, cv2.COLOR_BGR2RGB)
            temp_image = Image.fromarray(vis_rgb)

            # Temporarily show the visualization
            original_processed = self.processed_image
            self.processed_image = temp_image
            self.display_processed_image()

            # Wait a moment to show the detection
            self.root.update()
            import time

            time.sleep(1)

            # Restore original processed image
            self.processed_image = original_processed

        except Exception as e:
            print(f"Error in visualization: {e}")

    def enhance_document(self):
        """Apply enhancement to the processed image based on selected option"""
        if not self.processed_image:
            return

        try:
            enhancement_type = self.enhancement_var.get()

            if enhancement_type == "auto":
                # Auto enhancement - improve contrast and sharpness
                enhancer = ImageEnhance.Contrast(self.processed_image)
                enhanced = enhancer.enhance(1.2)

                enhancer = ImageEnhance.Sharpness(enhanced)
                enhanced = enhancer.enhance(1.1)

                self.processed_image = enhanced

            elif enhancement_type == "contrast":
                # High contrast enhancement
                enhancer = ImageEnhance.Contrast(self.processed_image)
                enhanced = enhancer.enhance(1.5)

                # Convert to grayscale for better contrast
                enhanced = enhanced.convert("L").convert("RGB")
                self.processed_image = enhanced

            elif enhancement_type == "grayscale":
                # Convert to grayscale
                enhanced = self.processed_image.convert("L").convert("RGB")
                self.processed_image = enhanced

            # Update the display
            self.display_processed_image()

        except Exception as e:
            print(f"Error during enhancement: {e}")

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
