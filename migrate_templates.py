#!/usr/bin/env python3
"""
Migrate Existing Custom Templates

This script fixes existing custom templates to use the correct mask paths.
"""

import shutil
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from apps.scanner.template_manager import TemplateManager


def migrate_existing_templates():
    """Migrate existing custom templates to use correct mask paths."""
    print("🔧 Migrating Existing Custom Templates")
    print("=" * 50)

    manager = TemplateManager()
    templates = manager.read_all_templates()

    scanner_mask_dir = Path("data/markers/templates")
    scanner_mask_dir.mkdir(parents=True, exist_ok=True)

    for template in templates:
        print(f"\n📝 Processing template: {template.name}")

        # Check if mask is in the wrong location
        mask_path = Path(template.mask_path)
        expected_dir = Path("data/markers/templates")
        is_in_scanner_dir = (
            expected_dir in mask_path.parents or mask_path.parent == expected_dir
        )

        if not is_in_scanner_dir and mask_path.exists():
            print(f"   ⚠️  Mask in wrong location: {mask_path}")

            # Generate new mask filename
            new_mask_filename = f"{template.name}_mask.png"
            new_mask_path = scanner_mask_dir / new_mask_filename

            # Copy mask file to scanner location
            shutil.copy2(mask_path, new_mask_path)
            print(f"   📁 Copied mask to: {new_mask_path}")

            # Update template in database
            template.mask_path = str(new_mask_path)
            success = manager.registry.save_template(template)

            if success:
                print(f"   ✅ Updated database with new mask path")
            else:
                print(f"   ❌ Failed to update database")

        elif is_in_scanner_dir:
            print(f"   ✅ Mask already in correct location")
        else:
            print(f"   ❌ Mask file missing: {mask_path}")

    print(f"\n🎉 Migration completed!")
    print(f"📊 All custom templates should now work with scanner")


if __name__ == "__main__":
    migrate_existing_templates()
