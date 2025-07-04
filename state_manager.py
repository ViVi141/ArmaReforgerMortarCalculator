import tkinter as tk

class StateManager:
    """
    Manages the state of the application using tkinter variables.
    This class centralizes all state variables, decoupling them from the main
    application logic and UI components.
    """
    def __init__(self):
        # UI Variables
        self.disable_danger_close_var = tk.BooleanVar(value=False)
        self.map_x_max_var = tk.DoubleVar(value=4607)
        self.map_y_max_var = tk.DoubleVar(value=4607)
        self.selected_map_var = tk.StringVar()
        self.admin_mode_enabled = tk.BooleanVar(value=False)
        self.admin_target_pin = None

        # Map State
        self.map_image = None
        self.map_photo = None
        self.map_view = [0, 0, 4607, 4607]
        self.pan_start_x = 0
        self.pan_start_y = 0
        self.last_coords = {}
        self.last_solutions = []
        
        self.num_mortars_var = tk.IntVar(value=1)
        self.fire_mission_type_var = tk.StringVar(value="Regular")
        
        # This list will hold dictionaries of tk.Variables for each mortar
        self.mortar_input_vars = []

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
        
        # Calculated Target Details
        self.target_grid_10_var = tk.StringVar(value="----- -----")
        self.target_elev_var = tk.StringVar(value="-- m")
        self.mortar_to_target_azimuth_var = tk.StringVar(value="-- MIL")
        self.mortar_to_target_dist_var = tk.StringVar(value="-- m")
        self.mortar_to_target_elev_diff_var = tk.StringVar(value="-- m")
        
        self.correction_status_var = tk.StringVar()
        
        # Firing Solution Variables (for single solution display, now mostly deprecated)
        self.least_tof_charge_var = tk.StringVar(value="--")
        self.least_tof_elev_var = tk.StringVar(value="-- MIL")
        self.least_tof_tof_var = tk.StringVar(value="-- sec")
        self.least_tof_disp_var = tk.StringVar(value="-- m")
        self.most_tof_charge_var = tk.StringVar(value="--")
        self.most_tof_elev_var = tk.StringVar(value="-- MIL")
        self.most_tof_tof_var = tk.StringVar(value="-- sec")
        self.most_tof_disp_var = tk.StringVar(value="-- m")

        # Quick Fire Data
        self.quick_azimuth_var = tk.StringVar(value="---- MIL")
        self.quick_least_tof_elev_var = tk.StringVar(value="C-: ---- MIL")
        self.quick_most_tof_elev_var = tk.StringVar(value="C-: ---- MIL")

        # Mission Log State
        self.loaded_target_name = tk.StringVar()

    def add_mortar(self):
        """Adds a new set of variables for a mortar."""
        self.mortar_input_vars.append({
            "grid": tk.StringVar(value="0000000000"),
            "elev": tk.DoubleVar(value=100),
            "callsign": tk.StringVar(),
            "locked": tk.BooleanVar(value=False)
        })

    def clear_mortars(self):
        """Clears all mortar variables."""
        self.mortar_input_vars.clear()

    def get_mortar_vars(self, index):
        """Returns the variables for a specific mortar."""
        return self.mortar_input_vars[index]
