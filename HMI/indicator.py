import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Rectangle
from colors import HPHMI

RECT = {
    'control_status': [0.022, 0.885, 0.954, 0.07],
    'water_inlet_desc': [0.022, 0.815, 0.32, 0.07],
    'water_inlet_dynamic': [0.022, 0.745, 0.32, 0.07],
    'excite_switch_desc': [0.505, 0.815, 0.32, 0.07],
    'excite_switch_dynamic': [0.505, 0.745, 0.32, 0.07],
    'filler_box_right': [0.825, 0.465, 0.151, 0.42],
    'filler_box_left': [0.342, 0.325, 0.163, 0.56],
    'cooling_switch_desc': [0.022, 0.675, 0.32, 0.07],
    'cooling_switch_dynamic': [0.022, 0.605, 0.32, 0.07],
    'transformer_sw_desc': [0.505, 0.675, 0.32, 0.07],
    'transformer_sw_dynamic': [0.505, 0.605, 0.32, 0.07],
    'start_seq_desc': [0.022, 0.535, 0.32, 0.07],
    'start_seq_dynamic': [0.022, 0.465, 0.32, 0.07],
    'grid_switch_desc': [0.505, 0.535, 0.32, 0.07],
    'grid_switch_dynamic': [0.505, 0.465, 0.32, 0.07],
    'shutdown_seq_desc': [0.022, 0.395, 0.32, 0.07],
    'shutdown_seq_dynamic': [0.022, 0.325, 0.32, 0.07]
}

class Indicator:
    def __init__(self, master):
        """Initialize the Matplotlib figure and axis."""
        self.fig, self.ax = plt.subplots(figsize=(5, 3.2))
        self.master = master
        
        # Setup the initial view
        self.setup_view()
        
        # Embed the Matplotlib figure into the Tkinter window
        self.canvas = FigureCanvasTkAgg(self.fig, master=master)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.grid(row=9, columnspan=4, rowspan=8, column=0, pady=20, padx=20)


    def setup_view(self):
        """Setup the Matplotlib figure and axis."""
        # Set the figure and axis background color
        self.fig.patch.set_facecolor(HPHMI.gray)
        self.ax.set_facecolor(HPHMI.gray)

        # Remove axis labels and ticks
        self.ax.axis('off')

        # Create a description box
        rect = RECT['control_status']

        # Add the rectangle to the axis instead of the figure
        self.description_box = self.ax.add_patch(
            Rectangle((rect[0], rect[1]), rect[2], rect[3], transform=self.fig.transFigure, 
                    facecolor=HPHMI.gray, edgecolor=HPHMI.darker_gray, linewidth=0.5, clip_on=False)
        )

        # Calculate the center of the rectangle
        center_x = rect[0] + rect[2] / 2
        center_y = rect[1] + rect[3] / 2

        # Add text to the rectangle
        self.desc_text = self.ax.text(center_x, center_y, "Control Status", weight='bold', ha='center',
                         va='center', fontsize=10, color=HPHMI.darker_gray, transform=self.fig.transFigure)

        # Create a water_inlet description box
        rect = RECT['water_inlet_desc']

        self.description_box = self.ax.add_patch(
            Rectangle((rect[0], rect[1]), rect[2], rect[3], transform=self.fig.transFigure, 
                    facecolor=HPHMI.gray, edgecolor=HPHMI.darker_gray, linewidth=0.5, clip_on=False)
        )

        center_x = rect[0] + rect[2] / 2
        center_y = rect[1] + rect[3] / 2

        self.desc_text = self.ax.text(center_x, center_y, "WATER INLET", weight='bold', ha='center',
                                      va='center', fontsize=10, color=HPHMI.darker_gray, transform=self.fig.transFigure)


        # Create a water_inlet dynamic box
        rect = RECT['water_inlet_dynamic']

        self.water_inlet_box = self.ax.add_patch(
            Rectangle((rect[0], rect[1]), rect[2], rect[3], transform=self.fig.transFigure, 
                    facecolor=HPHMI.gray, edgecolor=HPHMI.darker_gray, linewidth=0.5, clip_on=False)
        )

        center_x = rect[0] + rect[2] / 2
        center_y = rect[1] + rect[3] / 2

        self.water_inlet_text = self.ax.text(center_x, center_y, "Loading...", weight='bold', ha='center',
                         va='center', fontsize=10, color=HPHMI.darker_gray, transform=self.fig.transFigure)


        # Create a excite_switch description box
        rect = RECT['excite_switch_desc']

        self.description_box = self.ax.add_patch(
            Rectangle((rect[0], rect[1]), rect[2], rect[3], transform=self.fig.transFigure, 
                    facecolor=HPHMI.gray, edgecolor=HPHMI.darker_gray, linewidth=0.5, clip_on=False)
        )

        center_x = rect[0] + rect[2] / 2
        center_y = rect[1] + rect[3] / 2

        self.desc_text = self.ax.text(center_x, center_y, "EXCITE SWITCH", weight='bold', ha='center',
                         va='center', fontsize=10, color=HPHMI.darker_gray, transform=self.fig.transFigure)


        # Create a excite_switch dynamic box
        rect = RECT['excite_switch_dynamic']

        self.excite_switch_box = self.ax.add_patch(
            Rectangle((rect[0], rect[1]), rect[2], rect[3], transform=self.fig.transFigure, 
                    facecolor=HPHMI.gray, edgecolor=HPHMI.darker_gray, linewidth=0.5, clip_on=False)
        )

        center_x = rect[0] + rect[2] / 2
        center_y = rect[1] + rect[3] / 2

        self.excite_switch_text = self.ax.text(center_x, center_y, "Loading...", weight='bold', ha='center',
                         va='center', fontsize=10, color=HPHMI.darker_gray, transform=self.fig.transFigure)


        # Create filler box right
        rect = RECT['filler_box_right']

        # Add the rectangle to the axis instead of the figure
        self.description_box = self.ax.add_patch(
            Rectangle((rect[0], rect[1]), rect[2], rect[3], transform=self.fig.transFigure, 
                    facecolor=HPHMI.gray, edgecolor=HPHMI.darker_gray, linewidth=0.5, clip_on=False)
        )

        # Create filler box left
        rect = RECT['filler_box_left']

        # Add the rectangle to the axis instead of the figure
        self.description_box = self.ax.add_patch(
            Rectangle((rect[0], rect[1]), rect[2], rect[3], transform=self.fig.transFigure, 
                    facecolor=HPHMI.gray, edgecolor=HPHMI.darker_gray, linewidth=0.5, clip_on=False)
        )

        # Add an outline box around the entire figure
        outline_box = Rectangle((0, 0), 1, 1, transform=self.fig.transFigure, 
                                facecolor='none', edgecolor=HPHMI.dark_gray, linewidth=2, clip_on=False)
        self.fig.patches.extend([outline_box])


        # Create a cooling_switch description box
        rect = RECT['cooling_switch_desc']

        self.description_box = self.ax.add_patch(
            Rectangle((rect[0], rect[1]), rect[2], rect[3], transform=self.fig.transFigure, 
                    facecolor=HPHMI.gray, edgecolor=HPHMI.darker_gray, linewidth=0.5, clip_on=False)
        )

        center_x = rect[0] + rect[2] / 2
        center_y = rect[1] + rect[3] / 2

        self.desc_text = self.ax.text(center_x, center_y, "COOLING SYSTEM", weight='bold', ha='center',
                                      va='center', fontsize=10, color=HPHMI.darker_gray, transform=self.fig.transFigure)


        # Create a cooling_switch dynamic box
        rect = RECT['cooling_switch_dynamic']

        self.cooling_switch_box = self.ax.add_patch(
            Rectangle((rect[0], rect[1]), rect[2], rect[3], transform=self.fig.transFigure, 
                    facecolor=HPHMI.gray, edgecolor=HPHMI.darker_gray, linewidth=0.5, clip_on=False)
        )

        center_x = rect[0] + rect[2] / 2
        center_y = rect[1] + rect[3] / 2

        self.cooling_switch_text = self.ax.text(center_x, center_y, "Loading...", weight='bold', ha='center',
                         va='center', fontsize=10, color=HPHMI.darker_gray, transform=self.fig.transFigure)


        # Create a transformer_sw description box
        rect = RECT['transformer_sw_desc']

        self.description_box = self.ax.add_patch(
            Rectangle((rect[0], rect[1]), rect[2], rect[3], transform=self.fig.transFigure, 
                    facecolor=HPHMI.gray, edgecolor=HPHMI.darker_gray, linewidth=0.5, clip_on=False)
        )

        center_x = rect[0] + rect[2] / 2
        center_y = rect[1] + rect[3] / 2

        self.desc_text = self.ax.text(center_x, center_y, "TRANSF SWITCH", weight='bold', ha='center',
                                      va='center', fontsize=10, color=HPHMI.darker_gray, transform=self.fig.transFigure)


        # Create a transformer_sw dynamic box
        rect = RECT['transformer_sw_dynamic']

        self.transformer_sw_box = self.ax.add_patch(
            Rectangle((rect[0], rect[1]), rect[2], rect[3], transform=self.fig.transFigure, 
                    facecolor=HPHMI.gray, edgecolor=HPHMI.darker_gray, linewidth=0.5, clip_on=False)
        )

        center_x = rect[0] + rect[2] / 2
        center_y = rect[1] + rect[3] / 2

        self.transformer_sw_text = self.ax.text(center_x, center_y, "Loading...", weight='bold', ha='center',
                         va='center', fontsize=10, color=HPHMI.darker_gray, transform=self.fig.transFigure)


        # Create a start_seq description box
        rect = RECT['start_seq_desc']

        self.description_box = self.ax.add_patch(
            Rectangle((rect[0], rect[1]), rect[2], rect[3], transform=self.fig.transFigure, 
                    facecolor=HPHMI.gray, edgecolor=HPHMI.darker_gray, linewidth=0.5, clip_on=False)
        )

        center_x = rect[0] + rect[2] / 2
        center_y = rect[1] + rect[3] / 2

        self.desc_text = self.ax.text(center_x, center_y, "STARTUP", weight='bold', ha='center',
                                      va='center', fontsize=10, color=HPHMI.darker_gray, transform=self.fig.transFigure)

        # Create a start_seq dynamic box
        rect = RECT['start_seq_dynamic']

        self.start_seq_box = self.ax.add_patch(
            Rectangle((rect[0], rect[1]), rect[2], rect[3], transform=self.fig.transFigure, 
                    facecolor=HPHMI.gray, edgecolor=HPHMI.darker_gray, linewidth=0.5, clip_on=False)
        )

        center_x = rect[0] + rect[2] / 2
        center_y = rect[1] + rect[3] / 2

        self.start_seq_text = self.ax.text(center_x, center_y, "Loading...", weight='bold', ha='center',
                         va='center', fontsize=10, color=HPHMI.darker_gray, transform=self.fig.transFigure)

        # Create a grid_switch description box
        rect = RECT['grid_switch_desc']

        self.description_box = self.ax.add_patch(
            Rectangle((rect[0], rect[1]), rect[2], rect[3], transform=self.fig.transFigure, 
                    facecolor=HPHMI.gray, edgecolor=HPHMI.darker_gray, linewidth=0.5, clip_on=False)
        )

        center_x = rect[0] + rect[2] / 2
        center_y = rect[1] + rect[3] / 2

        self.desc_text = self.ax.text(center_x, center_y, "GRID SWITCH", weight='bold', ha='center',
                                      va='center', fontsize=10, color=HPHMI.darker_gray, transform=self.fig.transFigure)

        # Create a grid_switch dynamic box
        rect = RECT['grid_switch_dynamic']

        self.grid_switch_box = self.ax.add_patch(
            Rectangle((rect[0], rect[1]), rect[2], rect[3], transform=self.fig.transFigure, 
                    facecolor=HPHMI.gray, edgecolor=HPHMI.darker_gray, linewidth=0.5, clip_on=False)
        )

        center_x = rect[0] + rect[2] / 2
        center_y = rect[1] + rect[3] / 2

        self.grid_switch_text = self.ax.text(center_x, center_y, "Loading...", weight='bold', ha='center',
                         va='center', fontsize=10, color=HPHMI.darker_gray, transform=self.fig.transFigure)

        # Create a shutdown_seq description box
        rect = RECT['shutdown_seq_desc']

        self.description_box = self.ax.add_patch(
            Rectangle((rect[0], rect[1]), rect[2], rect[3], transform=self.fig.transFigure, 
                    facecolor=HPHMI.gray, edgecolor=HPHMI.darker_gray, linewidth=0.5, clip_on=False)
        )

        center_x = rect[0] + rect[2] / 2
        center_y = rect[1] + rect[3] / 2

        self.desc_text = self.ax.text(center_x, center_y, "SHUTDOWN", weight='bold', ha='center',
                                      va='center', fontsize=10, color=HPHMI.darker_gray, transform=self.fig.transFigure)

        # Create a shutdown_seq dynamic box
        rect = RECT['shutdown_seq_dynamic']

        self.shutdown_seq_box = self.ax.add_patch(
            Rectangle((rect[0], rect[1]), rect[2], rect[3], transform=self.fig.transFigure, 
                    facecolor=HPHMI.gray, edgecolor=HPHMI.darker_gray, linewidth=0.5, clip_on=False)
        )

        center_x = rect[0] + rect[2] / 2
        center_y = rect[1] + rect[3] / 2

        self.shutdown_seq_text = self.ax.text(center_x, center_y, "Loading...", weight='bold', ha='center',
                         va='center', fontsize=10, color=HPHMI.darker_gray, transform=self.fig.transFigure)



    def update_status(self, water_in, exc_sw, cool_sw, tr_sw, start, grid_sw, shutdown):
        """Update the status of boxes based on the read statuses."""

        # Update 'water_inlet' box and text
        if water_in:
            self.water_inlet_box.set_facecolor(HPHMI.white)
            self.water_inlet_text.set_text("OPEN")
            self.water_inlet_text.set_color(HPHMI.dark_blue)
        else:
            self.water_inlet_box.set_facecolor(HPHMI.dark_gray)
            self.water_inlet_text.set_text("CLOSED")
            self.water_inlet_text.set_color(HPHMI.dark_blue)

        if exc_sw:
            self.excite_switch_box.set_facecolor(HPHMI.white)
            self.excite_switch_text.set_text("ON")
            self.excite_switch_text.set_color(HPHMI.dark_blue)
        else:
            self.excite_switch_box.set_facecolor(HPHMI.dark_gray)
            self.excite_switch_text.set_text("OFF")
            self.excite_switch_text.set_color(HPHMI.dark_blue)

        if cool_sw:
            self.cooling_switch_box.set_facecolor(HPHMI.white)
            self.cooling_switch_text.set_text("ON")
            self.cooling_switch_text.set_color(HPHMI.dark_blue)
        else:
            self.cooling_switch_box.set_facecolor(HPHMI.dark_gray)
            self.cooling_switch_text.set_text("OFF")
            self.cooling_switch_text.set_color(HPHMI.dark_blue)

        if tr_sw:
            self.transformer_sw_box.set_facecolor(HPHMI.white)
            self.transformer_sw_text.set_text("ON")
            self.transformer_sw_text.set_color(HPHMI.dark_blue)
        else:
            self.transformer_sw_box.set_facecolor(HPHMI.dark_gray)
            self.transformer_sw_text.set_text("OFF")
            self.transformer_sw_text.set_color(HPHMI.dark_blue)

        if start:
            self.start_seq_box.set_facecolor(HPHMI.white)
            self.start_seq_text.set_text("ACTIVE")
            self.start_seq_text.set_color(HPHMI.dark_blue)
        else:
            self.start_seq_box.set_facecolor(HPHMI.dark_gray)
            self.start_seq_text.set_text("OFF")
            self.start_seq_text.set_color(HPHMI.dark_blue)

        if grid_sw:
            self.grid_switch_box.set_facecolor(HPHMI.white)
            self.grid_switch_text.set_text("ON")
            self.grid_switch_text.set_color(HPHMI.dark_blue)
        else:
            self.grid_switch_box.set_facecolor(HPHMI.dark_gray)
            self.grid_switch_text.set_text("OFF")
            self.grid_switch_text.set_color(HPHMI.dark_blue)

        if shutdown:
            self.shutdown_seq_box.set_facecolor(HPHMI.white)
            self.shutdown_seq_text.set_text("ACTIVE")
            self.shutdown_seq_text.set_color(HPHMI.dark_blue)
        else:
            self.shutdown_seq_box.set_facecolor(HPHMI.dark_gray)
            self.shutdown_seq_text.set_text("OFF")
            self.shutdown_seq_text.set_color(HPHMI.dark_blue)

        self.canvas.draw()
