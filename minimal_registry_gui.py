#!/usr/bin/env python3
"""
Minimal Registry GUI - Debug Version
"""

print("🚀 Starting minimal registry GUI...")

try:
    print("📦 Importing tkinter...")
    import tkinter as tk
    from tkinter import messagebox, ttk

    print("✅ Tkinter imported")

    print("📦 Importing system modules...")
    import sys
    from pathlib import Path

    print("✅ System modules imported")

    print("📦 Importing registry components...")
    from template_registry import get_registry

    print("✅ Registry imported")

    from enhanced_template_maker import EnhancedKrathongTemplateMaker

    print("✅ Template maker imported")

    print("🎨 Creating GUI...")

    class MinimalRegistryGUI:
        def __init__(self):
            print("🏗️ Initializing GUI...")

            self.root = tk.Tk()
            self.root.title("Minimal Registry GUI")
            self.root.geometry("600x400")
            print("✅ Window created")

            # Try to initialize components
            try:
                print("📊 Initializing registry...")
                self.registry = get_registry()
                print("✅ Registry initialized")

                print("🛠️ Initializing template maker...")
                self.template_maker = EnhancedKrathongTemplateMaker()
                print("✅ Template maker initialized")

            except Exception as e:
                print(f"❌ Component initialization error: {e}")
                messagebox.showerror("Error", f"Failed to initialize: {e}")
                return

            # Create basic UI
            print("🎨 Setting up UI...")
            self.setup_ui()
            print("✅ UI setup complete")

        def setup_ui(self):
            # Main frame
            main_frame = ttk.Frame(self.root)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

            # Title
            title = ttk.Label(
                main_frame, text="🎯 Minimal Registry GUI", font=("Arial", 16, "bold")
            )
            title.pack(pady=10)

            # Status
            self.status_var = tk.StringVar(value="Ready")
            status_label = ttk.Label(main_frame, textvariable=self.status_var)
            status_label.pack(pady=5)

            # Test button
            def test_registry():
                try:
                    stats = self.registry.get_registry_stats()
                    self.status_var.set(
                        f"Registry: {stats['total_templates']} templates"
                    )
                except Exception as e:
                    self.status_var.set(f"Error: {e}")

            test_btn = ttk.Button(
                main_frame, text="Test Registry", command=test_registry
            )
            test_btn.pack(pady=10)

            # Close button
            close_btn = ttk.Button(main_frame, text="Close", command=self.root.destroy)
            close_btn.pack(pady=5)

        def run(self):
            print("🖥️ Starting mainloop...")

            # Auto-close after 15 seconds for testing
            self.root.after(15000, self.root.destroy)

            self.root.mainloop()
            print("👋 GUI closed")

    # Create and run GUI
    print("🚀 Creating GUI instance...")
    app = MinimalRegistryGUI()

    print("🏃 Running GUI...")
    app.run()

    print("✅ Program completed successfully")

except Exception as e:
    print(f"❌ Critical error: {e}")
    import traceback

    traceback.print_exc()
