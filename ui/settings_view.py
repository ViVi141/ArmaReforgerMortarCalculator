import tkinter as tk
from tkinter import ttk, filedialog, simpledialog, PhotoImage

class SettingsView(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding="10")
        self.app = app

        self.pack(fill="both", expand=True)

        # Map Settings
        map_settings_frame = ttk.LabelFrame(self, text="Map Settings")
        map_settings_frame.pack(fill="x", expand=True, pady=5)
        
        ttk.Label(map_settings_frame, text="Select Map:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.map_selection_combo = ttk.Combobox(map_settings_frame, textvariable=self.app.selected_map_var, state="readonly")
        self.map_selection_combo.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        self.map_selection_combo.bind("<<ComboboxSelected>>", self.on_map_selected)

        ttk.Label(map_settings_frame, text="Map X-Max (m):").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(map_settings_frame, textvariable=self.app.map_x_max_var, width=10).grid(row=1, column=1, padx=5, pady=2)
        
        ttk.Label(map_settings_frame, text="Map Y-Max (m):").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(map_settings_frame, textvariable=self.app.map_y_max_var, width=10).grid(row=2, column=1, padx=5, pady=2)

        ttk.Button(map_settings_frame, text="Upload New Map", command=self.upload_map).grid(row=3, column=0, columnspan=2, pady=10)
        map_settings_frame.grid_columnconfigure(1, weight=1)

        # Theme
        theme_frame = ttk.LabelFrame(self, text="Theme")
        theme_frame.pack(fill="x", expand=True, pady=5)
        self.theme_button = ttk.Button(theme_frame, text="Toggle Dark Mode", command=self.app.toggle_theme)
        self.theme_button.pack(pady=10)

        # Warnings
        warnings_frame = ttk.LabelFrame(self, text="Warnings")
        warnings_frame.pack(fill="x", expand=True, pady=5)
        ttk.Checkbutton(warnings_frame, text="Disable 'Danger Close' Warning", variable=self.app.disable_danger_close_var).pack(pady=5, padx=5, anchor="w")

        # Admin
        # --- Admin Mode (Hidden Feature) ---
        # NOTE: The admin mode, advanced targeting system, and this hidden button are internal features.
        # They should NEVER be mentioned in the public RELEASE_NOTES.md or any user-facing documentation.
        self.admin_frame = ttk.LabelFrame(self, text="Admin")
        self.admin_status_label = ttk.Label(self.admin_frame, text="Admin Mode Enabled")
        self.admin_status_label.pack(pady=5)

        # Transparent 1x1 pixel GIF
        self.transparent_img = PhotoImage(data='R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7')
        
        self.hidden_button_label = tk.Label(self, image=self.transparent_img, width=75, height=75, bd=0, highlightthickness=0)
        self.hidden_button_label.place(relx=1.0, rely=1.0, anchor="se")
        self.hidden_button_label.bind("<Button-1>", self.prompt_for_admin_password)

    def on_map_selected(self, event=None):
        map_name = self.app.selected_map_var.get()
        if not map_name:
            return

        config = self.app.config_manager.get_map_config(map_name)
        self.app.map_x_max_var.set(config.get('x_max', 1000))
        self.app.map_y_max_var.set(config.get('y_max', 1000))
        
        self.app.load_map_image_and_view()

    def upload_map(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
        if not file_path:
            return

        x_max = self.app.map_x_max_var.get()
        y_max = self.app.map_y_max_var.get()
        
        success, map_filename = self.app.config_manager.add_new_map(file_path, x_max, y_max)
        
        if success:
            self.refresh_map_list()
            self.app.selected_map_var.set(map_filename)
            self.on_map_selected()

    def prompt_for_admin_password(self, event=None):
        password = simpledialog.askstring("Password", "Enter Admin Password:", show='*')
        if password == "admin":
            self.app.admin_mode_enabled.set(True)
            self.admin_frame.pack(fill="x", expand=True, pady=5)
            if self.app.is_dark_mode:
                self.admin_status_label.config(foreground="#00FF00")
            else:
                self.admin_status_label.config(foreground="green")
        else:
            self.app.admin_mode_enabled.set(False)
            self.admin_frame.pack_forget()

    def refresh_map_list(self):
        map_files = self.app.config_manager.get_map_list()
        self.map_selection_combo['values'] = map_files