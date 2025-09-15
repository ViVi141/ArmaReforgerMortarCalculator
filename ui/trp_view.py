import tkinter as tk
from tkinter import ttk, filedialog, simpledialog, messagebox
import json
from utils import format_grid_10_digit

class TRPSelectDialog(tk.Toplevel):
    def __init__(self, parent, title, valid_trps_data, is_dark_mode):
        super().__init__(parent)
        self.title(title)
        self.result = None # To store the selected TRP data
        self.transient(parent)
        self.valid_trps_data = valid_trps_data # Store valid_trps_data as an instance variable

        bg_color = "#252526" if is_dark_mode else "SystemButtonFace"
        fg_color = "#00FF00" if is_dark_mode else "black"
        self.configure(bg=bg_color)

        # Treeview to display valid TRPs
        tree_frame = ttk.Frame(self)
        tree_frame.pack(padx=10, pady=10, fill="both", expand=True)

        columns = ("Grid", "Elevation", "Name/ID")
        self.trp_tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        self.trp_tree.heading("Grid", text="网格")
        self.trp_tree.heading("Elevation", text="海拔")
        self.trp_tree.heading("Name/ID", text="名称/ID")
        
        self.trp_tree.column("Grid", width=100, anchor="center")
        self.trp_tree.column("Elevation", width=70, anchor="center")
        self.trp_tree.column("Name/ID", width=150, anchor="w")
        
        self.trp_tree.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.trp_tree.yview)
        self.trp_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # Populate the treeview
        for i, trp_data in enumerate(self.valid_trps_data): # Now self.valid_trps_data contains full TRP dicts
            self.trp_tree.insert("", "end", iid=str(i), values=(
                trp_data['grid'],
                f"{trp_data['elev']:.1f}",
                trp_data['name']
            ))
        
        # Bind double click to select
        self.trp_tree.bind("<Double-1>", self.on_double_click)
        self.trp_tree.bind("<MouseWheel>", self._on_mousewheel) # Bind mouse wheel to treeview

        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=5)
        select_button = ttk.Button(button_frame, text="选择TRP", command=self.on_select)
        select_button.pack(side="left", padx=10)
        cancel_button = ttk.Button(button_frame, text="取消", command=self.destroy)
        cancel_button.pack(side="left", padx=10)

        self.update_idletasks()
        parent_x, parent_y = parent.winfo_x(), parent.winfo_y()
        parent_width, parent_height = parent.winfo_width(), parent.winfo_height()
        dialog_width, dialog_height = 400, 300 # Fixed size for the dialog
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        self.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.grab_set()
        self.wait_window()

    def _on_mousewheel(self, event):
        self.trp_tree.yview_scroll(int(-1*(event.delta/120)), "units")
        return "break" # Stop event propagation

    def on_double_click(self, event):
        self.on_select()

    def on_select(self):
        selected_item = self.trp_tree.selection()
        if selected_item:
            index = self.trp_tree.index(selected_item[0])
            self.result = self.valid_trps_data[index] # Access self.valid_trps_data
            self.destroy()

class TRPView(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding="10")
        self.app = app
        self.pack(fill="both", expand=True)

        # Input Frame for new TRPs
        input_frame = ttk.LabelFrame(self, text="添加新TRP")
        input_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(input_frame, text="网格:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.grid_entry = ttk.Entry(input_frame, width=15)
        self.grid_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        
        ttk.Label(input_frame, text="海拔 (米):").grid(row=0, column=2, padx=5, pady=2, sticky="w")
        self.elev_entry = ttk.Entry(input_frame, width=10)
        self.elev_entry.grid(row=0, column=3, padx=5, pady=2, sticky="ew")
        
        ttk.Label(input_frame, text="名称/ID:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.name_entry = ttk.Entry(input_frame, width=20)
        self.name_entry.grid(row=1, column=1, columnspan=3, padx=5, pady=2, sticky="ew")
        
        add_button = ttk.Button(input_frame, text="添加TRP", command=self.add_trp)
        add_button.grid(row=2, column=0, columnspan=4, pady=5)

        # TRP List Display
        list_frame = ttk.LabelFrame(self, text="目标参考点")
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.trp_tree = ttk.Treeview(list_frame, columns=("Grid", "Elevation", "Name/ID", "Status"), show="headings")
        self.trp_tree.heading("Grid", text="网格")
        self.trp_tree.heading("Elevation", text="海拔")
        self.trp_tree.heading("Name/ID", text="名称/ID")
        self.trp_tree.heading("Status", text="状态")
        
        self.trp_tree.column("Grid", width=100, anchor="center")
        self.trp_tree.column("Elevation", width=70, anchor="center")
        self.trp_tree.column("Name/ID", width=120, anchor="w")
        self.trp_tree.column("Status", width=100, anchor="center")
        
        self.trp_tree.pack(fill="both", expand=True)

        # Scrollbar for Treeview
        scrollbar = ttk.Scrollbar(self.trp_tree, orient="vertical", command=self.trp_tree.yview)
        self.trp_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        # Bind selection event to display details
        self.trp_tree.bind("<<TreeviewSelect>>", self.on_trp_selected)

        # TRP Details Display
        self.details_frame = ttk.LabelFrame(self, text="选中TRP详情")
        self.details_frame.pack(fill="x", padx=10, pady=5)

        self.detail_grid_label = ttk.Label(self.details_frame, text="网格: ")
        self.detail_grid_label.grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.detail_elev_label = ttk.Label(self.details_frame, text="海拔: ")
        self.detail_elev_label.grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.detail_name_label = ttk.Label(self.details_frame, text="名称/ID: ")
        self.detail_name_label.grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.detail_status_label = ttk.Label(self.details_frame, text="状态: ")
        self.detail_status_label.grid(row=3, column=0, padx=5, pady=2, sticky="w")

        # Buttons for list management
        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(button_frame, text="删除选中TRP", command=self.remove_selected_trp).pack(side="left", padx=5)
        ttk.Button(button_frame, text="清空所有TRP", command=self.clear_all_trps).pack(side="left", padx=5)
        ttk.Button(button_frame, text="计算所有TRP", command=self.calculate_all_trps).pack(side="right", padx=5)
        ttk.Button(button_frame, text="从任务日志加载TRP", command=self.load_trps_from_log).pack(side="right", padx=5)

        self.refresh_trp_list() # Initial population

    def add_trp(self):
        grid = self.grid_entry.get()
        elev = self.elev_entry.get()
        name = self.name_entry.get()

        if not grid or not elev:
            messagebox.showerror("输入错误", "网格和海拔是必需的。")
            return

        try:
            float(elev) # Validate elevation is a number
        except ValueError:
            messagebox.showerror("输入错误", "海拔必须是数字。")
            return

        self.app.state.add_trp()
        new_trp_vars = self.app.state.get_trp_vars(len(self.app.state.trp_input_vars) - 1)
        new_trp_vars['grid'].set(format_grid_10_digit(grid))
        new_trp_vars['elev'].set(float(elev))
        new_trp_vars['name'].set(name if name else f"TRP {len(self.app.state.trp_input_vars)}")
        new_trp_vars['status'].set("Pending") # Initialize status
        
        self.grid_entry.delete(0, tk.END)
        self.elev_entry.delete(0, tk.END)
        self.name_entry.delete(0, tk.END)
        self.refresh_trp_list()

    def remove_selected_trp(self):
        selected_items = self.trp_tree.selection()
        if not selected_items:
            messagebox.showinfo("选择", "没有选中要删除的TRP。")
            return

        # Remove from state_manager and then refresh UI
        for item_id in selected_items:
            index = self.trp_tree.index(item_id)
            if 0 <= index < len(self.app.state.trp_input_vars):
                del self.app.state.trp_input_vars[index]
        self.refresh_trp_list()

    def clear_all_trps(self):
        if messagebox.askyesno("清空所有", "确定要清空所有TRP吗？"):
            self.app.state.clear_trps()
            self.refresh_trp_list()

    def refresh_trp_list(self):
        # Clear existing items in the Treeview
        for item in self.trp_tree.get_children():
            self.trp_tree.delete(item)

        # Populate Treeview from state_manager
        for i, trp_vars in enumerate(self.app.state.trp_input_vars):
            status = trp_vars['status'].get()
            tags = ()
            if "Out of Range" in status or "Error" in status or "No Solution" in status:
                tags = ('out_of_range',) # Apply a tag for styling
            elif "Valid" in status or "Solution" in status:
                tags = ('valid_solution',)

            self.trp_tree.insert("", "end", iid=str(i), values=(
                trp_vars['grid'].get(),
                trp_vars['elev'].get(),
                trp_vars['name'].get(),
                status # Display status
            ), tags=tags)
        
        # The tags will be configured in apply_theme based on the current theme.

    def calculate_all_trps(self):
        if not self.app.state.trp_input_vars:
            messagebox.showinfo("无TRP", "请在计算前向列表添加TRP。")
            return
        self.app.calculate_trps_from_list()

    def load_trps_from_log(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="加载任务日志以获取TRP"
        )
        if not file_path:
            return

        try:
            with open(file_path, 'r') as f:
                log_data = json.load(f)
            
            self.app.state.clear_trps() # Clear existing TRPs before loading new ones

            for entry in log_data:
                # Determine initial status based on log entry type
                initial_status = "Loaded"
                if entry.get("type") == "TRP_BATCH_RESULT":
                    trp_result = entry.get("data", {})
                    grid = str(trp_result.get("original_trp_grid", trp_result.get("Target Grid", ""))).replace(" ", "")
                    elev_str = str(trp_result.get("Target Elevation", "")).replace(" m", "")
                    name = trp_result.get("TRP Name", "")
                    initial_status = trp_result.get("Status", "Loaded") # Use status from batch result
                else:
                    # Existing mission log entry
                    grid_raw = entry.get("original_trp_grid") # Prioritize original_trp_grid
                    if grid_raw is None:
                        grid_raw = entry.get("calculated_target_grid")
                        if grid_raw is None:
                            grid_raw = entry.get("target_grid_str", "")
                    grid = str(grid_raw).replace(" ", "")

                    elev_raw = entry.get("target_elev")
                    if elev_raw is None:
                        elev_raw = entry.get("fo_elev", 100)
                    elev_str = str(elev_raw).replace(" m", "")

                    name = entry.get("target_name")
                    if not name:
                        name = entry.get("fo_id", f"TRP from Log {len(self.app.state.trp_input_vars) + 1}")
                
                try:
                    elev = float(elev_str)
                except ValueError:
                    elev = 100

                if grid:
                    self.app.state.add_trp()
                    new_trp_vars = self.app.state.get_trp_vars(len(self.app.state.trp_input_vars) - 1)
                    new_trp_vars['grid'].set(format_grid_10_digit(grid))
                    new_trp_vars['elev'].set(elev)
                    new_trp_vars['name'].set(name)
                    new_trp_vars['status'].set(initial_status) # Set initial status
                else:
                    print(f"由于缺少网格数据，跳过日志条目: {entry}")
                    messagebox.showwarning("加载警告", f"由于缺少网格数据，跳过了日志中的条目: {name}")

            self.refresh_trp_list()
            messagebox.showinfo("成功", f"从日志文件加载了 {len(self.app.state.trp_input_vars)} 个TRP。")

        except json.JSONDecodeError:
            messagebox.showerror("错误", "无效的JSON文件。请选择有效的任务日志。")
        except Exception as e:
            messagebox.showerror("错误", f"加载TRP时发生错误: {e}")

    def load_valid_trp_to_main(self):
        all_trps_data = []
        for trp_vars in self.app.state.trp_input_vars:
            all_trps_data.append({
                'grid': trp_vars['grid'].get(),
                'elev': trp_vars['elev'].get(),
                'name': trp_vars['name'].get(),
                'status': trp_vars['status'].get()
            })

        if not all_trps_data:
            messagebox.showinfo("无TRP", "列表中没有找到可加载到主界面的TRP。")
            return

        dialog = TRPSelectDialog(self.app, "从列表选择TRP", all_trps_data, self.app.is_dark_mode)
        selected_trp = dialog.result

        if selected_trp:
            # Update main UI's TRP input fields
            self.app.state.trp_grid_var.set(selected_trp['grid'])
            self.app.state.trp_elev_var.set(selected_trp['elev'])
            self.app.state.targeting_mode_var.set("Grid") # Ensure Grid mode is selected
            self.app.on_targeting_mode_change() # Update UI based on mode change
            self.app.notebook.select(0) # Switch to Main tab
            messagebox.showinfo("TRP已加载", f"TRP '{selected_trp['name']}' 已加载到主界面。")
            self.app.calculate_all() # Auto-calculate after loading
    
    def on_trp_selected(self, event):
        selected_items = self.trp_tree.selection()
        if selected_items:
            item_id = selected_items[0]
            index = self.trp_tree.index(item_id)
            if 0 <= index < len(self.app.state.trp_input_vars):
                selected_trp_vars = self.app.state.get_trp_vars(index)
                self.detail_grid_label.config(text=f"网格: {selected_trp_vars['grid'].get()}")
                self.detail_elev_label.config(text=f"海拔: {selected_trp_vars['elev'].get():.1f} 米")
                self.detail_name_label.config(text=f"名称/ID: {selected_trp_vars['name'].get()}")
                self.detail_status_label.config(text=f"状态: {selected_trp_vars['status'].get()}")
        else:
            self.detail_grid_label.config(text="网格: ")
            self.detail_elev_label.config(text="海拔: ")
            self.detail_name_label.config(text="名称/ID: ")
            self.detail_status_label.config(text="状态: ")
            
    def apply_theme(self):
        # This method will be called by the main app to apply theme changes
        # Update Treeview colors based on theme
        if self.app.is_dark_mode:
            self.app.style.configure("Treeview", background="#3C3C3C", fieldbackground="#3C3C3C")
            self.app.style.map("Treeview",
                                background=[("selected", "#4a4a4a")],
                                foreground=[("selected", "white")]) # Keep selected text white for visibility
            self.app.style.configure("Treeview.Heading", background="#252526", foreground="#00FF00")
            # Configure tags for styling in dark mode
            self.trp_tree.tag_configure('out_of_range', foreground='red')
            self.trp_tree.tag_configure('valid_solution', foreground='#00FF00') # Vibrant green for dark mode
            
            self.app.style.layout("TRPDetails.TLabelFrame", [('TLabelframe.border', {'sticky': 'nswe', 'border': '1', 'children': [('TLabelframe.padding', {'sticky': 'nswe', 'children': [('TLabelframe.label', {'sticky': 'nw'}), ('TLabelframe.contents', {'sticky': 'nswe'})]})]})])
            self.app.style.configure("TRPDetails.TLabelFrame", background="#252526", bordercolor="#3C3C3C", relief="solid")
            self.app.style.configure("TRPDetails.TLabelFrame.Label", background="#252526", foreground="#00FF00", font=("Consolas", 10, "bold"))
            self.app.style.configure("TRPDetails.TLabel", background="#252526", foreground="#00FF00", font=("Consolas", 10))
            self.app.update_idletasks() # Force update to ensure style is registered
            self.details_frame.config(style="TRPDetails.TLabelFrame")
            for child in self.details_frame.winfo_children():
                if isinstance(child, ttk.Label):
                    child.config(style="TRPDetails.TLabel")
        else:
            self.app.style.layout("TRPDetails.TLabelFrame", [('TLabelframe.border', {'sticky': 'nswe', 'border': '1', 'children': [('TLabelframe.padding', {'sticky': 'nswe', 'children': [('TLabelframe.label', {'sticky': 'nw'}), ('TLabelframe.contents', {'sticky': 'nswe'})]})]})])
            self.app.style.configure("TRPDetails.TLabelFrame", background="SystemButtonFace", bordercolor="SystemButtonFace", relief="solid")
            self.app.style.configure("TRPDetails.TLabelFrame.Label", background="SystemButtonFace", foreground="black", font=("Consolas", 10, "bold"))
            self.app.style.configure("TRPDetails.TLabel", background="SystemButtonFace", foreground="black", font=("Consolas", 10))
            self.app.update_idletasks() # Force update to ensure style is registered
            self.details_frame.config(style="TRPDetails.TLabelFrame")
            for child in self.details_frame.winfo_children():
                if isinstance(child, ttk.Label):
                    child.config(style="TRPDetails.TLabel")
        self.refresh_trp_list() # Refresh to apply new colors