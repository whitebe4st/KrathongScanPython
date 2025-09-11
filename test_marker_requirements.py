#!/usr/bin/env python3
"""
Test Template Detection Requirements

This shows how many markers are needed for template detection.
"""

import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.aruco_detector.template_config import (
    detect_template_from_markers,
    detect_template_partial,
)


def test_marker_requirements():
    """Test marker requirements for template detection."""
    print("🧪 Testing Template Detection Requirements")
    print("=" * 50)

    # Test different marker combinations
    test_cases = [
        ("krathong1 - All markers", [0, 1, 2, 3]),
        ("krathong1 - Missing 1", [0, 1, 2]),
        ("krathong1 - Missing 2", [0, 1]),
        ("krathong2 - All markers", [4, 5, 6, 7]),
        ("krathong2 - Missing 1", [4, 5, 6]),
        ("Test1 - All markers", [20, 21, 22, 23]),
        ("Test1 - Missing 1", [20, 21, 22]),
        ("Mixed markers", [0, 1, 4, 5]),
        ("Unknown markers", [100, 101, 102, 103]),
    ]

    print("\n1️⃣ STRICT MODE (Used for Scanning):")
    print("   - Requires ALL 4 markers of template")
    print("   - Used when processing images for scanning")
    print("-" * 40)

    for description, markers in test_cases:
        result = detect_template_from_markers(markers)
        status = f"✅ {result}" if result else "❌ No match"
        print(f"   {description:25} {markers} → {status}")

    print("\n2️⃣ PARTIAL MODE (Used for Preview/Display):")
    print("   - Requires minimum 3 markers")
    print("   - Used for live preview and display")
    print("-" * 40)

    for description, markers in test_cases:
        if len(markers) >= 3:  # Only test if we have enough markers
            result = detect_template_partial(markers, min_markers=3)
            status = f"✅ {result}" if result else "❌ No match"
            print(f"   {description:25} {markers} → {status}")
        else:
            print(f"   {description:25} {markers} → ❌ Too few markers")

    print("\n💡 KEY INSIGHTS:")
    print("   📸 For IMAGE SCANNING: Need ALL 4 markers (strict mode)")
    print("   👁️  For LIVE PREVIEW: Need minimum 3 markers (partial mode)")
    print("   🎯 Each template uses 4 specific marker IDs")
    print("   ⚠️  Mixed markers from different templates = No match")


if __name__ == "__main__":
    test_marker_requirements()
