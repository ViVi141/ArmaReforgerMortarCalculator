import os
import sys
import json
import shutil
from tkinter import messagebox
from utils import resource_path

class ConfigManager:
    def __init__(self):
        self.maps_dir = resource_path('maps')
        self.config_path = resource_path('maps_config.json')
        self.log_file_path = resource_path('fire_missions.json')
        self.maps_config = {}
        self._initialize()


    def _initialize(self):
        if not os.path.exists(self.maps_dir):
            os.makedirs(self.maps_dir)
        
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                self.maps_config = json.load(f)
        else:
            self.maps_config = {
                "Zarichne.png": { "x_max": 4607, "y_max": 4607 },
                "danger_close_distance": 100
            }
            self.save_config()

    def get_map_list(self):
        return [f for f in os.listdir(self.maps_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    def get_map_config(self, map_name):
        return self.maps_config.get(map_name, {})

    def save_config(self):
        with open(self.config_path, 'w') as f:
            json.dump(self.maps_config, f, indent=4)

    def get_danger_close_distance(self):
        return self.maps_config.get("danger_close_distance", 100)

    def set_danger_close_distance(self, distance):
        self.maps_config["danger_close_distance"] = distance
        self.save_config()

    def add_new_map(self, file_path, x_max, y_max):
        map_filename = os.path.basename(file_path)
        dest_path = os.path.join(self.maps_dir, map_filename)

        try:
            shutil.copy(file_path, dest_path)
            self.maps_config[map_filename] = {
                "x_max": x_max,
                "y_max": y_max
            }
            self.save_config()
            messagebox.showinfo("Success", f"Map '{map_filename}' uploaded and saved.")
            return True, map_filename
        except Exception as e:
            messagebox.showerror("Error", f"Failed to upload map: {e}")
            return False, None