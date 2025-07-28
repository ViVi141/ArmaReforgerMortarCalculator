import json
import os
from tkinter import messagebox
from utils import resource_path

class ThemeManager:
    def __init__(self, app):
        self.app = app
        self.theme_config = {}
        self.theme_config_path = resource_path('theme_config.json')
        self._initialize_theme()

    def _initialize_theme(self):
        if os.path.exists(self.theme_config_path):
            with open(self.theme_config_path, 'r') as f:
                self.theme_config = json.load(f)
        else:
            self.theme_config = {
                "title": "Arma Reforger Mortar Calculator",
                "logo_path": "",
                "use_logo_as_background": False
            }
            self.save_theme_config()

    def save_theme_config(self):
        with open(self.theme_config_path, 'w') as f:
            json.dump(self.theme_config, f, indent=4)

    def apply_theme(self):
        self.app.title(self.theme_config.get("title", "Arma Reforger Mortar Calculator"))
        
        logo_path = self.theme_config.get("logo_path")
        if logo_path and os.path.exists(logo_path):
            if self.theme_config.get("use_logo_as_background"):
                # This will require changes in MapView to handle a background image
                pass
        
        # The dark/light mode toggle will remain as the primary theme mechanism for now.
        # The color palette feature can be added later if desired.
        self.app.toggle_theme()

    # def set_title(self, title):
    #     self.theme_config["title"] = title
    #     self.save_theme_config()
    #     self.app.title(title)

    # def set_logo(self, logo_path, use_as_background):
    #     self.theme_config["logo_path"] = logo_path
    #     self.theme_config["use_logo_as_background"] = use_as_background
    #     self.save_theme_config()
    #     # This will require a mechanism to update the view
    #     messagebox.showinfo("Theme Update", "Logo updated. Restart the application to see changes.")
