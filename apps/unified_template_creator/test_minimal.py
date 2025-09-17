#!/usr/bin/env python3
"""
Unified Template Creator - Minimal Test Version

This is a simplified test version to validate the unified template creation concept.
"""

import logging
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Test imports
try:
    from apps.scanner.template_manager import TemplateManager
    from database.models import TemplateData

    print("✅ Core imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


class MinimalUnifiedTemplateCreator:
    """Minimal version for testing the unified concept."""

    def __init__(self):
        # Initialize backend
        try:
            self.template_manager = TemplateManager()
            print("✅ Template Manager initialized")
        except Exception as e:
            print(f"❌ Template Manager error: {e}")
            return

        # Create UI
        self.root = tk.Tk()
        self.root.title("🎯 Unified Template Creator (Test)")
        self.root.geometry("800x600")

        self.setup_ui()

    def setup_ui(self):
        """Setup minimal test UI."""
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title = ttk.Label(
            main_frame, text="🎯 Unified Template Creator", font=("Arial", 16, "bold")
        )
        title.pack(pady=(0, 20))

        # Description
        desc = ttk.Label(
            main_frame,
            text="Test version demonstrating unified template creation workflow\nwith integrated database storage.",
            justify=tk.CENTER,
        )
        desc.pack(pady=(0, 30))

        # Template name
        name_frame = ttk.Frame(main_frame)
        name_frame.pack(fill=tk.X, pady=(0, 20))

        ttk.Label(name_frame, text="Template Name:").pack(side=tk.LEFT)
        self.name_var = tk.StringVar(value="test_template")
        ttk.Entry(name_frame, textvariable=self.name_var, width=30).pack(
            side=tk.LEFT, padx=(10, 0)
        )

        # Action buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=20)

        ttk.Button(
            btn_frame, text="📋 List Templates", command=self.list_templates
        ).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(
            btn_frame, text="🧪 Create Test Template", command=self.create_test_template
        ).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(
            btn_frame, text="📊 Show Statistics", command=self.show_statistics
        ).pack(side=tk.LEFT)

        # Status area
        self.status_text = tk.Text(main_frame, height=15, width=80)
        self.status_text.pack(fill=tk.BOTH, expand=True, pady=(20, 0))

        # Scrollbar for status
        scrollbar = ttk.Scrollbar(
            main_frame, orient="vertical", command=self.status_text.yview
        )
        scrollbar.pack(side="right", fill="y")
        self.status_text.configure(yscrollcommand=scrollbar.set)

        # Initial status
        self.log("🚀 Unified Template Creator initialized")
        self.log("💾 Database connection successful")
        self.log("Ready for template creation operations...")

    def log(self, message):
        """Add message to status log."""
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.see(tk.END)
        self.root.update()
        print(message)

    def list_templates(self):
        """List all existing templates."""
        try:
            self.log("\n📋 Listing all templates...")
            templates = self.template_manager.read_all_templates()

            if not templates:
                self.log("No templates found in database.")
            else:
                self.log(f"Found {len(templates)} templates:")
                for i, template in enumerate(templates, 1):
                    self.log(f"  {i}. {template.name} (markers: {template.marker_ids})")
        except Exception as e:
            self.log(f"❌ Error listing templates: {e}")

    def create_test_template(self):
        """Create a test template to validate the workflow."""
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Error", "Please enter a template name")
            return

        try:
            self.log(f"\n🧪 Creating test template: {name}")

            # Check if template exists
            existing = self.template_manager.read_template(name)
            if existing:
                if not messagebox.askyesno(
                    "Confirm", f"Template '{name}' exists. Overwrite?"
                ):
                    return
                self.log(f"⚠️ Overwriting existing template: {name}")

            # Create minimal test files
            temp_dir = Path("temp")
            temp_dir.mkdir(exist_ok=True)

            # Create dummy template and mask files for testing
            import cv2
            import numpy as np

            # Create test template image (simple colored rectangle)
            test_image = np.zeros((720, 1270, 3), dtype=np.uint8)
            test_image[:] = (100, 150, 200)  # Light blue background
            cv2.rectangle(
                test_image, (100, 100), (1170, 620), (50, 200, 50), -1
            )  # Green template area
            cv2.putText(
                test_image,
                f"TEST: {name}",
                (400, 400),
                cv2.FONT_HERSHEY_SIMPLEX,
                2,
                (255, 255, 255),
                3,
            )

            # Create test mask (white rectangle on black background)
            test_mask = np.zeros((720, 1270), dtype=np.uint8)
            cv2.rectangle(test_mask, (100, 100), (1170, 620), 255, -1)

            # Save test files
            template_file = temp_dir / f"{name}_template.png"
            mask_file = temp_dir / f"{name}_mask.png"

            cv2.imwrite(str(template_file), test_image)
            cv2.imwrite(str(mask_file), test_mask)

            self.log(f"📁 Created test files:")
            self.log(f"  Template: {template_file}")
            self.log(f"  Mask: {mask_file}")

            # Get available marker IDs
            marker_ids = self.template_manager.get_next_available_markers()
            if not marker_ids:
                self.log("❌ No available marker IDs")
                return

            self.log(f"🎯 Assigned marker IDs: {marker_ids}")

            # Create template in database
            self.log("💾 Saving to database...")
            success = self.template_manager.create_template(
                name=name,
                template_file=str(template_file),
                mask_file=str(mask_file),
                marker_ids=marker_ids,
                template_width=1270,
                template_height=720,
            )

            if success:
                self.log(f"✅ Template '{name}' created successfully!")
                self.log("🎯 Template is now available to scanner!")

                # Show success dialog
                messagebox.showinfo(
                    "Success",
                    f"✅ Template '{name}' created successfully!\n\n"
                    f"• Saved to database (scanner.db)\n"
                    f"• Marker IDs: {marker_ids}\n"
                    f"• Template is scanner-ready!",
                )
            else:
                self.log(f"❌ Failed to create template '{name}'")
                messagebox.showerror("Error", f"Failed to create template '{name}'")

        except Exception as e:
            self.log(f"❌ Error creating test template: {e}")
            messagebox.showerror("Error", f"Error creating template: {e}")

    def show_statistics(self):
        """Show template system statistics."""
        try:
            self.log("\n📊 Template System Statistics:")
            stats = self.template_manager.get_statistics()

            for key, value in stats.items():
                self.log(f"  {key}: {value}")

            # Available markers
            available = self.template_manager.get_available_marker_ids()
            self.log(
                f"\n🎯 Available marker IDs: {available[:10]}{'...' if len(available) > 10 else ''}"
            )

        except Exception as e:
            self.log(f"❌ Error getting statistics: {e}")

    def run(self):
        """Run the application."""
        try:
            self.root.mainloop()
        except Exception as e:
            print(f"❌ Application error: {e}")


def main():
    """Main entry point."""
    print("🚀 Starting Unified Template Creator (Test Version)...")

    app = MinimalUnifiedTemplateCreator()
    app.run()

    print("✅ Application closed")


if __name__ == "__main__":
    main()
