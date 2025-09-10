#!/usr/bin/env python3
"""
Test Template CRUD System

Test the template management system with sample data.
"""

import json
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_template_manager():
    """Test the template manager functionality."""
    try:
        from apps.scanner.template_manager import TemplateManager

        print("🎯 Testing Template Manager...")
        manager = TemplateManager()

        # Show statistics
        print("\n📊 Current Statistics:")
        stats = manager.get_statistics()
        for key, value in stats.items():
            print(f"  {key}: {value}")

        # Show available markers
        available = manager.get_available_marker_ids()
        print(
            f"\n🎯 Available Marker IDs: {available[:10]}{'...' if len(available) > 10 else ''}"
        )
        print(f"   Total available: {len(available)}")

        # Show used markers
        used = manager.get_used_marker_ids()
        print(f"🔒 Used Marker IDs: {sorted(used)}")

        # Test template configuration generation
        config = manager.get_template_config_dict()
        print(f"\n📋 Template Configuration:")
        for template_id, template_info in config.items():
            print(
                f"  {template_id}: {template_info['name']} - {template_info['markers']}"
            )

        print("\n✅ Template Manager test completed successfully!")

    except Exception as e:
        print(f"❌ Error testing template manager: {e}")
        import traceback

        traceback.print_exc()


def create_sample_metadata():
    """Create a sample metadata file for testing import."""
    try:
        sample_metadata = {
            "template_name": "test_custom_template",
            "aruco_ids": [20, 21, 22, 23],
            "template_file": "test_template.png",
            "mask_file": "test_template_mask.png",
            "template_width": 1270,
            "template_height": 720,
            "created_at": "2025-09-11T01:00:00",
            "marker_positions": {
                "top_left": 20,
                "top_right": 21,
                "bottom_left": 22,
                "bottom_right": 23,
            },
            "dictionary_type": "4X4_50",
        }

        # Create sample files (empty for testing)
        Path("test_template.png").touch()
        Path("test_template_mask.png").touch()

        # Save metadata
        with open("test_template_metadata.json", "w") as f:
            json.dump(sample_metadata, f, indent=2)

        print("📄 Created sample metadata file: test_template_metadata.json")
        print(
            "📁 Created sample template files: test_template.png, test_template_mask.png"
        )
        print("💡 You can now test importing this template using the GUI!")

    except Exception as e:
        print(f"❌ Error creating sample metadata: {e}")


if __name__ == "__main__":
    print("🧪 KrathongScanner Template CRUD System Test")
    print("=" * 50)

    test_template_manager()

    print("\n" + "=" * 50)
    create_sample_metadata()

    print("\n🎯 Next steps:")
    print("1. Run 'python run_template_crud.py' to open the management GUI")
    print("2. Use 'Import from Metadata' to import the test template")
    print("3. Create custom templates using the template maker GUI")
    print("4. Test the scanner with custom templates")
