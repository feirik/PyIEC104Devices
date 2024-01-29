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

SINGLE_COMMAND_START = b'\x68\x0e\x00\x00\x00\x00\x2d\x01\x06\x01'
SET_POINT_START = b'\x68\x0e\x00\x00\x00\x00\x32\x01\x06\x01'
INTERROGATION_FRAME = b'\x68\x08\x00\x00\x00\x00\x64\x01\x06\x01\x00\x00\x00\x00'

WATER_INLET = 100 # IOA 100 - BOOL - Water inlet valve to turbine
EXCITE_SWITCH = 101 # IOA 101 - BOOL - Switch exciting voltage in generator
TRANSFORMER_SWITCH = 102 # IOA 102 - BOOL - Switch between generator and transformer
GRID_SWITCH = 103 # IOA 103 - BOOL - Switch between transformer and power grid
COOLING_SWITCH = 104 # IOA 104 - BOOL - Enable cooling fluid system for bearings, auto-operated if above limit

TURBINE_SPEED = 110 # IOA 110 - Float - RPM of turbine
GENERATOR_VOLTAGE = 111 # IOA 111 - Float - Voltage produced by generator
GRID_VOLTAGE = 112 # IOA 112 - Estimated MHw produced, demand will fluctuate
BEARING_TEMP = 113 # IOA 113 - Bearing temp

MAX_WATER_SPEED = 5 # m3/s
MAX_TURBINE_SPEED = 250 # RPM
PROD_VOLTAGE = 6500 # Volts

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

        self.ioa_register[TURBINE_SPEED] = 0.0
        self.ioa_register[GENERATOR_VOLTAGE] = 0.0
        self.ioa_register[GRID_VOLTAGE] = 0.0
        self.ioa_register[BEARING_TEMP] = 0.0

        self.used_bool_ioa.extend([WATER_INLET, EXCITE_SWITCH, TRANSFORMER_SWITCH, GRID_SWITCH, COOLING_SWITCH])
        self.used_float_ioa.extend([TURBINE_SPEED, GENERATOR_VOLTAGE, GRID_VOLTAGE, BEARING_TEMP])

        self.water_speed = 0.0

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
            self.update_water_speed()
            self.ioa_register[TURBINE_SPEED] = self.calculate_turbine_speed()
            self.ioa_register[GENERATOR_VOLTAGE] = self.update_generator_voltage()



            time.sleep(1)

    
    def update_water_speed(self):
        """
        Update the water speed based on the status of the water inlet.
        """
        if self.ioa_register[WATER_INLET] == 1:
            # Increase water speed but don't let it go above MAX_WATER_SPEED
            self.water_speed = min(MAX_WATER_SPEED, self.water_speed + 0.5)
        else:
            # Decrease water speed but don't let it go below 0
            self.water_speed = max(0, self.water_speed - 0.5)

        # Optionally print the current water speed for debugging
        if self.debug:
            print(f"Current water speed: {self.water_speed}")


    def calculate_turbine_speed(self):
        """
        Calculate turbine speed as a function of water speed.
        """
        if self.water_speed <= 0.80 * MAX_WATER_SPEED:
            turbine_speed = self.water_speed * (MAX_TURBINE_SPEED / MAX_WATER_SPEED)
        else:
            turbine_speed = self.ioa_register[TURBINE_SPEED] + 3

        # Ensure turbine speed does not exceed maximum
        turbine_speed = min(turbine_speed, MAX_TURBINE_SPEED)

        # Optionally print the current turbine speed for debugging
        if self.debug:
            print(f"Current turbine speed: {turbine_speed}")

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

        # Optionally print the current generator voltage for debugging
        if self.debug:
            print(f"Current generator voltage: {self.ioa_register[GENERATOR_VOLTAGE]}")

        return generator_voltage




    def listen(self):
        self.listening = True
        self.socket.listen(1)

        while self.listening:
            conn, addr = self.socket.accept()
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

        # Send Type 1 responses
        for i in range(1, 9):
            asdu = self.construct_asdu(SINGLE_INFO, 6, 1, 110, self.ioa_register[110])
            self.send_asdu_response(conn, asdu)
            time.sleep(DELAY_TIME)

        for i in range(1, 5):
            asdu = self.construct_asdu(FLOAT_INFO, 6, 1, 100, self.ioa_register[100])
            self.send_asdu_response(conn, asdu)
            time.sleep(DELAY_TIME)
        

    def handle_single_command(self, request, conn):
        # Assuming the IOA starts at byte 10 (6 bytes APCI + 4 bytes ASDU header)
        ioa_index = 10
        # Extract IOA (2 bytes, with an optional 3rd byte)
        ioa_msb = request[ioa_index]  # Most Significant Byte
        ioa_lsb = request[ioa_index + 1]  # Least Significant Byte

        # Convert IOA bytes to integer (little endian)
        ioa_bytes = bytes([ioa_lsb, ioa_msb])
        ioa = int.from_bytes(ioa_bytes, 'little')
        print(f"Extracted IOA bytes: {ioa_bytes.hex()} --> IOA: {ioa}")

        # The command value and qualifier are after the IOA
        command_value_index = ioa_index + 3
        if command_value_index < len(request):
            # Extract command qualifier and value
            command_value = request[command_value_index + 1] if command_value_index + 1 < len(request) else None
            print(f"Handling single command --- IOA: {ioa}, Value: {command_value}")
            self.ioa_register[ioa] = command_value

            # Construct and send response ASDU
            response_asdu = self.construct_asdu(SINGLE_CMD, ACT_CONF_COT, CASDU, ioa, command_value)
            self.send_asdu_response(conn, response_asdu)
        else:
            print("Index out of range for command value extraction")
            response_asdu = self.construct_asdu(SINGLE_CMD, IOA_ERROR_COT, CASDU, ioa, command_value)
            self.send_asdu_response(conn, response_asdu)


    def handle_setpoint_command(self, request, conn):
        # Assuming the IOA starts at byte 10 (6 bytes APCI + 4 bytes ASDU header)
        ioa_index = 10

        # Extract IOA (2 bytes, with an optional 3rd byte)
        ioa_msb = request[ioa_index]  # Most Significant Byte
        ioa_lsb = request[ioa_index + 1]  # Least Significant Byte

        # Convert IOA bytes to integer (little endian)
        ioa_bytes = bytes([ioa_lsb, ioa_msb])
        ioa = int.from_bytes(ioa_bytes, 'little')
        print(f"Extracted IOA bytes: {ioa_bytes.hex()} --> IOA: {ioa}")

        # The setpoint value starts 3 bytes after the IOA index
        setpoint_value_index = ioa_index + 4
        if setpoint_value_index + 4 <= len(request):
            # Extract setpoint value (4 bytes, IEEE 754 format)
            setpoint_value_bytes = request[setpoint_value_index:setpoint_value_index + 4]
            print("Extracted setpoint value bytes: " + setpoint_value_bytes.hex())

            # Use struct.unpack with the correct format specifier for big-endian 32-bit float
            setpoint_value = struct.unpack('>f', setpoint_value_bytes)[0]
            print(f"Handling setpoint command --- IOA: {ioa}, Value: {setpoint_value}")
            self.ioa_register[ioa] = setpoint_value

            # Construct and send response ASDU
            response_asdu = self.construct_asdu(SET_POINT_CMD, ACT_CONF_COT, CASDU, ioa, setpoint_value)
            self.send_asdu_response(conn, response_asdu)
        else:
            print("Index out of range for setpoint value extraction")
            response_asdu = self.construct_asdu(SET_POINT_CMD, IOA_ERROR_COT, CASDU, ioa, None)
            self.send_asdu_response(conn, response_asdu)


    def send_asdu_response(self, conn, asdu):
            """
            Send an ASDU response to the client.
            """
            send_sequence_number = (self.send_sequence_number << 1).to_bytes(2, byteorder='big')
            receive_sequence_number = (self.receive_sequence_number << 1).to_bytes(2, byteorder='big')
            apci = b'\x68\x0E' + send_sequence_number + receive_sequence_number
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

        # Common Address of ASDU (assuming 2 bytes)
        asdu += casdu.to_bytes(2, byteorder='little')

        # Information Object Address (assuming 3 bytes)
        asdu += ioa.to_bytes(3, byteorder='little')

        # Information Elements based on Type ID
        if type_id == 1:  # Single-point information
            # Assuming 'value' is a boolean for ON/OFF status
            status_value = 0x01 if value else 0x00
            asdu.append(status_value)

        elif type_id == FLOAT_INFO:
            # Convert the float value to IEEE 754 format (4 bytes)
            floating_value = struct.pack('>f', value)
            asdu += floating_value

        if type_id == SINGLE_CMD:
            # Include the command value
            command_value = 0x01 if value else 0x00
            asdu.append(command_value)

        elif type_id == SET_POINT_CMD:
            # Convert the float value to IEEE 754 format (4 bytes)
            floating_value = struct.pack('>f', value)
            asdu += floating_value

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
