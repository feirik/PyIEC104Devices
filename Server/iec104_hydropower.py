import argparse
import socket
import struct
import threading
import random
import time

IEC104_PORT = 2404
DELAY_TIME = 0.05

IOA_SIZE = 65536

SINGLE_INFO = 1 # M_SP_NA_1
FLOAT_INFO = 13 # M_ME_NC_1
SINGLE_CMD = 45 # C_SC_NA_1
SET_POINT_CMD = 50 # C_SE_NC_1
INTERROGATION_CMD = 100 # C_IC_NA_1

ACT_COT = 6 # Activation
ACT_CONF_COT = 7 # Activation confirmation
IOA_ERROR_COT = 47 # Unknown IOA

CASDU = 1 # Using CASDU address 1

STARTDT_ACT_FRAME = b'\x68\x04\x07\x00\x00\x00'
STARTDT_CON_FRAME = b'\x68\x04\x0b\x00\x00\x00'
STOPDT_ACT_FRAME = b'\x68\x04\x13\x00\x00\x00'
STOPDT_CON_FRAME = b'\x68\x04\x23\x00\x00\x00'

SINGLE_COMMAND_START = b'\x68\x0e\x00\x00\x00\x00\x2d\x01\x06\x00\x01'
SET_POINT_START = b'\x68\x12\x00\x00\x00\x00\x32\x01\x06\x00\x01'
INTERROGATION_FRAME = b'\x68\x0e\x00\x00\x00\x00\x64\x01\x06\x00\x01\x00\x00\x00\x00\x14'

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

MAX_WATER_SPEED = 5 # m3/s
MAX_TURBINE_SPEED = 250 # RPM
PROD_VOLTAGE = 5500 # Volts
POWER_OUTPUT_CONV = 0.234 # P (kW) = V * sqrt(3) * I * cos(phi) / kW conv = V * sqrt(3) * 150 * 0.9 / 1000 = V * 0.234

GRID_POWER_ADJUSTMENT_INTERVAL = 120  # 2 minutes in seconds
GRID_POWER_FLUCTUATION = 0.4  # 30% change in demand
GRID_POWER_MIDPOINT = 1305 # kW produced midpoint
ADJUSTMENT_FACTOR = 30 # Used for setting how fast the grid power will change towards target point

TEMPERATURE_ENV = 15 # 15 degrees celsius assumed for environment
TEMPERATURE_START_COOLING = 70 # Start cooling system at 70 degrees celsius
TEMPERATURE_STOP_COOLING = 40 # Stop cooling system at 40 degrees celsius
COOLING_FACTOR = 0.02
COOLING_DURATION = 30 # 30 seconds cycles of cooling

class IEC104Server:
    def __init__(self, host, port, debug=False):
        self.debug = debug
        self.listening = False

        # Initialize IOA array with default values (0)
        self.ioa_register = [0] * IOA_SIZE
        self.used_bool_ioa = []
        self.used_float_ioa = []

        # Set IOA startup values
        self.ioa_register[WATER_INLET] = 0
        self.ioa_register[EXCITE_SWITCH] = 0
        self.ioa_register[TRANSFORMER_SWITCH] = 0
        self.ioa_register[GRID_SWITCH] = 0
        self.ioa_register[COOLING_SWITCH] = 0
        self.ioa_register[START_PROCESS] = 0
        self.ioa_register[SHUTDOWN_PROCESS] = 0

        self.ioa_register[TURBINE_SPEED] = 0.0
        self.ioa_register[GENERATOR_VOLTAGE] = 0.0
        self.ioa_register[GRID_POWER] = 0.0
        self.ioa_register[BEARING_TEMP] = TEMPERATURE_ENV

        self.used_bool_ioa.extend([WATER_INLET, EXCITE_SWITCH, TRANSFORMER_SWITCH, GRID_SWITCH, 
                                   COOLING_SWITCH, START_PROCESS, SHUTDOWN_PROCESS])
        
        self.used_float_ioa.extend([TURBINE_SPEED, GENERATOR_VOLTAGE, GRID_POWER, BEARING_TEMP, FLOAT_TEST])

        self.water_speed = 0.0
        self.grid_power_target = GRID_POWER_MIDPOINT
        self.last_target_update_time = time.time()
        self.last_cooling_start_time = None

        # Sequence numbers
        self.send_sequence_number = 0
        self.receive_sequence_number = 0

        # Create a socket and bind it to the specified host and port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((host, port))

        # Start a thread to simulate data changes
        self.simulation_thread = threading.Thread(target=self.simulate_data)
        self.simulation_thread.daemon = True
        self.simulation_thread.start()


    def simulate_data(self):
        while True:
            if self.ioa_register[START_PROCESS] == 1 and self.ioa_register[SHUTDOWN_PROCESS] == 0:
                startup_thread = threading.Thread(target=self.start_process_sequence)
                startup_thread.start()

            if self.ioa_register[SHUTDOWN_PROCESS] == 1 and self.ioa_register[START_PROCESS] == 0:
                shutdown_thread = threading.Thread(target=self.shutdown_process_sequence)
                shutdown_thread.start()

            self.update_water_speed()
            self.ioa_register[TURBINE_SPEED] = self.calculate_turbine_speed()
            self.ioa_register[GENERATOR_VOLTAGE] = self.update_generator_voltage()
            self.ioa_register[GRID_POWER] = self.update_grid_power()
            self.ioa_register[BEARING_TEMP] = self.update_bearing_temperature()
            self.ioa_register[COOLING_SWITCH] = self.manage_cooling_system()

            time.sleep(1)


    # Simulated startup process
    def start_process_sequence(self):
        self.ioa_register[WATER_INLET] = 1
        time.sleep(15)
        self.ioa_register[EXCITE_SWITCH] = 1
        time.sleep(25)
        self.ioa_register[TRANSFORMER_SWITCH] = 1
        self.ioa_register[GRID_SWITCH] = 1
        self.ioa_register[START_PROCESS] = 0


    # Simulated shutdown process
    def shutdown_process_sequence(self):
        self.ioa_register[GRID_SWITCH] = 0
        self.ioa_register[TRANSFORMER_SWITCH] = 0
        time.sleep(1)
        self.ioa_register[EXCITE_SWITCH] = 0
        time.sleep(3)
        self.ioa_register[WATER_INLET] = 0
        self.ioa_register[COOLING_SWITCH] = 0
        self.ioa_register[SHUTDOWN_PROCESS] = 0  # Reset the shutdown process flag

    
    def update_water_speed(self):
        """
        Update the water speed based on the status of the water inlet.
        """
        if self.ioa_register[WATER_INLET] == 1:
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
            turbine_speed = self.ioa_register[TURBINE_SPEED] + 3

        turbine_speed = min(turbine_speed, MAX_TURBINE_SPEED)

        return turbine_speed


    def update_generator_voltage(self):
        """
        Update the generator voltage based on the turbine speed and excite switch.
        """
        if self.ioa_register[EXCITE_SWITCH] == 0:
            # If the excite switch is off, set generator voltage to 0
            generator_voltage = 0.0
        else:
            # If the excite switch is on, calculate generator voltage based on turbine speed
            proportion = self.ioa_register[TURBINE_SPEED] / MAX_TURBINE_SPEED
            base_voltage = proportion * PROD_VOLTAGE
            # Random fluctuation of 3%
            fluctuation = random.uniform(-0.03, 0.03)
            generator_voltage = base_voltage * (1 + fluctuation)

        return generator_voltage


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
        if (self.ioa_register[TRANSFORMER_SWITCH] == 0 or 
            self.ioa_register[GRID_SWITCH] == 0 or
            self.ioa_register[GENERATOR_VOLTAGE] < PROD_VOLTAGE * 0.8):

            grid_power = 0
        else:
            if self.ioa_register[GRID_POWER] == 0:
                # Start from mid point if grid power was 0
                power_difference = self.grid_power_target - GRID_POWER_MIDPOINT
                adjustment_step = power_difference / ADJUSTMENT_FACTOR
                grid_power = GRID_POWER_MIDPOINT + adjustment_step
            else:
                power_difference = self.grid_power_target - self.ioa_register[GRID_POWER]
                adjustment_step = power_difference / ADJUSTMENT_FACTOR
                grid_power = self.ioa_register[GRID_POWER] + adjustment_step

        return grid_power


    def update_bearing_temperature(self):
        """
        Update the bearing temperature based on the turbine speed.
        """
        # Let bearing temp increase faster if the grid load is high
        grid_load_factor = (self.ioa_register[GRID_POWER] / GRID_POWER_MIDPOINT)
        grid_load = 0.5 + (grid_load_factor * grid_load_factor)
        
        if self.ioa_register[TURBINE_SPEED] > 0:
        # Calculate the increment rate based on turbine speed
            increment_rate = (self.ioa_register[TURBINE_SPEED] / MAX_TURBINE_SPEED) * 0.5 * grid_load
            bearing_temp = self.ioa_register[BEARING_TEMP] + increment_rate
        else:
            # Decrease the bearing temperature if turbine isnt running
            decrease_amount = self.ioa_register[BEARING_TEMP] * COOLING_FACTOR
            bearing_temp = max(self.ioa_register[BEARING_TEMP] - decrease_amount, TEMPERATURE_ENV)

        # If cooling system is active, cool down bearing temp
        if self.ioa_register[COOLING_SWITCH] == 1:
            decrease_amount = self.ioa_register[BEARING_TEMP] * COOLING_FACTOR
            bearing_temp = max(self.ioa_register[BEARING_TEMP] - decrease_amount, TEMPERATURE_ENV)

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

        if self.ioa_register[BEARING_TEMP] > TEMPERATURE_START_COOLING:
            if not self.last_cooling_start_time or cooling_active_duration >= COOLING_DURATION:
                self.last_cooling_start_time = current_time
                enable_cooling = 1
            else:
                enable_cooling = self.ioa_register[COOLING_SWITCH]
        elif cooling_active_duration > COOLING_DURATION:
            enable_cooling = 0
            self.last_cooling_start_time = None
        else:
            enable_cooling = self.ioa_register[COOLING_SWITCH]

        return enable_cooling


    def listen(self):
        self.listening = True
        self.socket.listen(1)

        while self.listening:
            conn, addr = self.socket.accept()
            if self.debug:
             print(f"Client connected from {addr}")

            while True:
                request = conn.recv(1024)
                if not request:
                    break

                if self.debug:
                    print(f"Received data from client: {request.hex()}")

                if request == INTERROGATION_FRAME:
                    self.handle_interrogation_command(conn)

                elif request.startswith(SINGLE_COMMAND_START):
                    self.handle_single_command(request, conn)

                elif request.startswith(SET_POINT_START):
                    self.handle_setpoint_command(request, conn)
                
                else:
                    response = self.handle_handshake_request(request)
                    conn.sendall(response)

                self.receive_sequence_number += 1

            conn.close()
            if self.debug:
                print(f"Client disconnected: {addr}")


    def handle_handshake_request(self, request):
        # Initialize the response as an empty byte string
        response = b''

        # Check if the request is a STARTDT ACT frame
        if request == STARTDT_ACT_FRAME:  # STARTDT ACT frame
            if self.debug:
                print("Received STARTDT ACT, sending STARTDT CON")
            # Set STARTDT CON frame as the response
            response = STARTDT_CON_FRAME
        
        # Check if the request is a STOPDT ACT frame
        elif request == STOPDT_ACT_FRAME:  # STOPDT ACT frame
            if self.debug:
                print("Received STOPDT ACT, sending STOPDT CON")
            # Send STOPDT CON frame in response
            return STOPDT_CON_FRAME

        return response


    def handle_interrogation_command(self, conn):
        """
        Handle the interrogation command by sending multiple ASDUs.
        """
        if self.debug:
            print("Received Interrogation Command, sending responses")

        # Send Type 1 bool responses
        for ioa in self.used_bool_ioa:
            asdu = self.construct_asdu(SINGLE_INFO, ACT_COT, CASDU, ioa, self.ioa_register[ioa])
            self.send_asdu_response(conn, asdu, SINGLE_INFO)
            time.sleep(DELAY_TIME)

        # Send Type 13 float responses
        for ioa in self.used_float_ioa:
            asdu = self.construct_asdu(FLOAT_INFO, ACT_COT, CASDU, ioa, self.ioa_register[ioa])
            self.send_asdu_response(conn, asdu, FLOAT_INFO)
            time.sleep(DELAY_TIME)
        

    def handle_single_command(self, request, conn):
        # Assuming the IOA starts at byte 11 (6 bytes APCI + 5 bytes ASDU header)
        ioa_index = 11
        # Extract IOA (2 bytes, with an optional 3rd byte)
        ioa_msb = request[ioa_index]  # Most Significant Byte
        ioa_lsb = request[ioa_index + 1]  # Least Significant Byte

        # Convert IOA bytes to integer (little endian)
        ioa_bytes = bytes([ioa_lsb, ioa_msb])
        ioa = int.from_bytes(ioa_bytes, 'little')

        # The command value and qualifier are after the IOA
        command_value_index = ioa_index + 3
        if command_value_index < len(request):
            # Extract command qualifier and value
            command_value = request[command_value_index + 1] if command_value_index + 1 < len(request) else None
            print(f"Handling single command --- IOA: {ioa}, Value: {command_value}")
            self.ioa_register[ioa] = command_value

            # Construct and send response ASDU
            response_asdu = self.construct_asdu(SINGLE_CMD, ACT_CONF_COT, CASDU, ioa, command_value)
            self.send_asdu_response(conn, response_asdu, SINGLE_CMD)
        else:
            print("Index out of range for command value extraction")
            response_asdu = self.construct_asdu(SINGLE_CMD, IOA_ERROR_COT, CASDU, ioa, command_value)
            self.send_asdu_response(conn, response_asdu, SINGLE_CMD)


    def handle_setpoint_command(self, request, conn):
        # Assuming the IOA starts at byte 11 (6 bytes APCI + 5 bytes ASDU header)
        ioa_index = 11

        # Extract IOA (2 bytes, with an optional 3rd byte)
        ioa_msb = request[ioa_index]  # Most Significant Byte
        ioa_lsb = request[ioa_index + 1]  # Least Significant Byte

        # Convert IOA bytes to integer (little endian)
        ioa_bytes = bytes([ioa_lsb, ioa_msb])
        ioa = int.from_bytes(ioa_bytes, 'little')

        # The setpoint value starts 3 bytes after the IOA index
        setpoint_value_index = ioa_index + 4
        if setpoint_value_index + 4 <= len(request):
            # Extract setpoint value (4 bytes, IEEE 754 format)
            setpoint_value_bytes = request[setpoint_value_index:setpoint_value_index + 4]

            # Use struct.unpack with the correct format specifier for big-endian 32-bit float
            setpoint_value = struct.unpack('<f', setpoint_value_bytes)[0]
            print(f"Handling setpoint command --- IOA: {ioa}, Value: {setpoint_value}")
            self.ioa_register[ioa] = setpoint_value

            # Construct and send response ASDU
            response_asdu = self.construct_asdu(SET_POINT_CMD, ACT_CONF_COT, CASDU, ioa, setpoint_value)
            self.send_asdu_response(conn, response_asdu, SET_POINT_CMD)
        else:
            print("Index out of range for setpoint value extraction")
            response_asdu = self.construct_asdu(SET_POINT_CMD, IOA_ERROR_COT, CASDU, ioa, None)
            self.send_asdu_response(conn, response_asdu, SET_POINT_CMD)


    def send_asdu_response(self, conn, asdu, type_id):
            """
            Send an ASDU response to the client.
            """
            send_sequence_number = (self.send_sequence_number << 1).to_bytes(2, byteorder='big')
            receive_sequence_number = (self.receive_sequence_number << 1).to_bytes(2, byteorder='big')
            if type_id == SET_POINT_CMD or type_id == FLOAT_INFO:
                apci = b'\x68\x12' + send_sequence_number + receive_sequence_number
            else:
                apci = b'\x68\x0e' + send_sequence_number + receive_sequence_number

            response = apci + asdu
            conn.sendall(response)
            if self.debug:
                print(f"Sent response: {response.hex()}")
            self.send_sequence_number += 1
            time.sleep(DELAY_TIME)


    def construct_asdu(self, type_id, cot, casdu, ioa, value=None):
        """
        Construct an ASDU frame.

        :param type_id: Type ID of the ASDU.
        :param cot: Cause of Transmission.
        :param casdu: Common Address of ASDU.
        :param ioa: Information Object Address.
        :param value: The value to be sent (optional, depending on the type).
        :return: The constructed ASDU as bytes.
        """
        asdu = bytearray()

        # Type ID
        asdu.append(type_id)

        # Variable Structure Qualifier (assuming a single information object)
        asdu.append(0x01)

        # Cause of Transmission
        asdu.append(cot)

        # Pre-CASDU
        asdu.append(0x00)

        # Common Address of ASDU (assuming 2 bytes)
        asdu += casdu.to_bytes(2, byteorder='little')

        # Information Object Address (assuming 3 bytes)
        asdu += ioa.to_bytes(3, byteorder='little')

        # Information Elements based on Type ID
        if type_id == SINGLE_INFO:
            # Assuming 'value' is a boolean for ON/OFF status
            status_value = 0x01 if value else 0x00
            asdu.append(status_value)

        elif type_id == FLOAT_INFO:
            # Convert the float value to IEEE 754 format (4 bytes)
            floating_value = struct.pack('<f', value)
            asdu += floating_value
            asdu += b'\x00' # QDS

        if type_id == SINGLE_CMD:
            # Include the command value
            command_value = 0x01 if value else 0x00
            asdu.append(command_value)

        elif type_id == SET_POINT_CMD:
            # Convert the float value to IEEE 754 format (4 bytes)
            floating_value = struct.pack('<f', value)
            asdu += floating_value
            asdu += b'\x80' # QDS

        return asdu


    def start(self):
        self.listen()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host IP address')
    parser.add_argument('-p', '--port', type=int, default=IEC104_PORT, help='Port number')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug mode')

    args = parser.parse_args()

    print(f"Starting IEC 104 server at {args.host}:{args.port} with debug mode {'enabled' if args.debug else 'disabled'}")

    server = IEC104Server(args.host, args.port, args.debug)
    server.start()
