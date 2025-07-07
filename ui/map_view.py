import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import math

class MapView(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.graph_canvas = tk.Canvas(self, bg="white", width=400, height=400)
        self.graph_canvas.grid(row=0, column=0, sticky="nsew")

        self.graph_canvas.bind("<MouseWheel>", self.zoom)
        self.graph_canvas.bind("<ButtonPress-1>", self.start_pan)
        self.graph_canvas.bind("<B1-Motion>", self.pan)
        self.graph_canvas.bind("<Button-3>", self.app.on_map_right_click)

        zoom_button_frame = ttk.Frame(self)
        zoom_button_frame.place(relx=0.98, rely=0.02, anchor="ne")
        ttk.Button(zoom_button_frame, text="+", width=2, command=self.zoom_in).pack()
        ttk.Button(zoom_button_frame, text="-", width=2, command=self.zoom_out).pack()

        self.show_saved_target_var = tk.BooleanVar(value=False)
        show_saved_target_check = ttk.Checkbutton(self, text="Show Logged Targets", variable=self.show_saved_target_var, command=self.plot_positions)
        show_saved_target_check.place(relx=0.02, rely=0.02, anchor="nw")

    def plot_positions(self):
        self.graph_canvas.delete("all")

        bg_color = "#252526" if self.app.is_dark_mode else "white"
        mortar_colors = ["blue", "green", "purple", "orange"]
        fo_color, target_color = "yellow", "red"
        self.graph_canvas.config(bg=bg_color)

        canvas_width = self.graph_canvas.winfo_width()
        canvas_height = self.graph_canvas.winfo_height()
        min_e, min_n, max_e, max_n = self.app.state.map_view
        view_width = max_e - min_e
        view_height = max_n - min_n

        # 1. Draw Map Background
        if self.app.state.map_image and view_width > 0 and view_height > 0:
            self._draw_map_image(canvas_width, canvas_height, view_width, view_height)
        elif self.app.theme_manager.theme_config.get("use_logo_as_background"):
            self._draw_logo_background()
        
        # 2. Define Coordinate Transformation Function
        def transform(e, n):
            scale = min(canvas_width / view_width, canvas_height / view_height)
            render_width = view_width * scale
            render_height = view_height * scale
            offset_x = (canvas_width - render_width) // 2
            offset_y = (canvas_height - render_height) // 2
            x = offset_x + ((e - min_e) * scale)
            y = offset_y + ((max_n - n) * scale)
            return x, y, scale

        # 3. Draw Pins and Overlays
        if self.app.state.last_solutions:
            self._plot_solution_pins(transform, mortar_colors, fo_color, canvas_width, canvas_height)
        elif self.show_saved_target_var.get():
            self._plot_logged_targets(transform)
        elif self.app.state.admin_mode_enabled.get() and self.app.state.admin_target_pin:
            self._plot_admin_pin(transform, target_color)
        elif not self.app.state.map_image:
            self._draw_placeholder_pins(mortar_colors, fo_color, target_color, canvas_height)

    def _draw_map_image(self, canvas_width, canvas_height, view_width, view_height):
        map_scale_x = self.app.state.map_x_max_var.get()
        map_scale_y = self.app.state.map_y_max_var.get()
        img_width, img_height = self.app.state.map_image.size

        if map_scale_x <= 0 or map_scale_y <= 0: return

        scale = min(canvas_width / view_width, canvas_height / view_height)
        render_width = int(view_width * scale)
        render_height = int(view_height * scale)
        offset_x = (canvas_width - render_width) // 2
        offset_y = (canvas_height - render_height) // 2

        min_e, min_n, max_e, max_n = self.app.state.map_view
        crop_min_x = (min_e / map_scale_x) * img_width
        crop_max_x = (max_e / map_scale_x) * img_width
        crop_min_y = ((map_scale_y - max_n) / map_scale_y) * img_height
        crop_max_y = ((map_scale_y - min_n) / map_scale_y) * img_height

        if crop_max_x > crop_min_x and crop_max_y > crop_min_y:
            cropped_img = self.app.state.map_image.crop((crop_min_x, crop_min_y, crop_max_x, crop_max_y))
            resized_image = cropped_img.resize((render_width, render_height), Image.LANCZOS)
            self.app.state.map_photo = ImageTk.PhotoImage(resized_image)
            self.graph_canvas.create_image(offset_x, offset_y, anchor="nw", image=self.app.state.map_photo)

    def _draw_logo_background(self):
        logo_path = self.app.theme_manager.theme_config.get("logo_path")
        if logo_path and os.path.exists(logo_path):
            try:
                logo_image = Image.open(logo_path)
                self.logo_photo = ImageTk.PhotoImage(logo_image)
                self.graph_canvas.create_image(0, 0, anchor="nw", image=self.logo_photo)
            except Exception as e:
                print(f"Error loading logo image: {e}")

    def _plot_solution_pins(self, transform, mortar_colors, fo_color, canvas_width, canvas_height):
        solutions = self.app.state.last_solutions
        num_mortars = len(solutions)
        
        for i in range(num_mortars):
            mortar_e, mortar_n = solutions[i]['mortar_coords']
            mortar_x, mortar_y, _ = transform(mortar_e, mortar_n)
            self.graph_canvas.create_oval(mortar_x-5, mortar_y-5, mortar_x+5, mortar_y+5, fill=mortar_colors[i], outline="black")
            self.graph_canvas.create_text(mortar_x, mortar_y - 15, text=f"Gun {i+1}", fill="black")

        fo_x, fo_y, _ = transform(solutions[0]['fo_coords'][0], solutions[0]['fo_coords'][1])
        
        if not (self.app.state.admin_mode_enabled.get() and self.app.state.admin_target_pin):
            self.graph_canvas.create_oval(fo_x-5, fo_y-5, fo_x+5, fo_y+5, fill=fo_color, outline="black")
            self.graph_canvas.create_text(fo_x, fo_y - 15, text="FO", fill="black")

        mission_type = self.app.state.fire_mission_type_var.get()
        
        if mission_type == "Regular":
            self._plot_regular_mission(solutions, transform, mortar_colors, canvas_width, canvas_height)
        elif mission_type in ["Small Barrage", "Large Barrage"]:
            self._plot_barrage_mission(solutions, transform, mortar_colors)
        elif mission_type == "Creeping Barrage":
            self._plot_creeping_barrage(solutions, transform, mortar_colors)

    def _plot_regular_mission(self, solutions, transform, mortar_colors, canvas_width, canvas_height):
        target_e, target_n = solutions[0]['target_coords']
        target_x, target_y, scale = transform(target_e, target_n)

        min_disp_radius = min(sol['least_tof']['dispersion'] for sol in solutions)
        max_disp_radius = max(sol['most_tof']['dispersion'] for sol in solutions)
        scaled_min_disp = min_disp_radius * scale
        scaled_max_disp = max_disp_radius * scale

        if scaled_max_disp > scaled_min_disp:
            self.graph_canvas.create_oval(target_x - scaled_max_disp, target_y - scaled_max_disp, target_x + scaled_max_disp, target_y + scaled_max_disp, outline="yellow", width=2)
        if scaled_min_disp > 0:
            self.graph_canvas.create_oval(target_x - scaled_min_disp, target_y - scaled_min_disp, target_x + scaled_min_disp, target_y + scaled_min_disp, outline="red", width=2)

        target_label = self.app.state.loaded_target_name.get() or "Target"
        for i, sol in enumerate(solutions):
            self.graph_canvas.create_oval(target_x - 10, target_y - 10, target_x + 10, target_y + 10, outline=mortar_colors[i], width=2)
            self.graph_canvas.create_polygon(target_x, target_y-7, target_x-7, target_y+7, target_x+7, target_y+7, fill=mortar_colors[i], outline="black")
        self.graph_canvas.create_text(target_x, target_y + 15, text=target_label, fill="black")

        legend_x = canvas_width - 150
        legend_y = canvas_height - 50
        self.graph_canvas.create_rectangle(legend_x, legend_y, legend_x + 20, legend_y + 20, fill="red", outline="black")
        self.graph_canvas.create_text(legend_x + 30, legend_y + 10, text="Kill Area", anchor="w", fill="black")
        self.graph_canvas.create_rectangle(legend_x, legend_y + 25, legend_x + 20, legend_y + 45, fill="yellow", outline="black")
        self.graph_canvas.create_text(legend_x + 30, legend_y + 35, text="Expected Injury Area", anchor="w", fill="black")

    def _plot_barrage_mission(self, solutions, transform, mortar_colors):
        sol = solutions[0]
        target_e, target_n = sol['target_coords']
        target_x, target_y, scale = transform(target_e, target_n)
        for i, sol_i in enumerate(solutions):
            self.graph_canvas.create_oval(target_x - 10, target_y - 10, target_x + 10, target_y + 10, outline=mortar_colors[i], width=2)
            self.graph_canvas.create_polygon(target_x, target_y-7, target_x-7, target_y+7, target_x+7, target_y+7, fill=mortar_colors[i], outline="black")
        self.graph_canvas.create_text(target_x, target_y + 15, text="Target", fill="black")
        
        disp = sol['least_tof']['dispersion'] * scale
        self.graph_canvas.create_oval(target_x - disp, target_y - disp, target_x + disp, target_y + disp, outline="red", width=2)

    def _plot_creeping_barrage(self, solutions, transform, mortar_colors):
        first_target = solutions[0]['target_coords']
        last_target = solutions[-1]['target_coords']
        dispersion = solutions[0]['least_tof']['dispersion']
        
        for i, sol in enumerate(solutions):
            target_e, target_n = sol['target_coords']
            target_x, target_y, _ = transform(target_e, target_n)
            self.graph_canvas.create_oval(target_x - 10, target_y - 10, target_x + 10, target_y + 10, outline=mortar_colors[i], width=2)
            self.graph_canvas.create_polygon(target_x, target_y-7, target_x-7, target_y+7, target_x+7, target_y+7, fill=mortar_colors[i], outline="black")
            self.graph_canvas.create_text(target_x, target_y + 15, text=f"Target {i+1}", fill="black")

        creep_vec_e = last_target[0] - first_target[0]
        creep_vec_n = last_target[1] - first_target[1]
        
        if creep_vec_e == 0 and creep_vec_n == 0:
            creep_angle_rad = 0
        else:
            creep_angle_rad = math.atan2(creep_vec_e, creep_vec_n)

        perp_angle_rad = creep_angle_rad + math.pi / 2
        
        _, _, scale = transform(0,0) # Get scale
        radius_scaled = dispersion * scale

        start_e = first_target[0] - dispersion * math.sin(creep_angle_rad)
        start_n = first_target[1] - dispersion * math.cos(creep_angle_rad)
        end_e = last_target[0] + dispersion * math.sin(creep_angle_rad)
        end_n = last_target[1] + dispersion * math.cos(creep_angle_rad)

        p1_x, p1_y, _ = transform(start_e - dispersion * math.sin(perp_angle_rad), start_n - dispersion * math.cos(perp_angle_rad))
        p2_x, p2_y, _ = transform(start_e + dispersion * math.sin(perp_angle_rad), start_n + dispersion * math.cos(perp_angle_rad))
        p3_x, p3_y, _ = transform(end_e + dispersion * math.sin(perp_angle_rad), end_n + dispersion * math.cos(perp_angle_rad))
        p4_x, p4_y, _ = transform(end_e - dispersion * math.sin(perp_angle_rad), end_n - dispersion * math.cos(perp_angle_rad))
        
        self.graph_canvas.create_polygon(p1_x, p1_y, p2_x, p2_y, p3_x, p3_y, p4_x, p4_y, outline="red", fill="", width=2)

    def _plot_admin_pin(self, transform, target_color):
        target_e, target_n = self.app.state.admin_target_pin
        target_x, target_y, _ = transform(target_e, target_n)
        self.graph_canvas.create_polygon(target_x, target_y-7, target_x-7, target_y+7, target_x+7, target_y+7, fill=target_color, outline="black")
        self.graph_canvas.create_text(target_x, target_y + 15, text="Target", fill="black")

    def _draw_placeholder_pins(self, mortar_colors, fo_color, target_color, canvas_height):
        text_color = "black"
        placeholder_x = 50
        mortar_y, fo_y, target_y = canvas_height - 80, canvas_height - 50, canvas_height - 20
        self.graph_canvas.create_oval(placeholder_x - 5, mortar_y - 5, placeholder_x + 5, mortar_y + 5, fill=mortar_colors[0], outline="black")
        self.graph_canvas.create_text(placeholder_x + 25, mortar_y, text="Mortar", fill=text_color, anchor="w")
        self.graph_canvas.create_oval(placeholder_x - 5, fo_y - 5, placeholder_x + 5, fo_y + 5, fill=fo_color, outline="black")
        self.graph_canvas.create_text(placeholder_x + 25, fo_y, text="FO", fill=text_color, anchor="w")
        self.graph_canvas.create_polygon(placeholder_x, target_y - 7, placeholder_x - 7, target_y + 7, placeholder_x + 7, target_y + 7, fill=target_color, outline="black")
        self.graph_canvas.create_text(placeholder_x + 25, target_y, text="Target", fill=text_color, anchor="w")


    def _plot_logged_targets(self, transform_func):
        """Plots all targets from the mission log on the map."""
        logged_targets = self.app.mission_log.logged_target_coords
        for target in logged_targets:
            try:
                target_e, target_n = target["coords"]
                target_x, target_y, _ = transform_func(target_e, target_n)
                
                # Draw a distinct pin for logged targets
                self.graph_canvas.create_polygon(
                    target_x, target_y - 9,
                    target_x - 5, target_y,
                    target_x, target_y + 9,
                    target_x + 5, target_y,
                    fill="cyan", outline="black", tags="logged_target"
                )
                self.graph_canvas.create_text(target_x, target_y + 18, text=target["name"], fill="black", font=("Consolas", 9, "bold"), tags="logged_target")
            except Exception as e:
                print(f"Could not plot logged target {target.get('name', 'Unknown')}: {e}")

    def zoom(self, event):
        if not self.app.state.map_image:
            return

        canvas_width = self.graph_canvas.winfo_width()
        canvas_height = self.graph_canvas.winfo_height()
        
        min_e, min_n, max_e, max_n = self.app.state.map_view
        view_width = max_e - min_e
        view_height = max_n - min_n

        if view_width <= 0 or view_height <= 0: return

        scale = min(canvas_width / view_width, canvas_height / view_height)
        render_width = view_width * scale
        render_height = view_height * scale
        offset_x = (canvas_width - render_width) / 2
        offset_y = (canvas_height - render_height) / 2

        cursor_e = min_e + (event.x - offset_x) / scale
        cursor_n = max_n - (event.y - offset_y) / scale

        zoom_factor = 1.1 if event.delta > 0 else 1 / 1.1
        new_view_width = view_width / zoom_factor
        new_view_height = view_height / zoom_factor

        new_min_e = cursor_e - (event.x - offset_x) / scale * (new_view_width / view_width)
        new_max_e = new_min_e + new_view_width
        
        new_min_n = cursor_n - (1 - ((event.y - offset_y) / render_height)) * new_view_height
        new_max_n = new_min_n + new_view_height
        
        self.app.state.map_view = [new_min_e, new_min_n, new_max_e, new_max_n]
        self.plot_positions()

    def zoom_in(self):
        event = tk.Event()
        event.delta = 120
        event.x = self.graph_canvas.winfo_width() // 2
        event.y = self.graph_canvas.winfo_height() // 2
        self.zoom(event)

    def zoom_out(self):
        event = tk.Event()
        event.delta = -120
        event.x = self.graph_canvas.winfo_width() // 2
        event.y = self.graph_canvas.winfo_height() // 2
        self.zoom(event)

    def start_pan(self, event):
        self.app.state.pan_start_x = event.x
        self.app.state.pan_start_y = event.y

    def pan(self, event):
        if not self.app.state.map_image:
            return
            
        dx = event.x - self.app.state.pan_start_x
        dy = event.y - self.app.state.pan_start_y

        canvas_width = self.graph_canvas.winfo_width()
        canvas_height = self.graph_canvas.winfo_height()
        
        min_e, min_n, max_e, max_n = self.app.state.map_view
        map_width = max_e - min_e
        map_height = max_n - min_n

        scale = min(canvas_width / map_width, canvas_height / map_height)
        
        delta_e = dx / scale
        delta_n = dy / scale

        self.app.state.map_view = [min_e - delta_e, min_n + delta_n, max_e - delta_e, max_n + delta_n]

        self.app.state.pan_start_x = event.x
        self.app.state.pan_start_y = event.y
        
        self.plot_positions()

    def auto_zoom_to_pins(self):
        if not self.app.state.last_coords:
            return

        coords = self.app.state.last_coords.get('mortars', []) + [
            (self.app.state.last_coords['fo_e'], self.app.state.last_coords['fo_n']),
            (self.app.state.last_coords['target_e'], self.app.state.last_coords['target_n'])
        ]

        min_e = min(c[0] for c in coords)
        max_e = max(c[0] for c in coords)
        min_n = min(c[1] for c in coords)
        max_n = max(c[1] for c in coords)

        padding_e = (max_e - min_e) * 0.2
        padding_n = (max_n - min_n) * 0.2
        
        if padding_e == 0: padding_e = 100
        if padding_n == 0: padding_n = 100

        view_min_e = min_e - padding_e
        view_max_e = max_e + padding_e
        view_min_n = min_n - padding_n
        view_max_n = max_n + padding_n

        view_width = view_max_e - view_min_e
        view_height = view_max_n - view_min_n
        
        canvas_width = self.graph_canvas.winfo_width()
        canvas_height = self.graph_canvas.winfo_height()
        
        if canvas_width > 1 and canvas_height > 1 and view_width > 0 and view_height > 0:
            canvas_aspect = canvas_width / canvas_height
            view_aspect = view_width / view_height

            if canvas_aspect > view_aspect:
                new_width = view_height * canvas_aspect
                diff = new_width - view_width
                view_min_e -= diff / 2
                view_max_e += diff / 2
            elif canvas_aspect < view_aspect:
                new_height = view_width / canvas_aspect
                diff = new_height - view_height
                view_min_n -= diff / 2
                view_max_n += diff / 2
        
        self.app.state.map_view = [view_min_e, view_min_n, view_max_e, view_max_n]

    def canvas_to_map_coords(self, canvas_x, canvas_y):
        if not self.app.state.map_image:
            return None, None

        canvas_width = self.graph_canvas.winfo_width()
        canvas_height = self.graph_canvas.winfo_height()
        min_e, min_n, max_e, max_n = self.app.state.map_view
        map_width = max_e - min_e
        map_height = max_n - min_n

        if map_width <= 0 or map_height <= 0:
            return None, None

        scale = min(canvas_width / map_width, canvas_height / map_height)
        render_width = map_width * scale
        render_height = map_height * scale
        offset_x = (canvas_width - render_width) // 2
        offset_y = (canvas_height - render_height) // 2

        if not (offset_x <= canvas_x < offset_x + render_width and 
                offset_y <= canvas_y < offset_y + render_height):
            return None, None

        map_e = min_e + (canvas_x - offset_x) / scale
        map_n = max_n - (canvas_y - offset_y) / scale
        
        return map_e, map_n