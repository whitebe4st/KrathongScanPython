#!/usr/bin/env python3
"""
Simple test version of the registry GUI to diagnose issues
"""

import sys
import tkinter as tk
from tkinter import messagebox, ttk


def test_simple_gui():
    """Test a simple GUI version."""
    print("🚀 Starting simple GUI test...")

    try:
        # Test basic imports first
        print("📦 Testing imports...")
        from enhanced_template_maker import EnhancedKrathongTemplateMaker
        from template_registry import get_registry

        print("✅ Imports successful")

        # Create GUI
        print("🎨 Creating GUI...")
        root = tk.Tk()
        root.title("Simple Registry Test")
        root.geometry("400x300")

        # Add some basic widgets
        title_label = tk.Label(
            root, text="Registry GUI Test", font=("Arial", 14, "bold")
        )
        title_label.pack(pady=20)

        status_label = tk.Label(root, text="Testing registry system...")
        status_label.pack(pady=10)

        def test_registry():
            try:
                registry = get_registry()
                stats = registry.get_registry_stats()
                status_label.config(
                    text=f"Registry works! Templates: {stats['total_templates']}"
                )
            except Exception as e:
                status_label.config(text=f"Registry error: {e}")

        def test_template_maker():
            try:
                maker = EnhancedKrathongTemplateMaker()
                ids = maker.get_auto_assigned_ids()
                status_label.config(text=f"Template maker works! Next IDs: {ids}")
            except Exception as e:
                status_label.config(text=f"Template maker error: {e}")

        def close_app():
            print("👋 Closing application...")
            root.destroy()

        # Add test buttons
        button_frame = tk.Frame(root)
        button_frame.pack(pady=20)

        tk.Button(button_frame, text="Test Registry", command=test_registry).pack(
            side=tk.LEFT, padx=5
        )
        tk.Button(
            button_frame, text="Test Template Maker", command=test_template_maker
        ).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Close", command=close_app).pack(
            side=tk.LEFT, padx=5
        )

        print("🖥️ Starting GUI mainloop...")

        # Auto-close after 10 seconds for testing
        root.after(10000, close_app)

        root.mainloop()
        print("✅ GUI test completed successfully")

    except Exception as e:
        print(f"❌ GUI test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_simple_gui()
