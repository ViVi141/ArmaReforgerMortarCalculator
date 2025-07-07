import os
import sys
import json
import shutil
from tkinter import messagebox

class ConfigManager:
    def __init__(self):
        self.app_dir = self._get_app_dir()
        self.maps_dir = os.path.join(self.app_dir, 'maps')
        self.config_path = os.path.join(self.app_dir, 'maps_config.json')
        self.log_file_path = os.path.join(self.app_dir, 'fire_missions.json')
        self.maps_config = {}
        self._initialize()

    def _get_app_dir(self):
        if getattr(sys, 'frozen', False):
            return sys._MEIPASS
        else:
            # This assumes config_manager.py is in a 'config' subdirectory.
            return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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