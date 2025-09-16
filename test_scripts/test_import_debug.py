#!/usr/bin/env python3
"""
Test import debug - Find what's causing the minimal GUI to run
"""

print("=== Starting import debug ===")

print("Step 1: Testing individual imports...")

print("Importing sys...")
import sys

print("Importing tkinter...")
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

print("Importing pathlib...")
from pathlib import Path

print("Importing json...")
import json

print("Step 2: Testing template_registry...")
from template_registry import get_registry

print("template_registry imported successfully")

print("Step 3: Testing enhanced_template_maker...")
from enhanced_template_maker import EnhancedKrathongTemplateMaker

print("enhanced_template_maker imported successfully")

print("Step 4: About to import registry_template_gui...")
print("Before import - checking for MinimalRegistryGUI in sys.modules:")
print([name for name in sys.modules if "minimal" in name.lower()])

print("Importing registry_template_gui...")
import registry_template_gui

print("registry_template_gui imported")

print("After import - available classes in registry_template_gui:")
print([name for name in dir(registry_template_gui) if "GUI" in name])

print("Checking sys.modules for minimal after import:")
print([name for name in sys.modules if "minimal" in name.lower()])

print("=== Import debug complete ===")
