import argparse
import threading
import random
import time

import c104

IEC104_PORT = 2404

CASDU = 1 # Using CASDU address 1

IOA_SIZE = 65536
SET_POINT_OFFSET = 14000

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

MAX_WATER_SPEED = 5 # m3/s
MAX_TURBINE_SPEED = 250 # RPM
PROD_VOLTAGE_MIDPOINT = 3300 # Volts
PROD_VOLTAGE_LOW = 2500 # Volts

GRID_POWER_ADJUSTMENT_INTERVAL = 120  # 2 minutes in seconds
GRID_POWER_FLUCTUATION = 0.4  # 40% change in demand
GRID_POWER_MIDPOINT = 1305 # kW produced midpoint
ADJUSTMENT_FACTOR = 30 # Used for setting how fast the grid power will change towards target point

TEMPERATURE_ENV = 15 # 15 degrees celsius assumed for environment
TEMPERATURE_START_COOLING = 70 # Start cooling system at 70 degrees celsius
TEMPERATURE_STOP_COOLING = 40 # Stop cooling system at 40 degrees celsius
COOLING_FACTOR = 0.02
COOLING_DURATION = 30 # 30 seconds cycles of cooling

# Error constants
TEMPERATURE_ERROR = 110
ERROR_FLOAT = 9999
ERROR_BOOL = 1

class IEC104Server:
    def __init__(self, host, port, debug=False):
        self.debug = debug
        
        # Create server and station
        self.server  = c104.Server(ip=host, port=port)
        self.station = self.server.add_station(common_address=CASDU)

        if self.debug:
            c104.set_debug_mode(c104.Debug.Server |
                                 c104.Debug.Point |
                                 c104.Debug.Callback)

        # Add single point measurement points
        self.sp_pts = {}
        for ioa in (
            SP_WATER_INLET, SP_EXCITE_SWITCH, SP_TRANSFORMER_SWITCH,
            SP_GRID_SWITCH, SP_COOLING_SWITCH, SP_START_PROCESS, SP_SHUTDOWN_PROCESS
        ):
            pt = self.station.add_point(io_address=ioa, type=c104.Type.M_SP_NA_1)
            self.sp_pts[ioa] = pt

        # Add single point command points
        self.cmd_pts = {}
        for ioa in (
            CMD_WATER_INLET, CMD_EXCITE_SWITCH, CMD_TRANSFORMER_SWITCH,
            CMD_GRID_SWITCH, CMD_COOLING_SWITCH, CMD_START_PROCESS, CMD_SHUTDOWN_PROCESS
        ):
            pt = self.station.add_point(io_address=ioa, type=c104.Type.C_SC_NA_1)
            pt.on_receive(self.on_bool_write)
            self.cmd_pts[ioa] = pt

        # Add analog float measurement points
        self.ana_pts = {}
        for ioa in (ANA_TURBINE_SPEED, ANA_GENERATOR_VOLTAGE, ANA_GRID_POWER, ANA_BEARING_TEMP):
            pt = self.station.add_point(io_address=ioa, type=c104.Type.M_ME_NC_1)
            self.ana_pts[ioa] = pt

        # Initialize IOA array with default values (0)
        self.ioa_register = [0] * IOA_SIZE

        # Error boolean indicating process is malfunctioning
        self.process_error = False

        # Set IOA startup values
        self.ioa_register[SP_WATER_INLET] = 0
        self.ioa_register[SP_EXCITE_SWITCH] = 0
        self.ioa_register[SP_TRANSFORMER_SWITCH] = 0
        self.ioa_register[SP_GRID_SWITCH] = 0
        self.ioa_register[SP_COOLING_SWITCH] = 0
        self.ioa_register[SP_START_PROCESS] = 0
        self.ioa_register[SP_SHUTDOWN_PROCESS] = 0

        self.ioa_register[ANA_TURBINE_SPEED] = 0.0
        self.ioa_register[ANA_GENERATOR_VOLTAGE] = 0.0
        self.ioa_register[ANA_GRID_POWER] = 0.0
        self.ioa_register[ANA_BEARING_TEMP] = TEMPERATURE_ENV

        for ioa, pt in self.sp_pts.items():
            pt.value = bool(self.ioa_register[ioa])
        for ioa, pt in self.ana_pts.items():
            pt.value = float(self.ioa_register[ioa])

        self.water_speed = 0.0
        self.grid_voltage = GRID_POWER_MIDPOINT
        self.grid_power_target = GRID_POWER_MIDPOINT
        self.last_target_update_time = time.time()
        self.last_cooling_start_time = None

        self.listener_thread = threading.Thread(
            target=self.server.start,
            daemon=True,
            name="IEC104-Listener"
        )
        self.listener_thread.start()

        # Start a thread to simulate data changes
        self.simulation_thread = threading.Thread(target=self.simulate_data)
        self.simulation_thread.daemon = True
        self.simulation_thread.start()

    def on_bool_write(
        self,
        point: c104.Point,
        previous_info: c104.Information,
        message:    c104.IncomingMessage
    ) -> c104.ResponseState:
        # Extract the 0/1 payload
        cmd: c104.SingleCmd = message.info
        
        if cmd.value:
            new_val = 1
        else:
            new_val = 0

        if self.debug:
            print(f"[WRITE] IOA {point.io_address} -> {new_val}")

        # Update IOA register for command point
        self.ioa_register[ point.io_address ] = new_val
        # Update IOA register for measurement point
        self.ioa_register[ point.io_address - SET_POINT_OFFSET ] = new_val

        return c104.ResponseState.SUCCESS


    def push_all_points(self):
        # Update IEC-104 point values based on IOA register (simulated values)
        for ioa, pt in self.sp_pts.items():
            pt.value = bool(self.ioa_register[ioa])
        # Analog measurement values
        for ioa, pt in self.ana_pts.items():
            pt.value = float(self.ioa_register[ioa])


    def simulate_data(self):
        while True:
            if self.ioa_register[SP_START_PROCESS] == 1 and self.ioa_register[SP_SHUTDOWN_PROCESS] == 0:
                startup_thread = threading.Thread(target=self.start_process_sequence)
                startup_thread.start()

            if self.ioa_register[SP_SHUTDOWN_PROCESS] == 1 and self.ioa_register[SP_START_PROCESS] == 0:
                shutdown_thread = threading.Thread(target=self.shutdown_process_sequence)
                shutdown_thread.start()

            self.update_water_speed()
            self.update_grid_voltage()
            self.ioa_register[ANA_TURBINE_SPEED] = self.calculate_turbine_speed()
            self.ioa_register[ANA_GENERATOR_VOLTAGE] = self.update_generator_voltage()
            self.ioa_register[ANA_GRID_POWER] = self.update_grid_power()
            self.ioa_register[ANA_BEARING_TEMP] = self.update_bearing_temperature()
            self.ioa_register[SP_COOLING_SWITCH] = self.manage_cooling_system()

            # Overwrite values if process is malfunctioning
            if self.process_error:
                self.set_error_values()

            self.push_all_points()
            time.sleep(1)


    # Simulated startup process
    def start_process_sequence(self):
        self.ioa_register[SP_WATER_INLET] = 1
        time.sleep(15)
        self.ioa_register[SP_EXCITE_SWITCH] = 1
        time.sleep(25)
        self.ioa_register[SP_TRANSFORMER_SWITCH] = 1
        time.sleep(3)
        self.ioa_register[SP_GRID_SWITCH] = 1
        self.ioa_register[SP_START_PROCESS] = 0


    # Simulated shutdown process
    def shutdown_process_sequence(self):
        self.ioa_register[SP_GRID_SWITCH] = 0
        self.ioa_register[SP_TRANSFORMER_SWITCH] = 0
        time.sleep(1)
        self.ioa_register[SP_EXCITE_SWITCH] = 0
        time.sleep(3)
        self.ioa_register[SP_WATER_INLET] = 0
        self.ioa_register[SP_COOLING_SWITCH] = 0
        self.ioa_register[SP_SHUTDOWN_PROCESS] = 0  # Reset the shutdown process flag

    
    def update_water_speed(self):
        """
        Update the water speed based on the status of the water inlet.
        """
        if self.ioa_register[SP_WATER_INLET] == 1:
            # Increase water speed but don't let it go above MAX_WATER_SPEED
            self.water_speed = min(MAX_WATER_SPEED, self.water_speed + 0.15)
        else:
            # Decrease water speed but don't let it go below 0
            self.water_speed = max(0, self.water_speed - 0.15)


    def calculate_turbine_speed(self):
        """
        Calculate turbine speed as a function of water speed.
        """
        # Turbine speed increases more slowly towards maximum RPM
        if self.water_speed <= 0.80 * MAX_WATER_SPEED:
            turbine_speed = self.water_speed * (MAX_TURBINE_SPEED / MAX_WATER_SPEED)
        else:
            turbine_speed = self.ioa_register[ANA_TURBINE_SPEED] + 3

        turbine_speed = min(turbine_speed, MAX_TURBINE_SPEED)

        return turbine_speed


    def update_generator_voltage(self):
        """
        Update the generator voltage based on the turbine speed and excite switch.
        """
        if self.ioa_register[SP_EXCITE_SWITCH] == 0:
            # If the excite switch is off, set generator voltage to 0
            generator_voltage = 0.0
        else:
            # If the excite switch is on, calculate generator voltage based on turbine speed
            proportion = self.ioa_register[ANA_TURBINE_SPEED] / MAX_TURBINE_SPEED
            base_voltage = proportion * PROD_VOLTAGE_MIDPOINT
            # Random fluctuation of 5% for the generator voltage
            fluctuation = random.uniform(-0.05, 0.05)
            generator_voltage = base_voltage * (1 + fluctuation)

        if self.ioa_register[SP_GRID_SWITCH] == 1:
            # Check if grid breaker was closed with a large voltage difference with the grid
            if generator_voltage < (PROD_VOLTAGE_LOW):
                self.process_error = True
            else:
                # Generator is forced to follow the grid voltage
                generator_voltage = self.grid_voltage

        return generator_voltage


    def update_grid_voltage(self):
        """
        Update the grid voltage with random fluctuations.
        """
        fluctuation = random.uniform(-0.03, 0.03)
        self.grid_voltage = int(PROD_VOLTAGE_MIDPOINT * (1 + fluctuation))


    def update_grid_power_target(self):
        """
        Update the target grid power every 2 minutes.
        """
        current_time = time.time()
        if current_time - self.last_target_update_time >= GRID_POWER_ADJUSTMENT_INTERVAL:
            fluctuation = GRID_POWER_MIDPOINT * GRID_POWER_FLUCTUATION
            self.grid_power_target = GRID_POWER_MIDPOINT + random.uniform(-fluctuation, fluctuation)
            self.last_target_update_time = current_time

            if self.debug:
                print(f"New grid power target is: {self.grid_power_target}")


    def update_grid_power(self):
        """
        Gradually adjust the grid power towards the target based on transformer and grid switches.
        """
        self.update_grid_power_target()
        # Output is 0 if transformer switch or grid switch is off, or low generator voltage
        if (self.ioa_register[SP_TRANSFORMER_SWITCH] == 0 or 
            self.ioa_register[SP_GRID_SWITCH] == 0 or
            self.ioa_register[ANA_GENERATOR_VOLTAGE] < PROD_VOLTAGE_MIDPOINT * 0.8):

            grid_power = 0
        else:
            if self.ioa_register[ANA_GRID_POWER] == 0:
                # Start from mid point if grid power was 0
                power_difference = self.grid_power_target - GRID_POWER_MIDPOINT
                adjustment_step = power_difference / ADJUSTMENT_FACTOR
                grid_power = GRID_POWER_MIDPOINT + adjustment_step
            else:
                power_difference = self.grid_power_target - self.ioa_register[ANA_GRID_POWER]
                adjustment_step = power_difference / ADJUSTMENT_FACTOR
                grid_power = self.ioa_register[ANA_GRID_POWER] + adjustment_step

        return grid_power


    def update_bearing_temperature(self):
        """
        Update the bearing temperature based on the turbine speed.
        """
        # Let bearing temp increase faster if the grid load is high
        grid_load_factor = (self.ioa_register[ANA_GRID_POWER] / GRID_POWER_MIDPOINT)
        grid_load = 0.5 + (grid_load_factor * grid_load_factor)
        
        if self.ioa_register[ANA_TURBINE_SPEED] > 0:
        # Calculate the increment rate based on turbine speed
            increment_rate = (self.ioa_register[ANA_TURBINE_SPEED] / MAX_TURBINE_SPEED) * 0.5 * grid_load
            bearing_temp = self.ioa_register[ANA_BEARING_TEMP] + increment_rate
        else:
            # Decrease the bearing temperature if turbine isnt running
            decrease_amount = self.ioa_register[ANA_BEARING_TEMP] * COOLING_FACTOR
            bearing_temp = max(self.ioa_register[ANA_BEARING_TEMP] - decrease_amount, TEMPERATURE_ENV)

        # If cooling system is active, cool down bearing temp
        if self.ioa_register[SP_COOLING_SWITCH] == 1:
            decrease_amount = self.ioa_register[ANA_BEARING_TEMP] * COOLING_FACTOR
            bearing_temp = max(self.ioa_register[ANA_BEARING_TEMP] - decrease_amount, TEMPERATURE_ENV)

        # Check if process is malfunctioning due to high temperature
        if bearing_temp > TEMPERATURE_ERROR:
            self.process_error = True

        return bearing_temp


    def manage_cooling_system(self):
        """
        Automatically manage the cooling system based on bearing temperature and timer
        """
        current_time = time.time()
        if self.last_cooling_start_time:
            cooling_active_duration = current_time - self.last_cooling_start_time
        else:
            cooling_active_duration = 0

        if self.ioa_register[ANA_BEARING_TEMP] > TEMPERATURE_START_COOLING:
            if not self.last_cooling_start_time or cooling_active_duration >= COOLING_DURATION:
                self.last_cooling_start_time = current_time
                enable_cooling = 1
            else:
                enable_cooling = self.ioa_register[SP_COOLING_SWITCH]
        elif cooling_active_duration > COOLING_DURATION:
            enable_cooling = 0
            self.last_cooling_start_time = None
        else:
            enable_cooling = self.ioa_register[SP_COOLING_SWITCH]

        return enable_cooling


    def set_error_values(self):
        self.ioa_register[ANA_TURBINE_SPEED] = ERROR_FLOAT
        self.ioa_register[ANA_GENERATOR_VOLTAGE] = ERROR_FLOAT
        self.ioa_register[ANA_GRID_POWER] = ERROR_FLOAT
        self.ioa_register[ANA_BEARING_TEMP] = ERROR_FLOAT

        self.ioa_register[SP_WATER_INLET] = ERROR_BOOL
        self.ioa_register[SP_EXCITE_SWITCH] = ERROR_BOOL
        self.ioa_register[SP_TRANSFORMER_SWITCH] = ERROR_BOOL
        self.ioa_register[SP_GRID_SWITCH] = ERROR_BOOL
        self.ioa_register[SP_COOLING_SWITCH] = ERROR_BOOL
        self.ioa_register[SP_START_PROCESS] = ERROR_BOOL
        self.ioa_register[SP_SHUTDOWN_PROCESS] = ERROR_BOOL


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host IP address')
    parser.add_argument('-p', '--port', type=int, default=IEC104_PORT, help='Port number')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug mode')

    args = parser.parse_args()

    print(f"Starting IEC 104 server at {args.host}:{args.port} with debug mode {'enabled' if args.debug else 'disabled'}")

    server = IEC104Server(args.host, args.port, args.debug)
    print("IEC-104 server is now listening on port", args.port)
    input("Press Enter to terminate the server\n")
    server.server.stop()
