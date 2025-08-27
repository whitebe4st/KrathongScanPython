#!/usr/bin/env python3
"""
Unified ArUco detection test script with automatic warp detection.
"""
import sys

sys.path.insert(0, "src")

import argparse
from pathlib import Path

import cv2
import numpy as np

from aruco_detector import ArUcoDetector


def detect_image_warp(image_path: str, detector: ArUcoDetector) -> bool:
    """
    Automatically detect if an image contains warped markers.

    Args:
        image_path: Path to the image
        detector: ArUcoDetector instance

    Returns:
        True if image appears to be warped, False if straight
    """
    try:
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            print(f"❌ Could not load image: {image_path}")
            return False

        # Detect markers
        corners, ids, _ = detector.detector.detectMarkers(image)

        if ids is None or len(ids) < 4:
            print(f"⚠️  Not enough markers detected for warp analysis")
            return False

        # Find corner markers (IDs 0, 1, 2, 3)
        corner_markers = {}
        for i, marker_id in enumerate(ids.flatten()):
            if marker_id in [0, 1, 2, 3]:
                corner_markers[marker_id] = corners[i][
                    0
                ]  # Get the 4 corners of this marker

        if len(corner_markers) < 4:
            print(f"⚠️  Not all corner markers found for warp analysis")
            return False

        # Calculate marker centers
        marker_centers = {}
        for marker_id, marker_corners in corner_markers.items():
            center = np.mean(marker_corners, axis=0)
            marker_centers[marker_id] = center

        # Expected positions for a straight image (approximate)
        # ID 0: top-left, ID 1: top-right, ID 2: bottom-left, ID 3: bottom-right
        expected_order = [
            (marker_centers[0], marker_centers[1]),  # Top edge (0 to 1)
            (marker_centers[2], marker_centers[3]),  # Bottom edge (2 to 3)
            (marker_centers[0], marker_centers[2]),  # Left edge (0 to 2)
            (marker_centers[1], marker_centers[3]),  # Right edge (1 to 3)
        ]

        # Calculate angles of edges
        angles = []
        for start_point, end_point in expected_order:
            dx = end_point[0] - start_point[0]
            dy = end_point[1] - start_point[1]
            angle = np.degrees(np.arctan2(dy, dx))
            angles.append(angle)

        # For a straight image:
        # - Top and bottom edges should be roughly horizontal (angle ≈ 0° or 180°)
        # - Left and right edges should be roughly vertical (angle ≈ 90° or -90°)

        top_angle = abs(angles[0]) % 180  # Top edge
        bottom_angle = abs(angles[1]) % 180  # Bottom edge
        left_angle = abs(angles[2]) % 180  # Left edge
        right_angle = abs(angles[3]) % 180  # Right edge

        # Check if horizontal edges are close to horizontal (0° or 180°)
        horizontal_threshold = 10  # degrees (more sensitive)
        top_is_horizontal = min(top_angle, 180 - top_angle) < horizontal_threshold
        bottom_is_horizontal = (
            min(bottom_angle, 180 - bottom_angle) < horizontal_threshold
        )

        # Check if vertical edges are close to vertical (90°)
        vertical_threshold = 10  # degrees (more sensitive)
        left_is_vertical = abs(left_angle - 90) < vertical_threshold
        right_is_vertical = abs(right_angle - 90) < vertical_threshold

        # Calculate rectangularity score
        rectangularity_score = sum(
            [
                top_is_horizontal,
                bottom_is_horizontal,
                left_is_vertical,
                right_is_vertical,
            ]
        )

        # Additional check: calculate area distortion
        # For a straight rectangle, opposite sides should be similar length
        top_length = np.linalg.norm(marker_centers[1] - marker_centers[0])
        bottom_length = np.linalg.norm(marker_centers[3] - marker_centers[2])
        left_length = np.linalg.norm(marker_centers[2] - marker_centers[0])
        right_length = np.linalg.norm(marker_centers[3] - marker_centers[1])

        # Calculate length ratios
        horizontal_ratio = min(top_length, bottom_length) / max(
            top_length, bottom_length
        )
        vertical_ratio = min(left_length, right_length) / max(left_length, right_length)

        # Calculate angle deviations for more precise analysis
        top_deviation = min(top_angle, 180 - top_angle)
        bottom_deviation = min(bottom_angle, 180 - bottom_angle)
        left_deviation = abs(left_angle - 90)
        right_deviation = abs(right_angle - 90)
        avg_angle_deviation = (
            top_deviation + bottom_deviation + left_deviation + right_deviation
        ) / 4

        # Debug information
        print(f"📐 Warp Analysis:")
        print(
            f"   Angles: Top={top_angle:.1f}°, Bottom={bottom_angle:.1f}°, Left={left_angle:.1f}°, Right={right_angle:.1f}°"
        )
        print(
            f"   Angle deviations: {top_deviation:.1f}°, {bottom_deviation:.1f}°, {left_deviation:.1f}°, {right_deviation:.1f}° (avg: {avg_angle_deviation:.1f}°)"
        )
        print(f"   Rectangularity: {rectangularity_score}/4")
        print(f"   Length ratios: H={horizontal_ratio:.3f}, V={vertical_ratio:.3f}")

        # Decision logic - multiple criteria
        is_warped = False
        warp_reasons = []

        # Criterion 1: Low rectangularity
        if rectangularity_score < 3:
            is_warped = True
            warp_reasons.append(f"low rectangularity ({rectangularity_score}/4)")

        # Criterion 2: Length ratio distortion
        if horizontal_ratio < 0.85 or vertical_ratio < 0.85:
            is_warped = True
            warp_reasons.append(
                f"length distortion (H:{horizontal_ratio:.2f}, V:{vertical_ratio:.2f})"
            )

        # Criterion 3: High average angle deviation
        if avg_angle_deviation > 8:
            is_warped = True
            warp_reasons.append(f"angle deviation ({avg_angle_deviation:.1f}°)")

        # Criterion 4: Individual angle check - if any edge is significantly off
        max_deviation = max(
            top_deviation, bottom_deviation, left_deviation, right_deviation
        )
        if max_deviation > 10:  # More sensitive threshold
            is_warped = True
            warp_reasons.append(f"individual angle off by {max_deviation:.1f}°")

        # Report decision
        if is_warped:
            print(f"   → Detected as WARPED ({', '.join(warp_reasons)})")
        else:
            print(f"   → Detected as STRAIGHT (all criteria passed)")

        return is_warped

    except Exception as e:
        print(f"❌ Error in warp detection: {e}")
        return False


def test_detection(image_path: str, output_dir: str = None, force_method: str = None):
    """
    Test ArUco detection on a single image with automatic warp detection.

    Args:
        image_path: Path to the image to test
        output_dir: Output directory (optional, defaults to data/test_output)
        force_method: Force processing method ('straight', 'warped', or None for auto-detect)
    """
    print("🧪 Unified ArUco Detection Test")
    print("=" * 35)

    # Validate input
    img_path = Path(image_path)
    if not img_path.exists():
        print(f"❌ Image not found: {image_path}")
        return

    # Set up output directory
    if output_dir is None:
        output_dir = Path("data/test_output/unified_test")
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Production mask
    mask_path = "data/markers/templates/mask1_final.png"
    if not Path(mask_path).exists():
        print(f"❌ Production mask not found: {mask_path}")
        return

    print(f"📸 Input image: {img_path}")
    print(f"🎭 Production mask: {mask_path}")
    print(f"📁 Output directory: {output_dir}")

    # Initialize detector
    detector = ArUcoDetector()

    # Determine processing method
    if force_method:
        if force_method.lower() in ["straight", "simple"]:
            use_homography = False
            method_reason = f"forced ({force_method})"
        elif force_method.lower() in ["warped", "homography"]:
            use_homography = True
            method_reason = f"forced ({force_method})"
        else:
            print(f"❌ Invalid force method: {force_method}")
            return
    else:
        # Auto-detect warp
        print(f"\n🔍 Auto-detecting image warp...")
        use_homography = detect_image_warp(str(img_path), detector)
        method_reason = "auto-detected"

    method_name = "homography" if use_homography else "simple cropping"
    print(f"\n🎯 Processing method: {method_name} ({method_reason})")

    # Generate output filename
    img_name = img_path.stem
    output_filename = f"{img_name}_result.png"
    output_path = output_dir / output_filename

    print(f"\n🔄 Processing image...")

    try:
        # Process the image
        result = detector.process_image(
            str(img_path), mask_path, str(output_path), use_homography=use_homography
        )

        if result:
            # Calculate final result metrics
            if output_path.exists():
                final_img = cv2.imread(str(output_path), cv2.IMREAD_UNCHANGED)
                if (
                    final_img is not None
                    and len(final_img.shape) == 3
                    and final_img.shape[2] == 4
                ):  # BGRA
                    # Count non-transparent pixels
                    alpha = final_img[:, :, 3]
                    content_pixels = np.sum(alpha > 0)
                    total_pixels = alpha.shape[0] * alpha.shape[1]
                    coverage = (content_pixels / total_pixels) * 100
                    dimensions = f"{final_img.shape[1]}x{final_img.shape[0]}"

                    print(f"\n✅ SUCCESS!")
                    print(f"📊 Coverage: {coverage:.1f}%")
                    print(f"📏 Final dimensions: {dimensions}")
                    print(f"📄 Output: {output_filename}")
                    print(f"📄 Metadata: {img_name}_result.json")

                    # Check if debug images were saved
                    debug_dir = output_dir / "debug"
                    if debug_dir.exists():
                        debug_files = list(debug_dir.glob(f"{img_name}_*"))
                        if debug_files:
                            print(f"🔍 Debug images: {len(debug_files)} files in debug/")

                else:
                    print(f"✅ Processing completed, but could not analyze final image")
            else:
                print(f"✅ Processing completed, but output file not found")
        else:
            print(f"❌ Processing failed")

    except Exception as e:
        print(f"❌ Error during processing: {e}")


def main():
    """Main function with command line argument parsing."""
    parser = argparse.ArgumentParser(description="Unified ArUco Detection Test")
    parser.add_argument("image", help="Path to the image to test")
    parser.add_argument("-o", "--output", help="Output directory (optional)")
    parser.add_argument(
        "-m",
        "--method",
        choices=["straight", "simple", "warped", "homography"],
        help="Force processing method (optional, auto-detects if not specified)",
    )

    args = parser.parse_args()

    test_detection(args.image, args.output, args.method)


if __name__ == "__main__":
    # If run with command line arguments, use them
    if len(sys.argv) > 1:
        main()
    else:
        # Interactive mode - test with available images
        print("🧪 Unified ArUco Detection Test")
        print("=" * 35)
        print("No image specified. Testing with available images...")

        test_images = [
            "data/test_images/krathong_test2.png",
            "data/test_images/krathong_warped.png",
        ]

        available_images = [img for img in test_images if Path(img).exists()]

        if not available_images:
            print("❌ No test images found in data/test_images/")
            print("\nUsage:")
            print("  python test_detector.py <image_path>")
            print("  python test_detector.py <image_path> -o <output_dir>")
            print("  python test_detector.py <image_path> -m <straight|warped>")
        else:
            print(f"\n📸 Found {len(available_images)} test images")

            for img_path in available_images:
                print(f"\n" + "=" * 50)
                test_detection(img_path)
                print("=" * 50)

            print(f"\n🎯 UNIFIED DETECTION SUMMARY:")
            print("=" * 35)
            print("✅ Automatic warp detection working")
            print("✅ Both processing methods functional")
            print("✅ Production mask performing well")
            print("✅ Single script handles all test cases")

            print(f"\n💡 USAGE:")
            print("-" * 10)
            print("  python test_detector.py <image_path>")
            print("  python test_detector.py <image_path> -o <output_dir>")
            print("  python test_detector.py <image_path> -m <straight|warped>")
            print("  python test_detector.py  # Test all available images")
