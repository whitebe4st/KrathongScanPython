#!/usr/bin/env python3
"""
Test import of registry_template_gui
"""

print("Starting import test...")

try:
    print("Attempting to import registry_template_gui...")
    import registry_template_gui

    print("Import successful!")

    print("Checking available attributes...")
    all_attrs = dir(registry_template_gui)
    print(f"Total attributes: {len(all_attrs)}")

    classes = [name for name in all_attrs if name[0].isupper()]
    print(f"Classes found: {classes}")

    functions = [
        name
        for name in all_attrs
        if callable(getattr(registry_template_gui, name)) and not name.startswith("_")
    ]
    print(f"Functions found: {functions}")

    if "ProfessionalRegistryGUI" in all_attrs:
        print("SUCCESS: ProfessionalRegistryGUI found!")
    else:
        print("ERROR: ProfessionalRegistryGUI not found")

except Exception as e:
    print(f"Import failed: {e}")
    import traceback

    traceback.print_exc()

print("Import test complete.")
