#!/usr/bin/env python3
"""
Test the web server rectangle detection import fix.
"""

import sys
from pathlib import Path

# Add paths for imports
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent / "web"))


def test_rectangle_import():
    """Test if the web server can now import rectangle_cropper correctly"""
    print("🔍 Testing rectangle_cropper import fix...")

    try:
        # This should work now
        from src.rectangle_cropper import detect_and_crop_rectangle

        print(
            "✅ Successfully imported detect_and_crop_rectangle from src.rectangle_cropper"
        )

        # Test with a real image
        import cv2
        import numpy as np

        test_image_path = "data/test_images/real_photo_test.jpg"
        if Path(test_image_path).exists():
            image = cv2.imread(test_image_path)
            print(f"📏 Test image loaded: {image.shape[1]}x{image.shape[0]}")

            # Test the function
            rect_cropped, rect_contour = detect_and_crop_rectangle(image)

            if rect_cropped is not None:
                print(
                    f"✅ Rectangle detection successful: {rect_cropped.shape[1]}x{rect_cropped.shape[0]}"
                )

                # Save test result
                cv2.imwrite("test_web_rectangle_crop.png", rect_cropped)
                print("💾 Saved test result to: test_web_rectangle_crop.png")

                return True
            else:
                print("❌ Rectangle detection returned None")
                return False
        else:
            print(f"❌ Test image not found: {test_image_path}")
            return False

    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def test_web_server_import():
    """Test if the web server import works"""
    print("\n🔍 Testing web server import...")

    try:
        # Simulate what the web server does
        import os

        os.chdir(Path(__file__).parent)

        exec(
            """
from src.rectangle_cropper import detect_and_crop_rectangle
print("✅ Web server style import successful")
"""
        )
        return True
    except Exception as e:
        print(f"❌ Web server style import failed: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Testing Rectangle Cropper Import Fix")
    print("=" * 50)

    success1 = test_rectangle_import()
    success2 = test_web_server_import()

    if success1 and success2:
        print(
            "\n✅ All tests passed! Rectangle detection should now work in main program."
        )
    else:
        print("\n❌ Some tests failed. Rectangle detection may still have issues.")
