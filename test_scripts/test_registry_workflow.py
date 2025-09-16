#!/usr/bin/env python3
"""
Test Script: Complete Template Registry Workflow

This script demonstrates the complete template registry system workflow.
"""

from enhanced_template_maker import EnhancedKrathongTemplateMaker
from template_registry import get_registry


def test_complete_workflow():
    """Test the complete template registry workflow."""

    print("🎯 Testing Complete Template Registry Workflow")
    print("=" * 50)

    # Initialize components
    registry = get_registry()
    maker = EnhancedKrathongTemplateMaker()

    # Show initial stats
    initial_stats = registry.get_registry_stats()
    print(f"📊 Initial Registry Stats:")
    print(f"   Total Templates: {initial_stats['total_templates']}")
    print(f"   Next Available IDs: {initial_stats['next_available_ids']}")
    print()

    # Test template creation with auto-assigned IDs
    print("✅ Creating test template with auto-assigned IDs...")
    success, message = maker.create_template_with_registry(
        template_name="workflow_test_template",
        client_name="TestClient123",
        marker_ids=None,  # Auto-assign
        output_dir="data/templates",
    )

    if success:
        print(f"✅ Template created successfully!")
        print(f"📝 Details: {message}")
    else:
        print(f"❌ Template creation failed: {message}")
        return False

    # Show updated stats
    updated_stats = registry.get_registry_stats()
    print(f"\n📊 Updated Registry Stats:")
    print(f"   Total Templates: {updated_stats['total_templates']}")
    print(f"   Next Available IDs: {updated_stats['next_available_ids']}")
    print()

    # List all templates
    print("📋 All Registered Templates:")
    templates = registry.list_all_templates()
    for name, data in templates.items():
        print(
            f"   - {name}: {data.get('marker_ids', [])} (Client: {data.get('client', 'Unknown')})"
        )

    print("\n🎉 Workflow test completed successfully!")
    return True


if __name__ == "__main__":
    test_complete_workflow()
