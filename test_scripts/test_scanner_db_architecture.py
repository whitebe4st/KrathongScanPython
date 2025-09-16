#!/usr/bin/env python3
"""
Test Scanner Database Architecture

Tests the new architecture where:
1. Scanner loads templates from data/db/scanner.db
2. Falls back to hardcoded templates if database is empty
3. CRUD acts as database editor
"""

import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from apps.scanner.template_manager import TemplateManager
from src.aruco_detector.detector import ArUcoDetector


def test_scanner_database_architecture():
    """Test the scanner database architecture."""
    print("🧪 Testing Scanner Database Architecture")
    print("=" * 50)

    # Test 1: Template Manager (Database Editor)
    print("\n1️⃣ Testing Template Manager (Database Editor)")
    print("-" * 30)

    manager = TemplateManager()
    stats = manager.get_statistics()

    print(f"📊 Database: {manager.db_path}")
    print(f"📈 Custom templates in database: {stats['custom_templates']}")
    print(f"📋 Hardcoded templates: {stats['hardcoded_templates']}")
    print(f"🎯 Total templates: {stats['total_templates']}")

    # List templates in database
    templates = manager.read_all_templates()
    if templates:
        print(f"\n📝 Templates in data/db/scanner.db:")
        for template in templates:
            status = "✅ Active" if template.is_active else "❌ Inactive"
            print(f"   - {template.name}: markers {template.marker_ids} ({status})")
    else:
        print("📋 No custom templates in database")

    # Test 2: ArUco Detector (Scanner)
    print("\n2️⃣ Testing ArUco Detector (Scanner)")
    print("-" * 30)

    detector = ArUcoDetector()

    print(f"🎯 Total template configs loaded: {len(detector.template_configs)}")
    print(f"🔢 Total marker mappings: {len(detector.marker_to_template)}")

    print(f"\n📝 Available templates:")
    for template_name in detector.template_configs.keys():
        markers = [
            k for k, v in detector.marker_to_template.items() if v == template_name
        ]
        print(f"   - {template_name}: markers {sorted(markers)}")

    # Test 3: Architecture Verification
    print("\n3️⃣ Architecture Verification")
    print("-" * 30)

    # Check if hardcoded templates are always available
    hardcoded_templates = [
        "krathong1",
        "krathong2",
        "krathong3",
        "krathong4",
        "krathong5",
    ]
    hardcoded_available = all(
        t in detector.template_configs for t in hardcoded_templates
    )

    print(
        f"📋 Hardcoded templates available: {'✅ Yes' if hardcoded_available else '❌ No'}"
    )

    # Check database integration
    db_templates = [t.name for t in templates if t.is_active]
    db_integrated = all(t in detector.template_configs for t in db_templates)

    print(f"🗃️  Database templates integrated: {'✅ Yes' if db_integrated else '❌ No'}")

    # Test reload functionality
    print(f"\n🔄 Testing template reload...")
    detector.reload_custom_templates()
    print(f"✅ Reload completed")

    print(f"\n🎉 Architecture test completed!")
    print(f"📊 Summary:")
    print(f"   - Database: data/db/scanner.db")
    print(f"   - Custom templates: {len(db_templates)}")
    print(f"   - Hardcoded fallback: {len(hardcoded_templates)} templates")
    print(f"   - Total available: {len(detector.template_configs)} templates")


if __name__ == "__main__":
    test_scanner_database_architecture()
