import tkinter as tk
import os
import sys
import threading
import time
import c104

from dynamic_bar import DynamicBar
from graph import GraphView
from indicator import Indicator
from button import ButtonView

READ_INTERVAL_MS = 2000

CASDU = 1
SET_POINT_OFFSET = 14000

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

# SP (single-point) MEASUREMENT IOAs  (type=M_SP_NA_1)
SP_WATER_INLET       = 1100  # IOA 1100 - BOOL - Water inlet valve to turbine
SP_EXCITE_SWITCH     = 1101  # IOA 1101 - BOOL - Switch exciting voltage in generator
SP_TRANSFORMER_SWITCH= 1102  # IOA 1102 - BOOL - Switch between generator and transformer
SP_GRID_SWITCH       = 1103  # IOA 1103 - BOOL - Switch between transformer and power grid
SP_COOLING_SWITCH    = 1104  # IOA 1104 - BOOL - Enable cooling fluid system for bearings
SP_START_PROCESS     = 1105  # IOA 1105 - BOOL - Activate startup sequence
SP_SHUTDOWN_PROCESS  = 1106  # IOA 1106 - BOOL - Activate shutdown sequence

# SP COMMAND IOAs (type=C_SC_NA_1)
CMD_WATER_INLET       = 15100
CMD_EXCITE_SWITCH     = 15101
CMD_TRANSFORMER_SWITCH= 15102
CMD_GRID_SWITCH       = 15103
CMD_COOLING_SWITCH    = 15104
CMD_START_PROCESS     = 15105
CMD_SHUTDOWN_PROCESS  = 15106

# Analog (float) MEASUREMENT IOAs (type=M_ME_NC_1)
ANA_TURBINE_SPEED     = 10010  # IOA 15010 - RPM of turbine
ANA_GENERATOR_VOLTAGE = 10011  # IOA 15011 - Voltage produced by generator
ANA_GRID_POWER        = 10012  # IOA 15012 - Estimated kW produced
ANA_BEARING_TEMP      = 10013  # IOA 15013 - Bearing temperature

class HMIController:
    def __init__(self, view, host, port, timeout, os):
        self.view = view
        self.host = host
        self.port = port
        self.timeout = timeout
        self.os = os

        # # Debug modes
        # c104.set_debug_mode(
        #     c104.Debug.Client    |
        #     c104.Debug.Connection |
        #     c104.Debug.Callback
        # )

        # Set up c104 client
        self.client = c104.Client()
        self.conn   = self.client.add_connection(
            ip=self.host, port=self.port, init=c104.Init.NONE
        )
        # Handle unexpected messages
        self.conn.on_unexpected_message(callable=self.on_unexpected)

        station = self.conn.add_station(common_address=CASDU)

        # Register single point measurement points
        sp_ioas = (
            SP_WATER_INLET, SP_EXCITE_SWITCH, SP_TRANSFORMER_SWITCH,
            SP_GRID_SWITCH,  SP_COOLING_SWITCH, SP_START_PROCESS,
            SP_SHUTDOWN_PROCESS
        )
        self.sp_points = {}
        for ioa in sp_ioas:
            pt = station.add_point(io_address=ioa, type=c104.Type.M_SP_NA_1)
            self.sp_points[ioa] = pt

        # Register analogue measurement points
        ana_ioas = (
            ANA_TURBINE_SPEED, ANA_GENERATOR_VOLTAGE,
            ANA_GRID_POWER,    ANA_BEARING_TEMP
        )
        self.analog_points = {}
        for ioa in ana_ioas:
            pt = station.add_point(io_address=ioa, type=c104.Type.M_ME_NC_1)
            self.analog_points[ioa] = pt

        # Register single command points
        cmd_ioas = (
            CMD_WATER_INLET, CMD_EXCITE_SWITCH, CMD_TRANSFORMER_SWITCH,
            CMD_GRID_SWITCH,  CMD_COOLING_SWITCH,  CMD_START_PROCESS,
            CMD_SHUTDOWN_PROCESS
        )
        self.command_points = {}
        for ioa in cmd_ioas:
            pt = station.add_point(io_address=ioa, type=c104.Type.C_SC_NA_1)
            self.command_points[ioa] = pt

        # Start the client connection and wait for open state
        self.client.start()
        while self.conn.state != c104.ConnectionState.OPEN:
            time.sleep(0.01)

        # Store state of read values
        self.data = {}

        # Keep track of if there is an active interrogation or not
        self.interrogating = False

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

    
    def on_unexpected(
        self,
        connection: c104.Connection,
        message:    c104.IncomingMessage,
        cause:      c104.Umc
    ) -> None:
        print(f"Unexpected message from server: {cause}")


    def write_bool(self, addr, value):
        """ Send a single-point (bool) command """
        pt = self.command_points[addr]
        pt.value = bool(value)
        return pt.transmit(cause=c104.Cot.ACTIVATION)


    def read_values(self):
        """
        Do a general interrogation and return a dict of the latest point values.
        """
        self.interrogating = True

        ok = self.conn.interrogation(
            common_address=CASDU,
            cause=c104.Cot.ACTIVATION,
            qualifier=c104.Qoi.STATION,
            wait_for_response=False
        )

        self.interrogating = False

        if not ok:
            print("Interrogation failed")
            return None

        # build and return a snapshot of all point values
        snapshot = {}

        # update all single-point (bool) measurements
        for ioa, pt in self.sp_points.items():
            snapshot[ioa] = pt.value

        # update all analog (float) measurements
        for ioa, pt in self.analog_points.items():
            snapshot[ioa] = pt.value

        return snapshot


    def get_current_value(self, addr):
        # If we are reading command point addresses, return the data of the corresponding measurement point
        if(15000 < addr < 16000):
            addr -= SET_POINT_OFFSET

        return self.data[addr]


    def fetch_data_threaded(self, callback):
        def run():
            try:
                if self.interrogating is False:
                    data = self.read_values()  # Fetch data in the background thread
                    self.view.after(0, callback, data)  # Schedule the callback on the main thread
            except Exception as e:
                print(f"Error fetching data in background thread: {e}")
        
        # Start the background thread
        threading.Thread(target=run, daemon=True).start()


    def process_fetched_data(self, data):
        if data:
            self.data = data  # Update the data attribute on the main thread
        else:
            print("No data received or data fetch failed.")


    def read_data_periodically(self):
        # First, we cancel any previous scheduling to ensure that we don't have multiple calls scheduled
        if hasattr(self, '_after_id'):
            self.view.after_cancel(self._after_id)

        # Start the data fetching process in a separate thread
        self.fetch_data_threaded(self.process_fetched_data)

        try:
            if self.data:
                generator_voltage = round(self.data.get(ANA_GENERATOR_VOLTAGE, 0), 1)
                grid_power = round(self.data.get(ANA_GRID_POWER, 0), 1)
                bearing_temperature = round(self.data.get(ANA_BEARING_TEMP, 0), 1)
                turbine_speed = self.data.get(ANA_TURBINE_SPEED, 0)

                self.graph.update_graph(generator_voltage, grid_power)
                self.dynamic_bar.update_bars(bearing_temperature, turbine_speed, generator_voltage, grid_power)

                water_in = self.data.get(SP_WATER_INLET, 0)
                exc_sw = self.data.get(SP_EXCITE_SWITCH, 0)
                cool_sw = self.data.get(SP_COOLING_SWITCH, 0)
                tr_sw = self.data.get(SP_TRANSFORMER_SWITCH, 0)
                start = self.data.get(SP_START_PROCESS, 0)
                grid_sw = self.data.get(SP_GRID_SWITCH, 0)
                shutdown = self.data.get(SP_SHUTDOWN_PROCESS, 0)

                self.indicator.update_status(water_in, exc_sw, cool_sw, tr_sw, start, grid_sw, shutdown)
                self.button_view.update_labels(water_in, exc_sw, tr_sw, grid_sw, turbine_speed, 
                                            bearing_temperature, generator_voltage, grid_power)
        except Exception as e:
            print(f"Error during data processing: {e}")


        # Save the after_id to cancel it later upon closing
        self._after_id = self.view.after(READ_INTERVAL_MS, self.read_data_periodically)


    def on_closing(self):
        """Called when the Tkinter window is closing."""
        if hasattr(self, '_after_id'):
            self.view.after_cancel(self._after_id)
        self.view.master.quit()
        self.view.master.destroy()