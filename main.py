import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import math
from ballistics import BALLISTIC_DATA
from calculations import (
    parse_grid, 
    calculate_target_coords, 
    find_valid_solutions,
    check_target_on_mortar_fo_axis,
    check_danger_close
)
from mission_log import MissionLog

class CustomDialog(tk.Toplevel):
    def __init__(self, parent, title, message, is_dark_mode):
        super().__init__(parent)
        self.title(title)
        self.result = None

        # Style configuration
        bg_color = "#252526" if is_dark_mode else "SystemButtonFace"
        fg_color = "#FF5555" if is_dark_mode else "red" # Neon Red for dark mode
        button_bg = "#3C3C3C" if is_dark_mode else "SystemButtonFace"

        self.configure(bg=bg_color)

        # Message
        label = ttk.Label(self, text=message, background=bg_color, foreground=fg_color, font=("Consolas", 12))
        label.pack(padx=20, pady=20)

        # Buttons
        button_frame = ttk.Frame(self, style="TFrame")
        button_frame.pack(pady=10)

        yes_button = ttk.Button(button_frame, text="Yes", command=self.on_yes, style="TButton")
        yes_button.pack(side="left", padx=10)
        no_button = ttk.Button(button_frame, text="No", command=self.on_no, style="TButton")
        no_button.pack(side="left", padx=10)

        # Center the dialog on the parent window
        self.transient(parent)
        self.update_idletasks()
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        dialog_width = self.winfo_width()
        dialog_height = self.winfo_height()
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        self.geometry(f"+{x}+{y}")

        self.protocol("WM_DELETE_WINDOW", self.on_no) # Treat closing the window as a "No"
        self.grab_set() # Make modal
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
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        width = screen_width // 2
        height = screen_height
        x = screen_width // 2
        y = 0
        self.geometry(f"{width}x{height}+{x}+{y}")

        self.is_dark_mode = False
        self.danger_close_confirmed = False
        self.disable_danger_close_var = tk.BooleanVar(value=False)
        self.map_image = None
        self.map_photo = None
        self.map_view = [0, 0, 4607, 4607]  # min_e, min_n, max_e, max_n
        self.pan_start_x = 0
        self.pan_start_y = 0
        self.last_coords = {}
        self.map_scale_var = tk.DoubleVar(value=4607)

        self.style = ttk.Style(self)
        
        # Create a notebook for tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(pady=10, padx=10, fill="both", expand=True)

        # Create frames for each tab
        self.main_tab = ttk.Frame(self.notebook, padding="10")
        self.settings_tab = ttk.Frame(self.notebook, padding="10")

        self.notebook.add(self.main_tab, text="Main")
        self.notebook.add(self.settings_tab, text="Settings")

        self.setup_main_tab()
        self.setup_action_widgets()
        self.setup_results_widgets()
        self.setup_settings_tab()

        self.mission_log = MissionLog(self.main_tab, self)
        
        self.ammo_type_combo.current(0)
        self.update_charge_options()
        self.toggle_theme()

    def setup_main_tab(self):
        # This frame will hold all the content for the main tab
        input_frame = ttk.Frame(self.main_tab)
        input_frame.pack(fill="x", expand=True)

        # Mortar Position
        mortar_frame = ttk.LabelFrame(input_frame, text="1. Mortar Position")
        mortar_frame.pack(fill="x", expand=True, pady=5)
        ttk.Label(mortar_frame, text="10-Digit Grid:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.mortar_grid_var = tk.StringVar(value="0000000000")
        ttk.Entry(mortar_frame, textvariable=self.mortar_grid_var, width=12).grid(row=0, column=1, padx=5, pady=2)
        ttk.Label(mortar_frame, text="Elevation (m):").grid(row=0, column=2, padx=5, pady=2, sticky="w")
        self.mortar_elev_var = tk.DoubleVar(value=100)
        ttk.Entry(mortar_frame, textvariable=self.mortar_elev_var, width=7).grid(row=0, column=3, padx=5, pady=2)

        # FO Position
        fo_frame = ttk.LabelFrame(input_frame, text="2. Forward Observer (FO) Data")
        fo_frame.pack(fill="x", expand=True, pady=5)
        ttk.Label(fo_frame, text="FO 10-Digit Grid:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.fo_grid_var = tk.StringVar(value="0000000000")
        ttk.Entry(fo_frame, textvariable=self.fo_grid_var, width=12).grid(row=0, column=1, padx=5, pady=2)
        ttk.Label(fo_frame, text="FO Elevation (m):").grid(row=0, column=2, padx=5, pady=2, sticky="w")
        self.fo_elev_var = tk.DoubleVar(value=100)
        ttk.Entry(fo_frame, textvariable=self.fo_elev_var, width=7).grid(row=0, column=3, padx=5, pady=2)
        
        ttk.Label(fo_frame, text="Azimuth to Target (Degrees):").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.fo_azimuth_var = tk.DoubleVar(value=0)
        ttk.Entry(fo_frame, textvariable=self.fo_azimuth_var, width=7).grid(row=1, column=1, padx=5, pady=2)
        ttk.Label(fo_frame, text="Distance to Target (m):").grid(row=1, column=2, padx=5, pady=2, sticky="w")
        self.fo_dist_var = tk.DoubleVar(value=1000)
        ttk.Entry(fo_frame, textvariable=self.fo_dist_var, width=7).grid(row=1, column=3, padx=5, pady=2)
        ttk.Label(fo_frame, text="Elev. Change to Target (m):").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.fo_elev_diff_var = tk.DoubleVar(value=0)
        ttk.Entry(fo_frame, textvariable=self.fo_elev_diff_var, width=7).grid(row=2, column=1, padx=5, pady=2)

        # Corrections
        corr_frame = ttk.LabelFrame(input_frame, text="3. Fire Mission Corrections (Optional)")
        corr_frame.pack(fill="x", expand=True, pady=5)
        ttk.Label(corr_frame, text="Left (m):").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.corr_left_var = tk.DoubleVar(value=0)
        ttk.Entry(corr_frame, textvariable=self.corr_left_var, width=7).grid(row=0, column=1, padx=5, pady=2)
        ttk.Label(corr_frame, text="Right (m):").grid(row=0, column=2, padx=5, pady=2, sticky="w")
        self.corr_right_var = tk.DoubleVar(value=0)
        ttk.Entry(corr_frame, textvariable=self.corr_right_var, width=7).grid(row=0, column=3, padx=5, pady=2)
        ttk.Label(corr_frame, text="Add (m):").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.corr_add_var = tk.DoubleVar(value=0)
        ttk.Entry(corr_frame, textvariable=self.corr_add_var, width=7).grid(row=1, column=1, padx=5, pady=2)
        ttk.Label(corr_frame, text="Drop (m):").grid(row=1, column=2, padx=5, pady=2, sticky="w")
        self.corr_drop_var = tk.DoubleVar(value=0)
        ttk.Entry(corr_frame, textvariable=self.corr_drop_var, width=7).grid(row=1, column=3, padx=5, pady=2)
        
        ttk.Label(corr_frame, text="Charge Used for Spotting:").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.spotting_charge_var = tk.IntVar()
        self.spotting_charge_combo = ttk.Combobox(corr_frame, textvariable=self.spotting_charge_var, state="readonly", width=5)
        self.spotting_charge_combo.grid(row=2, column=1, padx=5, pady=2)

        # Ammunition
        ammo_frame = ttk.LabelFrame(input_frame, text="4. Ammunition")
        ammo_frame.pack(fill="x", expand=True, pady=5)
        ttk.Label(ammo_frame, text="Ammo Type:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.ammo_type_var = tk.StringVar()
        self.ammo_type_combo = ttk.Combobox(ammo_frame, textvariable=self.ammo_type_var, state="readonly")
        self.ammo_type_combo['values'] = list(BALLISTIC_DATA.keys())
        self.ammo_type_combo.grid(row=0, column=1, padx=5, pady=2)
        self.ammo_type_combo.bind("<<ComboboxSelected>>", self.update_charge_options)

    def setup_action_widgets(self):
        action_frame = ttk.Frame(self.main_tab)
        action_frame.pack(pady=10)
        ttk.Button(action_frame, text="Calculate Firing Solution", command=self.calculate_all).pack(side="left", padx=10)

    def setup_settings_tab(self):
        settings_frame = ttk.Frame(self.settings_tab)
        settings_frame.pack(fill="x", expand=True, pady=5)

        map_settings_frame = ttk.LabelFrame(settings_frame, text="Map Settings")
        map_settings_frame.pack(fill="x", expand=True, pady=5)
        
        ttk.Label(map_settings_frame, text="Uploaded Map Size (m):").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(map_settings_frame, textvariable=self.map_scale_var, width=10).grid(row=0, column=1, padx=5, pady=2)
        ttk.Button(map_settings_frame, text="Upload Map", command=self.upload_map).grid(row=1, column=0, columnspan=2, pady=10)

        theme_frame = ttk.LabelFrame(settings_frame, text="Theme")
        theme_frame.pack(fill="x", expand=True, pady=5)
        self.theme_button = ttk.Button(theme_frame, text="Toggle Dark Mode", command=self.toggle_theme)
        self.theme_button.pack(pady=10)

        warnings_frame = ttk.LabelFrame(settings_frame, text="Warnings")
        warnings_frame.pack(fill="x", expand=True, pady=5)
        ttk.Checkbutton(warnings_frame, text="Disable 'Danger Close' Warning", variable=self.disable_danger_close_var).pack(pady=5, padx=5, anchor="w")

    def setup_results_widgets(self):
        results_frame = ttk.Frame(self.main_tab)
        results_frame.pack(fill="both", expand=True)

        left_frame = ttk.Frame(results_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=5)

        right_frame = ttk.Frame(results_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=5)

        target_details_frame = ttk.LabelFrame(left_frame, text="Calculated Target Details")
        target_details_frame.pack(fill="x", expand=True, pady=5)
        self.target_grid_10_var = tk.StringVar(value="----- -----")
        self.target_elev_var = tk.StringVar(value="-- m")
        self.mortar_to_target_azimuth_var = tk.StringVar(value="-- MIL")
        self.mortar_to_target_dist_var = tk.StringVar(value="-- m")
        self.mortar_to_target_elev_diff_var = tk.StringVar(value="-- m")
        ttk.Label(target_details_frame, text="Target 10-Digit Grid:").grid(row=0, column=0, sticky="w", padx=5)
        ttk.Label(target_details_frame, textvariable=self.target_grid_10_var, font="SegoeUI 10 bold").grid(row=0, column=1, sticky="w", padx=5)
        ttk.Label(target_details_frame, text="Target Elevation:").grid(row=1, column=0, sticky="w", padx=5)
        ttk.Label(target_details_frame, textvariable=self.target_elev_var, font="SegoeUI 10 bold").grid(row=1, column=1, sticky="w", padx=5)
        ttk.Label(target_details_frame, text="Mortar-Target Azimuth:").grid(row=2, column=0, sticky="w", padx=5)
        ttk.Label(target_details_frame, textvariable=self.mortar_to_target_azimuth_var, font="SegoeUI 10 bold").grid(row=2, column=1, sticky="w", padx=5)
        ttk.Label(target_details_frame, text="Mortar-Target Distance:").grid(row=3, column=0, sticky="w", padx=5)
        ttk.Label(target_details_frame, textvariable=self.mortar_to_target_dist_var, font="SegoeUI 10 bold").grid(row=3, column=1, sticky="w", padx=5)
        ttk.Label(target_details_frame, text="Mortar-Target Elev. Change:").grid(row=4, column=0, sticky="w", padx=5)
        ttk.Label(target_details_frame, textvariable=self.mortar_to_target_elev_diff_var, font="SegoeUI 10 bold").grid(row=4, column=1, sticky="w", padx=5)

        solution_frame = ttk.LabelFrame(left_frame, text="Final Firing Solution")
        solution_frame.pack(fill="both", expand=True, pady=5)

        # --- Graph ---
        graph_frame = ttk.LabelFrame(right_frame, text="Visual Representation")
        graph_frame.pack(fill="both", expand=True, pady=5)
        self.graph_canvas = tk.Canvas(graph_frame, bg="white", width=400, height=400)
        self.graph_canvas.pack(fill="both", expand=True)
        self.graph_canvas.bind("<MouseWheel>", self.zoom)
        self.graph_canvas.bind("<ButtonPress-1>", self.start_pan)
        self.graph_canvas.bind("<B1-Motion>", self.pan)

        # Zoom buttons
        zoom_button_frame = ttk.Frame(graph_frame)
        zoom_button_frame.place(relx=0.98, rely=0.02, anchor="ne")
        ttk.Button(zoom_button_frame, text="+", width=2, command=self.zoom_in).pack()
        ttk.Button(zoom_button_frame, text="-", width=2, command=self.zoom_out).pack()

        self.correction_status_var = tk.StringVar()
        self.status_label = ttk.Label(solution_frame, textvariable=self.correction_status_var, font="SegoeUI 10 bold")
        self.status_label.grid(row=0, column=0, columnspan=3, pady=(0, 5))
        
        # Headers
        ttk.Label(solution_frame, text="").grid(row=1, column=0, padx=5)
        ttk.Label(solution_frame, text="Least Time of Flight", font="SegoeUI 10 bold").grid(row=1, column=1, padx=5)
        ttk.Label(solution_frame, text="Most Time of Flight", font="SegoeUI 10 bold").grid(row=1, column=2, padx=5)

        # Charge
        ttk.Label(solution_frame, text="Charge (Rings):").grid(row=2, column=0, sticky="w", padx=5)
        self.least_tof_charge_var = tk.StringVar(value="--")
        ttk.Label(solution_frame, textvariable=self.least_tof_charge_var, font="SegoeUI 10 bold").grid(row=2, column=1, padx=5)
        self.most_tof_charge_var = tk.StringVar(value="--")
        ttk.Label(solution_frame, textvariable=self.most_tof_charge_var, font="SegoeUI 10 bold").grid(row=2, column=2, padx=5)

        # Corrected Elevation
        ttk.Label(solution_frame, text="Corrected Elevation:").grid(row=3, column=0, sticky="w", padx=5)
        self.least_tof_elev_var = tk.StringVar(value="-- MIL")
        ttk.Label(solution_frame, textvariable=self.least_tof_elev_var, font="SegoeUI 12 bold").grid(row=3, column=1, padx=5)
        self.most_tof_elev_var = tk.StringVar(value="-- MIL")
        ttk.Label(solution_frame, textvariable=self.most_tof_elev_var, font="SegoeUI 12 bold").grid(row=3, column=2, padx=5)

        # Time of Flight
        ttk.Label(solution_frame, text="Time of Flight:").grid(row=4, column=0, sticky="w", padx=5)
        self.least_tof_tof_var = tk.StringVar(value="-- sec")
        ttk.Label(solution_frame, textvariable=self.least_tof_tof_var, font="SegoeUI 10 bold").grid(row=4, column=1, padx=5)
        self.most_tof_tof_var = tk.StringVar(value="-- sec")
        ttk.Label(solution_frame, textvariable=self.most_tof_tof_var, font="SegoeUI 10 bold").grid(row=4, column=2, padx=5)

        # Dispersion
        ttk.Label(solution_frame, text="Dispersion Radius:").grid(row=5, column=0, sticky="w", padx=5)
        self.least_tof_disp_var = tk.StringVar(value="-- m")
        ttk.Label(solution_frame, textvariable=self.least_tof_disp_var, font="SegoeUI 10 bold").grid(row=5, column=1, padx=5)
        self.most_tof_disp_var = tk.StringVar(value="-- m")
        ttk.Label(solution_frame, textvariable=self.most_tof_disp_var, font="SegoeUI 10 bold").grid(row=5, column=2, padx=5)

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        if self.is_dark_mode:
            self.theme_button.config(text="Toggle Light Mode")
            # VS Code-like Dark Theme
            bg_color = "#1E1E1E"
            fg_color = "#00FF00"  # Neon Green
            frame_bg = "#252526"
            entry_bg = "#3C3C3C"
            button_bg = "#3C3C3C"
            border_color = "#3C3C3C"

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
            self.style.configure("TEntry", fieldbackground=entry_bg, foreground=fg_color, insertcolor=fg_color)
            self.style.configure("Treeview", background=entry_bg, foreground=fg_color, fieldbackground=entry_bg)
            self.style.configure("Treeview.Heading", background=button_bg, foreground=fg_color)
            
            # Style the tabs
            self.style.configure("TNotebook", background=bg_color, borderwidth=0)
            self.style.configure("TNotebook.Tab", background=frame_bg, foreground=fg_color, padding=[5, 2])
            self.style.map("TNotebook.Tab", background=[("selected", bg_color)], foreground=[("selected", fg_color)])
            
            # Style the checkbutton
            self.style.configure("TCheckbutton", background=frame_bg, foreground=fg_color, font=("Consolas", 10))
            self.style.map("TCheckbutton", background=[('active', '#6E6E6E')], foreground=[('active', fg_color)])

            self.configure(background=bg_color)
            self.graph_canvas.config(bg=frame_bg)
            self.status_label.config(foreground="#FF5555")

            # Recursively update all widgets
            def update_widget_colors(widget):
                try:
                    widget.config(bg=bg_color)
                except tk.TclError:
                    pass # Some widgets don't have a bg attribute
                
                if isinstance(widget, (ttk.LabelFrame)):
                    widget.config(style="TLabelFrame")
                    for child in widget.winfo_children():
                        update_widget_colors(child)
                elif isinstance(widget, (ttk.Frame, tk.Frame)):
                     for child in widget.winfo_children():
                        update_widget_colors(child)

            update_widget_colors(self)

        else:
            self.theme_button.config(text="Toggle Dark Mode")
            self.style.theme_use('vista') # Or any other default light theme
            # You might need to manually reset colors for some widgets here
            # if they don't revert properly with the theme change.
            self.graph_canvas.config(bg="white")
            self.status_label.config(foreground="red")
            def reset_widget_colors(widget):
                try:
                    widget.config(bg="SystemButtonFace") # Default light color
                except tk.TclError:
                    pass
                if isinstance(widget, (ttk.Frame, tk.Frame, ttk.LabelFrame)):
                     for child in widget.winfo_children():
                        reset_widget_colors(child)
            reset_widget_colors(self)

    def update_charge_options(self, event=None):
        selected_ammo = self.ammo_type_var.get()
        if selected_ammo:
            charges = list(BALLISTIC_DATA[selected_ammo].keys())
            self.spotting_charge_combo['values'] = charges
            if charges:
                self.spotting_charge_combo.current(0)

    def calculate_all(self):
        try:
            self.correction_status_var.set("")
            
            mortar_grid_str = self.mortar_grid_var.get()
            mortar_elev = self.mortar_elev_var.get()
            fo_grid_str = self.fo_grid_var.get()
            fo_elev = self.fo_elev_var.get()
            fo_azimuth_deg = self.fo_azimuth_var.get()
            fo_dist = self.fo_dist_var.get()
            fo_elev_diff = self.fo_elev_diff_var.get()
            
            corr_left = self.corr_left_var.get()
            corr_right = self.corr_right_var.get()
            corr_add = self.corr_add_var.get()
            corr_drop = self.corr_drop_var.get()
            net_corr_lr = corr_right - corr_left
            net_corr_add_drop = corr_add - corr_drop
            
            ammo = self.ammo_type_var.get()
            spotting_charge = self.spotting_charge_var.get()

            mortar_easting, mortar_northing = parse_grid(mortar_grid_str, digits=10)
            fo_easting, fo_northing = parse_grid(fo_grid_str, digits=10)

            target_easting, target_northing = calculate_target_coords(fo_grid_str, fo_azimuth_deg, fo_dist, fo_elev_diff, net_corr_lr, net_corr_add_drop)
            target_elev = fo_elev + fo_elev_diff

            if check_target_on_mortar_fo_axis((mortar_easting, mortar_northing), (fo_easting, fo_northing), (target_easting, target_northing)):
                self.correction_status_var.set("UNRELIABLE CORRECTION (Target is between Mortar and FO)")
            
            correction_distance = math.sqrt(net_corr_lr**2 + net_corr_add_drop**2)
            if correction_distance > 0:
                try:
                    dispersion_to_check = BALLISTIC_DATA[ammo][spotting_charge]['dispersion']
                    if correction_distance <= dispersion_to_check:
                        self.correction_status_var.set("Correction ignored (within dispersion radius)")
                except KeyError:
                    # This can happen if the ammo or charge is not found in the ballistic data
                    pass

            delta_easting = target_easting - mortar_easting
            delta_northing = target_northing - mortar_northing
            
            mortar_target_dist = math.sqrt(delta_easting**2 + delta_northing**2)
            mortar_target_elev_diff = target_elev - mortar_elev
            
            azimuth_rad_mt = math.atan2(delta_easting, delta_northing)
            azimuth_mils_mt = (azimuth_rad_mt / math.pi) * 3200
            if azimuth_mils_mt < 0:
                azimuth_mils_mt += 6400

            valid_solutions = find_valid_solutions(ammo, mortar_target_dist, mortar_target_elev_diff)
            if not valid_solutions:
                raise ValueError("No valid charges for this range")

            valid_solutions.sort(key=lambda x: x["tof"])
            least_tof_solution = valid_solutions[0]
            most_tof_solution = valid_solutions[-1]

            if not self.disable_danger_close_var.get() and check_danger_close((fo_easting, fo_northing), (target_easting, target_northing), least_tof_solution['dispersion']):
                if not self.danger_close_confirmed:
                    self.confirm_danger_close()
                    return

            self.update_ui_with_solution(mortar_easting, mortar_northing, fo_easting, fo_northing, target_easting, target_northing, target_elev, azimuth_mils_mt, mortar_target_dist, mortar_target_elev_diff, least_tof_solution, most_tof_solution)
            self.danger_close_confirmed = False

        except Exception as e:
            self.handle_calculation_error(e)

    def confirm_danger_close(self):
        self.status_label.config(text="DANGER CLOSE ARE YOU SURE?", foreground="red")
        self.flash_danger_warning()

        dialog = CustomDialog(self, "DANGER CLOSE", "The target is dangerously close to the FO.\nAre you sure you want to proceed?", self.is_dark_mode)
        
        if dialog.result:
            self.danger_close_confirmed = True
            self.calculate_all()
        else:
            self.clear_solution()
        
        self.status_label.config(text="")
        self.after_cancel(self.flash_job)

    def flash_danger_warning(self):
        current_color = self.status_label.cget("foreground")
        next_color = "white" if current_color == "red" else "red"
        self.status_label.config(foreground=next_color)
        self.flash_job = self.after(500, self.flash_danger_warning)

    def update_ui_with_solution(self, mortar_e, mortar_n, fo_e, fo_n, target_e, target_n, target_elev, azimuth_mils_mt, mortar_target_dist, mortar_target_elev_diff, least_tof, most_tof):
        self.last_coords = {
            'mortar_e': mortar_e, 'mortar_n': mortar_n,
            'fo_e': fo_e, 'fo_n': fo_n,
            'target_e': target_e, 'target_n': target_n
        }
        self.target_grid_10_var.set(f"{int(round(target_e)):05d} {int(round(target_n)):05d}")
        self.target_elev_var.set(f"{target_elev:.1f} m")
        self.mortar_to_target_azimuth_var.set(f"{azimuth_mils_mt:.0f} MIL")
        self.mortar_to_target_dist_var.set(f"{mortar_target_dist:.0f} m")
        self.mortar_to_target_elev_diff_var.set(f"{mortar_target_elev_diff:.1f} m")
        
        self.least_tof_charge_var.set(f"{least_tof['charge']}")
        self.least_tof_elev_var.set(f"{least_tof['elev']:.0f} MIL")
        self.least_tof_tof_var.set(f"{least_tof['tof']:.1f} sec")
        self.least_tof_disp_var.set(f"{least_tof['dispersion']} m")
        
        self.most_tof_charge_var.set(f"{most_tof['charge']}")
        self.most_tof_elev_var.set(f"{most_tof['elev']:.0f} MIL")
        self.most_tof_tof_var.set(f"{most_tof['tof']:.1f} sec")
        self.most_tof_disp_var.set(f"{most_tof['dispersion']} m")

        self.auto_zoom_to_pins()
        self.plot_positions()

    def handle_calculation_error(self, e):
        self.least_tof_charge_var.set("ERROR")
        self.least_tof_elev_var.set(str(e))
        self.clear_solution(clear_error=False)

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

    def get_current_mission_data_for_log(self):
        try:
            target_easting, target_northing = calculate_target_coords(
                self.fo_grid_var.get(), self.fo_azimuth_var.get(), self.fo_dist_var.get(),
                self.fo_elev_diff_var.get(), self.corr_right_var.get() - self.corr_left_var.get(),
                self.corr_add_var.get() - self.corr_drop_var.get()
            )
            calculated_target_grid = f"{int(round(target_easting)):05d} {int(round(target_northing)):05d}"
        except Exception:
            calculated_target_grid = "Calculation Error"

        return {
            "target_name": self.mission_log.target_name_var.get(),
            "mortar_grid": self.mortar_grid_var.get(),
            "mortar_elev": self.mortar_elev_var.get(),
            "fo_grid": self.fo_grid_var.get(),
            "fo_elev": self.fo_elev_var.get(),
            "fo_azimuth_deg": self.fo_azimuth_var.get(),
            "fo_dist": self.fo_dist_var.get(),
            "fo_elev_diff": self.fo_elev_diff_var.get(),
            "corr_left": self.corr_left_var.get(),
            "corr_right": self.corr_right_var.get(),
            "corr_add": self.corr_add_var.get(),
            "corr_drop": self.corr_drop_var.get(),
            "spotting_charge": self.spotting_charge_var.get(),
            "ammo": self.ammo_type_var.get(),
            "calculated_target_grid": calculated_target_grid,
            "mortar_to_target_azimuth": self.mortar_to_target_azimuth_var.get(),
            "mortar_to_target_dist": self.mortar_to_target_dist_var.get(),
        }

    def load_mission_data_from_log(self, mission_data):
        self.mission_log.target_name_var.set(mission_data.get("target_name", "Target"))
        self.mortar_grid_var.set(mission_data.get("mortar_grid", ""))
        self.mortar_elev_var.set(mission_data.get("mortar_elev", 0))
        self.fo_grid_var.set(mission_data.get("fo_grid", ""))
        self.fo_elev_var.set(mission_data.get("fo_elev", 0))
        self.fo_azimuth_var.set(mission_data.get("fo_azimuth_deg", 0))
        self.fo_dist_var.set(mission_data.get("fo_dist", 0))
        self.fo_elev_diff_var.set(mission_data.get("fo_elev_diff", 0))
        self.corr_left_var.set(mission_data.get("corr_left", 0))
        self.corr_right_var.set(mission_data.get("corr_right", 0))
        self.corr_add_var.set(mission_data.get("corr_add", 0))
        self.corr_drop_var.set(mission_data.get("corr_drop", 0))
        self.ammo_type_var.set(mission_data.get("ammo", ""))
        self.update_charge_options()
        self.spotting_charge_var.set(mission_data.get("spotting_charge", 0))
        
        self.calculate_all()

    def upload_map(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")])
        if file_path:
            self.map_image = Image.open(file_path)
            map_scale = self.map_scale_var.get()
            self.map_view = [0, 0, map_scale, map_scale]  # Reset view to full map
            self.plot_positions()

    def zoom(self, event):
        if not self.map_image:
            return

        canvas_width = self.graph_canvas.winfo_width()
        canvas_height = self.graph_canvas.winfo_height()
        
        min_e, min_n, max_e, max_n = self.map_view
        map_width = max_e - min_e
        map_height = max_n - min_n # Should be same as width

        # Determine the real-world coordinates at the cursor
        # This requires knowing the actual rendered size and position of the map on the canvas
        scale = min(canvas_width / map_width, canvas_height / map_height)
        pixel_width = map_width * scale
        pixel_height = map_height * scale
        offset_x = (canvas_width - pixel_width) / 2
        offset_y = (canvas_height - pixel_height) / 2

        # Convert cursor screen coords to map coords
        cursor_e = min_e + (event.x - offset_x) / scale
        cursor_n = max_n - (event.y - offset_y) / scale

        zoom_factor = 1.1 if event.delta > 0 else 1 / 1.1
        new_map_width = map_width / zoom_factor
        new_map_height = map_height / zoom_factor

        # New view, centered on cursor, maintaining square aspect ratio
        new_min_e = cursor_e - (event.x - offset_x) / scale * (new_map_width / map_width)
        new_max_e = new_min_e + new_map_width
        new_min_n = cursor_n - (1 - ((event.y - offset_y) / pixel_height)) * new_map_height
        new_max_n = new_min_n + new_map_height
        
        self.map_view = [new_min_e, new_min_n, new_max_e, new_max_n]
        self.plot_positions()

    def zoom_in(self):
        # Simulate a zoom-in event at the center of the canvas
        event = tk.Event()
        event.delta = 120 # Standard for a single wheel-up tick
        event.x = self.graph_canvas.winfo_width() // 2
        event.y = self.graph_canvas.winfo_height() // 2
        self.zoom(event)

    def zoom_out(self):
        # Simulate a zoom-out event at the center of the canvas
        event = tk.Event()
        event.delta = -120 # Standard for a single wheel-down tick
        event.x = self.graph_canvas.winfo_width() // 2
        event.y = self.graph_canvas.winfo_height() // 2
        self.zoom(event)

    def start_pan(self, event):
        self.pan_start_x = event.x
        self.pan_start_y = event.y

    def pan(self, event):
        if not self.map_image:
            return
            
        dx = event.x - self.pan_start_x
        dy = event.y - self.pan_start_y

        canvas_width = self.graph_canvas.winfo_width()
        canvas_height = self.graph_canvas.winfo_height()
        
        min_e, min_n, max_e, max_n = self.map_view
        map_width = max_e - min_e
        map_height = max_n - min_n

        # Determine the scale to convert pixels to map units
        scale = min(canvas_width / map_width, canvas_height / map_height)
        
        delta_e = dx / scale
        delta_n = dy / scale

        # Update map view by subtracting the delta (pan left moves view right)
        self.map_view = [min_e - delta_e, min_n + delta_n, max_e - delta_e, max_n + delta_n]

        self.pan_start_x = event.x
        self.pan_start_y = event.y
        
        self.plot_positions()

    def auto_zoom_to_pins(self):
        if not self.last_coords:
            return

        coords = [
            (self.last_coords['mortar_e'], self.last_coords['mortar_n']),
            (self.last_coords['fo_e'], self.last_coords['fo_n']),
            (self.last_coords['target_e'], self.last_coords['target_n'])
        ]

        min_e = min(c[0] for c in coords)
        max_e = max(c[0] for c in coords)
        min_n = min(c[1] for c in coords)
        max_n = max(c[1] for c in coords)

        # Add some padding
        padding_e = (max_e - min_e) * 0.2
        padding_n = (max_n - min_n) * 0.2
        
        # Handle cases where padding is zero
        if padding_e == 0:
            padding_e = 100 # default padding
        if padding_n == 0:
            padding_n = 100 # default padding

        view_min_e = min_e - padding_e
        view_max_e = max_e + padding_e
        view_min_n = min_n - padding_n
        view_max_n = max_n + padding_n

        # Make the view square
        width = view_max_e - view_min_e
        height = view_max_n - view_min_n
        
        if width > height:
            diff = width - height
            view_min_n -= diff / 2
            view_max_n += diff / 2
        elif height > width:
            diff = height - width
            view_min_e -= diff / 2
            view_max_e += diff / 2

        self.map_view = [view_min_e, view_min_n, view_max_e, view_max_n]

    def plot_positions(self):
        self.graph_canvas.delete("all")
        
        bg_color = "#252526" if self.is_dark_mode else "white"
        mortar_color, fo_color, target_color = "blue", "red", "yellow"
        self.graph_canvas.config(bg=bg_color)

        canvas_width = self.graph_canvas.winfo_width()
        canvas_height = self.graph_canvas.winfo_height()
        min_e, min_n, max_e, max_n = self.map_view
        map_width = max_e - min_e
        map_height = max_n - min_n

        if self.map_image and map_width > 0 and map_height > 0:
            map_scale = self.map_scale_var.get()
            img_width, img_height = self.map_image.size

            # Determine the scale to fit the square map view onto the canvas without distortion
            scale = min(canvas_width / map_width, canvas_height / map_height)
            
            # Calculate the size of the rendered map image
            render_width = int(map_width * scale)
            render_height = int(map_height * scale)

            # Calculate offsets to center the image on the canvas (letterboxing)
            offset_x = (canvas_width - render_width) // 2
            offset_y = (canvas_height - render_height) // 2

            # Crop the original image based on the map view
            crop_min_x = (min_e / map_scale) * img_width
            crop_max_x = (max_e / map_scale) * img_width
            crop_min_y = ((map_scale - max_n) / map_scale) * img_height
            crop_max_y = ((map_scale - min_n) / map_scale) * img_height

            if crop_max_x > crop_min_x and crop_max_y > crop_min_y:
                cropped_img = self.map_image.crop((crop_min_x, crop_min_y, crop_max_x, crop_max_y))
                resized_image = cropped_img.resize((render_width, render_height), Image.LANCZOS)
                
                self.map_photo = ImageTk.PhotoImage(resized_image)
                self.graph_canvas.create_image(offset_x, offset_y, anchor="nw", image=self.map_photo)

        if self.last_coords:
            def transform(e, n):
                # This transform function now accounts for the centered, non-distorted map
                scale = min(canvas_width / map_width, canvas_height / map_height)
                render_width = map_width * scale
                render_height = map_height * scale
                offset_x = (canvas_width - render_width) // 2
                offset_y = (canvas_height - render_height) // 2

                x = offset_x + ((e - min_e) * scale)
                y = offset_y + ((max_n - n) * scale)
                return x, y

            mortar_x, mortar_y = transform(self.last_coords['mortar_e'], self.last_coords['mortar_n'])
            fo_x, fo_y = transform(self.last_coords['fo_e'], self.last_coords['fo_n'])
            target_x, target_y = transform(self.last_coords['target_e'], self.last_coords['target_n'])
            
            self.graph_canvas.create_oval(mortar_x-5, mortar_y-5, mortar_x+5, mortar_y+5, fill=mortar_color, outline="black")
            self.graph_canvas.create_text(mortar_x, mortar_y - 15, text="Mortar", fill="black")
            self.graph_canvas.create_oval(fo_x-5, fo_y-5, fo_x+5, fo_y+5, fill=fo_color, outline="black")
            self.graph_canvas.create_text(fo_x, fo_y - 15, text="FO", fill="black")
            self.graph_canvas.create_polygon(target_x, target_y-7, target_x-7, target_y+7, target_x+7, target_y+7, fill=target_color, outline="black")
            self.graph_canvas.create_text(target_x, target_y + 15, text="Target", fill="black")

if __name__ == "__main__":
    app = MortarCalculatorApp()
    app.mainloop()