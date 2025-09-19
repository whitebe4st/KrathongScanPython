#!/usr/bin/env python3
"""
Simple script to run the ArUco generator
"""

import sys

sys.path.insert(0, "src")

from aruco_generator.generator import ArUcoMarkerGenerator


def main():
    print("🎯 Running ArUco Generator")
    print("=" * 30)

    # Create generator (will use default: data/aruco_markers)
    generator = ArUcoMarkerGenerator()

    # Generate 4 markers
    print("📝 Generating 4 markers...")
    markers = generator.generate_simple_markers(4)

    print(f"\n✅ Generated {len(markers)} markers!")
    print("📁 Check 'data/aruco_markers' folder for your markers!")


if __name__ == "__main__":
    main()
