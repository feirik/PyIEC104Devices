import tkinter as tk
import os
import sys

# Add the parent directory of this script to the system path to allow importing modules from there
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Client.api_py104get import IEC104ClientAPI

from dynamic_bar import DynamicBar
from graph import GraphView
from indicator import Indicator
from button import ButtonView

READ_INTERVAL_MS = 1000

# Define constants for dynamic bar layout
DYNAMIC_BAR_ROW = 0
DYNAMIC_BAR_COLUMN = 5
DYNAMIC_BAR_COLUMN_SPAN = 4
DYNAMIC_BAR_ROW_SPAN = 8
DYNAMIC_BAR_PAD_Y = 20
DYNAMIC_BAR_PAD_X = 20

# Define constants for the button view layout
BUTTON_VIEW_ROW = 9
BUTTON_VIEW_COLUMN = 5
BUTTON_VIEW_COLUMN_SPAN = 4
BUTTON_VIEW_ROW_SPAN = 8
BUTTON_VIEW_PAD_Y = 20
BUTTON_VIEW_PAD_X = 20

# IOA addresses
WATER_INLET = 100 # IOA 100 - BOOL - Water inlet valve to turbine
EXCITE_SWITCH = 101 # IOA 101 - BOOL - Switch exciting voltage in generator
TRANSFORMER_SWITCH = 102 # IOA 102 - BOOL - Switch between generator and transformer
GRID_SWITCH = 103 # IOA 103 - BOOL - Switch between transformer and power grid
COOLING_SWITCH = 104 # IOA 104 - BOOL - Enable cooling fluid system for bearings, auto-operated if above limit
START_PROCESS = 105 # IOA 105 - BOOL - Activate startup sequence
SHUTDOWN_PROCESS = 106 # IOA 106 - BOOL - Activate shutdown sequence

TURBINE_SPEED = 110 # IOA 110 - Float - RPM of turbine
GENERATOR_VOLTAGE = 111 # IOA 111 - Float - Voltage produced by generator
GRID_POWER = 112 # IOA 112 - Estimated kW produced, demand will fluctuate
BEARING_TEMP = 113 # IOA 113 - Bearing temp
FLOAT_TEST = 120 # IOA 120 - Testing float write and read

class HMIController:
    def __init__(self, view, host, port, timeout, os):
        self.view = view
        self.host = host
        self.port = port
        self.timeout = timeout
        self.os = os

        # Store state of read values
        self.data = None

        # Initialize the Graph
        self.graph = GraphView(self.view)
        self.graph.canvas_widget.grid(row=0, column=0, columnspan=2, pady=20, padx=20)
        
        # Initialization for periodic reading of holding register
        self._after_id = self.view.after(READ_INTERVAL_MS, self.read_data_periodically)

        self.dynamic_bar = DynamicBar(self.view)
        self.dynamic_bar.canvas_widget.grid(row=DYNAMIC_BAR_ROW, 
                                            column=DYNAMIC_BAR_COLUMN, 
                                            columnspan=DYNAMIC_BAR_COLUMN_SPAN, 
                                            rowspan=DYNAMIC_BAR_ROW_SPAN, 
                                            pady=DYNAMIC_BAR_PAD_Y, 
                                            padx=DYNAMIC_BAR_PAD_X)

        self.indicator = Indicator(self.view)

        self.button_view = ButtonView(self.view, self, self.os)
        self.button_view.canvas_widget.grid(row=BUTTON_VIEW_ROW, 
                                            column=BUTTON_VIEW_COLUMN, 
                                            columnspan=BUTTON_VIEW_COLUMN_SPAN, 
                                            rowspan=BUTTON_VIEW_ROW_SPAN, 
                                            pady=BUTTON_VIEW_PAD_Y, 
                                            padx=BUTTON_VIEW_PAD_X)

        # Bind the window's close event
        self.view.master.protocol("WM_DELETE_WINDOW", self.on_closing)


    def set_default_view(self, event=None):
        self.graph.set_view_type('default')

    def set_low_view(self, event=None):
        self.graph.set_view_type('low')

    def set_high_view(self, event=None):
        self.graph.set_view_type('high')


    def write_bool(self, addr, value):
        client = IEC104ClientAPI(self.host, self.port, self.timeout)
        result = client.write_single_command(addr, value)
        client.close()
        return result

    def write_float(self, addr, value):
        client = IEC104ClientAPI(self.host, self.port, self.timeout)
        result = client.write_setpoint_command(addr, value)
        client.close()
        return result

    def read_values(self):
        client = IEC104ClientAPI(self.host, self.port, self.timeout)
        data = client.request_data()
        client.close()
        
        return data

    def get_current_value(self, addr):
        return self.data[addr]


    def read_data_periodically(self):
        # First, we cancel any previous scheduling to ensure that we don't have multiple calls scheduled
        if hasattr(self, '_after_id'):
            self.view.after_cancel(self._after_id)

        try:
            # TODO, use new functions

            data = self.read_values()

            if data:
                generator_voltage = data[GENERATOR_VOLTAGE]
                grid_power = data[GRID_POWER]
                bearing_temperature = data[BEARING_TEMP]

                self.graph.update_graph(generator_voltage, grid_power)
                self.data = data

                # TODO fix limits if needed
                self.dynamic_bar.set_value(0, 120, round(bearing_temperature, 1))
            

            # Pass in data instead
            self.indicator.update_status(data)

            # Save the after_id to cancel it later upon closing
            self._after_id = self.view.after(READ_INTERVAL_MS, self.read_data_periodically)

        except Exception as e:
            print('Error:', e)


    def on_closing(self):
        """Called when the Tkinter window is closing."""
        if hasattr(self, '_after_id'):
            self.view.after_cancel(self._after_id)
        self.view.master.quit()
        self.view.master.destroy()