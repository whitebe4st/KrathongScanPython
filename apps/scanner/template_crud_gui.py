"""
Template Management GUI for KrathongScanner CRUD System.

A simple GUI for managing custom templates with CRUD operations.
"""

import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import List, Optional

from apps.scanner.template_manager import TemplateManager
from database.models import TemplateData

# Import PNG metadata utilities
try:
    import sys
    from pathlib import Path

    # Add project root to path for import
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    from src.utils.png_metadata import extract_marker_ids, read_template_metadata

    PNG_METADATA_AVAILABLE = True
except ImportError as e:
    print(f"Warning: PNG metadata utilities not available: {e}")
    read_template_metadata = None
    extract_marker_ids = None
    PNG_METADATA_AVAILABLE = False


class TemplateManagementGUI:
    """Simple GUI for template CRUD operations."""

    def __init__(self, db_path: str = None):
        self.db_path = db_path
        self.manager = None
        self.root = tk.Tk()
        self.root.title("KrathongScanner - Template Management")
        self.root.geometry("900x600")

        # Initialize database connection
        self._initialize_database()

        self.setup_gui()
        self.refresh_template_list()

    def _initialize_database(self):
        """Initialize database connection with fallback to selection."""
        try:
            if self.db_path:
                # Use provided database path
                self.manager = TemplateManager(self.db_path)
                print(f"✅ Connected to database: {self.db_path}")
            else:
                # Try default database path
                default_db_path = (
                    Path(__file__).parent.parent.parent / "data" / "db" / "scanner.db"
                )
                if default_db_path.exists():
                    self.manager = TemplateManager(str(default_db_path))
                    self.db_path = str(default_db_path)
                    print(f"✅ Connected to default database: {default_db_path}")
                else:
                    # Show database selection dialog
                    self._show_database_selection()
        except Exception as e:
            print(f"❌ Database initialization error: {e}")
            self._show_database_selection()

    def _show_database_selection(self):
        """Show database selection dialog."""
        choice = messagebox.askyesnocancel(
            "Database Selection",
            "Scanner database not found!\n\n"
            "Would you like to:\n"
            "• Yes: Select existing database file\n"
            "• No: Create new database\n"
            "• Cancel: Exit program",
        )

        if choice is True:
            # Select existing database
            self._select_database_file()
        elif choice is False:
            # Create new database
            self._create_new_database()
        else:
            # Cancel - exit program
            print("❌ No database selected. Exiting...")
            self.root.destroy()
            exit(1)

    def _select_database_file(self):
        """Allow user to select an existing database file."""
        db_file = filedialog.askopenfilename(
            title="Select Scanner Database File",
            filetypes=[("SQLite Database", "*.db"), ("All Files", "*.*")],
            initialdir=str(Path(__file__).parent.parent.parent / "data" / "db"),
        )

        if db_file:
            try:
                self.manager = TemplateManager(db_file)
                self.db_path = db_file
                print(f"✅ Connected to selected database: {db_file}")

                # Update GUI
                self.db_label.config(text=Path(db_file).name)
                self.refresh_template_list()

                messagebox.showinfo(
                    "Success", f"Connected to database:\n{Path(db_file).name}"
                )
            except Exception as e:
                messagebox.showerror(
                    "Database Error", f"Failed to connect to database:\n{str(e)}"
                )

    def _create_new_database(self):
        """Create a new database file."""
        db_file = filedialog.asksaveasfilename(
            title="Create New Scanner Database",
            defaultextension=".db",
            filetypes=[("SQLite Database", "*.db"), ("All Files", "*.*")],
            initialdir=str(Path(__file__).parent.parent.parent / "data" / "db"),
            initialfile="scanner.db",
        )

        if db_file:
            try:
                # Create directory if it doesn't exist
                Path(db_file).parent.mkdir(parents=True, exist_ok=True)

                # Create new database
                self.manager = TemplateManager(db_file)
                self.db_path = db_file
                print(f"✅ Created new database: {db_file}")

                # Update GUI
                self.db_label.config(text=Path(db_file).name)
                self.refresh_template_list()

                messagebox.showinfo(
                    "Success", f"Created new database:\n{Path(db_file).name}"
                )
            except Exception as e:
                messagebox.showerror(
                    "Database Error", f"Failed to create database:\n{str(e)}"
                )

    def setup_gui(self):
        """Setup the GUI interface."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)  # Template list column
        main_frame.columnconfigure(1, weight=2)  # Details column (wider)
        main_frame.columnconfigure(2, weight=1)  # Database/Actions column
        main_frame.rowconfigure(1, weight=1)

        # Title
        title_label = ttk.Label(
            main_frame, text="🎯 Template Management System", font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # Left panel - Template list
        list_frame = ttk.LabelFrame(main_frame, text="📋 Templates", padding="10")
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)

        # Template listbox with scrollbar
        listbox_frame = ttk.Frame(list_frame)
        listbox_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        listbox_frame.rowconfigure(0, weight=1)
        listbox_frame.columnconfigure(0, weight=1)

        self.template_listbox = tk.Listbox(listbox_frame, height=15)
        self.template_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.template_listbox.bind("<<ListboxSelect>>", self.on_template_select)

        scrollbar = ttk.Scrollbar(
            listbox_frame, orient="vertical", command=self.template_listbox.yview
        )
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.template_listbox.configure(yscrollcommand=scrollbar.set)

        # Refresh button
        refresh_btn = ttk.Button(
            list_frame, text="🔄 Refresh", command=self.refresh_template_list
        )
        refresh_btn.grid(row=1, column=0, pady=(10, 0))

        # Middle panel - Template Details
        details_frame = ttk.LabelFrame(
            main_frame, text="📝 Template Details", padding="10"
        )
        details_frame.grid(
            row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 5)
        )
        details_frame.columnconfigure(1, weight=1)

        # Right panel - Database Management & Actions
        right_panel = ttk.Frame(main_frame)
        right_panel.grid(row=1, column=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))

        # Database management section
        db_frame = ttk.LabelFrame(right_panel, text="🗃️ Database", padding="10")
        db_frame.pack(fill=tk.X, pady=(0, 10))

        # Database status
        ttk.Label(db_frame, text="Connected to:", font=("Arial", 9, "bold")).pack(
            anchor=tk.W
        )
        self.db_label = ttk.Label(
            db_frame,
            text=Path(self.db_path).name if self.db_path else "No database",
            font=("Arial", 9),
            foreground="blue",
            wraplength=150,
        )
        self.db_label.pack(anchor=tk.W, pady=(2, 10))

        # Database controls
        ttk.Button(
            db_frame,
            text="Select Database",
            command=self._select_database_file,
            width=18,
        ).pack(fill=tk.X, pady=(0, 5))

        ttk.Button(
            db_frame,
            text="Create New Database",
            command=self._create_new_database,
            width=18,
        ).pack(fill=tk.X, pady=(0, 5))

        # Actions section
        actions_frame = ttk.LabelFrame(right_panel, text="⚡ Actions", padding="10")
        actions_frame.pack(fill=tk.X, pady=(0, 10))
        details_frame.columnconfigure(1, weight=1)

        # Template details
        ttk.Label(details_frame, text="Name:").grid(row=0, column=0, sticky=tk.W)
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(
            details_frame, textvariable=self.name_var, state="readonly"
        )
        self.name_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0))

        ttk.Label(details_frame, text="Marker IDs:").grid(
            row=1, column=0, sticky=tk.W, pady=(10, 0)
        )
        self.markers_var = tk.StringVar()
        self.markers_entry = ttk.Entry(
            details_frame, textvariable=self.markers_var, state="readonly"
        )
        self.markers_entry.grid(
            row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=(10, 0)
        )

        ttk.Label(details_frame, text="Image File:").grid(
            row=2, column=0, sticky=tk.W, pady=(10, 0)
        )
        self.image_var = tk.StringVar()
        self.image_entry = ttk.Entry(
            details_frame, textvariable=self.image_var, state="readonly"
        )
        self.image_entry.grid(
            row=2, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=(10, 0)
        )

        ttk.Label(details_frame, text="Mask File:").grid(
            row=3, column=0, sticky=tk.W, pady=(10, 0)
        )
        self.mask_var = tk.StringVar()
        self.mask_entry = ttk.Entry(
            details_frame, textvariable=self.mask_var, state="readonly"
        )
        self.mask_entry.grid(
            row=3, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=(10, 0)
        )

        ttk.Label(details_frame, text="Status:").grid(
            row=4, column=0, sticky=tk.W, pady=(10, 0)
        )
        self.status_var = tk.StringVar()
        self.status_entry = ttk.Entry(
            details_frame, textvariable=self.status_var, state="readonly"
        )
        self.status_entry.grid(
            row=4, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=(10, 0)
        )

        # Import from metadata
        import_btn = ttk.Button(
            actions_frame, text="📥 Import from Metadata", command=self.import_template
        )
        import_btn.pack(fill=tk.X, pady=(0, 5))

        # Create new template
        create_btn = ttk.Button(
            actions_frame, text="➕ Create New Template", command=self.create_template
        )
        create_btn.pack(fill=tk.X, pady=(0, 5))

        # Toggle active status
        self.toggle_btn = ttk.Button(
            actions_frame, text="🔄 Toggle Active", command=self.toggle_template_status
        )
        self.toggle_btn.pack(fill=tk.X, pady=(0, 5))

        # Delete template
        self.delete_btn = ttk.Button(
            actions_frame, text="🗑️ Delete Template", command=self.delete_template
        )
        self.delete_btn.pack(fill=tk.X, pady=(0, 5))

        # Separator
        ttk.Separator(actions_frame, orient="horizontal").pack(fill=tk.X, pady=(10, 10))

        # Statistics
        stats_btn = ttk.Button(
            actions_frame, text="📊 View Statistics", command=self.show_statistics
        )
        stats_btn.pack(fill=tk.X, pady=(0, 5))

        # Available markers
        markers_btn = ttk.Button(
            actions_frame,
            text="🎯 Available Markers",
            command=self.show_available_markers,
        )
        markers_btn.pack(fill=tk.X, pady=(0, 5))

        # Initially disable action buttons
        self.toggle_btn.config(state="disabled")
        self.delete_btn.config(state="disabled")

    def refresh_template_list(self):
        """Refresh the template list."""
        self.template_listbox.delete(0, tk.END)

        # Add hardcoded templates (read-only)
        hardcoded = [
            "krathong1 (Traditional) - [0,1,2,3] - HARDCODED",
            "krathong2 (Modern) - [4,5,6,7] - HARDCODED",
            "krathong3 (Lotus) - [8,9,10,11] - HARDCODED",
            "krathong4 (Royal) - [12,13,14,15] - HARDCODED",
            "krathong5 (Children) - [16,17,18,19] - HARDCODED",
        ]

        for template in hardcoded:
            self.template_listbox.insert(tk.END, template)

        # Add custom templates
        custom_templates = self.manager.read_all_templates(include_inactive=True)
        for template in custom_templates:
            status = "ACTIVE" if template.is_active else "INACTIVE"
            display_text = f"{template.name} - {template.marker_ids} - {status}"
            self.template_listbox.insert(tk.END, display_text)

    def on_template_select(self, event):
        """Handle template selection."""
        selection = self.template_listbox.curselection()
        if not selection:
            self.clear_details()
            return

        index = selection[0]
        selected_text = self.template_listbox.get(index)

        # Check if it's a hardcoded template
        if "HARDCODED" in selected_text:
            self.show_hardcoded_details(selected_text)
            self.toggle_btn.config(state="disabled")
            self.delete_btn.config(state="disabled")
        else:
            # Custom template
            template_name = selected_text.split(" - ")[0]
            template = self.manager.read_template(template_name)
            if template:
                self.show_template_details(template)
                self.toggle_btn.config(state="normal")
                self.delete_btn.config(state="normal")

    def show_hardcoded_details(self, display_text: str):
        """Show details for hardcoded templates."""
        parts = display_text.split(" - ")
        name = parts[0]
        markers = parts[1]

        self.name_var.set(name)
        self.markers_var.set(markers)
        self.image_var.set("Built-in template")
        self.mask_var.set("Built-in mask")
        self.status_var.set("HARDCODED (Read-only)")

    def show_template_details(self, template: TemplateData):
        """Show details for a custom template."""
        self.name_var.set(template.name)
        self.markers_var.set(str(template.marker_ids))
        self.image_var.set(Path(template.image_path).name)
        self.mask_var.set(Path(template.mask_path).name)
        self.status_var.set("ACTIVE" if template.is_active else "INACTIVE")

    def clear_details(self):
        """Clear the details panel."""
        self.name_var.set("")
        self.markers_var.set("")
        self.image_var.set("")
        self.mask_var.set("")
        self.status_var.set("")
        self.toggle_btn.config(state="disabled")
        self.delete_btn.config(state="disabled")

    def import_template(self):
        """Import template from metadata file."""
        metadata_file = filedialog.askopenfilename(
            title="Select Template Metadata File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )

        if not metadata_file:
            return

        success = self.manager.import_template_from_metadata(metadata_file)
        if success:
            messagebox.showinfo("Success", "Template imported successfully!")
            self.refresh_template_list()
        else:
            messagebox.showerror(
                "Error", "Failed to import template. Check console for details."
            )

    def create_template(self):
        """Create a new template manually."""
        dialog = CreateTemplateDialog(self.root, self.manager)
        if dialog.result:
            self.refresh_template_list()

    def toggle_template_status(self):
        """Toggle template active status."""
        selection = self.template_listbox.curselection()
        if not selection:
            return

        selected_text = self.template_listbox.get(selection[0])
        if "HARDCODED" in selected_text:
            return

        template_name = selected_text.split(" - ")[0]
        template = self.manager.read_template(template_name)
        if not template:
            return

        new_status = not template.is_active
        success = self.manager.update_template(template_name, is_active=new_status)

        if success:
            status_text = "activated" if new_status else "deactivated"
            messagebox.showinfo("Success", f"Template {status_text} successfully!")
            self.refresh_template_list()
        else:
            messagebox.showerror("Error", "Failed to update template status.")

    def delete_template(self):
        """Delete a template."""
        selection = self.template_listbox.curselection()
        if not selection:
            return

        selected_text = self.template_listbox.get(selection[0])
        if "HARDCODED" in selected_text:
            return

        template_name = selected_text.split(" - ")[0]

        result = messagebox.askyesnocancel(
            "Delete Template",
            f"Delete template '{template_name}'?\n\n"
            "Click 'Yes' to delete from database only\n"
            "Click 'No' to delete database entry and files\n"
            "Click 'Cancel' to abort",
        )

        if result is None:  # Cancel
            return

        delete_files = (
            not result
        )  # Yes = False (don't delete files), No = True (delete files)
        success = self.manager.delete_template(template_name, delete_files=delete_files)

        if success:
            files_text = " and files" if delete_files else ""
            messagebox.showinfo(
                "Success", f"Template deleted{files_text} successfully!"
            )
            self.refresh_template_list()
            self.clear_details()
        else:
            messagebox.showerror("Error", "Failed to delete template.")

    def show_statistics(self):
        """Show template system statistics."""
        stats = self.manager.get_statistics()

        stats_text = "📊 Template System Statistics\n\n"
        for key, value in stats.items():
            formatted_key = key.replace("_", " ").title()
            stats_text += f"{formatted_key}: {value}\n"

        messagebox.showinfo("Statistics", stats_text)

    def show_available_markers(self):
        """Show available marker IDs."""
        available = self.manager.get_available_marker_ids()

        if available:
            marker_text = f"🎯 Available Marker IDs ({len(available)} total):\n\n"
            marker_text += ", ".join(map(str, available[:20]))  # Show first 20
            if len(available) > 20:
                marker_text += f"\n... and {len(available) - 20} more"
        else:
            marker_text = (
                "❌ No marker IDs available!\n\nAll markers (20-49) are in use."
            )

        messagebox.showinfo("Available Markers", marker_text)

    def run(self):
        """Run the GUI."""
        self.root.mainloop()


class CreateTemplateDialog:
    """Dialog for creating a new template."""

    def __init__(self, parent, manager: TemplateManager):
        self.manager = manager
        self.result = False

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Create New Template")
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.setup_dialog()

    def setup_dialog(self):
        """Setup the dialog interface."""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        ttk.Label(
            main_frame, text="➕ Create New Template", font=("Arial", 14, "bold")
        ).pack(pady=(0, 20))

        # Template name
        ttk.Label(main_frame, text="Template Name:").pack(anchor=tk.W)
        self.name_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.name_var, width=50).pack(
            fill=tk.X, pady=(5, 15)
        )

        # Template file
        ttk.Label(main_frame, text="Template Image File:").pack(anchor=tk.W)
        template_frame = ttk.Frame(main_frame)
        template_frame.pack(fill=tk.X, pady=(5, 15))

        self.template_var = tk.StringVar()
        ttk.Entry(template_frame, textvariable=self.template_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )
        ttk.Button(template_frame, text="Browse", command=self.browse_template).pack(
            side=tk.RIGHT, padx=(10, 0)
        )

        # Read Metadata button temporarily disabled — comment out to avoid showing in CRUD GUI
        # The code is kept here for easy re-enabling in future if desired.
        # if PNG_METADATA_AVAILABLE:
        #     ttk.Button(template_frame, text="Read Metadata", command=self.read_template_metadata).pack(
        #         side=tk.RIGHT, padx=(5, 0)
        #     )

        # Mask file
        ttk.Label(main_frame, text="Mask File:").pack(anchor=tk.W)
        mask_frame = ttk.Frame(main_frame)
        mask_frame.pack(fill=tk.X, pady=(5, 15))

        self.mask_var = tk.StringVar()
        ttk.Entry(mask_frame, textvariable=self.mask_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )
        ttk.Button(mask_frame, text="Browse", command=self.browse_mask).pack(
            side=tk.RIGHT, padx=(10, 0)
        )

        # Marker IDs (optional)
        ttk.Label(
            main_frame, text="Marker IDs (optional, leave blank for auto-assign):"
        ).pack(anchor=tk.W)
        self.markers_var = tk.StringVar()
        markers_entry = ttk.Entry(main_frame, textvariable=self.markers_var, width=50)
        markers_entry.pack(fill=tk.X, pady=(5, 5))

        ttk.Label(
            main_frame,
            text="Format: 20,21,22,23 (4 numbers separated by commas)",
            font=("Arial", 8),
        ).pack(anchor=tk.W, pady=(0, 15))

        # Available markers info
        available = self.manager.get_available_marker_ids()
        if available:
            info_text = f"Available markers: {', '.join(map(str, available[:10]))}"
            if len(available) > 10:
                info_text += f" ... (+{len(available) - 10} more)"
        else:
            info_text = "No markers available!"

        ttk.Label(
            main_frame, text=info_text, font=("Arial", 8), foreground="blue"
        ).pack(anchor=tk.W, pady=(0, 20))

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)

        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(
            side=tk.RIGHT, padx=(10, 0)
        )
        ttk.Button(button_frame, text="Create", command=self.create).pack(side=tk.RIGHT)

    def browse_template(self):
        """Browse for template file."""
        filename = filedialog.askopenfilename(
            title="Select Template Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg"), ("All files", "*.*")],
        )
        if filename:
            self.template_var.set(filename)

            # 🎯 Try to read metadata from PNG and auto-populate fields
            if PNG_METADATA_AVAILABLE and filename.lower().endswith(".png"):
                try:
                    metadata = read_template_metadata(filename)
                    if metadata:
                        print(f"✅ Found embedded metadata in {Path(filename).name}")

                        # Auto-populate template name if not set
                        if (
                            not self.name_var.get().strip()
                            and "template_name" in metadata
                        ):
                            self.name_var.set(metadata["template_name"])
                            print(
                                f"   Auto-populated name: {metadata['template_name']}"
                            )

                        # Auto-populate marker IDs if not set
                        if (
                            not self.markers_var.get().strip()
                            and "marker_ids" in metadata
                        ):
                            marker_ids_str = ",".join(map(str, metadata["marker_ids"]))
                            self.markers_var.set(marker_ids_str)
                            print(f"   Auto-populated markers: {marker_ids_str}")

                        # Auto-populate mask file if available and exists
                        if not self.mask_var.get().strip() and "mask_path" in metadata:
                            mask_path = metadata["mask_path"]
                            if mask_path and Path(mask_path).exists():
                                self.mask_var.set(mask_path)
                                print(f"   Auto-populated mask: {Path(mask_path).name}")
                            elif mask_path:
                                # Try relative to template file directory
                                template_dir = Path(filename).parent
                                relative_mask = template_dir / Path(mask_path).name
                                if relative_mask.exists():
                                    self.mask_var.set(str(relative_mask))
                                    print(
                                        f"   Auto-populated mask (relative): {relative_mask.name}"
                                    )

                        # Show info message about auto-population
                        messagebox.showinfo(
                            "Metadata Found",
                            f"Auto-populated fields from embedded metadata:\n"
                            f"• Template: {metadata.get('template_name', 'N/A')}\n"
                            f"• Marker IDs: {metadata.get('marker_ids', 'N/A')}\n"
                            f"• Version: {metadata.get('version', 'N/A')}",
                        )
                    else:
                        print(f"ℹ️ No embedded metadata found in {Path(filename).name}")
                except Exception as e:
                    print(f"⚠️ Error reading metadata from {filename}: {e}")
            elif not PNG_METADATA_AVAILABLE:
                print("ℹ️ PNG metadata reading not available")

    def browse_mask(self):
        """Browse for mask file."""
        filename = filedialog.askopenfilename(
            title="Select Mask File",
            filetypes=[("Image files", "*.png *.jpg *.jpeg"), ("All files", "*.*")],
        )
        if filename:
            self.mask_var.set(filename)

    def read_template_metadata(self):
        """Read metadata from currently selected template file."""
        if not PNG_METADATA_AVAILABLE:
            messagebox.showwarning(
                "Feature Unavailable", "PNG metadata reading is not available."
            )
            return

        template_file = self.template_var.get().strip()
        if not template_file:
            messagebox.showwarning(
                "No File Selected", "Please select a template file first."
            )
            return

        if not Path(template_file).exists():
            messagebox.showerror(
                "File Not Found", f"Template file not found:\n{template_file}"
            )
            return

        if not template_file.lower().endswith(".png"):
            messagebox.showinfo(
                "PNG Required", "Metadata reading is only supported for PNG files."
            )
            return

        try:
            metadata = read_template_metadata(template_file)
            if metadata:
                # Ask user what to do with the metadata
                response = messagebox.askyesnocancel(
                    "Metadata Found",
                    f"Found embedded metadata in template:\n\n"
                    f"• Template: {metadata.get('template_name', 'N/A')}\n"
                    f"• Marker IDs: {metadata.get('marker_ids', 'N/A')}\n"
                    f"• Version: {metadata.get('version', 'N/A')}\n"
                    f"• Created: {metadata.get('created_date', 'N/A')}\n\n"
                    f"Auto-populate fields with this metadata?\n\n"
                    f"Yes = Auto-populate\n"
                    f"No = Show details only\n"
                    f"Cancel = Close",
                )

                if response is True:  # Yes - auto-populate
                    # Auto-populate template name if not set or user confirms
                    if "template_name" in metadata:
                        current_name = self.name_var.get().strip()
                        if not current_name or messagebox.askyesno(
                            "Update Name",
                            f"Replace current name '{current_name}' with '{metadata['template_name']}'?",
                        ):
                            self.name_var.set(metadata["template_name"])

                    # Auto-populate marker IDs if not set or user confirms
                    if "marker_ids" in metadata:
                        current_markers = self.markers_var.get().strip()
                        new_markers = ",".join(map(str, metadata["marker_ids"]))
                        if not current_markers or messagebox.askyesno(
                            "Update Markers",
                            f"Replace current markers '{current_markers}' with '{new_markers}'?",
                        ):
                            self.markers_var.set(new_markers)

                    # Auto-populate mask file if available
                    if "mask_path" in metadata and metadata["mask_path"]:
                        mask_path = metadata["mask_path"]
                        if Path(mask_path).exists():
                            current_mask = self.mask_var.get().strip()
                            if not current_mask or messagebox.askyesno(
                                "Update Mask",
                                f"Set mask file to '{Path(mask_path).name}'?",
                            ):
                                self.mask_var.set(mask_path)
                        else:
                            # Try relative to template file
                            template_dir = Path(template_file).parent
                            relative_mask = template_dir / Path(mask_path).name
                            if relative_mask.exists():
                                current_mask = self.mask_var.get().strip()
                                if not current_mask or messagebox.askyesno(
                                    "Update Mask",
                                    f"Set mask file to '{relative_mask.name}'?",
                                ):
                                    self.mask_var.set(str(relative_mask))

                    messagebox.showinfo("Success", "Fields updated with metadata!")

                elif response is False:  # No - show details only
                    # Show detailed metadata in a new window
                    self._show_metadata_details(metadata, template_file)

            else:
                messagebox.showinfo(
                    "No Metadata",
                    f"No KrathongScanner metadata found in:\n{Path(template_file).name}",
                )

        except Exception as e:
            messagebox.showerror("Error", f"Failed to read metadata:\n{str(e)}")

    def _show_metadata_details(self, metadata, template_file):
        """Show detailed metadata in a popup window."""
        details_window = tk.Toplevel(self.root)
        details_window.title("Template Metadata Details")
        details_window.geometry("500x400")
        details_window.transient(self.root)
        details_window.grab_set()

        # Create scrollable text widget
        frame = ttk.Frame(details_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        text_widget = tk.Text(frame, wrap=tk.WORD, font=("Courier", 10))
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)

        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Format metadata for display
        content = f"Template Metadata Details\n"
        content += f"File: {Path(template_file).name}\n"
        content += f"{'='*50}\n\n"

        for key, value in metadata.items():
            content += f"{key.replace('_', ' ').title()}: {value}\n"

        text_widget.insert(tk.END, content)
        text_widget.config(state=tk.DISABLED)

        # Close button
        ttk.Button(details_window, text="Close", command=details_window.destroy).pack(
            pady=10
        )

    def create(self):
        """Create the template."""
        name = self.name_var.get().strip()
        template_file = self.template_var.get().strip()
        mask_file = self.mask_var.get().strip()
        markers_text = self.markers_var.get().strip()

        # Validate inputs
        if not name:
            messagebox.showerror("Error", "Please enter a template name")
            return

        if not template_file or not Path(template_file).exists():
            messagebox.showerror("Error", "Please select a valid template file")
            return

        if not mask_file or not Path(mask_file).exists():
            messagebox.showerror("Error", "Please select a valid mask file")
            return

        # Parse marker IDs
        marker_ids = None
        if markers_text:
            try:
                marker_ids = [int(x.strip()) for x in markers_text.split(",")]
                if len(marker_ids) != 4:
                    raise ValueError("Must have exactly 4 marker IDs")
            except ValueError as e:
                messagebox.showerror("Error", f"Invalid marker IDs: {e}")
                return

        # Create template
        success = self.manager.create_template(
            name=name,
            template_file=template_file,
            mask_file=mask_file,
            marker_ids=marker_ids,
        )

        if success:
            messagebox.showinfo("Success", "Template created successfully!")
            self.result = True
            self.dialog.destroy()
        else:
            messagebox.showerror(
                "Error", "Failed to create template. Check console for details."
            )

    def cancel(self):
        """Cancel the dialog."""
        self.dialog.destroy()


if __name__ == "__main__":
    # Run the template management GUI
    app = TemplateManagementGUI()
    app.run()
