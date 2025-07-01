import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

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

    def plot_positions(self):
        self.graph_canvas.delete("all")
        
        bg_color = "#252526" if self.app.is_dark_mode else "white"
        mortar_color, fo_color, target_color = "blue", "yellow", "red"
        self.graph_canvas.config(bg=bg_color)

        canvas_width = self.graph_canvas.winfo_width()
        canvas_height = self.graph_canvas.winfo_height()
        min_e, min_n, max_e, max_n = self.app.map_view
        view_width = max_e - min_e
        view_height = max_n - min_n

        if self.app.map_image and view_width > 0 and view_height > 0:
            map_scale_x = self.app.map_x_max_var.get()
            map_scale_y = self.app.map_y_max_var.get()
            img_width, img_height = self.app.map_image.size

            if map_scale_x <= 0 or map_scale_y <= 0: return

            scale = min(canvas_width / view_width, canvas_height / view_height)
            render_width = int(view_width * scale)
            render_height = int(view_height * scale)
            offset_x = (canvas_width - render_width) // 2
            offset_y = (canvas_height - render_height) // 2

            crop_min_x = (min_e / map_scale_x) * img_width
            crop_max_x = (max_e / map_scale_x) * img_width
            crop_min_y = ((map_scale_y - max_n) / map_scale_y) * img_height
            crop_max_y = ((map_scale_y - min_n) / map_scale_y) * img_height

            if crop_max_x > crop_min_x and crop_max_y > crop_min_y:
                cropped_img = self.app.map_image.crop((crop_min_x, crop_min_y, crop_max_x, crop_max_y))
                resized_image = cropped_img.resize((render_width, render_height), Image.LANCZOS)
                self.app.map_photo = ImageTk.PhotoImage(resized_image)
                self.graph_canvas.create_image(offset_x, offset_y, anchor="nw", image=self.app.map_photo)

        def transform(e, n):
            scale = min(canvas_width / view_width, canvas_height / view_height)
            render_width = view_width * scale
            render_height = view_height * scale
            offset_x = (canvas_width - render_width) // 2
            offset_y = (canvas_height - render_height) // 2
            x = offset_x + ((e - min_e) * scale)
            y = offset_y + ((max_n - n) * scale)
            return x, y

        if self.app.last_coords:
            mortar_x, mortar_y = transform(self.app.last_coords['mortar_e'], self.app.last_coords['mortar_n'])
            fo_x, fo_y = transform(self.app.last_coords['fo_e'], self.app.last_coords['fo_n'])
            target_x, target_y = transform(self.app.last_coords['target_e'], self.app.last_coords['target_n'])
            
            self.graph_canvas.create_oval(mortar_x-5, mortar_y-5, mortar_x+5, mortar_y+5, fill=mortar_color, outline="black")
            self.graph_canvas.create_text(mortar_x, mortar_y - 15, text="Mortar", fill="black")
            if not (self.app.admin_mode_enabled.get() and self.app.admin_target_pin):
                self.graph_canvas.create_oval(fo_x-5, fo_y-5, fo_x+5, fo_y+5, fill=fo_color, outline="black")
                self.graph_canvas.create_text(fo_x, fo_y - 15, text="FO", fill="black")
            self.graph_canvas.create_polygon(target_x, target_y-7, target_x-7, target_y+7, target_x+7, target_y+7, fill=target_color, outline="black")
            self.graph_canvas.create_text(target_x, target_y + 15, text="Target", fill="black")
        elif self.app.admin_mode_enabled.get() and self.app.admin_target_pin:
            target_e, target_n = self.app.admin_target_pin
            target_x, target_y = transform(target_e, target_n)
            self.graph_canvas.create_polygon(target_x, target_y-7, target_x-7, target_y+7, target_x+7, target_y+7, fill=target_color, outline="black")
            self.graph_canvas.create_text(target_x, target_y + 15, text="Target", fill="black")
        elif self.app.map_image:
             pass
        else:
            text_color = "black"
            placeholder_x = 50
            mortar_y, fo_y, target_y = canvas_height - 80, canvas_height - 50, canvas_height - 20
            self.graph_canvas.create_oval(placeholder_x - 5, mortar_y - 5, placeholder_x + 5, mortar_y + 5, fill=mortar_color, outline="black")
            self.graph_canvas.create_text(placeholder_x + 25, mortar_y, text="Mortar", fill=text_color, anchor="w")
            self.graph_canvas.create_oval(placeholder_x - 5, fo_y - 5, placeholder_x + 5, fo_y + 5, fill=fo_color, outline="black")
            self.graph_canvas.create_text(placeholder_x + 25, fo_y, text="FO", fill=text_color, anchor="w")
            self.graph_canvas.create_polygon(placeholder_x, target_y - 7, placeholder_x - 7, target_y + 7, placeholder_x + 7, target_y + 7, fill=target_color, outline="black")
            self.graph_canvas.create_text(placeholder_x + 25, target_y, text="Target", fill=text_color, anchor="w")

    def zoom(self, event):
        if not self.app.map_image:
            return

        canvas_width = self.graph_canvas.winfo_width()
        canvas_height = self.graph_canvas.winfo_height()
        
        min_e, min_n, max_e, max_n = self.app.map_view
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
        
        self.app.map_view = [new_min_e, new_min_n, new_max_e, new_max_n]
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
        self.app.pan_start_x = event.x
        self.app.pan_start_y = event.y

    def pan(self, event):
        if not self.app.map_image:
            return
            
        dx = event.x - self.app.pan_start_x
        dy = event.y - self.app.pan_start_y

        canvas_width = self.graph_canvas.winfo_width()
        canvas_height = self.graph_canvas.winfo_height()
        
        min_e, min_n, max_e, max_n = self.app.map_view
        map_width = max_e - min_e
        map_height = max_n - min_n

        scale = min(canvas_width / map_width, canvas_height / map_height)
        
        delta_e = dx / scale
        delta_n = dy / scale

        self.app.map_view = [min_e - delta_e, min_n + delta_n, max_e - delta_e, max_n + delta_n]

        self.app.pan_start_x = event.x
        self.app.pan_start_y = event.y
        
        self.plot_positions()

    def auto_zoom_to_pins(self):
        if not self.app.last_coords:
            return

        coords = [
            (self.app.last_coords['mortar_e'], self.app.last_coords['mortar_n']),
            (self.app.last_coords['fo_e'], self.app.last_coords['fo_n']),
            (self.app.last_coords['target_e'], self.app.last_coords['target_n'])
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
        
        self.app.map_view = [view_min_e, view_min_n, view_max_e, view_max_n]

    def canvas_to_map_coords(self, canvas_x, canvas_y):
        if not self.app.map_image:
            return None, None

        canvas_width = self.graph_canvas.winfo_width()
        canvas_height = self.graph_canvas.winfo_height()
        min_e, min_n, max_e, max_n = self.app.map_view
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