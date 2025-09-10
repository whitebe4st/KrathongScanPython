"""
Admin GUI for managing templates and scanner database.
"""

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any, Dict, List, Optional

from database.models import TemplateData
from database.registry import LocalTemplateRegistry
from utils.config import Config
from utils.file_utils import FileUtils


class AdminGUI:
    """Admin GUI for template management."""

    def __init__(self):
        """Initialize admin GUI."""
        self.root = tk.Tk()
        self.root.title("Template Admin")
        self.root.geometry("1000x700")

        # Database connections
        self.scanner_db = LocalTemplateRegistry(Config.SCANNER_DB)
        self.file_utils = FileUtils()

        # Current template package
        self.current_metadata: Optional[Dict[str, Any]] = None
        self.current_package_dir: Optional[Path] = None

        self.setup_ui()

    def setup_ui(self):
        """Setup the user interface."""
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Title
        title_label = ttk.Label(
            main_frame, text="Template Admin", font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 20))

        # Template package selection
        package_frame = ttk.LabelFrame(main_frame, text="Template Package Management")
        package_frame.pack(fill=tk.X, pady=5)

        # Package selection
        selection_frame = ttk.Frame(package_frame)
        selection_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(
            selection_frame,
            text="Browse Template Package",
            command=self.browse_template_package,
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.package_path_var = tk.StringVar()
        ttk.Label(selection_frame, textvariable=self.package_path_var).pack(
            side=tk.LEFT
        )

        # Template preview and info
        preview_frame = ttk.LabelFrame(main_frame, text="Template Information")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Template info
        self.template_info = tk.Text(preview_frame, height=15, wrap=tk.WORD)
        self.template_info.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Action buttons
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=5)

        ttk.Button(
            action_frame, text="Add to Scanner", command=self.add_to_scanner
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            action_frame,
            text="View Scanner Templates",
            command=self.view_scanner_templates,
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            action_frame, text="Refresh Scanner DB", command=self.refresh_scanner_db
        ).pack(side=tk.LEFT, padx=5)

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(
            main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W
        )
        status_bar.pack(fill=tk.X, pady=(10, 0))

    def browse_template_package(self):
        """Browse for template package directory."""
        package_dir = filedialog.askdirectory(
            title="Select Template Package Directory",
            initialdir=str(Config.EXPORTS_DIR),
        )

        if package_dir:
            self.load_template_package(Path(package_dir))

    def load_template_package(self, package_dir: Path):
        """Load template package from directory."""
        try:
            self.status_var.set("Loading template package...")
            self.root.update()

            # Load metadata
            metadata_path = package_dir / "metadata.json"
            if not metadata_path.exists():
                messagebox.showerror("Error", "No metadata.json found in package")
                self.status_var.set("Error: No metadata.json found")
                return

            self.current_metadata = self.file_utils.load_json(metadata_path)
            if not self.current_metadata:
                messagebox.showerror("Error", "Failed to load metadata.json")
                self.status_var.set("Error: Failed to load metadata")
                return

            self.current_package_dir = package_dir
            self.package_path_var.set(str(package_dir))

            # Display template info
            self.display_template_info()

            self.status_var.set("Template package loaded successfully")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load template package: {e}")
            self.status_var.set(f"Error: {e}")

    def display_template_info(self):
        """Display template information."""
        if not self.current_metadata:
            return

        info_text = f"TEMPLATE PACKAGE INFORMATION\n"
        info_text += "=" * 50 + "\n\n"
        info_text += f"Template Name: {self.current_metadata['template_name']}\n"
        info_text += f"Marker IDs: {self.current_metadata['marker_ids']}\n"
        info_text += f"Template Size: {self.current_metadata['template_width']}x{self.current_metadata['template_height']}\n"
        info_text += f"Created: {self.current_metadata['created_at']}\n"
        info_text += f"Created By: {self.current_metadata['created_by']}\n"
        info_text += f"Version: {self.current_metadata.get('version', 'Unknown')}\n\n"

        info_text += "MARKER FILES:\n"
        for i, marker_file in enumerate(self.current_metadata["marker_files"]):
            info_text += f"  Marker {i+1}: {marker_file}\n"

        info_text += f"\nTEMPLATE FILE: {self.current_metadata['template_file']}\n"
        info_text += f"MASK FILE: {self.current_metadata['mask_file']}\n\n"

        # Check if template already exists in scanner
        existing = self.scanner_db.get_template_by_name(
            self.current_metadata["template_name"]
        )
        if existing:
            info_text += (
                "⚠️  WARNING: This template already exists in scanner database!\n"
            )
            info_text += f"   Last updated: {existing.updated_at}\n"
        else:
            info_text += "✅ Template is new and ready to be added to scanner\n"

        self.template_info.delete(1.0, tk.END)
        self.template_info.insert(1.0, info_text)

    def add_to_scanner(self):
        """Add template to scanner database."""
        if not self.current_metadata:
            messagebox.showerror("Error", "No template package loaded")
            return

        try:
            self.status_var.set("Adding template to scanner...")
            self.root.update()

            # Check if template already exists in scanner
            existing = self.scanner_db.get_template_by_name(
                self.current_metadata["template_name"]
            )
            if existing:
                if not messagebox.askyesno(
                    "Template Exists",
                    f"Template '{self.current_metadata['template_name']}' already exists in scanner. Overwrite?",
                ):
                    self.status_var.set("Operation cancelled")
                    return

            # Copy files to scanner directory
            scanner_template_dir = Config.SCANNER_TEMPLATES_DIR
            scanner_template_dir.mkdir(parents=True, exist_ok=True)

            # Copy template image
            template_src = (
                self.current_package_dir / self.current_metadata["template_file"]
            )
            template_dst = scanner_template_dir / self.current_metadata["template_file"]
            if not self.file_utils.copy_file(template_src, template_dst):
                raise Exception("Failed to copy template image")

            # Copy mask
            mask_src = self.current_package_dir / self.current_metadata["mask_file"]
            mask_dst = scanner_template_dir / self.current_metadata["mask_file"]
            if not self.file_utils.copy_file(mask_src, mask_dst):
                raise Exception("Failed to copy mask image")

            # Create template data
            template_data = TemplateData(
                name=self.current_metadata["template_name"],
                marker_ids=self.current_metadata["marker_ids"],
                image_path=str(template_dst),
                mask_path=str(mask_dst),
                template_width=self.current_metadata["template_width"],
                template_height=self.current_metadata["template_height"],
            )

            # Add to scanner database
            success = self.scanner_db.save_template(template_data)

            if success:
                messagebox.showinfo(
                    "Success",
                    f"Template '{self.current_metadata['template_name']}' added to scanner successfully!",
                )
                self.status_var.set("Template added to scanner successfully")
                # Refresh the display
                self.display_template_info()
            else:
                messagebox.showerror(
                    "Error", "Failed to add template to scanner database"
                )
                self.status_var.set("Error: Failed to add to database")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to add template to scanner: {e}")
            self.status_var.set(f"Error: {e}")

    def view_scanner_templates(self):
        """View all templates in scanner database."""
        try:
            templates = self.scanner_db.get_templates()

            # Create new window
            view_window = tk.Toplevel(self.root)
            view_window.title("Scanner Templates")
            view_window.geometry("800x500")

            # Create frame for treeview and buttons
            main_frame = ttk.Frame(view_window)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # Create treeview
            columns = ("name", "markers", "active", "created", "updated")
            tree = ttk.Treeview(main_frame, columns=columns, show="headings")

            # Define headings
            tree.heading("name", text="Template Name")
            tree.heading("markers", text="Marker IDs")
            tree.heading("active", text="Active")
            tree.heading("created", text="Created")
            tree.heading("updated", text="Updated")

            # Configure column widths
            tree.column("name", width=200)
            tree.column("markers", width=150)
            tree.column("active", width=80)
            tree.column("created", width=120)
            tree.column("updated", width=120)

            # Insert data
            for template in templates:
                tree.insert(
                    "",
                    "end",
                    values=(
                        template.name,
                        str(template.marker_ids),
                        "Yes" if template.is_active else "No",
                        template.created_at[:10] if template.created_at else "Unknown",
                        template.updated_at[:10] if template.updated_at else "Unknown",
                    ),
                )

            # Add scrollbar
            scrollbar = ttk.Scrollbar(
                main_frame, orient=tk.VERTICAL, command=tree.yview
            )
            tree.configure(yscrollcommand=scrollbar.set)

            # Pack treeview and scrollbar
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            # Add buttons
            button_frame = ttk.Frame(view_window)
            button_frame.pack(fill=tk.X, padx=10, pady=5)

            ttk.Button(
                button_frame,
                text="Delete Selected",
                command=lambda: self.delete_selected_template(tree),
            ).pack(side=tk.LEFT, padx=5)
            ttk.Button(
                button_frame,
                text="Toggle Active",
                command=lambda: self.toggle_template_active(tree),
            ).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Close", command=view_window.destroy).pack(
                side=tk.RIGHT, padx=5
            )

        except Exception as e:
            messagebox.showerror("Error", f"Failed to view scanner templates: {e}")

    def delete_selected_template(self, tree):
        """Delete selected template from scanner database."""
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a template to delete")
            return

        item = tree.item(selected[0])
        template_name = item["values"][0]

        if messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete template '{template_name}'?",
        ):
            try:
                success = self.scanner_db.delete_template(template_name)
                if success:
                    messagebox.showinfo(
                        "Success", f"Template '{template_name}' deleted successfully"
                    )
                    # Refresh the treeview
                    self.view_scanner_templates()
                else:
                    messagebox.showerror("Error", "Failed to delete template")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete template: {e}")

    def toggle_template_active(self, tree):
        """Toggle active status of selected template."""
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a template to toggle")
            return

        item = tree.item(selected[0])
        template_name = item["values"][0]

        try:
            template = self.scanner_db.get_template_by_name(template_name)
            if template:
                template.is_active = not template.is_active
                success = self.scanner_db.save_template(template)
                if success:
                    messagebox.showinfo(
                        "Success",
                        f"Template '{template_name}' {'activated' if template.is_active else 'deactivated'}",
                    )
                    # Refresh the treeview
                    self.view_scanner_templates()
                else:
                    messagebox.showerror("Error", "Failed to update template status")
            else:
                messagebox.showerror("Error", "Template not found")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to toggle template status: {e}")

    def refresh_scanner_db(self):
        """Refresh scanner database connection."""
        try:
            self.scanner_db = LocalTemplateRegistry(Config.SCANNER_DB)
            self.status_var.set("Scanner database refreshed")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh scanner database: {e}")
            self.status_var.set(f"Error: {e}")

    def run(self):
        """Run the admin GUI."""
        self.root.mainloop()
