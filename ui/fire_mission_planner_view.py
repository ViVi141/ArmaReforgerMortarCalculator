import tkinter as tk
import json
import os
from tkinter import ttk, filedialog, simpledialog
from PIL import Image, ImageTk, ImageGrab

class Tooltip:
    def __init__(self, widget, text, display_widget):
        self.widget = widget
        self.text = text
        self.display_widget = display_widget
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        self.display_widget.config(text=self.text)

    def hide_tooltip(self, event=None):
        self.display_widget.config(text="")

class ListSelectDialog(tk.Toplevel):
    def __init__(self, parent, title, items, is_dark_mode):
        super().__init__(parent)
        self.title(title)
        self.result = None
        self.transient(parent)

        bg_color = "#252526" if is_dark_mode else "SystemButtonFace"
        fg_color = "#00FF00" if is_dark_mode else "black"
        self.configure(bg=bg_color)

        listbox = tk.Listbox(self, bg=bg_color, fg=fg_color, selectbackground="#4a4a4a" if is_dark_mode else "blue", selectforeground="white")
        listbox.pack(padx=10, pady=10, fill="both", expand=True)
        for item in items:
            listbox.insert(tk.END, item)

        def on_select():
            if listbox.curselection():
                self.result = listbox.get(listbox.curselection())
                self.destroy()

        button_frame = ttk.Frame(self, style="TFrame")
        button_frame.pack(pady=5)
        select_button = ttk.Button(button_frame, text="Select", command=on_select, style="TButton")
        select_button.pack(side="left", padx=10)
        cancel_button = ttk.Button(button_frame, text="Cancel", command=self.destroy, style="TButton")
        cancel_button.pack(side="left", padx=10)

        self.update_idletasks()
        parent_x, parent_y = parent.winfo_x(), parent.winfo_y()
        parent_width, parent_height = parent.winfo_width(), parent.winfo_height()
        dialog_width, dialog_height = 300, 250
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        self.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.grab_set()
        self.wait_window()

class FireMissionPlannerView(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding="10")
        self.app = app
        self.start_x = None
        self.start_y = None
        self.drawn_items = []
        self.image_path = None
        self.resize_handles = []

        self.pack(fill="both", expand=True)

        # Toolbar
        self.toolbar = ttk.Frame(self)
        self.toolbar.pack(side="top", fill="x", pady=5)

        ttk.Button(self.toolbar, text="Upload Image", command=self.upload_image).pack(side="left", padx=5)
        ttk.Button(self.toolbar, text="Load Default Map", command=self.load_default_map).pack(side="left", padx=5)
        ttk.Button(self.toolbar, text="Save Plan", command=self.save_plan).pack(side="left", padx=5)
        ttk.Button(self.toolbar, text="Clear All", command=self.clear_all).pack(side="left", padx=5)
        
        ttk.Separator(self.toolbar, orient='vertical').pack(side='left', padx=5, fill='y')

        self.selected_tool = tk.StringVar(value="line")
        ttk.Radiobutton(self.toolbar, text="Line", variable=self.selected_tool, value="line").pack(side="left")
        ttk.Radiobutton(self.toolbar, text="Arrow", variable=self.selected_tool, value="arrow").pack(side="left")
        ttk.Radiobutton(self.toolbar, text="Circle", variable=self.selected_tool, value="circle").pack(side="left")
        ttk.Radiobutton(self.toolbar, text="Rectangle", variable=self.selected_tool, value="rectangle").pack(side="left")
        ttk.Radiobutton(self.toolbar, text="Text", variable=self.selected_tool, value="text").pack(side="left")
        ttk.Radiobutton(self.toolbar, text="Delete", variable=self.selected_tool, value="delete").pack(side="left")
        ttk.Radiobutton(self.toolbar, text="Resize", variable=self.selected_tool, value="resize").pack(side="left")

        ttk.Separator(self.toolbar, orient='vertical').pack(side='left', padx=5, fill='y')

        self.selected_color = tk.StringVar(value="red")
        colors = ["red", "green", "blue", "yellow", "black", "white"]
        color_menu = ttk.OptionMenu(self.toolbar, self.selected_color, self.selected_color.get(), *colors)
        color_menu.pack(side="left", padx=5)

        self.tooltip_label = ttk.Label(self.toolbar, text="", style="Tooltip.TLabel", relief="solid", borderwidth=1)
        self.tooltip_label.pack(side="right", padx=10, fill="both", expand=True)


        # Canvas for battle plan
        self.canvas = tk.Canvas(self, bg="white")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind("<ButtonPress-2>", self.start_pan)
        self.canvas.bind("<B2-Motion>", self.pan)

        Tooltip(self.canvas, "Mouse Wheel: Zoom\nMiddle Mouse Button: Pan", self.tooltip_label)

        self.apply_theme()

    def load_default_map(self):
        map_list = self.app.config_manager.get_map_list()
        if not map_list:
            return

        dialog = ListSelectDialog(self.app, "Select Default Map", map_list, self.app.is_dark_mode)
        selected_map = dialog.result

        if selected_map:
            map_path = os.path.join(self.app.config_manager.maps_dir, selected_map)
            self.load_image(map_path)

    def upload_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
        if not file_path:
            return
        self.load_image(file_path)

    def load_image(self, file_path):
        self.image_path = file_path
        image = Image.open(file_path)
        self.original_image = image.copy()
        self.zoom_level = 1.0
        self.update_image()

    def on_press(self, event):
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        if self.selected_tool.get() == "text":
            self.draw_text(self.start_x, self.start_y)
        elif self.selected_tool.get() == "delete":
            self.delete_item(event)
        elif self.selected_tool.get() == "resize":
            self.select_for_resize(event)
        else:
            self.current_item = None

    def on_drag(self, event):
        if self.selected_tool.get() == "resize" and self.current_item:
            self.resize_item(event)
        elif self.selected_tool.get() in ["line", "arrow", "circle", "rectangle"]:
            cur_x = self.canvas.canvasx(event.x)
            cur_y = self.canvas.canvasy(event.y)
            if self.current_item:
                self.canvas.delete(self.current_item)
            
            tool = self.selected_tool.get()
            color = self.selected_color.get()

            if tool == "line":
                self.current_item = self.canvas.create_line(self.start_x, self.start_y, cur_x, cur_y, fill=color, width=2)
            elif tool == "arrow":
                self.current_item = self.canvas.create_line(self.start_x, self.start_y, cur_x, cur_y, fill=color, width=2, arrow=tk.LAST)
            elif tool == "circle":
                self.current_item = self.canvas.create_oval(self.start_x, self.start_y, cur_x, cur_y, outline=color, width=2)
            elif tool == "rectangle":
                self.current_item = self.canvas.create_rectangle(self.start_x, self.start_y, cur_x, cur_y, outline=color, width=2)

    def on_release(self, event):
        if self.selected_tool.get() == "resize":
            self.current_item = None
            self.clear_resize_handles()
        elif self.current_item:
            self.drawn_items.append(self.current_item)
            self.current_item = None

    def draw_text(self, x, y):
        text = simpledialog.askstring("Input", "Enter text:", parent=self)
        if text:
            color = self.selected_color.get()
            item = self.canvas.create_text(x, y, text=text, fill=color, font=("Arial", 12))
            self.drawn_items.append(item)

    def save_plan(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Files", "*.png")])
        if not file_path:
            return
        
        x = self.canvas.winfo_rootx()
        y = self.canvas.winfo_rooty()
        x1 = x + self.canvas.winfo_width()
        y1 = y + self.canvas.winfo_height()
        
        ImageGrab.grab().crop((x, y, x1, y1)).save(file_path)

    def update_image(self):
        if not hasattr(self, 'original_image'):
            return
            
        width = int(self.original_image.width * self.zoom_level)
        height = int(self.original_image.height * self.zoom_level)
        
        resized_image = self.original_image.resize((width, height), Image.LANCZOS)
        self.battle_plan_image = ImageTk.PhotoImage(resized_image)
        
        self.canvas.delete("image")
        self.canvas.create_image(0, 0, anchor="nw", image=self.battle_plan_image, tags="image")
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))
        self.canvas.tag_lower("image")

    def on_mouse_wheel(self, event):
        if event.delta > 0:
            self.zoom_level *= 1.1
        else:
            self.zoom_level /= 1.1
        self.update_image()

    def start_pan(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def pan(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def delete_item(self, event):
        item = self.canvas.find_closest(self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))[0]
        if item in self.drawn_items:
            self.canvas.delete(item)
            self.drawn_items.remove(item)

    def clear_all(self):
        for item in self.drawn_items:
            self.canvas.delete(item)
        self.drawn_items = []

    def select_for_resize(self, event):
        self.clear_resize_handles()
        item = self.canvas.find_closest(self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))[0]
        if item in self.drawn_items:
            self.current_item = item
            self.show_resize_handles(item)

    def show_resize_handles(self, item):
        bbox = self.canvas.bbox(item)
        x1, y1, x2, y2 = bbox
        self.resize_handles.append(self.canvas.create_rectangle(x1-3, y1-3, x1+3, y1+3, fill="blue"))
        self.resize_handles.append(self.canvas.create_rectangle(x2-3, y1-3, x2+3, y1+3, fill="blue"))
        self.resize_handles.append(self.canvas.create_rectangle(x1-3, y2-3, x1+3, y2+3, fill="blue"))
        self.resize_handles.append(self.canvas.create_rectangle(x2-3, y2-3, x2+3, y2+3, fill="blue"))

    def clear_resize_handles(self):
        for handle in self.resize_handles:
            self.canvas.delete(handle)
        self.resize_handles = []

    def resize_item(self, event):
        if not self.current_item:
            return

        cur_x = self.canvas.canvasx(event.x)
        cur_y = self.canvas.canvasy(event.y)
        coords = self.canvas.coords(self.current_item)

        item_type = self.canvas.type(self.current_item)
        if item_type in ["rectangle", "oval"]:
            self.canvas.coords(self.current_item, coords[0], coords[1], cur_x, cur_y)
        elif item_type == "line":
            self.canvas.coords(self.current_item, coords[0], coords[1], cur_x, cur_y)
        elif item_type == "text":
            # For text, we can change the font size
            # This is a simplified approach
            current_font = self.canvas.itemcget(self.current_item, "font")
            font_family, font_size, font_style = self.canvas.tk.splitlist(current_font)
            new_size = int(font_size) + (cur_y - self.start_y) // 10 # Change size based on vertical drag
            self.canvas.itemconfigure(self.current_item, font=(font_family, new_size, font_style))
            self.start_y = cur_y


        self.clear_resize_handles()
        self.show_resize_handles(self.current_item)

    def apply_theme(self):
        bg_color = "#252526" if self.app.is_dark_mode else "white"
        self.canvas.config(bg=bg_color)
        
        if self.app.is_dark_mode:
            self.app.style.configure("Tooltip.TLabel", background="black", foreground="green", bordercolor="red")
        else:
            self.app.style.configure("Tooltip.TLabel", background="white", foreground="black", bordercolor="red")