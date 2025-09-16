#!/usr/bin/env python3
"""
Test dependencies for registry_template_gui
"""

print("Testing dependencies individually...")

print("1. Testing basic imports...")
try:
    import json
    import sys
    import tkinter as tk
    from pathlib import Path
    from tkinter import filedialog, messagebox, ttk

    print("✅ Basic imports successful")
except Exception as e:
    print(f"❌ Basic imports failed: {e}")
    exit(1)

print("2. Testing enhanced_template_maker...")
try:
    from enhanced_template_maker import EnhancedKrathongTemplateMaker

    print("✅ Enhanced template maker import successful")
except Exception as e:
    print(f"❌ Enhanced template maker import failed: {e}")
    exit(1)

print("3. Testing template_registry...")
try:
    from template_registry import get_registry

    print("✅ Template registry import successful")
except Exception as e:
    print(f"❌ Template registry import failed: {e}")
    exit(1)

print("4. Testing class definition...")
try:
    print("Executing class definition...")

    class TestProfessionalRegistryGUI:
        def __init__(self):
            print("Test class initialized")

    print("✅ Class definition successful")
    test_instance = TestProfessionalRegistryGUI()
    print("✅ Class instantiation successful")

except Exception as e:
    print(f"❌ Class definition failed: {e}")
    import traceback

    traceback.print_exc()

print("All dependency tests complete.")
