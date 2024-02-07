import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from colors import HPHMI

BAR_OUTLINES = {
    'gen_voltage': {
        'x': 0.9439,
        'y': 0.121,
        'width': 0.015,
        'height': 0.832
    },
    'grid_power': {
        'x': 0.96,
        'y': 0.121,
        'width': 0.015,
        'height': 0.832
    }
}

# Constants for dynamic bars
BASE_Y = 0.121
BAR_SCALE = 0.832
UPPER_BOUNDARY = 0.953
NUMBER_OF_READINGS = 300

Y_MAX = 6000
Y_MIN = 0

Y_LABEL_OFFSET = -8
Y_LABEL_MIN = 50
Y_LABEL_MAX = 5850

class GraphView:
    def __init__(self, master):
        """Initialize the Matplotlib figure and axis."""
        self.fig, self.ax = plt.subplots(figsize=(5, 3.2))
        self.view_type = 'default'
        self.master = master
        self.setup_view(master)

        self.grid_power = []
        self.gen_voltage = []


    def create_rectangle(self, x, y, width, height, facecolor, edgecolor, linewidth, transform=None, clip_on=False):
        """Utility function to create a rectangle with given parameters."""
        return Rectangle((x, y), width, height, transform=transform or self.fig.transFigure, 
                        facecolor=facecolor, edgecolor=edgecolor, linewidth=linewidth, clip_on=clip_on)


    def setup_view(self, master):
        """Setup the Matplotlib figure and axis."""
        # Set the figure background color
        self.fig.patch.set_facecolor(HPHMI.gray)

        # Set the axis background color
        self.ax.set_facecolor(HPHMI.gray)
        
        # Set consistent intervals for the X and Y axes
        self.ax.set_xlim(0, 300)  # Fixed at readings
        self.ax.set_ylim(Y_MIN, Y_MAX)

        self.ax.set_xticks([0, 60, 120, 180, 240, 300])
        self.ax.set_xticklabels(['-5','-4','-3', '-2', '-1', '5m'])
        xticks = self.ax.get_xticklabels()
        xticks[-1].set_color(HPHMI.dark_green)
        xticks[-1].set_weight('bold')
        
        # Generator voltage label
        self.ax.set_ylabel("0\nGen\nVoltage\n(V)", rotation=0, labelpad=20, va='center', 
                    bbox=dict(facecolor='none', edgecolor=HPHMI.dark_blue, boxstyle='square', linewidth=2))
        
        # Grid power label
        grid_power_label_text = f"0\n Power \nProd\n(kW)"
        x_position = -29
        y_position = 1200
        
        self.ax.text(x_position, y_position, grid_power_label_text, 
            rotation=0, ha='center', va='center',
            bbox=dict(facecolor='none', edgecolor=HPHMI.brown, boxstyle='square', linewidth=2))

        # Hide y-axis tick lables
        self.ax.set_yticklabels([])

        # Manually add the y-labels at desired positions
        y_label_min = self.ax.text(Y_LABEL_OFFSET, Y_LABEL_MIN, str(Y_MIN), ha='right', va='center')
        y_label_max = self.ax.text(Y_LABEL_OFFSET, Y_LABEL_MAX, str(Y_MAX), ha='right', va='center')

        # Format the y-labels
        y_label_min.set_color(HPHMI.dark_green)
        y_label_min.set_weight('bold')
        y_label_max.set_color(HPHMI.dark_green)
        y_label_max.set_weight('bold')

        # Outline bar for gen_voltage
        voltage_gen_outline = self.create_rectangle(BAR_OUTLINES['gen_voltage']['x'], 
                                                    BAR_OUTLINES['gen_voltage']['y'], 
                                                    BAR_OUTLINES['gen_voltage']['width'], 
                                                    BAR_OUTLINES['gen_voltage']['height'], 
                                                    HPHMI.gray, HPHMI.dark_gray, 1)

        
        # Outline bar for grid_power
        grid_power_outline = self.create_rectangle(BAR_OUTLINES['grid_power']['x'], 
                                                   BAR_OUTLINES['grid_power']['y'], 
                                                   BAR_OUTLINES['grid_power']['width'], 
                                                   BAR_OUTLINES['grid_power']['height'], 
                                                   HPHMI.gray, HPHMI.dark_gray, 1)

        self.fig.patches.extend([voltage_gen_outline, grid_power_outline])

        plt.setp(self.ax.spines.values(), color=HPHMI.dark_gray)

        # Use faint grid lines
        self.ax.grid(color=HPHMI.dark_gray, linestyle='--', linewidth=0.5, alpha=1)

        # Embed the Matplotlib figure into the Tkinter window
        self.canvas = FigureCanvasTkAgg(self.fig, master=master)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.grid(row=0, column=0, columnspan=4, rowspan=8, pady=20, padx=20)

        # Add an outline box around the entire figure
        outline_box = Rectangle((0, 0), 1, 1, transform=self.fig.transFigure, 
                                facecolor='none', edgecolor=HPHMI.dark_gray, linewidth=2, clip_on=False)
        self.fig.patches.extend([outline_box])

        self.fig.tight_layout()


    def update_graph(self, gen_voltage_data, grid_power_data):
        """Updates the graph with the provided readings."""
        
        self.gen_voltage.append(gen_voltage_data)
        self.grid_power.append(grid_power_data)

        # Ensure only the last 300 readings are kept
        if len(self.grid_power) > NUMBER_OF_READINGS:
            self.grid_power.pop(0)
        if len(self.gen_voltage) > NUMBER_OF_READINGS:
            self.gen_voltage.pop(0)

        # Find the minimum and maximum values
        gen_voltage_min = min(self.gen_voltage)
        gen_voltage_max = max(self.gen_voltage)
        grid_power_min = min(self.grid_power)
        grid_power_max = max(self.grid_power)

        self.ax.set_ylim(Y_MIN, Y_MAX)
        y_range = Y_MAX - Y_MIN

        normalized_min_in = (gen_voltage_min - Y_MIN) / y_range
        normalized_max_in = (gen_voltage_max - Y_MIN) / y_range

        normalized_min_out = (grid_power_min - Y_MIN) / y_range
        normalized_max_out = (grid_power_max - Y_MIN) / y_range

        # Clamp normalized values between 0 and 1
        normalized_min_in = min(max(normalized_min_in, 0), 1)
        normalized_max_in = min(max(normalized_max_in, 0), 1)

        normalized_min_out = min(max(normalized_min_out, 0), 1)
        normalized_max_out = min(max(normalized_max_out, 0), 1)

        # Use the normalized values to set the height and starting point of the colored rectangle
        rect_height_in = normalized_max_in - normalized_min_in
        rect_y_in = BASE_Y + normalized_min_in * BAR_SCALE

        rect_height_out = normalized_max_out - normalized_min_out
        rect_y_out = BASE_Y + normalized_min_out * BAR_SCALE

        # For the in_voltage dynamic bar, check bar is not below the lower boundary
        rect_y_in = max(BASE_Y, rect_y_in)

        # If the top of the dynamic bar exceeds the upper boundary, adjust the height and base
        if rect_y_in + rect_height_in * BAR_SCALE > UPPER_BOUNDARY:
            overflow = (rect_y_in + rect_height_in * BAR_SCALE) - UPPER_BOUNDARY
            rect_height_in -= overflow / BAR_SCALE
            rect_y_in += overflow

        # For the out_voltage dynamic bar, check bar is not below the lower boundary
        rect_y_out = max(BASE_Y, rect_y_out)

        # If the top of the dynamic bar exceeds the upper boundary, adjust the height and base
        if rect_y_out + rect_height_out * BAR_SCALE > UPPER_BOUNDARY:
            overflow = (rect_y_out + rect_height_out * BAR_SCALE) - UPPER_BOUNDARY
            rect_height_out -= overflow / BAR_SCALE
            rect_y_out += overflow

        # Update the Matplotlib plot
        self.ax.cla()
        
        # Plot the data
        self.ax.plot(self.gen_voltage, "-o", color=HPHMI.dark_blue, markersize=1)
        self.ax.plot(self.grid_power, "-o", color=HPHMI.brown, markersize=1)

        # Generator voltage label
        voltage_gen_label_text = f"{round(gen_voltage_data, 1)}\nGen\nVoltage\n(V)"
        self.ax.set_ylabel(voltage_gen_label_text, rotation=0, labelpad=20, va='center', 
                    bbox=dict(facecolor='none', edgecolor=HPHMI.dark_blue, boxstyle='square', linewidth=2))

        # Grid power label
        grid_power_label_text = f"{round(grid_power_data, 1)}\n Power \nProd\n(kW)"
        x_position = -29
        y_position = 1200
        self.ax.text(x_position, y_position, grid_power_label_text, 
            rotation=0, ha='center', va='center',
            bbox=dict(facecolor='none', edgecolor=HPHMI.brown, boxstyle='square', linewidth=2))

        # Hide y-axis tick lables
        self.ax.set_yticklabels([])

        # Manually add the y-labels at desired positions
        y_label_min = self.ax.text(Y_LABEL_OFFSET, Y_LABEL_MIN, str(Y_MIN), ha='right', va='center')
        y_label_max = self.ax.text(Y_LABEL_OFFSET, Y_LABEL_MAX, str(Y_MAX), ha='right', va='center')

        # Format the y-labels
        y_label_min.set_color(HPHMI.dark_green)
        y_label_min.set_weight('bold')
        y_label_max.set_color(HPHMI.dark_green)
        y_label_max.set_weight('bold')

        # Set x-ticks to represent elapsed time
        self.ax.set_xticks([0, 60, 120, 180, 240, 300])
        self.ax.set_xticklabels(['-5','-4','-3', '-2', '-1', '5m'])

        # Set rightmost x-tick to describe the x-axis
        xticks = self.ax.get_xticklabels()
        xticks[-1].set_color(HPHMI.dark_green)
        xticks[-1].set_weight('bold')

        # Outline bar for gen_voltage
        voltage_gen_outline = self.create_rectangle(BAR_OUTLINES['gen_voltage']['x'], 
                                                    BAR_OUTLINES['gen_voltage']['y'], 
                                                    BAR_OUTLINES['gen_voltage']['width'], 
                                                    BAR_OUTLINES['gen_voltage']['height'], 
                                                    HPHMI.gray, HPHMI.dark_gray, 1)

        # Inner bar representing the input voltage data range
        voltage_gen_bar = self.create_rectangle(BAR_OUTLINES['gen_voltage']['x'], 
                                               rect_y_in, 
                                               BAR_OUTLINES['gen_voltage']['width'], 
                                               rect_height_in * BAR_OUTLINES['gen_voltage']['height'], 
                                               HPHMI.dark_blue, 'none', 0.5)

        # Outline bar for grid_power
        grid_power_outline = self.create_rectangle(BAR_OUTLINES['grid_power']['x'], 
                                                   BAR_OUTLINES['grid_power']['y'], 
                                                   BAR_OUTLINES['grid_power']['width'], 
                                                   BAR_OUTLINES['grid_power']['height'], 
                                                   HPHMI.gray, HPHMI.dark_gray, 1)

        # Inner bar representing the output voltage data range
        grid_power_bar = self.create_rectangle(BAR_OUTLINES['grid_power']['x'], 
                                                rect_y_out, 
                                                BAR_OUTLINES['grid_power']['width'], 
                                                rect_height_out * BAR_OUTLINES['grid_power']['height'], 
                                                HPHMI.brown, 'none', 0.5)
        
        self.fig.patches.extend([voltage_gen_outline, voltage_gen_bar, grid_power_outline, grid_power_bar])

        # Set the axes labels and grid
        self.ax.set_xlim(0, 300)  # Fixed at 300 readings
        self.ax.set_ylim(Y_MIN, Y_MAX)
        self.ax.grid(color=HPHMI.dark_gray, linestyle='--', linewidth=0.5, alpha=1)
        self.fig.tight_layout()
        self.canvas.draw()
