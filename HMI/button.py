import tkinter as tk
from functools import partial

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.widgets import Button
from matplotlib.patches import Rectangle
from colors import HPHMI

# Dialog dimensions and position
DIALOG_X_POSITION = 818
DIALOG_Y_POSITION = 514
DIALOG_WIDTH = 225
DIALOG_HEIGHT = 106

INPUT_LOW_LIMIT = 0
INPUT_HIGH_LIMIT = 1024

# Button, text and rectangle positions
BTN_POS = {
    'sp_btn': [0.075, 0.74, 0.314, 0.12],
    'max_btn': [0.075, 0.575, 0.314, 0.12],
    'min_btn': [0.075, 0.41, 0.314, 0.12],
    'en_output_btn': [0.075, 0.245, 0.314, 0.12],
    'en_override_btn': [0.075, 0.08, 0.314, 0.12],
    'high_view_btn': [0.495, 0.295, 0.25, 0.07],
    'def_view_btn': [0.495, 0.1875, 0.25, 0.07],
    'low_view_btn': [0.495, 0.08, 0.25, 0.07],
}

RECT = {
    'faceplate_zone': [0.465, 0.52, 0.51, 0.433],
    'select_view': [0.465, 0.045, 0.31, 0.40],
    'manual_actions': [0.028, 0.045, 0.41, 0.907],
    'info_zone': [0.8, 0.045, 0.175, 0.40]
}

BTN_RECT_BORDER = {
    'start': (0.033, 0.03),
    'size': (0.94, 0.94),
    'line_width': 1.5
}

TEXT_PLACEMENT = {
    'select_view': (0, 0.405),
    'manual_actions': (0, 0.91),
    'info_zone': (0, -0.02)  # Relative to the center_y
}

class ButtonView:
    def __init__(self, master, controller, os):
        self.controller = controller
        self.fig, self.ax = plt.subplots(figsize=(4.4, 3.2))
        self.os = os

        # Update location of popup dialog for PIOS
        global DIALOG_X_POSITION, DIALOG_Y_POSITION

        if self.os == "PIOS":
            DIALOG_X_POSITION = 775
            DIALOG_Y_POSITION = 505
        
        # Hide the default axis
        self.ax.axis('off')
        
        # Style attributes
        self.fig.patch.set_facecolor(HPHMI.gray)  # Set figure background color
        outline_box = Rectangle((0, 0), 1, 1, transform=self.fig.transFigure, 
                                facecolor='none', edgecolor=HPHMI.dark_gray, linewidth=2, clip_on=False)
        self.fig.patches.extend([outline_box])

        # Initial setup
        self._setup_view()

        # Embed the widget
        self.canvas = FigureCanvasTkAgg(self.fig, master=master)
        self.canvas_widget = self.canvas.get_tk_widget()
        

    def _setup_view(self):
        # Set point button
        self.sp_button_ax = self.fig.add_axes(BTN_POS['sp_btn'])

        # Create the button with hover effect
        self.sp_button = Button(self.sp_button_ax, 'SET\nSET POINT', color=HPHMI.dark_gray, hovercolor=HPHMI.dark_green)
        self.sp_button.on_clicked(partial(self._on_button_click_set_value, title="Update Set Point", prompt="Enter value (0-1024):", addr=2))

        # Here, the rectangle is slightly smaller than the full button
        rectangle = plt.Rectangle(BTN_RECT_BORDER['start'], *BTN_RECT_BORDER['size'], 
                                facecolor=HPHMI.gray, edgecolor=HPHMI.dark_gray, linewidth=BTN_RECT_BORDER['line_width'])
        self.sp_button_ax.add_patch(rectangle)

        # Max limit button
        self.max_button_ax = self.fig.add_axes(BTN_POS['max_btn'])

        # Create the button with hover effect
        self.max_button = Button(self.max_button_ax, 'SET\nMAX LIMIT', color=HPHMI.dark_gray, hovercolor=HPHMI.dark_green)
        self.max_button.on_clicked(partial(self._on_button_click_set_value, title="Set Max Limit", prompt="Enter value (0-1024):", addr=4))

        rectangle = plt.Rectangle(BTN_RECT_BORDER['start'], *BTN_RECT_BORDER['size'], 
                                facecolor=HPHMI.gray, edgecolor=HPHMI.dark_gray, linewidth=BTN_RECT_BORDER['line_width'])
        self.max_button_ax.add_patch(rectangle)

        # Min limit button
        self.min_button_ax = self.fig.add_axes(BTN_POS['min_btn'])

        # Create the button with hover effect
        self.min_button = Button(self.min_button_ax, 'SET\nMIN LIMIT', color=HPHMI.dark_gray, hovercolor=HPHMI.dark_green)
        self.min_button.on_clicked(partial(self._on_button_click_set_value, title="Set Min Limit", prompt="Enter value (0-1024):", addr=3))

        # Add the rectangle
        rectangle = plt.Rectangle(BTN_RECT_BORDER['start'], *BTN_RECT_BORDER['size'], 
                                facecolor=HPHMI.gray, edgecolor=HPHMI.dark_gray, linewidth=BTN_RECT_BORDER['line_width'])
        self.min_button_ax.add_patch(rectangle)

        # Enable output toggle button
        self.en_output_button_ax = self.fig.add_axes(BTN_POS['en_output_btn'])

        # Create the button with hover effect
        self.en_output_button = Button(self.en_output_button_ax, 'TOGGLE\nENABLE OUTPUT', color=HPHMI.dark_gray, hovercolor=HPHMI.dark_green)
        self.en_output_button.on_clicked(partial(self._on_toggle_button_click, title="Change Enable Output", prompt="Enable output will be toggled.", addr=0))

        # Add the rectangle
        rectangle = plt.Rectangle(BTN_RECT_BORDER['start'], *BTN_RECT_BORDER['size'], 
                                facecolor=HPHMI.gray, edgecolor=HPHMI.dark_gray, linewidth=BTN_RECT_BORDER['line_width'])
        self.en_output_button_ax.add_patch(rectangle)

        # Enable override toggle button
        self.en_override_button_ax = self.fig.add_axes(BTN_POS['en_override_btn'])

        # Create the button with hover effect
        self.en_override_button = Button(self.en_override_button_ax, 'TOGGLE\nENBL OVERRIDE', color=HPHMI.dark_gray, hovercolor=HPHMI.dark_green)
        self.en_override_button.on_clicked(partial(self._on_toggle_button_click, title="Change Enable Override", prompt="Enable override will be toggled.", addr=1))

        # Add the rectangle
        rectangle = plt.Rectangle(BTN_RECT_BORDER['start'], *BTN_RECT_BORDER['size'], 
                                facecolor=HPHMI.gray, edgecolor=HPHMI.dark_gray, linewidth=BTN_RECT_BORDER['line_width'])
        self.en_override_button_ax.add_patch(rectangle)

        # View 0-400V button
        self.high_view_button_ax = self.fig.add_axes(BTN_POS['high_view_btn'])

        # Create the button with hover effect
        self.high_view_button = Button(self.high_view_button_ax, '0-400V', color=HPHMI.dark_gray, hovercolor=HPHMI.dark_green)
        #TODO self.high_view_button.on_clicked(self.controller.set_high_view)

        # Add the rectangle
        rectangle = plt.Rectangle(BTN_RECT_BORDER['start'], *BTN_RECT_BORDER['size'], 
                                facecolor=HPHMI.gray, edgecolor=HPHMI.dark_gray, linewidth=BTN_RECT_BORDER['line_width'])
        self.high_view_button_ax.add_patch(rectangle)

        # View 200-260V button
        self.def_view_button_ax = self.fig.add_axes(BTN_POS['def_view_btn'])

        # Create the button with hover effect
        self.def_view_button = Button(self.def_view_button_ax, '200-260V', color=HPHMI.dark_gray, hovercolor=HPHMI.dark_green)
        #TODO self.def_view_button.on_clicked(self.controller.set_default_view)

        # Add the rectangle
        rectangle = plt.Rectangle(BTN_RECT_BORDER['start'], *BTN_RECT_BORDER['size'], 
                                facecolor=HPHMI.gray, edgecolor=HPHMI.dark_gray, linewidth=BTN_RECT_BORDER['line_width'])
        self.def_view_button_ax.add_patch(rectangle)

        # View 100-140V button
        self.low_view_button_ax = self.fig.add_axes(BTN_POS['low_view_btn'])

        # Create the button with hover effect
        self.low_view_button = Button(self.low_view_button_ax, '100-140V', color=HPHMI.dark_gray, hovercolor=HPHMI.dark_green)
        #TODO self.low_view_button.on_clicked(self.controller.set_low_view)

        # Add the rectangle
        rectangle = plt.Rectangle(BTN_RECT_BORDER['start'], *BTN_RECT_BORDER['size'], 
                                facecolor=HPHMI.gray, edgecolor=HPHMI.dark_gray, linewidth=BTN_RECT_BORDER['line_width'])
        self.low_view_button_ax.add_patch(rectangle)

        # Create faceplate zone
        rect = RECT['faceplate_zone']

        # Add the rectangle to the axis instead of the figure
        self.description_box = self.ax.add_patch(
            Rectangle((rect[0], rect[1]), rect[2], rect[3], transform=self.fig.transFigure, 
                    facecolor=HPHMI.gray, edgecolor=HPHMI.dark_gray, linewidth=1, clip_on=False)
        )

        # Calculate the center of the rectangle
        center_x = rect[0] + rect[2] / 2
        center_y = rect[1] + rect[3] / 2 - 0.02

        # Add text to the rectangle
        self.desc_text = self.ax.text(center_x, center_y, "Reserved Faceplate Zone\n", weight='bold', ha='center',
                        va='center', fontsize=10, color=HPHMI.darker_gray, transform=self.fig.transFigure)

        # Create select view rectangle
        rect = RECT['select_view']

        # Add the rectangle to the axis instead of the figure
        self.description_box = self.ax.add_patch(
            Rectangle((rect[0], rect[1]), rect[2], rect[3], transform=self.fig.transFigure, 
                    facecolor=HPHMI.gray, edgecolor=HPHMI.dark_gray, linewidth=1, clip_on=False)
        )

        # Create manual actions zone
        rect = RECT['manual_actions']

        # Add the rectangle to the axis instead of the figure
        self.description_box = self.ax.add_patch(
            Rectangle((rect[0], rect[1]), rect[2], rect[3], transform=self.fig.transFigure, 
                    facecolor=HPHMI.gray, edgecolor=HPHMI.dark_gray, linewidth=1, clip_on=False)
        )

        # Create info rectangle
        rect = RECT['info_zone']

        # Add the rectangle to the axis instead of the figure
        self.description_box = self.ax.add_patch(
            Rectangle((rect[0], rect[1]), rect[2], rect[3], transform=self.fig.transFigure, 
                    facecolor=HPHMI.gray, edgecolor=HPHMI.dark_gray, linewidth=1, clip_on=False)
        )

        # For 'SELECT VIEW'
        rect = RECT['select_view']
        center_x = rect[0] + rect[2] / 2
        y_placement = TEXT_PLACEMENT['select_view'][1]

        self.desc_text = self.ax.text(center_x, y_placement, "SELECT VIEW", weight='bold', ha='center',
                        va='center', fontsize=10, color=HPHMI.darker_gray, transform=self.fig.transFigure)

        # For 'MANUAL ACTIONS'
        rect = RECT['manual_actions']
        center_x = rect[0] + rect[2] / 2
        y_placement = TEXT_PLACEMENT['manual_actions'][1]

        self.desc_text = self.ax.text(center_x, y_placement, "MANUAL ACTIONS", weight='bold', ha='center',
                        va='center', fontsize=10, color=HPHMI.darker_gray, transform=self.fig.transFigure)

        # For 'Static Info Zone'
        rect = RECT['info_zone']
        center_x = rect[0] + rect[2] / 2
        center_y = rect[1] + rect[3] / 2 + TEXT_PLACEMENT['info_zone'][1]

        self.desc_text = self.ax.text(center_x, center_y, "Static\nInfo\nZone", weight='bold', ha='center',
                        va='center', fontsize=10, color=HPHMI.darker_gray, transform=self.fig.transFigure)


    def _on_button_click_set_value(self, event, title, prompt, addr):
        # Display the custom input dialog and get the user input
        self.input_dialog(title, prompt)
        self.canvas._tkcanvas.master.wait_window(self.dialog_window)  # Wait until the dialog is closed
        user_input = self.result

        if user_input is not None:
            try:
                user_input = int(user_input)
                if INPUT_LOW_LIMIT <= user_input <= INPUT_HIGH_LIMIT:
                    # Check the result of the write operation
                    success = self.controller.write_float(addr, user_input)
                    if not success:
                        self.error_dialog("Register write failed.")
                else:
                    self.error_dialog("Input out of range.")

            except ValueError:
                self.error_dialog("Invalid input.")


    def _on_toggle_button_click(self, event, title, prompt, addr):
        # Display the toggle dialog
        self.toggle_dialog(title, prompt)
        self.canvas._tkcanvas.master.wait_window(self.dialog_window)  # Wait until the dialog is closed
        confirmed = self.result

        if confirmed:
            current_value = self.controller.get_current_value(addr)

            # Toggle the value
            toggled_value = 1 if current_value == 0 else 0

            # Write the toggled value back to the coil
            result = self.controller.write_bool(addr, toggled_value)


    def input_dialog(self, title, prompt):
        self.dialog_window = tk.Toplevel(self.canvas._tkcanvas.master)
        self.dialog_window.geometry(f"{DIALOG_WIDTH}x{DIALOG_HEIGHT}+{DIALOG_X_POSITION}+{DIALOG_Y_POSITION}")
        self.dialog_window.title(title)

        # Set the column weights. The center columns (1 and 2) have higher weights.
        self.dialog_window.grid_columnconfigure(0, weight=1)
        self.dialog_window.grid_columnconfigure(1, weight=2)
        self.dialog_window.grid_columnconfigure(2, weight=2)
        self.dialog_window.grid_columnconfigure(3, weight=1)

        label = tk.Label(self.dialog_window, text=prompt)
        label.grid(row=0, column=1, columnspan=2, pady=5)

        self.entry = tk.Entry(self.dialog_window, width=15)
        self.entry.grid(row=1, column=1, columnspan=2, pady=0)

        submit_button = tk.Button(self.dialog_window, text="Apply", command=self.submit_input)
        submit_button.grid(row=2, column=1, padx=5, pady=10, sticky=tk.E)

        cancel_button = tk.Button(self.dialog_window, text="Cancel", command=self.cancel_window)
        cancel_button.grid(row=2, column=2, padx=5, pady=10, sticky=tk.W)

        # Bind the close window action (clicking the 'X' button) to the close_window method
        self.dialog_window.protocol("WM_DELETE_WINDOW", self.close_window)


    def toggle_dialog(self, title, prompt):
        self.dialog_window = tk.Toplevel(self.canvas._tkcanvas.master)
        self.dialog_window.geometry(f"{DIALOG_WIDTH}x{DIALOG_HEIGHT}+{DIALOG_X_POSITION}+{DIALOG_Y_POSITION}")
        self.dialog_window.title(title)

        # Set the column weights. The center columns (1 and 2) have higher weights.
        self.dialog_window.grid_columnconfigure(0, weight=1)
        self.dialog_window.grid_columnconfigure(1, weight=2)
        self.dialog_window.grid_columnconfigure(2, weight=2)
        self.dialog_window.grid_columnconfigure(3, weight=1)

        label = tk.Label(self.dialog_window, text=prompt)
        label.grid(row=0, column=1, columnspan=2, pady=15)

        confirm_button = tk.Button(self.dialog_window, text="Confirm", command=self.confirm_toggle)
        confirm_button.grid(row=1, column=1, padx=5, pady=10, sticky=tk.E)

        cancel_button = tk.Button(self.dialog_window, text="Cancel", command=self.cancel_window)
        cancel_button.grid(row=1, column=2, padx=5, pady=10, sticky=tk.W)

        # Bind the close window action (clicking the 'X' button) to the close_window method
        self.dialog_window.protocol("WM_DELETE_WINDOW", self.close_window)


    def submit_input(self):
        self.result = self.entry.get()
        self.dialog_window.destroy()


    def cancel_window(self):
        self.result = None
        self.dialog_window.destroy()


    def confirm_toggle(self):
        self.result = True
        self.dialog_window.destroy()


    def error_dialog(self, message):
        error_window = tk.Toplevel(self.canvas._tkcanvas.master)
        error_window.geometry(f"{DIALOG_WIDTH}x{DIALOG_HEIGHT}+{DIALOG_X_POSITION}+{DIALOG_Y_POSITION}")
        error_window.title("ERROR")

        label = tk.Label(error_window, text=message)
        label.pack(pady=15)

        ok_button = tk.Button(error_window, text="OK", command=error_window.destroy, width=12)
        ok_button.pack(pady=10)


    def close_window(self):
        self.result = None
        self.dialog_window.destroy()
