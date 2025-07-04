import tkinter as tk
import json
import os
from tkinter import ttk, messagebox, filedialog, simpledialog
from PIL import Image, ImageTk
import math

from ballistics import BALLISTIC_DATA
from calculations import (
    parse_grid, 
    calculate_target_coords, 
    find_valid_solutions,
    check_target_on_mortar_fo_axis,
    check_danger_close,
    calculate_new_fo_data,
    calculate_regular_mission,
    calculate_small_barrage,
    calculate_large_barrage,
    calculate_creeping_barrage
)
from mission_log import MissionLog
from config.config_manager import ConfigManager
from config.theme_manager import ThemeManager
from ui.map_view import MapView
from ui.settings_view import SettingsView
from ui.fire_mission_planner_view import FireMissionPlannerView

class CustomDialog(tk.Toplevel):
    def __init__(self, parent, title, message, is_dark_mode):
        super().__init__(parent)
        self.title(title)
        self.result = None
        bg_color = "#252526" if is_dark_mode else "SystemButtonFace"
        fg_color = "#FF5555" if is_dark_mode else "red"
        self.configure(bg=bg_color)
        label = ttk.Label(self, text=message, background=bg_color, foreground=fg_color, font=("Consolas", 12))
        label.pack(padx=20, pady=20)
        button_frame = ttk.Frame(self, style="TFrame")
        button_frame.pack(pady=10)
        yes_button = ttk.Button(button_frame, text="Yes", command=self.on_yes, style="TButton")
        yes_button.pack(side="left", padx=10)
        no_button = ttk.Button(button_frame, text="No", command=self.on_no, style="TButton")
        no_button.pack(side="left", padx=10)
        self.transient(parent)
        self.update_idletasks()
        parent_x, parent_y = parent.winfo_x(), parent.winfo_y()
        parent_width, parent_height = parent.winfo_width(), parent.winfo_height()
        dialog_width, dialog_height = self.winfo_width(), self.winfo_height()
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        self.geometry(f"+{x}+{y}")
        self.protocol("WM_DELETE_WINDOW", self.on_no)
        self.grab_set()
        self.wait_window()

    def on_yes(self):
        self.result = True
        self.destroy()

    def on_no(self):
        self.result = False
        self.destroy()

class MortarCalculatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Arma Reforger Mortar Calculator")
        screen_width, screen_height = self.winfo_screenwidth(), self.winfo_screenheight()
        width, height = 1015, 1180
        x = screen_width - width
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

        # Core Application State
        self.is_dark_mode = False
        self.map_image = None
        self.map_photo = None
        self.map_view = [0, 0, 4607, 4607]
        self.pan_start_x, self.pan_start_y = 0, 0
        self.last_coords = {}
        self.last_solutions = []
        self.admin_target_pin = None
        self.loaded_target_name = tk.StringVar()

        # UI Variables
        self.disable_danger_close_var = tk.BooleanVar(value=False)
        self.map_x_max_var = tk.DoubleVar(value=4607)
        self.map_y_max_var = tk.DoubleVar(value=4607)
        self.selected_map_var = tk.StringVar()
        self.admin_mode_enabled = tk.BooleanVar(value=False)
        self.mortar_grid_var = tk.StringVar(value="0000000000")
        self.mortar_elev_var = tk.DoubleVar(value=100)
        self.mortar_callsign_var = tk.StringVar()

        self.num_mortars_var = tk.IntVar(value=1)
        self.fire_mission_type_var = tk.StringVar(value="Regular")
        
        self.mortar_input_vars = []
        self.mortar_input_widgets = []

        self.fo_grid_var = tk.StringVar(value="0000000000")
        self.fo_elev_var = tk.DoubleVar(value=100)
        self.fo_id_var = tk.StringVar()
        self.fo_azimuth_var = tk.DoubleVar(value=0)
        self.fo_dist_var = tk.DoubleVar(value=1000)
        self.fo_elev_diff_var = tk.DoubleVar(value=0)
        self.creep_direction_var = tk.DoubleVar(value=0)
        self.corr_lr_var = tk.DoubleVar(value=0)
        self.corr_ad_var = tk.DoubleVar(value=0)
        self.spotting_charge_var = tk.IntVar()
        self.ammo_type_var = tk.StringVar()
        self.target_grid_10_var = tk.StringVar(value="----- -----")
        self.target_elev_var = tk.StringVar(value="-- m")
        self.mortar_to_target_azimuth_var = tk.StringVar(value="-- MIL")
        self.mortar_to_target_dist_var = tk.StringVar(value="-- m")
        self.mortar_to_target_elev_diff_var = tk.StringVar(value="-- m")
        self.correction_status_var = tk.StringVar()
        self.least_tof_charge_var = tk.StringVar(value="--")
        self.least_tof_elev_var = tk.StringVar(value="-- MIL")
        self.least_tof_tof_var = tk.StringVar(value="-- sec")
        self.least_tof_disp_var = tk.StringVar(value="-- m")
        self.most_tof_charge_var = tk.StringVar(value="--")
        self.most_tof_elev_var = tk.StringVar(value="-- MIL")
        self.most_tof_tof_var = tk.StringVar(value="-- sec")
        self.most_tof_disp_var = tk.StringVar(value="-- m")
        self.quick_azimuth_var = tk.StringVar(value="---- MIL")
        self.quick_least_tof_elev_var = tk.StringVar(value="C-: ---- MIL")
        self.quick_most_tof_elev_var = tk.StringVar(value="C-: ---- MIL")

        self.style = ttk.Style(self)
        self.config_manager = ConfigManager()
        self.theme_manager = ThemeManager(self)
        
        self.setup_ui()
        
        self.ammo_type_combo.current(0)
        self.update_charge_options()
        self.theme_manager.apply_theme()
        self.after(100, self.post_init_load)

        self.bind('<Control-Return>', lambda event: self.calculate_all())
        self.bind('<Control-n>', lambda event: self.new_mission())
        self.bind('<Control-l>', lambda event: self.load_mission())

    def setup_ui(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(pady=10, padx=10, fill="both", expand=True)
        main_tab_frame = ttk.Frame(self.notebook, padding="10")
        self.fire_mission_planner_tab = ttk.Frame(self.notebook)
        self.settings_tab = ttk.Frame(self.notebook)
        
        canvas = tk.Canvas(main_tab_frame)
        scrollbar = ttk.Scrollbar(main_tab_frame, orient="vertical", command=canvas.yview)
        self.main_tab = ttk.Frame(canvas)
        
        self.main_tab.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas.create_window((0, 0), window=self.main_tab, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.notebook.add(main_tab_frame, text="Main")
        self.notebook.add(self.fire_mission_planner_tab, text="Fire Mission Planner")
        self.notebook.add(self.settings_tab, text="Settings")

        self.setup_main_tab()
        self.setup_results_widgets()
        self.setup_fire_mission_planner_tab()
        self.setup_settings_tab()
        self.mission_log = MissionLog(self.main_tab, self)

    def post_init_load(self):
        """Load configs and populate UI after the main loop has started."""
        self.settings_view.refresh_map_list()
        map_list = self.settings_view.map_selection_combo['values']
        if "Zarichne.png" in map_list:
            self.selected_map_var.set("Zarichne.png")
        elif map_list:
            self.selected_map_var.set(map_list[0])
        self.settings_view.on_map_selected()

    def setup_main_tab(self):
        input_frame = ttk.Frame(self.main_tab)
        input_frame.pack(fill="x", expand=True)
        
        self.mortar_frame = ttk.LabelFrame(input_frame, text="1. Mortar Positions")
        self.mortar_frame.pack(fill="x", expand=True, pady=5)
        self.update_mortar_inputs()

        fire_mission_frame = ttk.LabelFrame(input_frame, text="2. Fire Mission")
        fire_mission_frame.pack(fill="x", expand=True, pady=5)

        # --- Left Frame for Mortar Count ---
        left_fm_frame = ttk.Frame(fire_mission_frame)
        left_fm_frame.pack(side="left", padx=5, pady=5, anchor="w")
        ttk.Label(left_fm_frame, text="Number of Mortars:").grid(row=0, column=0, sticky="w")
        num_mortars_combo = ttk.Combobox(left_fm_frame, textvariable=self.num_mortars_var, values=[1, 2, 3, 4], width=5, state="readonly")
        num_mortars_combo.grid(row=0, column=1, sticky="w", padx=5)
        num_mortars_combo.bind("<<ComboboxSelected>>", self.update_mortar_inputs)

        # --- Right Frame for Ammo ---
        right_fm_frame = ttk.Frame(fire_mission_frame)
        right_fm_frame.pack(side="right", padx=20, pady=5, anchor="e")
        ttk.Label(right_fm_frame, text="Ammunition:").pack(anchor="w")
        self.ammo_type_combo = ttk.Combobox(right_fm_frame, textvariable=self.ammo_type_var, state="readonly")
        self.ammo_type_combo['values'] = list(BALLISTIC_DATA.keys())
        self.ammo_type_combo.pack(anchor="w")
        self.ammo_type_combo.bind("<<ComboboxSelected>>", self.update_charge_options)

        # --- Center Frame for Mission Type ---
        center_fm_frame = ttk.Frame(fire_mission_frame)
        center_fm_frame.pack(expand=True, pady=5)
        
        ttk.Label(center_fm_frame, text="Mission Type:").grid(row=0, column=0, sticky="ns", pady=2, rowspan=2)
        
        mission_type_grid = ttk.Frame(center_fm_frame)
        mission_type_grid.grid(row=0, column=1, sticky="w", padx=5, rowspan=2)

        mission_types = ["Regular", "Small Barrage", "Large Barrage", "Creeping Barrage"]
        ttk.Radiobutton(mission_type_grid, text=mission_types[0], variable=self.fire_mission_type_var, value=mission_types[0], command=self.on_mission_type_change).grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(mission_type_grid, text=mission_types[3], variable=self.fire_mission_type_var, value=mission_types[3], command=self.on_mission_type_change).grid(row=1, column=0, sticky="w")
        ttk.Radiobutton(mission_type_grid, text=mission_types[1], variable=self.fire_mission_type_var, value=mission_types[1], command=self.on_mission_type_change).grid(row=0, column=1, sticky="w")
        ttk.Radiobutton(mission_type_grid, text=mission_types[2], variable=self.fire_mission_type_var, value=mission_types[2], command=self.on_mission_type_change).grid(row=1, column=1, sticky="w")

        fo_frame = ttk.LabelFrame(input_frame, text="3. Forward Observer (FO) Data")
        fo_frame.pack(fill="x", expand=True, pady=5)

        ttk.Label(fo_frame, text="FO 10-Digit Grid:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(fo_frame, textvariable=self.fo_grid_var, width=12).grid(row=0, column=1, padx=5, pady=2)
        ttk.Label(fo_frame, text="FO Elevation (m):").grid(row=0, column=2, padx=5, pady=2, sticky="w")
        ttk.Entry(fo_frame, textvariable=self.fo_elev_var, width=7).grid(row=0, column=3, padx=5, pady=2)
        ttk.Label(fo_frame, text="FO ID:").grid(row=0, column=4, padx=5, pady=2, sticky="w")
        ttk.Entry(fo_frame, textvariable=self.fo_id_var, width=12).grid(row=0, column=5, padx=5, pady=2)
        ttk.Label(fo_frame, text="Azimuth to Target (Degrees):").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(fo_frame, textvariable=self.fo_azimuth_var, width=7).grid(row=1, column=1, padx=5, pady=2)
        ttk.Label(fo_frame, text="Distance to Target (m):").grid(row=1, column=2, padx=5, pady=2, sticky="w")
        ttk.Entry(fo_frame, textvariable=self.fo_dist_var, width=7).grid(row=1, column=3, padx=5, pady=2)
        ttk.Label(fo_frame, text="Elev. Change to Target (m):").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(fo_frame, textvariable=self.fo_elev_diff_var, width=7).grid(row=2, column=1, padx=5, pady=2)
        
        ttk.Label(fo_frame, text="Creep Direction (Degrees):").grid(row=2, column=2, padx=5, pady=2, sticky="w")
        ttk.Entry(fo_frame, textvariable=self.creep_direction_var, width=7).grid(row=2, column=3, padx=5, pady=2)

        corr_frame = ttk.LabelFrame(input_frame, text="4. Fire Mission Corrections (Optional)")
        corr_frame.pack(fill="x", expand=True, pady=5)
        ttk.Label(corr_frame, text="Left(-)/Right(+) (m):").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(corr_frame, textvariable=self.corr_lr_var, width=7).grid(row=0, column=1, padx=5, pady=2)
        ttk.Label(corr_frame, text="Add(+)/Drop(-) (m):").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(corr_frame, textvariable=self.corr_ad_var, width=7).grid(row=1, column=1, padx=5, pady=2)
        ttk.Label(corr_frame, text="Charge Used for Spotting:").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.spotting_charge_combo = ttk.Combobox(corr_frame, textvariable=self.spotting_charge_var, state="readonly", width=5)
        self.spotting_charge_combo.grid(row=2, column=1, padx=5, pady=2)


        self.quick_fire_frame = ttk.LabelFrame(input_frame, text="Quick Fire Data")
        self.quick_fire_frame.pack(fill="x", expand=True, pady=5)
        
        self.danger_close_label = ttk.Label(self.quick_fire_frame, text="DANGER CLOSE FIRE MISSION", style="DangerClose.TLabel")
        self.danger_close_label.grid(row=0, column=2, rowspan=3, padx=20)
        self.danger_close_label.grid_remove()

    def setup_action_widgets(self):
        """This method is now deprecated as the calculate button is handled in setup_ui."""
        pass

    def setup_fire_mission_planner_tab(self):
        self.fire_mission_planner_view = FireMissionPlannerView(self.fire_mission_planner_tab, self)

    def setup_settings_tab(self):
        self.settings_view = SettingsView(self.settings_tab, self)

    def setup_results_widgets(self):
        results_frame = ttk.Frame(self.main_tab)
        results_frame.pack(fill="both", expand=True)
        left_frame = ttk.Frame(results_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=5)
        right_frame = ttk.Frame(results_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=5)

        action_frame = ttk.Frame(left_frame)
        action_frame.pack(pady=10, fill="x")
        action_frame.grid_columnconfigure(0, weight=1)
        ttk.Button(action_frame, text="Calculate Firing Solution", command=self.calculate_all).grid(row=0, column=0)

        target_details_frame = ttk.LabelFrame(left_frame, text="Calculated Target Details")
        target_details_frame.pack(fill="x", expand=True, pady=5)
        ttk.Label(target_details_frame, text="Target 10-Digit Grid:").grid(row=0, column=0, sticky="w", padx=5)
        ttk.Label(target_details_frame, textvariable=self.target_grid_10_var, font="SegoeUI 10 bold").grid(row=0, column=1, sticky="w", padx=5)
        ttk.Label(target_details_frame, text="Target Elevation:").grid(row=1, column=0, sticky="w", padx=5)
        ttk.Label(target_details_frame, textvariable=self.target_elev_var, font="SegoeUI 10 bold").grid(row=1, column=1, sticky="w", padx=5)
        azimuth_frame = ttk.Frame(target_details_frame, style="Highlight.TFrame")
        azimuth_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=2)
        inner_azimuth_frame = ttk.Frame(azimuth_frame, style="TFrame")
        inner_azimuth_frame.pack(fill="both", expand=True, padx=1, pady=1)
        inner_azimuth_frame.grid_columnconfigure(1, weight=1)
        ttk.Label(inner_azimuth_frame, text="Mortar-Target Azimuth:", style="Highlight.TLabel").grid(row=0, column=0, sticky="w", padx=(5, 10))
        ttk.Label(inner_azimuth_frame, textvariable=self.mortar_to_target_azimuth_var, style="Highlight.Bold.TLabel").grid(row=0, column=1, sticky="w", padx=(0, 5))
        ttk.Label(target_details_frame, text="Mortar-Target Distance:").grid(row=3, column=0, sticky="w", padx=5)
        ttk.Label(target_details_frame, textvariable=self.mortar_to_target_dist_var, font="SegoeUI 10 bold").grid(row=3, column=1, sticky="w", padx=5)
        ttk.Label(target_details_frame, text="Mortar-Target Elev. Change:").grid(row=4, column=0, sticky="w", padx=5)
        ttk.Label(target_details_frame, textvariable=self.mortar_to_target_elev_diff_var, font="SegoeUI 10 bold").grid(row=4, column=1, sticky="w", padx=5)

        self.solution_frame = ttk.LabelFrame(left_frame, text="Final Firing Solution")
        self.solution_frame.pack(fill="both", expand=True, pady=5)
        
        self.map_view_widget = MapView(right_frame, self)
        self.map_view_widget.pack(fill="both", expand=True, pady=5)

        self.status_label = ttk.Label(self.solution_frame, textvariable=self.correction_status_var, font="SegoeUI 10 bold")
        self.status_label.grid(row=0, column=0, columnspan=3, pady=(0, 5))

        self.solution_notebook = ttk.Notebook(self.solution_frame)
        self.solution_notebook.grid(row=1, column=0, columnspan=3, sticky="nsew")
        self.solution_frame.grid_rowconfigure(1, weight=1)
        self.solution_frame.grid_columnconfigure(0, weight=1)

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        if self.is_dark_mode:
            self.settings_view.theme_button.config(text="Toggle Light Mode")
            bg_color, fg_color, frame_bg, entry_bg, button_bg, border_color = "#1E1E1E", "#00FF00", "#252526", "#3C3C3C", "#3C3C3C", "#3C3C3C"
            self.style.theme_use('default')
            self.style.configure(".", background=bg_color, foreground=fg_color)
            self.style.configure("TFrame", background=bg_color)
            self.style.configure("TLabel", background=bg_color, foreground=fg_color, font=("Consolas", 10))
            self.style.configure("TLabelFrame", background=frame_bg, bordercolor=border_color, relief="solid")
            self.style.configure("TLabelFrame.Label", background=frame_bg, foreground=fg_color, font=("Consolas", 10, "bold"))
            self.style.configure("TButton", background=button_bg, foreground=fg_color, font=("Consolas", 10), borderwidth=1)
            self.style.map("TButton", background=[('active', '#6E6E6E')])
            self.style.configure("TCombobox", selectbackground=entry_bg, fieldbackground=entry_bg, background=button_bg, foreground=fg_color)
            self.style.map('TCombobox', fieldbackground=[('readonly', entry_bg)], selectbackground=[('readonly', entry_bg)], selectforeground=[('readonly', fg_color)])
            self.option_add('*TCombobox*Listbox.background', entry_bg)
            self.option_add('*TCombobox*Listbox.foreground', fg_color)
            self.option_add('*TCombobox*Listbox.selectBackground', button_bg)
            self.option_add('*TCombobox*Listbox.selectForeground', fg_color)
            self.style.configure("TEntry", fieldbackground=entry_bg, foreground=fg_color, insertcolor=fg_color)
            self.style.configure("Treeview", background=entry_bg, foreground=fg_color, fieldbackground=entry_bg)
            self.style.configure("Treeview.Heading", background=button_bg, foreground=fg_color)
            self.style.configure("TNotebook", background=bg_color, borderwidth=0)
            self.style.configure("TNotebook.Tab", background=frame_bg, foreground=fg_color, padding=[5, 2])
            self.style.map("TNotebook.Tab", background=[("selected", bg_color)], foreground=[("selected", fg_color)])
            self.style.configure("TCheckbutton", background=frame_bg, foreground=fg_color, font=("Consolas", 10))
            self.style.map("TCheckbutton", background=[('active', '#6E6E6E')], foreground=[('active', fg_color)])
            self.style.configure("Highlight.TFrame", background=bg_color, relief="solid", borderwidth=1, bordercolor="white")
            self.style.configure("Highlight.TLabel", background=bg_color, foreground=fg_color, font=("Consolas", 10))
            self.style.configure("Highlight.Bold.TLabel", background=bg_color, foreground=fg_color, font=("Consolas", 10, "bold"))
            self.style.configure("Highlight.BigBold.TLabel", background=bg_color, foreground=fg_color, font=("Consolas", 12, "bold"))
            self.style.configure("QuickFire.TLabel", background=frame_bg, foreground="red", font=("Consolas", 14, "bold"))
            self.style.configure("DangerClose.TLabel", background=frame_bg, foreground="red", font=("Consolas", 18, "bold"))
            self.configure(background=bg_color)
            self.map_view_widget.graph_canvas.config(bg=frame_bg)
            self.status_label.config(foreground="#FF5555")
            if hasattr(self.settings_view, 'admin_status_label') and self.admin_mode_enabled.get():
                self.settings_view.admin_status_label.config(foreground="#00FF00")
            if hasattr(self.settings_view, 'hidden_button_label'):
                self.settings_view.hidden_button_label.config(bg=bg_color)
            if hasattr(self, 'fire_mission_planner_view'):
                self.fire_mission_planner_view.apply_theme()
        else:
            self.settings_view.theme_button.config(text="Toggle Dark Mode")
            self.style.theme_use('vista')
            self.configure(background="SystemButtonFace")
            self.map_view_widget.graph_canvas.config(bg="white")
            self.status_label.config(foreground="red")
            self.option_add('*TCombobox*Listbox.background', "white")
            self.option_add('*TCombobox*Listbox.foreground', "black")
            self.option_add('*TCombobox*Listbox.selectBackground', "blue")
            self.option_add('*TCombobox*Listbox.selectForeground', "white")
            if hasattr(self.settings_view, 'admin_status_label') and self.admin_mode_enabled.get():
                self.settings_view.admin_status_label.config(foreground="green")
            if hasattr(self.settings_view, 'hidden_button_label'):
                self.settings_view.hidden_button_label.config(bg=self.cget('bg'))
            if hasattr(self, 'fire_mission_planner_view'):
                self.fire_mission_planner_view.apply_theme()

    def update_mortar_inputs(self, event=None):
        # Clear all widgets from the frame for a clean slate
        for widget in self.mortar_frame.winfo_children():
            widget.destroy()
        self.mortar_input_vars.clear()
        self.mortar_input_widgets.clear()

        num_mortars = self.num_mortars_var.get()
        
        # Add a vertical separator if there are two columns of guns
        if num_mortars > 1:
            row_span = 4 if num_mortars > 2 else 2
            sep = ttk.Separator(self.mortar_frame, orient='vertical')
            sep.grid(row=0, column=4, rowspan=row_span, sticky='ns', padx=10)

        for i in range(num_mortars):
            grid_var = tk.StringVar(value="0000000000")
            elev_var = tk.DoubleVar(value=100)
            callsign_var = tk.StringVar()
            self.mortar_input_vars.append({
                "grid": grid_var,
                "elev": elev_var,
                "callsign": callsign_var,
                "locked": tk.BooleanVar(value=False)
            })

            # Determine grid position (odd guns on left, even on right)
            row_base = (i // 2) * 2
            col_base = (i % 2) * 5

            # Create and place widgets
            ttk.Label(self.mortar_frame, text=f"Gun {i+1} Grid:").grid(row=row_base, column=col_base, padx=5, pady=2, sticky="w")
            grid_entry = ttk.Entry(self.mortar_frame, textvariable=grid_var, width=12)
            grid_entry.grid(row=row_base, column=col_base + 1, padx=5, pady=2)
            
            ttk.Label(self.mortar_frame, text="Elev:").grid(row=row_base, column=col_base + 2, padx=5, pady=2, sticky="w")
            elev_entry = ttk.Entry(self.mortar_frame, textvariable=elev_var, width=7)
            elev_entry.grid(row=row_base, column=col_base + 3, padx=5, pady=2)

            ttk.Label(self.mortar_frame, text="Callsign:").grid(row=row_base + 1, column=col_base, padx=5, pady=2, sticky="w")
            callsign_entry = ttk.Entry(self.mortar_frame, textvariable=callsign_var, width=12)
            callsign_entry.grid(row=row_base + 1, column=col_base + 1, padx=5, pady=2)

            lock_check = ttk.Checkbutton(self.mortar_frame, text="Lock", variable=self.mortar_input_vars[i]['locked'], command=lambda i=i: self.toggle_mortar_lock(i))
            lock_check.grid(row=row_base + 1, column=col_base + 2, padx=5, pady=2)

            self.mortar_input_widgets.append({"grid": grid_entry, "elev": elev_entry, "callsign": callsign_entry})
            self.toggle_mortar_lock(i)

    def toggle_mortar_lock(self, index):
        widgets = self.mortar_input_widgets[index]
        state = "readonly" if self.mortar_input_vars[index]['locked'].get() else "normal"
        
        widgets['grid'].config(state=state)
        widgets['elev'].config(state=state)
        widgets['callsign'].config(state=state)
        
        if state == "readonly":
            widgets['grid'].config(background="#CCCCCC")
            widgets['elev'].config(background="#CCCCCC")
            widgets['callsign'].config(background="#CCCCCC")
        else:
            bg_color = "#3C3C3C" if self.is_dark_mode else "white"
            widgets['grid'].config(background=bg_color)
            widgets['elev'].config(background=bg_color)
            widgets['callsign'].config(background=bg_color)

    def update_charge_options(self, event=None):
        selected_ammo = self.ammo_type_var.get()
        if selected_ammo:
            charges = list(BALLISTIC_DATA[selected_ammo].keys())
            self.spotting_charge_combo['values'] = charges
            if charges:
                self.spotting_charge_combo.current(0)

    def on_map_right_click(self, event):
        if not self.admin_mode_enabled.get():
            return
        map_e, map_n = self.map_view_widget.canvas_to_map_coords(event.x, event.y)
        if map_e is not None and map_n is not None:
            self.admin_target_pin = (map_e, map_n)
            self.target_grid_10_var.set(f"{int(round(map_e)):05d} {int(round(map_n)):05d}")
            target_elev = self.fo_elev_var.get() + self.fo_elev_diff_var.get()
            self.target_elev_var.set(f"{target_elev:.1f} m")
            self.mortar_to_target_azimuth_var.set("-- MIL")
            self.mortar_to_target_dist_var.set("-- m")
            self.mortar_to_target_elev_diff_var.set("-- m")
            self.clear_solution()
            self.fo_grid_var.set("--- ADMIN ---")
            self.fo_azimuth_var.set(0)
            self.fo_dist_var.set(0)
            self.last_coords = {}
            self.map_view_widget.plot_positions()

    def calculate_all(self):
        try:
            self.correction_status_var.set("")
            if hasattr(self, 'flash_dc_job'):
                self.after_cancel(self.flash_dc_job)
                self.danger_close_label.grid_remove()

            num_mortars = self.num_mortars_var.get()
            mission_type = self.fire_mission_type_var.get()
            ammo = self.ammo_type_var.get()
            
            fo_grid_str, fo_elev = self.fo_grid_var.get(), self.fo_elev_var.get()
            fo_azimuth_deg, fo_dist, fo_elev_diff = self.fo_azimuth_var.get(), self.fo_dist_var.get(), self.fo_elev_diff_var.get()
            corr_lr, corr_ad = self.corr_lr_var.get(), self.corr_ad_var.get()
            creep_direction = self.creep_direction_var.get()

            fo_easting, fo_northing = parse_grid(fo_grid_str, digits=10)
            initial_target_easting, initial_target_northing = calculate_target_coords(fo_grid_str, fo_azimuth_deg, fo_dist, fo_elev_diff, corr_lr, corr_ad)
            initial_target_elev = fo_elev + fo_elev_diff
            
            mortars = []
            for i in range(num_mortars):
                mortar_vars = self.mortar_input_vars[i]
                grid = mortar_vars['grid'].get()
                elev = mortar_vars['elev'].get()
                callsign = mortar_vars['callsign'].get()
                coords = parse_grid(grid)
                mortars.append({"coords": coords, "elev": elev, "callsign": callsign})

            if mission_type == "Regular":
                solutions = calculate_regular_mission(mortars, (initial_target_easting, initial_target_northing, initial_target_elev), ammo)
            elif mission_type == "Small Barrage":
                solutions = calculate_small_barrage(mortars, (initial_target_easting, initial_target_northing, initial_target_elev), ammo)
            elif mission_type == "Large Barrage":
                solutions = calculate_large_barrage(mortars, (initial_target_easting, initial_target_northing, initial_target_elev), ammo)
            elif mission_type == "Creeping Barrage":
                solutions = calculate_creeping_barrage(mortars, (initial_target_easting, initial_target_northing, initial_target_elev), creep_direction, ammo)
            else:
                raise ValueError("Invalid mission type")

            processed_solutions = []
            for sol in solutions:
                mortar_e, mortar_n = sol['mortar']['coords']
                target_e, target_n, target_elev = sol['target_coords']
                
                delta_easting, delta_northing = target_e - mortar_e, target_n - mortar_n
                mortar_target_dist = math.sqrt(delta_easting**2 + delta_northing**2)
                mortar_target_elev_diff = target_elev - sol['mortar']['elev']
                azimuth_rad_mt = math.atan2(delta_easting, delta_northing)
                azimuth_mils_mt = (azimuth_rad_mt / math.pi) * 3200
                if azimuth_mils_mt < 0: azimuth_mils_mt += 6400
                
                processed_solutions.append({
                    "mortar_coords": (mortar_e, mortar_n),
                    "fo_coords": (fo_easting, fo_northing),
                    "target_coords": (target_e, target_n),
                    "target_elev": target_elev,
                    "azimuth": azimuth_mils_mt,
                    "distance": mortar_target_dist,
                    "elev_diff": mortar_target_elev_diff,
                    "least_tof": sol['least_tof'],
                    "most_tof": sol['most_tof']
                })

            self.last_solutions = processed_solutions
            self.update_ui_with_solution(processed_solutions)

        except Exception as e:
            self.handle_calculation_error(e)

    def confirm_danger_close(self):
        self.status_label.config(text="DANGER CLOSE ARE YOU SURE?", foreground="red")
        self.flash_danger_warning()
        dialog = CustomDialog(self, "DANGER CLOSE", "The target is dangerously close to the FO.\nAre you sure you want to proceed?", self.is_dark_mode)

        if hasattr(self, 'flash_job'):
            self.after_cancel(self.flash_job)
        self.status_label.config(text="")

        return dialog.result

    def flash_danger_warning(self):
        current_color = self.status_label.cget("foreground")
        next_color = "white" if current_color == "red" else "red"
        self.status_label.config(foreground=next_color)
        self.flash_job = self.after(353, self.flash_danger_warning)

    def flash_danger_close_label(self):
        if self.danger_close_label.winfo_viewable():
            self.danger_close_label.grid_remove()
        else:
            self.danger_close_label.grid(row=0, column=2, rowspan=3, padx=20)
        self.flash_dc_job = self.after(353, self.flash_danger_close_label)

    def update_ui_with_solution(self, solutions):
        for tab in self.solution_notebook.tabs():
            self.solution_notebook.forget(tab)
            
        for widget in self.quick_fire_frame.winfo_children():
            widget.destroy()

        if not solutions:
            self.clear_solution()
            return

        self.last_coords = {'mortar_e': solutions[0]['mortar_coords'][0], 'mortar_n': solutions[0]['mortar_coords'][1], 'fo_e': solutions[0]['fo_coords'][0], 'fo_n': solutions[0]['fo_coords'][1], 'target_e': solutions[0]['target_coords'][0], 'target_n': solutions[0]['target_coords'][1]}
        self.target_grid_10_var.set(f"{int(round(solutions[0]['target_coords'][0])):.0f} {int(round(solutions[0]['target_coords'][1])):.0f}")
        self.target_elev_var.set(f"{solutions[0]['target_elev']:.1f} m")
        self.mortar_to_target_azimuth_var.set(f"{solutions[0]['azimuth']:.0f} MIL")
        self.mortar_to_target_dist_var.set(f"{solutions[0]['distance']:.0f} m")
        self.mortar_to_target_elev_diff_var.set(f"{solutions[0]['elev_diff']:.1f} m")

        num_mortars = self.num_mortars_var.get()

        if num_mortars == 1 and mission_type == "Regular":
            # Create a single tab for the regular mission
            tab_frame = ttk.Frame(self.solution_notebook)
            self.solution_notebook.add(tab_frame, text="Firing Solution")
            
            sol = solutions[0]
            ttk.Label(tab_frame, text="Least Time of Flight", font="SegoeUI 10 bold").grid(row=0, column=1, padx=5)
            ttk.Label(tab_frame, text="Most Time of Flight", font="SegoeUI 10 bold").grid(row=0, column=2, padx=5)
            ttk.Label(tab_frame, text="Charge (Rings):").grid(row=1, column=0, sticky="w", padx=5)
            ttk.Label(tab_frame, text=f"{sol['least_tof']['charge']}", font="SegoeUI 10 bold").grid(row=1, column=1, padx=5)
            ttk.Label(tab_frame, text=f"{sol['most_tof']['charge']}", font="SegoeUI 10 bold").grid(row=1, column=2, padx=5)
            
            elevation_frame = ttk.Frame(tab_frame, style="Highlight.TFrame")
            elevation_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=5, pady=2)
            inner_elevation_frame = ttk.Frame(elevation_frame, style="TFrame")
            inner_elevation_frame.pack(fill="both", expand=True, padx=1, pady=1)
            inner_elevation_frame.grid_columnconfigure(1, weight=1)
            inner_elevation_frame.grid_columnconfigure(2, weight=1)
            ttk.Label(inner_elevation_frame, text="Corrected Elevation:", style="Highlight.TLabel").grid(row=0, column=0, sticky="w", padx=5, pady=2)
            ttk.Label(inner_elevation_frame, text=f"{sol['least_tof']['elev']:.0f} MIL", style="Highlight.BigBold.TLabel").grid(row=0, column=1)
            ttk.Label(inner_elevation_frame, text=f"{sol['most_tof']['elev']:.0f} MIL", style="Highlight.BigBold.TLabel").grid(row=0, column=2)

            ttk.Label(tab_frame, text="Time of Flight:").grid(row=3, column=0, sticky="w", padx=5)
            ttk.Label(tab_frame, text=f"{sol['least_tof']['tof']:.1f} sec", font="SegoeUI 10 bold").grid(row=3, column=1, padx=5)
            ttk.Label(tab_frame, text=f"{sol['most_tof']['tof']:.1f} sec", font="SegoeUI 10 bold").grid(row=3, column=2, padx=5)

            ttk.Label(tab_frame, text="Dispersion Radius:").grid(row=4, column=0, sticky="w", padx=5)
            ttk.Label(tab_frame, text=f"{sol['least_tof']['dispersion']} m", font="SegoeUI 10 bold").grid(row=4, column=1, padx=5)
            ttk.Label(tab_frame, text=f"{sol['most_tof']['dispersion']} m", font="SegoeUI 10 bold").grid(row=4, column=2, padx=5)
            
            # Quick Fire Data for single regular mission
            gun_frame = ttk.LabelFrame(self.quick_fire_frame, text="Gun 1")
            gun_frame.grid(row=0, column=0, padx=5, pady=2, sticky="ns")
            ttk.Label(gun_frame, text="Azimuth:").pack(anchor="w")
            ttk.Label(gun_frame, text=f"{sol['azimuth']:.0f} MIL", style="QuickFire.TLabel").pack(anchor="w")
            ttk.Label(gun_frame, text="Least ToF Elev:").pack(anchor="w")
            ttk.Label(gun_frame, text=f"C-{sol['least_tof']['charge']}: {sol['least_tof']['elev']:.0f} MIL", style="QuickFire.TLabel").pack(anchor="w")
            ttk.Label(gun_frame, text="Most ToF Elev:").pack(anchor="w")
            ttk.Label(gun_frame, text=f"C-{sol['most_tof']['charge']}: {sol['most_tof']['elev']:.0f} MIL", style="QuickFire.TLabel").pack(anchor="w")
        else:
            for i, sol in enumerate(solutions):
                tab_frame = ttk.Frame(self.solution_notebook)
                self.solution_notebook.add(tab_frame, text=f"Gun {i+1}")
                
                ttk.Label(tab_frame, text="Least Time of Flight", font="SegoeUI 10 bold").grid(row=0, column=1, padx=5)
                ttk.Label(tab_frame, text="Most Time of Flight", font="SegoeUI 10 bold").grid(row=0, column=2, padx=5)
                ttk.Label(tab_frame, text="Charge (Rings):").grid(row=1, column=0, sticky="w", padx=5)
                ttk.Label(tab_frame, text=f"{sol['least_tof']['charge']}", font="SegoeUI 10 bold").grid(row=1, column=1, padx=5)
                ttk.Label(tab_frame, text=f"{sol['most_tof']['charge']}", font="SegoeUI 10 bold").grid(row=1, column=2, padx=5)
                
                elevation_frame = ttk.Frame(tab_frame, style="Highlight.TFrame")
                elevation_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=5, pady=2)
                inner_elevation_frame = ttk.Frame(elevation_frame, style="TFrame")
                inner_elevation_frame.pack(fill="both", expand=True, padx=1, pady=1)
                inner_elevation_frame.grid_columnconfigure(1, weight=1)
                inner_elevation_frame.grid_columnconfigure(2, weight=1)
                ttk.Label(inner_elevation_frame, text="Corrected Elevation:", style="Highlight.TLabel").grid(row=0, column=0, sticky="w", padx=5, pady=2)
                ttk.Label(inner_elevation_frame, text=f"{sol['least_tof']['elev']:.0f} MIL", style="Highlight.BigBold.TLabel").grid(row=0, column=1)
                ttk.Label(inner_elevation_frame, text=f"{sol['most_tof']['elev']:.0f} MIL", style="Highlight.BigBold.TLabel").grid(row=0, column=2)

                ttk.Label(tab_frame, text="Time of Flight:").grid(row=3, column=0, sticky="w", padx=5)
                ttk.Label(tab_frame, text=f"{sol['least_tof']['tof']:.1f} sec", font="SegoeUI 10 bold").grid(row=3, column=1, padx=5)
                ttk.Label(tab_frame, text=f"{sol['most_tof']['tof']:.1f} sec", font="SegoeUI 10 bold").grid(row=3, column=2, padx=5)

                ttk.Label(tab_frame, text="Dispersion Radius:").grid(row=4, column=0, sticky="w", padx=5)
                ttk.Label(tab_frame, text=f"{sol['least_tof']['dispersion']} m", font="SegoeUI 10 bold").grid(row=4, column=1, padx=5)
                ttk.Label(tab_frame, text=f"{sol['most_tof']['dispersion']} m", font="SegoeUI 10 bold").grid(row=4, column=2, padx=5)

                # Quick Fire Data
                gun_frame = ttk.LabelFrame(self.quick_fire_frame, text=f"Gun {i+1}")
                gun_frame.grid(row=0, column=i, padx=5, pady=2, sticky="ns")
                ttk.Label(gun_frame, text="Azimuth:").pack(anchor="w")
                ttk.Label(gun_frame, text=f"{sol['azimuth']:.0f} MIL", style="QuickFire.TLabel").pack(anchor="w")
                ttk.Label(gun_frame, text="Least ToF Elev:").pack(anchor="w")
                ttk.Label(gun_frame, text=f"C-{sol['least_tof']['charge']}: {sol['least_tof']['elev']:.0f} MIL", style="QuickFire.TLabel").pack(anchor="w")
                ttk.Label(gun_frame, text="Most ToF Elev:").pack(anchor="w")
                ttk.Label(gun_frame, text=f"C-{sol['most_tof']['charge']}: {sol['most_tof']['elev']:.0f} MIL", style="QuickFire.TLabel").pack(anchor="w")

        self.map_view_widget.auto_zoom_to_pins()
        self.map_view_widget.plot_positions()

    def handle_calculation_error(self, e):
        self.least_tof_charge_var.set("ERROR")
        self.least_tof_elev_var.set(str(e))
        self.clear_solution(clear_error=False)
        self.quick_azimuth_var.set("---- MIL")
        self.quick_least_tof_elev_var.set("C-: ---- MIL")
        self.quick_most_tof_elev_var.set("C-: ---- MIL")

    def clear_solution(self, clear_error=True):
        if clear_error:
            self.least_tof_charge_var.set("--")
            self.least_tof_elev_var.set("-- MIL")
        self.least_tof_tof_var.set("-- sec")
        self.least_tof_disp_var.set("-- m")
        self.most_tof_charge_var.set("--")
        self.most_tof_elev_var.set("-- MIL")
        self.most_tof_tof_var.set("-- sec")
        self.most_tof_disp_var.set("-- m")
        self.correction_status_var.set("")
        self.quick_azimuth_var.set("---- MIL")
        self.quick_least_tof_elev_var.set("C-: ---- MIL")
        self.quick_most_tof_elev_var.set("C-: ---- MIL")

    def get_current_mission_data_for_log(self):
        try:
            target_easting, target_northing = calculate_target_coords(self.fo_grid_var.get(), self.fo_azimuth_var.get(), self.fo_dist_var.get(), self.fo_elev_diff_var.get(), self.corr_lr_var.get(), self.corr_ad_var.get())
            calculated_target_grid = f"{int(round(target_easting)):05d} {int(round(target_northing)):05d}"
        except Exception:
            calculated_target_grid = "Calculation Error"
        return {
            "target_name": self.mission_log.target_name_var.get(),
            "mortars": [
                {
                    "grid": var['grid'].get(),
                    "elev": var['elev'].get(),
                    "callsign": var['callsign'].get(),
                    "locked": var['locked'].get()
                } for var in self.mortar_input_vars
            ],
            "num_mortars": self.num_mortars_var.get(),
            "fire_mission_type": self.fire_mission_type_var.get(),
            "fo_grid": self.fo_grid_var.get(),
            "fo_elev": self.fo_elev_var.get(),
            "fo_id": self.fo_id_var.get(),
            "fo_azimuth_deg": self.fo_azimuth_var.get(),
            "fo_dist": self.fo_dist_var.get(),
            "fo_elev_diff": self.fo_elev_diff_var.get(),
            "corr_lr": self.corr_lr_var.get(),
            "corr_ad": self.corr_ad_var.get(),
            "spotting_charge": self.spotting_charge_var.get(),
            "ammo": self.ammo_type_var.get(),
            "calculated_target_grid": calculated_target_grid,
            "mortar_to_target_azimuth": self.mortar_to_target_azimuth_var.get(),
            "mortar_to_target_dist": self.mortar_to_target_dist_var.get()
        }

    def load_mission_data_from_log(self, mission_data):
        self.loaded_target_name.set(mission_data.get("target_name", "Target"))
        self.mission_log.target_name_var.set(mission_data.get("target_name", "Target"))
        
        self.num_mortars_var.set(mission_data.get("num_mortars", 1))
        self.update_mortar_inputs()
        
        for i, mortar_data in enumerate(mission_data.get("mortars", [])):
            self.mortar_input_vars[i]['grid'].set(mortar_data.get("grid", ""))
            self.mortar_input_vars[i]['elev'].set(mortar_data.get("elev", 0))
            self.mortar_input_vars[i]['callsign'].set(mortar_data.get("callsign", ""))
            self.mortar_input_vars[i]['locked'].set(mortar_data.get("locked", False))
            self.toggle_mortar_lock(i)

        self.fire_mission_type_var.set("") # Clear mission type on load
        self.fo_grid_var.set(mission_data.get("fo_grid", ""))
        self.fo_elev_var.set(mission_data.get("fo_elev", 0))
        self.fo_id_var.set(mission_data.get("fo_id", ""))
        self.fo_azimuth_var.set(mission_data.get("fo_azimuth_deg", 0))
        self.fo_dist_var.set(mission_data.get("fo_dist", 0))
        self.fo_elev_diff_var.set(mission_data.get("fo_elev_diff", 0))
        self.corr_lr_var.set(mission_data.get("corr_lr", 0))
        self.corr_ad_var.set(mission_data.get("corr_ad", 0))
        self.ammo_type_var.set(mission_data.get("ammo", ""))
        self.update_charge_options()
        self.spotting_charge_var.set(mission_data.get("spotting_charge", 0))
        
        self.clear_solution()
        self.last_solutions = []
        self.last_coords = {}

        # Plot mortar and target positions without calculating a solution
        try:
            mortars = []
            for i in range(self.num_mortars_var.get()):
                mortar_vars = self.mortar_input_vars[i]
                grid = mortar_vars['grid'].get()
                coords = parse_grid(grid)
                mortars.append({"coords": coords})
            
            fo_e, fo_n = parse_grid(self.fo_grid_var.get())
            target_e, target_n = calculate_target_coords(self.fo_grid_var.get(), self.fo_azimuth_var.get(), self.fo_dist_var.get(), self.fo_elev_diff_var.get(), 0, 0)

            self.last_coords = {
                'mortars': [m['coords'] for m in mortars],
                'fo_e': fo_e, 'fo_n': fo_n,
                'target_e': target_e, 'target_n': target_n
            }
        except Exception:
            self.last_coords = {} # Clear if there's an error parsing

        self.map_view_widget.show_saved_target_var.set(True)
        self.map_view_widget.plot_positions()

    def on_mission_type_change(self):
        # self.calculate_all() # Removed to prevent auto-calculation on selection
        pass

    def save_log_as(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")], title="Save Fire Mission Log As...")
        if file_path:
            with open(file_path, 'w') as f:
                json.dump(self.mission_log.log_data, f, indent=4)
            messagebox.showinfo("Save Log", "Fire mission log saved successfully.")

    def load_log_from_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")], title="Load Fire Mission Log")
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    self.mission_log.log_data = json.load(f)
                self.mission_log.update_log_tree()
                messagebox.showinfo("Load Log", "Fire mission log loaded successfully.")
            except (json.JSONDecodeError, TypeError) as e:
                messagebox.showerror("Load Error", f"Failed to load log file: {e}\n\nThe file may be corrupt or in an unsupported format.")
            except Exception as e:
                messagebox.showerror("Load Error", f"An unexpected error occurred while loading the log file: {e}")

    def new_mission(self):
        """Clears all input fields for a new mission."""
        self.mortar_grid_var.set("0000000000")
        self.mortar_elev_var.set(100)
        self.mortar_callsign_var.set("")
        self.fo_grid_var.set("0000000000")
        self.fo_elev_var.set(100)
        self.fo_id_var.set("")
        self.fo_azimuth_var.set(0)
        self.fo_dist_var.set(1000)
        self.fo_elev_diff_var.set(0)
        self.corr_lr_var.set(0)
        self.corr_ad_var.set(0)
        self.clear_solution()
        self.target_grid_10_var.set("----- -----")
        self.target_elev_var.set("-- m")
        self.mortar_to_target_azimuth_var.set("-- MIL")
        self.mortar_to_target_dist_var.set("-- m")
        self.mortar_to_target_elev_diff_var.set("-- m")
        self.last_coords = {}
        self.loaded_target_name.set("")
        self.admin_target_pin = None
        self.map_view_widget.plot_positions()
        if hasattr(self, 'flash_dc_job'):
            self.after_cancel(self.flash_dc_job)
            self.danger_close_label.grid_remove()

    def load_map_image_and_view(self):
        map_name = self.selected_map_var.get()
        if not map_name:
            self.map_image = None
            self.map_view_widget.plot_positions()
            return
        map_path = os.path.join(self.config_manager.maps_dir, map_name)
        if os.path.exists(map_path):
            self.map_image = Image.open(map_path)
            x_max = self.map_x_max_var.get()
            y_max = self.map_y_max_var.get()
            self.map_view = [0, 0, x_max, y_max]
            self.last_coords = {}
            self.map_view_widget.plot_positions()
        else:
            self.map_image = None
            messagebox.showerror("Error", f"Map file not found: {map_name}")

if __name__ == "__main__":
    app = MortarCalculatorApp()
    app.mainloop()