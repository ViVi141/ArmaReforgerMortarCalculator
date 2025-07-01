import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import math
from ballistics import BALLISTIC_DATA
from calculations import (
    parse_grid, 
    calculate_target_coords, 
    find_valid_solutions, 
    check_mortar_fo_axis,
    check_danger_close,
    check_unreliable_correction
)
from mission_log import MissionLog

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
        self.map_image = None
        self.map_photo = None
        self.zoom_level = 1.0
        self.pan_start_x = 0
        self.pan_start_y = 0

        self.style = ttk.Style(self)
        
        self.main_frame = ttk.Frame(self, padding="10")
        self.main_frame.pack(pady=10, padx=10, fill="both", expand=True)

        self.setup_input_widgets()
        self.setup_action_widgets()
        self.setup_results_widgets()

        self.mission_log = MissionLog(self.main_frame, self)
        
        self.ammo_type_combo.current(0)
        self.update_charge_options()
        self.toggle_theme()

    def setup_input_widgets(self):
        input_frame = ttk.Frame(self.main_frame)
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
        action_frame = ttk.Frame(self.main_frame)
        action_frame.pack(pady=10)
        ttk.Button(action_frame, text="Calculate Firing Solution", command=self.calculate_all).pack(side="left", padx=10)
        self.theme_button = ttk.Button(action_frame, text="Toggle Dark Mode", command=self.toggle_theme)
        self.theme_button.pack(side="left", padx=10)
        ttk.Button(action_frame, text="Upload Map", command=self.upload_map).pack(side="left", padx=10)

    def setup_results_widgets(self):
        results_frame = ttk.Frame(self.main_frame)
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

            if check_mortar_fo_axis((mortar_easting, mortar_northing), (fo_easting, fo_northing), (target_easting, target_northing)):
                self.correction_status_var.set("Target is between Mortar Team and Forward Observer. Use caution.")
            elif check_unreliable_correction((mortar_easting, mortar_northing), (fo_easting, fo_northing), (target_easting, target_northing)):
                self.correction_status_var.set("UNRELIABLE CORRECTION (Target on Mortar-FO Axis)")
            
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

            if check_danger_close((fo_easting, fo_northing), (target_easting, target_northing), least_tof_solution['dispersion']):
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
        
        confirm = messagebox.askyesno("DANGER CLOSE", "The target is dangerously close to the FO. Are you sure you want to proceed?")
        if confirm:
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

        self.plot_positions(mortar_e, mortar_n, fo_e, fo_n, target_e, target_n)

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
            self.zoom_level = 1.0
            self.plot_positions(0,0,0,0,0,0) # Redraw with map

    def zoom(self, event):
        if self.map_image:
            if event.delta > 0:
                self.zoom_level *= 1.1
            else:
                self.zoom_level /= 1.1
            self.plot_positions(0,0,0,0,0,0) # Redraw with new zoom

    def start_pan(self, event):
        self.pan_start_x = event.x
        self.pan_start_y = event.y

    def pan(self, event):
        if self.map_image:
            dx = event.x - self.pan_start_x
            dy = event.y - self.pan_start_y
            self.graph_canvas.move("all", dx, dy)
            self.pan_start_x = event.x
            self.pan_start_y = event.y

    def plot_positions(self, mortar_e, mortar_n, fo_e, fo_n, target_e, target_n):
        self.graph_canvas.delete("all")
        
        # Define colors based on theme
        bg_color = "#252526" if self.is_dark_mode else "white"
        line_color = "white" if self.is_dark_mode else "black"
        mortar_color = "blue"
        fo_color = "red"
        target_color = "yellow"

        self.graph_canvas.config(bg=bg_color)

        canvas_width = self.graph_canvas.winfo_width()
        canvas_height = self.graph_canvas.winfo_height()

        if self.map_image:
            # Resize the map to fit the canvas area, establishing a fixed background
            resized_image = self.map_image.resize((canvas_width, canvas_height), Image.LANCZOS)
            self.map_photo = ImageTk.PhotoImage(resized_image)
            self.graph_canvas.create_image(0, 0, anchor="nw", image=self.map_photo)
        
        # Define the map's coordinate system boundaries.
        # This ensures a fixed scale where bottom-left is (0,0).
        min_e, max_e = 0, 4607
        min_n, max_n = 0, 4607
        
        # Calculate scale and offset
        scale_e = canvas_width / (max_e - min_e) if max_e - min_e != 0 else 1
        scale_n = canvas_height / (max_n - min_n) if max_n - min_n != 0 else 1
        scale = min(scale_e, scale_n)
        
        def transform(e, n):
            x = (e - min_e) * scale
            y = canvas_height - (n - min_n) * scale
            return x, y

        # Transform coordinates
        mortar_x, mortar_y = transform(mortar_e, mortar_n)
        fo_x, fo_y = transform(fo_e, fo_n)
        target_x, target_y = transform(target_e, target_n)
        
        # Draw elements
        self.graph_canvas.create_oval(mortar_x-5, mortar_y-5, mortar_x+5, mortar_y+5, fill=mortar_color, outline=line_color)
        self.graph_canvas.create_text(mortar_x, mortar_y - 15, text="Mortar", fill=line_color)
        
        self.graph_canvas.create_oval(fo_x-5, fo_y-5, fo_x+5, fo_y+5, fill=fo_color, outline=line_color)
        self.graph_canvas.create_text(fo_x, fo_y - 15, text="FO", fill=line_color)
        
        self.graph_canvas.create_polygon(target_x, target_y-7, target_x-7, target_y+7, target_x+7, target_y+7, fill=target_color, outline=line_color)
        self.graph_canvas.create_text(target_x, target_y + 15, text="Target", fill=line_color)

if __name__ == "__main__":
    app = MortarCalculatorApp()
    app.mainloop()