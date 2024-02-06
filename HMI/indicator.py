import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Rectangle
from colors import HPHMI

RECT = {
    'control_status': [0.022, 0.885, 0.954, 0.07],
    'enable_output_desc': [0.022, 0.815, 0.32, 0.07],
    'enable_output_dynamic': [0.022, 0.745, 0.32, 0.07],
    'enable_override_desc': [0.505, 0.815, 0.32, 0.07],
    'enable_override_dynamic': [0.505, 0.745, 0.32, 0.07],
    'filler_box_right': [0.825, 0.745, 0.151, 0.14],
    'filler_box_left': [0.342, 0.745, 0.163, 0.14]
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

        # Create a enable output description box
        rect = RECT['enable_output_desc']

        self.description_box = self.ax.add_patch(
            Rectangle((rect[0], rect[1]), rect[2], rect[3], transform=self.fig.transFigure, 
                    facecolor=HPHMI.gray, edgecolor=HPHMI.darker_gray, linewidth=0.5, clip_on=False)
        )

        center_x = rect[0] + rect[2] / 2
        center_y = rect[1] + rect[3] / 2

        self.desc_text = self.ax.text(center_x, center_y, "ENABLE OUTPUT", weight='bold', ha='center',
                                      va='center', fontsize=10, color=HPHMI.darker_gray, transform=self.fig.transFigure)


        # Create a enable output dynamic box
        rect = RECT['enable_output_dynamic']

        self.en_output_box = self.ax.add_patch(
            Rectangle((rect[0], rect[1]), rect[2], rect[3], transform=self.fig.transFigure, 
                    facecolor=HPHMI.gray, edgecolor=HPHMI.darker_gray, linewidth=0.5, clip_on=False)
        )

        center_x = rect[0] + rect[2] / 2
        center_y = rect[1] + rect[3] / 2

        self.en_output_text = self.ax.text(center_x, center_y, "Loading...", weight='bold', ha='center',
                         va='center', fontsize=10, color=HPHMI.darker_gray, transform=self.fig.transFigure)


        # Create a enable override description box
        rect = RECT['enable_override_desc']

        self.description_box = self.ax.add_patch(
            Rectangle((rect[0], rect[1]), rect[2], rect[3], transform=self.fig.transFigure, 
                    facecolor=HPHMI.gray, edgecolor=HPHMI.darker_gray, linewidth=0.5, clip_on=False)
        )

        center_x = rect[0] + rect[2] / 2
        center_y = rect[1] + rect[3] / 2

        self.desc_text = self.ax.text(center_x, center_y, "ENABLE OVERRIDE", weight='bold', ha='center',
                         va='center', fontsize=10, color=HPHMI.darker_gray, transform=self.fig.transFigure)


        # Create a enable override dynamic box
        rect = RECT['enable_override_dynamic']

        self.en_ovverride_box = self.ax.add_patch(
            Rectangle((rect[0], rect[1]), rect[2], rect[3], transform=self.fig.transFigure, 
                    facecolor=HPHMI.gray, edgecolor=HPHMI.darker_gray, linewidth=0.5, clip_on=False)
        )

        center_x = rect[0] + rect[2] / 2
        center_y = rect[1] + rect[3] / 2

        self.en_override_text = self.ax.text(center_x, center_y, "Loading...", weight='bold', ha='center',
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


    def update_status(self, data):
        """Update the status of both boxes based on the coil statuses."""
        
        # TODO, use actual new values from data
        enable_output = 1
        enable_override = 1

        # Update 'enable_output' box and text
        if enable_output:
            self.en_output_box.set_facecolor(HPHMI.white)
            self.en_output_text.set_text("ON")
            self.en_output_text.set_color(HPHMI.dark_blue)
        else:
            self.en_output_box.set_facecolor(HPHMI.dark_gray)
            self.en_output_text.set_text("OFF")
            self.en_output_text.set_color(HPHMI.dark_blue)

        # Update 'enable_override' box and text
        if enable_override:
            self.en_ovverride_box.set_facecolor(HPHMI.white)
            self.en_override_text.set_text("ON")
            self.en_override_text.set_color(HPHMI.dark_blue)
        else:
            self.en_ovverride_box.set_facecolor(HPHMI.dark_gray)
            self.en_override_text.set_text("OFF")
            self.en_override_text.set_color(HPHMI.dark_blue)

        self.canvas.draw()
