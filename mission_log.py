import tkinter as tk
from tkinter import ttk
import json
import os

class MissionLog:
    def __init__(self, parent_frame, app, config_manager):
        self.app = app
        self.config_manager = config_manager
        self.log_data = []
        self.logged_target_coords = []
        self.log_file = self.config_manager.log_file_path
        self.create_log_widgets(parent_frame)
        self.load_log()

    def create_log_widgets(self, parent_frame):
        log_frame = ttk.LabelFrame(parent_frame, text="Fire Mission Log")
        log_frame.pack(fill="both", expand=True, pady=10)

        # --- Action Buttons Frame ---
        action_frame = ttk.Frame(log_frame)
        action_frame.pack(pady=5, fill="x")

        ttk.Label(action_frame, text="Target Name:").pack(side="left", padx=(0, 5))
        self.target_name_var = tk.StringVar(value="Target")
        ttk.Entry(action_frame, textvariable=self.target_name_var).pack(side="left", padx=5)

        ttk.Button(action_frame, text="Log Current Mission", command=self.log_mission).pack(side="left", padx=5)
        ttk.Button(action_frame, text="Load Selected Mission", command=self.load_selected_mission).pack(side="left", padx=5)
        ttk.Button(action_frame, text="Delete Selected Mission", command=self.delete_selected_mission).pack(side="left", padx=5)
        
        # Add Save and Load buttons to the right
        ttk.Button(action_frame, text="Save Log As...", command=self.app.save_log_as).pack(side="right", padx=5)
        ttk.Button(action_frame, text="Load Log File", command=self.app.load_log_from_file).pack(side="right", padx=5)

        # --- Log Display Frame ---
        tree_frame = ttk.Frame(log_frame)
        tree_frame.pack(pady=5, fill="both", expand=True)

        columns = ("name", "target_grid", "ammo", "azimuth", "dist", "mortar_callsign", "fo_id")
        self.log_tree = ttk.Treeview(tree_frame, columns=columns, show="headings")

        self.log_tree.heading("name", text="Target Name")
        self.log_tree.heading("target_grid", text="Target Grid")
        self.log_tree.heading("ammo", text="Ammo")
        self.log_tree.heading("azimuth", text="Azimuth (MIL)")
        self.log_tree.heading("dist", text="Distance (m)")
        self.log_tree.heading("mortar_callsign", text="Mortar Callsign")
        self.log_tree.heading("fo_id", text="FO ID")

        self.log_tree.column("name", width=120)
        self.log_tree.column("target_grid", width=100)
        self.log_tree.column("ammo", width=80)
        self.log_tree.column("azimuth", width=100)
        self.log_tree.column("dist", width=100)
        self.log_tree.column("mortar_callsign", width=120)
        self.log_tree.column("fo_id", width=120)

        self.log_tree.pack(side="left", fill="both", expand=True)
        self.scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.log_tree.yview)
        self.log_tree.configure(yscroll=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")

    def log_mission(self):
        # This will now call a method on the main app to get the required data
        mission_data = self.app.get_current_mission_data_for_log()
        if mission_data:
            self.log_data.append(mission_data)
            self.update_log_tree()
            self.save_log()

    def load_selected_mission(self):
        selected_item = self.log_tree.selection()
        if not selected_item: return
        
        selected_index = self.log_tree.index(selected_item[0])
        mission_data = self.log_data[selected_index]
        self.app.load_mission_data_from_log(mission_data)

    def delete_selected_mission(self):
        selected_item = self.log_tree.selection()
        if not selected_item: return

        selected_index = self.log_tree.index(selected_item[0])
        del self.log_data[selected_index]
        self.update_log_tree()
        self.save_log()

    def clear_log(self):
        """Clears all entries from the log."""
        self.log_data = []
        self.update_log_tree()
        self.save_log()

    def get_log_data(self):
        return self.log_data

    def load_log_data(self, data):
        self.log_data = data
        self.update_log_tree()

    def save_log(self):
        with open(self.log_file, "w") as f:
            json.dump(self.log_data, f, indent=4)

    def load_log(self):
        if not os.path.exists(self.log_file):
            # Create the file if it does not exist
            with open(self.log_file, "w") as f:
                json.dump([], f)
        
        try:
            with open(self.log_file, "r") as f:
                self.log_data = json.load(f)
        except (json.JSONDecodeError, TypeError):
            self.log_data = []
        self.update_log_tree()

    def update_log_tree(self):
        """
        Updates the mission log Treeview.
        This version includes optimizations to prevent rendering artifacts during updates.
        """
        # Detach scrollbar to prevent visual glitches during update
        if hasattr(self, 'scrollbar'):
            self.log_tree.configure(yscrollcommand=None)

        # More efficient way to clear the tree
        self.log_tree.delete(*self.log_tree.get_children())
        self.logged_target_coords.clear()

        for mission in self.log_data:
            target_name = mission.get("target_name", "")
            grid_str = mission.get("calculated_target_grid", "")
            
            # Attempt to parse the grid to store coordinates for map plotting
            try:
                from calculations import parse_grid # Local import to avoid circular dependency
                easting, northing = parse_grid(grid_str)
                self.logged_target_coords.append({"name": target_name, "coords": (easting, northing)})
            except (ValueError, TypeError):
                pass # Ignore missions with invalid grids

            # Correctly extract the callsign from the nested data structure
            mortars = mission.get("mortars", [])
            callsign = mortars[0].get("callsign", "") if mortars else ""

            display_values = (
                target_name,
                grid_str,
                mission.get("ammo", ""),
                mission.get("mortar_to_target_azimuth", ""),
                mission.get("mortar_to_target_dist", ""),
                callsign,
                mission.get("fo_id", "")
            )
            self.log_tree.insert("", "end", values=display_values)

        # Re-attach scrollbar and force UI update
        if hasattr(self, 'scrollbar'):
            self.log_tree.configure(yscrollcommand=self.scrollbar.set)
        self.app.update_idletasks()