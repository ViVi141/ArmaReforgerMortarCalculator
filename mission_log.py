import tkinter as tk
from tkinter import ttk
import json
import os

class MissionLog:
    def __init__(self, parent_frame, app):
        self.app = app
        self.log_data = []
        self.log_file = "fire_missions.json"
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

        # --- Log Display Frame ---
        tree_frame = ttk.Frame(log_frame)
        tree_frame.pack(pady=5, fill="both", expand=True)

        columns = ("name", "target_grid", "ammo", "azimuth", "dist")
        self.log_tree = ttk.Treeview(tree_frame, columns=columns, show="headings")

        self.log_tree.heading("name", text="Target Name")
        self.log_tree.heading("target_grid", text="Target Grid")
        self.log_tree.heading("ammo", text="Ammo")
        self.log_tree.heading("azimuth", text="Azimuth (MIL)")
        self.log_tree.heading("dist", text="Distance (m)")
        
        for col in columns:
            self.log_tree.column(col, width=150)

        self.log_tree.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.log_tree.yview)
        self.log_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

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
        for i in self.log_tree.get_children():
            self.log_tree.delete(i)
        for mission in self.log_data:
            display_values = (
                mission.get("target_name", ""),
                mission.get("calculated_target_grid", ""),
                mission.get("ammo", ""),
                mission.get("mortar_to_target_azimuth", ""),
                mission.get("mortar_to_target_dist", "")
            )
            self.log_tree.insert("", "end", values=display_values)