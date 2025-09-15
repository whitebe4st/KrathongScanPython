import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import cv2

from src.aruco_detector.detector import ArUcoDetector

# Use the user's TESTTEST template image for reproduction
img_path = Path("data/templates/TESTTEST.png")
if not img_path.exists():
    print("Requested test image not found:", img_path)
    # fallback to previous behavior
    img_path = Path("data/test_images/krathong_test1.png")
    if not img_path.exists():
        candidates = list(Path("data/test_images").glob("*"))
        if not candidates:
            print("No test images found")
            sys.exit(1)
        img_path = candidates[0]

print("Testing image:", img_path)
img = cv2.imread(str(img_path))
if img is None:
    print("Failed to load image")
    sys.exit(1)

d = ArUcoDetector()
markers = d.detect_markers(img)
print("Detected markers IDs:", [m.id for m in markers])

template = d.detect_template([m.id for m in markers], use_partial=False)
print("Detected template (strict):", template)
if not template:
    template_partial = d.detect_template([m.id for m in markers], use_partial=True)
    print("Detected template (partial):", template_partial)

mask_path = d.get_template_mask_path()
print("Resolved mask path:", mask_path)

if mask_path:
    # apply mask to cropped area: need corner markers
    corner = d.get_corner_markers(markers)
    if corner:
        try:
            homography = d.create_perspective_transform(corner)
            corrected = d.apply_perspective_correction(img, homography)
            cropped = d._crop_perspective_corrected_area(corrected, corner)
        except Exception as e:
            print("Error during transform/crop:", e)
            cropped = img
    else:
        cropped = img

    masked = d.apply_template_mask(cropped, mask_path)
    out = Path("temp") / "debug_masked.png"
    out.parent.mkdir(exist_ok=True)
    cv2.imwrite(str(out), masked)
    print("Masked image saved to", out)
else:
    print("No mask found; cannot apply mask")
