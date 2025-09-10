import json
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from enhanced_template_maker import EnhancedKrathongTemplateMaker
from template_registry import get_registry


class ProfessionalRegistryGUI:
    def __init__(self):
        print("Initializing Professional Registry Template GUI...")

        self.root = tk.Tk()
        self.root.title("Professional Krathong Template Maker")
        self.root.geometry("900x700")
        self.root.resizable(True, True)

        try:
            print("Initializing template maker...")
            self.template_maker = EnhancedKrathongTemplateMaker()
            print("Initializing registry...")
            self.registry = get_registry()
            print("Components initialized successfully")
        except Exception as e:
            print(f"Initialization error: {e}")
            messagebox.showerror("Error", f"Failed to initialize: {e}")
            sys.exit(1)

        self.template_name_var = tk.StringVar(value="")
        self.client_name_var = tk.StringVar(value="")
        self.output_dir_var = tk.StringVar(value="data/templates")
        self.auto_assign_ids_var = tk.BooleanVar(value=True)
        self.status_var = tk.StringVar(value="Ready to create professional templates")

        print("Setting up professional UI...")
        self.setup_professional_ui()
        print("Loading registry stats...")
        self.update_registry_stats()
        print("Professional GUI ready")

    def setup_professional_ui(self):
        main_canvas = tk.Canvas(self.root)
        scrollbar = ttk.Scrollbar(
            self.root, orient="vertical", command=main_canvas.yview
        )
        scrollable_frame = ttk.Frame(main_canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all")),
        )

        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)

        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        content_frame = ttk.Frame(scrollable_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.create_header_section(content_frame)
        self.create_client_section(content_frame)
        self.create_template_section(content_frame)
        self.create_stats_section(content_frame)
        self.create_actions_section(content_frame)
        self.create_status_bar(content_frame)

    def create_header_section(self, parent):
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(0, 20))

        title_label = ttk.Label(
            header_frame,
            text="Professional Krathong Template Maker",
            font=("Arial", 18, "bold"),
        )
        title_label.pack()

        subtitle_label = ttk.Label(
            header_frame,
            text="Advanced Template Creation with Registry Integration",
            font=("Arial", 11, "italic"),
        )
        subtitle_label.pack(pady=(5, 0))

    def create_client_section(self, parent):
        client_frame = ttk.LabelFrame(parent, text="Client Information", padding=20)
        client_frame.pack(fill=tk.X, pady=10)

        client_row = ttk.Frame(client_frame)
        client_row.pack(fill=tk.X, pady=5)

        ttk.Label(client_row, text="Client Name:", font=("Arial", 11, "bold")).pack(
            side=tk.LEFT
        )
        client_entry = ttk.Entry(
            client_row, textvariable=self.client_name_var, width=40, font=("Arial", 11)
        )
        client_entry.pack(side=tk.LEFT, padx=(10, 0))
        client_entry.bind("<KeyRelease>", self.on_client_name_change)

        template_row = ttk.Frame(client_frame)
        template_row.pack(fill=tk.X, pady=5)

        ttk.Label(template_row, text="Template Name:", font=("Arial", 11, "bold")).pack(
            side=tk.LEFT
        )
        template_entry = ttk.Entry(
            template_row,
            textvariable=self.template_name_var,
            width=40,
            font=("Arial", 11),
        )
        template_entry.pack(side=tk.LEFT, padx=(10, 0))

        suggest_btn = ttk.Button(
            template_row, text="Auto-Suggest", command=self.suggest_template_name
        )
        suggest_btn.pack(side=tk.LEFT, padx=(10, 0))

    def create_template_section(self, parent):
        template_frame = ttk.LabelFrame(
            parent, text="Template Configuration", padding=20
        )
        template_frame.pack(fill=tk.X, pady=10)

        auto_frame = ttk.Frame(template_frame)
        auto_frame.pack(fill=tk.X, pady=5)

        auto_check = ttk.Checkbutton(
            auto_frame,
            text="Auto-assign unique ArUco marker IDs (Recommended)",
            variable=self.auto_assign_ids_var,
            command=self.on_auto_assign_change,
        )
        auto_check.pack(side=tk.LEFT)

        self.next_ids_label = ttk.Label(
            template_frame,
            text="Next available IDs: [0, 1, 2, 3]",
            foreground="green",
            font=("Arial", 11, "bold"),
        )
        self.next_ids_label.pack(anchor=tk.W, pady=(10, 0))

        output_frame = ttk.Frame(template_frame)
        output_frame.pack(fill=tk.X, pady=(15, 5))

        ttk.Label(
            output_frame, text="Output Directory:", font=("Arial", 11, "bold")
        ).pack(side=tk.LEFT)
        output_entry = ttk.Entry(
            output_frame, textvariable=self.output_dir_var, width=40, font=("Arial", 11)
        )
        output_entry.pack(side=tk.LEFT, padx=(10, 0))

        browse_btn = ttk.Button(
            output_frame, text="Browse", command=self.browse_output_directory
        )
        browse_btn.pack(side=tk.LEFT, padx=(10, 0))

    def create_stats_section(self, parent):
        stats_frame = ttk.LabelFrame(parent, text="Registry Statistics", padding=20)
        stats_frame.pack(fill=tk.X, pady=10)

        self.stats_text = tk.Text(
            stats_frame,
            height=6,
            width=70,
            font=("Courier", 10),
            state=tk.DISABLED,
            wrap=tk.WORD,
        )
        self.stats_text.pack(fill=tk.X)

        stats_btn_frame = ttk.Frame(stats_frame)
        stats_btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(
            stats_btn_frame, text="Refresh Stats", command=self.update_registry_stats
        ).pack(side=tk.LEFT)

        ttk.Button(
            stats_btn_frame,
            text="View All Templates",
            command=self.show_template_browser,
        ).pack(side=tk.LEFT, padx=(10, 0))

        ttk.Button(
            stats_btn_frame, text="Export Registry", command=self.export_registry
        ).pack(side=tk.LEFT, padx=(10, 0))

    def create_actions_section(self, parent):
        actions_frame = ttk.LabelFrame(parent, text="Template Actions", padding=20)
        actions_frame.pack(fill=tk.X, pady=10)

        main_btn_frame = ttk.Frame(actions_frame)
        main_btn_frame.pack(fill=tk.X)

        create_btn = ttk.Button(
            main_btn_frame,
            text="Create Professional Template",
            command=self.create_template,
            style="Accent.TButton",
        )
        create_btn.pack(side=tk.LEFT, padx=(0, 15))

        ttk.Button(
            main_btn_frame, text="Preview Template", command=self.preview_template
        ).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(
            main_btn_frame, text="Validate Settings", command=self.validate_settings
        ).pack(side=tk.LEFT, padx=(0, 10))

        util_frame = ttk.Frame(main_btn_frame)
        util_frame.pack(side=tk.RIGHT)

        ttk.Button(util_frame, text="Reset Form", command=self.reset_form).pack(
            side=tk.RIGHT, padx=(10, 0)
        )

        ttk.Button(util_frame, text="Help", command=self.show_help).pack(side=tk.RIGHT)

    def create_status_bar(self, parent):
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, pady=(20, 0))

        self.status_label = ttk.Label(
            status_frame,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            font=("Arial", 10),
        )
        self.status_label.pack(fill=tk.X)

    def on_client_name_change(self, event=None):
        if not self.template_name_var.get():
            try:
                suggested = self.template_maker.suggest_template_name(
                    self.client_name_var.get()
                )
                self.template_name_var.set(suggested)
            except:
                pass

    def suggest_template_name(self):
        try:
            client_name = self.client_name_var.get()
            if not client_name:
                messagebox.showwarning(
                    "Input Required", "Please enter a client name first."
                )
                return

            suggested = self.template_maker.suggest_template_name(client_name)
            self.template_name_var.set(suggested)
            self.status_var.set(f"Suggested template name: {suggested}")
        except Exception as e:
            messagebox.showerror("Suggestion Error", f"Failed to suggest name: {e}")

    def on_auto_assign_change(self):
        auto_assign = self.auto_assign_ids_var.get()

        if auto_assign:
            try:
                stats = self.registry.get_registry_stats()
                next_ids = stats.get("next_available_ids", [0, 1, 2, 3])
                self.next_ids_label.configure(
                    text=f"Next available IDs: {next_ids}", foreground="green"
                )
            except:
                self.next_ids_label.configure(
                    text="Next available IDs: [0, 1, 2, 3]", foreground="green"
                )
        else:
            self.next_ids_label.configure(
                text="Manual ID entry enabled", foreground="orange"
            )

    def browse_output_directory(self):
        directory = filedialog.askdirectory(
            title="Select Output Directory", initialdir=self.output_dir_var.get()
        )
        if directory:
            self.output_dir_var.set(directory)
            self.status_var.set(f"Output directory set to: {directory}")

    def validate_settings(self):
        errors = []

        if not self.template_name_var.get().strip():
            errors.append("Template name is required")

        if not self.client_name_var.get().strip():
            errors.append("Client name is required")

        if not self.output_dir_var.get().strip():
            errors.append("Output directory is required")

        if errors:
            messagebox.showerror(
                "Validation Errors", "\n".join(f" {error}" for error in errors)
            )
            return False
        else:
            messagebox.showinfo("Validation Success", "All settings are valid!")
            return True

    def preview_template(self):
        if not self.validate_basic_inputs():
            return

        preview_info = f"""Template Preview:
================
Client: {self.client_name_var.get()}
Template Name: {self.template_name_var.get()}
Output Directory: {self.output_dir_var.get()}
Auto-assign IDs: {'Yes' if self.auto_assign_ids_var.get() else 'No'}

Next Actions:
 Template will be created with unique ArUco markers
 Registry will be automatically updated
 Files will be saved to the specified directory"""

        messagebox.showinfo("Template Preview", preview_info.strip())

    def validate_basic_inputs(self):
        if not self.template_name_var.get().strip():
            messagebox.showerror("Input Required", "Please enter a template name.")
            return False

        if not self.client_name_var.get().strip():
            messagebox.showerror("Input Required", "Please enter a client name.")
            return False

        return True

    def reset_form(self):
        self.template_name_var.set("")
        self.client_name_var.set("")
        self.output_dir_var.set("data/templates")
        self.auto_assign_ids_var.set(True)
        self.on_auto_assign_change()
        self.status_var.set("Form reset - ready for new professional template")

    def update_registry_stats(self):
        try:
            stats = self.registry.get_registry_stats()

            stats_text = f"""Registry Overview:
 Total Templates: {stats['total_templates']}
 Active Templates: {stats['active_templates']}
 Next Available IDs: {stats['next_available_ids']}
 Registry File: {stats.get('registry_file', 'template_registry.json')}
 Last Updated: {stats['last_updated'][:19].replace('T', ' ')}

Professional Features Ready:
 Auto-ID assignment enabled
 Template validation active
 Registry integration online"""

            self.stats_text.configure(state=tk.NORMAL)
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(1.0, stats_text)
            self.stats_text.configure(state=tk.DISABLED)

            if self.auto_assign_ids_var.get():
                self.next_ids_label.configure(
                    text=f"Next available IDs: {stats['next_available_ids']}",
                    foreground="green",
                )

        except Exception as e:
            print(f"Failed to update registry stats: {e}")
            self.stats_text.configure(state=tk.NORMAL)
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(1.0, "Registry stats unavailable")
            self.stats_text.configure(state=tk.DISABLED)

    def create_template(self):
        try:
            if not self.validate_settings():
                return

            self.status_var.set("Creating professional template...")
            self.root.update()

            success, message = self.template_maker.create_template_with_registry(
                template_name=self.template_name_var.get(),
                client_name=self.client_name_var.get(),
                marker_ids=None if self.auto_assign_ids_var.get() else [],
                output_dir=self.output_dir_var.get(),
            )

            if success:
                messagebox.showinfo(
                    "Professional Template Created!",
                    f"Professional template created successfully!\n\n{message}",
                )
                self.reset_form()
                self.update_registry_stats()
                self.status_var.set("Professional template created successfully!")
            else:
                messagebox.showerror(
                    "Creation Failed",
                    f"Failed to create professional template:\n\n{message}",
                )
                self.status_var.set("Professional template creation failed")

        except Exception as e:
            messagebox.showerror(
                "Error", f"Professional template creation failed:\n\n{str(e)}"
            )
            self.status_var.set("Error occurred during creation")

    def show_template_browser(self):
        try:
            browser_window = tk.Toplevel(self.root)
            browser_window.title("Professional Template Browser")
            browser_window.geometry("1000x750")
            browser_window.resizable(True, True)

            main_frame = ttk.Frame(browser_window)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

            title_label = ttk.Label(
                main_frame,
                text="Professional Template Browser",
                font=("Arial", 16, "bold"),
            )
            title_label.pack(pady=(0, 20))

            list_frame = ttk.LabelFrame(
                main_frame, text="Registered Templates", padding=15
            )
            list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

            columns = (
                "Template Name",
                "Client",
                "Marker IDs",
                "Created Date",
                "Status",
            )
            template_tree = ttk.Treeview(
                list_frame, columns=columns, show="headings", height=18
            )

            for col in columns:
                template_tree.heading(col, text=col)

            tree_scroll = ttk.Scrollbar(
                list_frame, orient=tk.VERTICAL, command=template_tree.yview
            )
            template_tree.configure(yscrollcommand=tree_scroll.set)

            template_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

            self.populate_template_browser(template_tree)

            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill=tk.X, pady=(20, 0))

            ttk.Button(
                button_frame,
                text="Refresh List",
                command=lambda: self.populate_template_browser(template_tree),
            ).pack(side=tk.LEFT)

            ttk.Button(
                button_frame, text="Close Browser", command=browser_window.destroy
            ).pack(side=tk.RIGHT)

        except Exception as e:
            messagebox.showerror(
                "Browser Error", f"Failed to open template browser:\n\n{str(e)}"
            )

    def populate_template_browser(self, tree):
        try:
            for item in tree.get_children():
                tree.delete(item)

            templates = self.registry.list_all_templates()

            for name, data in templates.items():
                tree.insert(
                    "",
                    "end",
                    values=(
                        name,
                        data.get("client", "Unknown"),
                        str(data.get("marker_ids", [])),
                        data.get("created_date", "")[:10]
                        if data.get("created_date")
                        else "Unknown",
                        data.get("status", "active"),
                    ),
                )

        except Exception as e:
            messagebox.showerror(
                "Population Error", f"Failed to populate template browser:\n\n{str(e)}"
            )

    def export_registry(self):
        try:
            file_path = filedialog.asksaveasfilename(
                title="Export Professional Registry",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            )

            if file_path:
                success = self.registry.export_template_list(file_path)
                if success:
                    messagebox.showinfo(
                        "Export Success!",
                        f"Professional registry exported to:\n{file_path}",
                    )
                    self.status_var.set(f"Registry exported to: {Path(file_path).name}")
                else:
                    messagebox.showerror(
                        "Export Failed", "Failed to export professional registry"
                    )

        except Exception as e:
            messagebox.showerror(
                "Export Error", f"Professional registry export failed:\n\n{str(e)}"
            )

    def show_help(self):
        help_content = """PROFESSIONAL KRATHONG TEMPLATE MAKER HELP

GETTING STARTED:
1. Enter client name for auto-suggestions
2. Configure template settings
3. Click 'Create Professional Template'

FEATURES:
 Auto-ID assignment prevents conflicts
 Registry integration tracks all templates
 Professional validation and error handling
 Export capabilities for backup

WORKFLOW:
1. Client Information: Enter client details
2. Template Configuration: Set up options
3. Create Template: Generate professional template
4. Registry Management: Track and export data

For support, use the validation features and check registry statistics."""

        messagebox.showinfo("Professional Template Maker Help", help_content)

    def run(self):
        print("Starting Professional Registry Template Maker GUI...")

        try:
            style = ttk.Style()
            style.configure("Accent.TButton", font=("Arial", 12, "bold"))
        except:
            pass

        print("Starting professional main loop...")

        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (self.root.winfo_width() // 2)
        y = (self.root.winfo_screenheight() // 2) - (self.root.winfo_height() // 2)
        self.root.geometry(f"+{x}+{y}")

        self.root.mainloop()
        print("Professional Registry Template GUI closed")


def main():
    print("Professional Registry Template GUI - Starting application...")
    try:
        app = ProfessionalRegistryGUI()
        app.run()
    except Exception as e:
        print(f"Professional application error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
