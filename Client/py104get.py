import socket
import struct
import argparse
import sys
import re
import time

IEC104_PORT = 2404

MAX_UINT16 = 65535
DEFAULT_TIMEOUT = 5
MAX_TIMEOUT = 120
HEX_BASE = 16

DELAY_TIME=0.05

STARTDT_ACT_FRAME = b'\x68\x04\x07\x00\x00\x00'
STARTDT_CON_FRAME = b'\x68\x04\x0b\x00\x00\x00'
STOPDT_ACT_FRAME = b'\x68\x04\x13\x00\x00\x00'
STOPDT_CON_FRAME = b'\x68\x04\x23\x00\x00\x00'

SINGLE_INFO = 1 # M_SP_NA_1
FLOAT_INFO = 13 # M_ME_NC_1
SINGLE_CMD = 45 # C_SC_NA_1
SET_POINT_CMD = 50 # C_SE_NC_1
INTERROGATION_CMD = 100 # C_IC_NA_1

ACT_COT = 6 # Activation
ACT_CONF_COT = 7 # Activation confirmation
IOA_ERROR_COT = 47 # Unknown IOA
CASDU = 1 # Using CASDU address 1

COT_OFFSET = 10

# Cause of Transmission (COT) values
COT_TABLE = {
    1: "Periodic, cyclic",
    2: "Background scan",
    3: "Spontaneous",
    4: "Initialized",
    5: "Request",
    6: "Activation",
    7: "Activation confirmation",
    8: "Deactivation",
    9: "Deactivation confirmation",
    10: "Activation termination",
    20: "File transfer",
    44: "Unknown type identification",
    45: "Unknown cause of transmission",
    46: "Unknown common address of ASDU",
    47: "Unknown information object address"
}


class IEC104Client:
    def __init__(self, server, port=IEC104_PORT, timeout=DEFAULT_TIMEOUT, print_debug=False):
        self.server = server
        self.port = port
        self.timeout = timeout
        self.sock = None
        self.print_debug = print_debug


    def start_data_transfer(self):
        """
        Send the STARTDT ACT command to start data transfer and wait for confirmation.
        """
        success = False  # Default success status

        try:
            # Send STARTDT ACT frame
            self.sock.send(STARTDT_ACT_FRAME)
            if self.print_debug:
                print(f"Sent STARTDT ACT: {STARTDT_ACT_FRAME.hex()}")

            # Short delay to ensure the message is sent properly
            time.sleep(DELAY_TIME)

            # Receive and check for STARTDT CON response
            response = self.sock.recv(1024)
            if response == STARTDT_CON_FRAME:
                if self.print_debug:
                    print("Received STARTDT CON, proceeding")
                success = True
            else:
                if self.print_debug:
                    print(f"Unexpected response: {response.hex()}")

        except socket.error as e:
            print(f"Error sending STARTDT ACT: {e}")

        return success


    def connect(self):
        """
        Connect to the IEC 104 server.
        """
        try:
            # Create a socket object
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Set timeout for the socket
            self.sock.settimeout(self.timeout)

            # Connect to the server
            self.sock.connect((self.server, self.port))
            if self.print_debug:
                print(f"Connected to {self.server} on port {self.port}")

            if self.sock:
                self.start_data_transfer()  # Start data transfer after connecting

        except socket.error as e:
            print(f"Failed to connect to {self.server}:{self.port}, error: {e}")
            self.sock = None


    def send_stopdt_act(self):
        """
        Send a STOPDT ACT (Stop Data Transfer Activation) frame to the server
        and wait for the STOPDT CON (Stop Data Transfer Confirmation) frame.
        """
        success = False

        if self.sock:
            try:
                self.sock.send(STOPDT_ACT_FRAME)
                if self.print_debug:
                    print(f"Sent STOPDT ACT: {STOPDT_ACT_FRAME.hex()}")

                # Wait for the STOPDT CON response
                response = self.sock.recv(1024)
                if response == STOPDT_CON_FRAME:
                    if self.print_debug:
                        print("Received STOPDT CON, stopping data transfer")
                    success = True
                else:
                    if self.print_debug:
                        print(f"Unexpected response: {response.hex()}")

            except socket.error as e:
                print(f"Error sending STOPDT ACT: {e}")

        return success


    def close(self):
        """
        Close the connection.
        """
        self.send_stopdt_act()  # Send STOPDT ACT before closing
        
        if self.sock:
            self.sock.close()
            self.sock = None
            if self.print_debug:
                print(f"Disconnected from {self.server}")


    def send(self, type_id, cot, casdu, ioa, value):
        """
        Send an ASDU with APCI to the IEC 104 server.

        :param type_id: Type ID of the ASDU.
        :param cot: Cause of Transmission.
        :param casdu: Common Address of ASDU.
        :param ioa: Information Object Address.
        :param value: The value to be sent.
        """
        if self.sock:
            try:
                # Construct the APCI header
                if type_id == SINGLE_CMD:
                    start_bytes = b'\x68\x0E'
                elif type_id == SET_POINT_CMD:
                    start_bytes = b'\x68\x12'
                else:
                    start_bytes = b'\x68\x0E'
                # Assuming control fields for I-format frame, assumed client sends first message in TCP
                send_sequence_number = b'\x00\x00'
                receive_sequence_number = b'\x00\x00'
                apci = start_bytes + send_sequence_number + receive_sequence_number  # Length is 14 bytes including APCI and ASDU

                # Construct the ASDU
                asdu = self.construct_asdu(type_id, cot, casdu, ioa, value)

                # Combine APCI and ASDU
                frame = apci + asdu

                # Send the frame
                self.sock.send(frame)
                if self.print_debug:
                    print(f"Sent Frame: {frame.hex()}")
            except socket.error as e:
                print(f"Error sending frame: {e}")


    def send_interrogation_command(self):
        """
        Dynamically construct and send an Interrogation Command to the IEC 104 server.
        """
        try:
            # Assume client sends first message
            send_sequence_number = 0x00
            receive_sequence_number = 0x00
            
            asdu = self.construct_asdu(INTERROGATION_CMD, ACT_COT, CASDU, 0)
            
            apci = b'\x68\x0e' + \
                (send_sequence_number << 1).to_bytes(2, byteorder='big') + \
                (receive_sequence_number << 1).to_bytes(2, byteorder='big')
            
            frame = apci + asdu
            self.sock.send(frame)
            if self.print_debug:
                print(f"Sent Interrogation Command Frame: {frame.hex()}")
        except socket.error as e:
            print(f"Error sending Interrogation Command: {e}")


    def receive(self):
        """
        Receive and parse ASDUs from the IEC 104 server.
        Returns the received packet if successful, None otherwise.
        """
        if self.sock:
            try:
                response = self.sock.recv(1024)
                if response:
                    if self.print_debug:
                        print(f"Received: {response.hex()}")
                    return response
                else:
                    if self.print_debug:
                        print("Received an empty response.")
            except socket.timeout:
                print("No response received within the timeout period.")
        return None

                
    def receive_multiple(self, timeout=2):
        """
        Receive messages from the IEC 104 server within a given timeout.

        :param timeout: Timeout in seconds to wait for additional messages.
        """
        messages = []
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                self.sock.settimeout(timeout - (time.time() - start_time))
                response = self.sock.recv(1024)

                if response:
                    if self.print_debug:
                        print(f"Received: {response.hex()}")
                    messages.append(response)
                else:
                    break

            except socket.timeout:
                break

        return messages


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

        asdu.append(type_id)
        asdu.append(0x01)
        asdu.append(cot)
        asdu.append(0x00) # Part of CASDU

        asdu += casdu.to_bytes(2, 'little')
        asdu += ioa.to_bytes(3, 'little') 

        if type_id == SINGLE_CMD:
            command_value = 0x01 if value else 0x00
            asdu.append(command_value)

        elif type_id == SET_POINT_CMD:
            floating_value = struct.pack('<f', value)
            asdu += floating_value
            asdu += b'\x80'

        elif type_id == INTERROGATION_CMD:
            asdu += b'\x14'  # Station/global interrogation

        return asdu

    
    def decode_iec104_response(self, response):
        success = True
        ioa_value = None
        return_value = None

        if len(response) < 13:
            print("ERROR - Response from server too short to decode")
            success = False
        else:
            # APCI part (6 bytes)
            apci_length = 6

            # Extracting the ASDU header
            asdu_header = response[apci_length:apci_length+6]
            type_id, vsq, cot = struct.unpack('>BBB', asdu_header[:3])

            # Lookup the string representation of COT
            cot_desc = COT_TABLE.get(cot, f"Unknown COT ({cot})")

            # Process the Information Object Address (IOA) - 3 bytes
            ioa_start = apci_length + 6
            if len(response) >= ioa_start + 3:
                ioa = response[ioa_start:ioa_start+3]
                ioa_value = int.from_bytes(ioa, 'little')

                # Define maximum width for printing alignment
                max_width = 10

                value_start = ioa_start + 3
                if type_id == SINGLE_INFO and len(response) >= value_start + 1:
                    status = response[value_start]
                    return_value = status
                    status_str = f"{status}".rjust(max_width)
                    if self.print_debug:
                        print(f"(IOA {ioa_value:3}): {status_str:<{max_width}}   ---   Type: Single point  ---   COT: {cot_desc}")
                    else:
                        print(f"(IOA {ioa_value:3}): {status_str:<{max_width}}")
                elif type_id == FLOAT_INFO and len(response) >= value_start + 4:
                    floating_value_bytes = response[value_start:value_start+4]
                    measured_value = struct.unpack('<f', floating_value_bytes)[0]
                    return_value = measured_value
                    measured_value_formatted = f"{measured_value:>{max_width}.2f}"
                    if self.print_debug:
                        print(f"(IOA {ioa_value:3}): {measured_value_formatted}   ---   Type: Measured Value (Short Float)   ---   COT: {cot_desc}")
                    else:
                        print(f"(IOA {ioa_value:3}): {measured_value_formatted}")
                else:
                    print("Not enough data for value")
                    success = False
            else:
                print("Not enough data for IOA")
                success = False

        return success, ioa_value, return_value

    
    def process_cot(self, command, response):
        """
        Process the Cause of Transmission (COT) from the received response using COT_TABLE.
        """
        success = False
        # Assuming COT is in a specific position in the response
        if response and len(response) >= COT_OFFSET:
            cot = response[8]
            cot_desc = COT_TABLE.get(cot, f"Unknown COT ({cot})")

            if cot == ACT_CONF_COT:
                if command == SET_POINT_CMD:
                    print("Set point command (float) successfully processed by server.")
                    success = True
                elif command == SINGLE_CMD:
                    print("Single command (bool) successfully processed by server.")
                    success = True
                else:
                    print(f"Server successfully processed (COT: 7 - {cot_desc}).")
                    success = True
            elif cot == IOA_ERROR_COT:
                print(f"Command failed (COT: 47 - {cot_desc}).")
            else:
                print(f"ERROR - Received unexpected COT: {cot}, {cot_desc}.")
        else:
            print("Invalid or too short response to process COT.")

        return success


    def api_single_command(self, ioa, value):
        """
        Send a single command to the IEC 104 server and check for successful processing.

        :param ioa: Information Object Address of the command.
        :param value: The boolean value to be sent (True or False).
        :return: True if the command was successfully processed, False otherwise.
        """
        success = False
        self.send(SINGLE_CMD, ACT_COT, CASDU, ioa, value)
        response = self.receive()

        if not response:
            print("No valid response received.")

        success = self.process_cot(SINGLE_CMD, response)

        return success


    def api_setpoint_command(self, ioa, value):
        """
        Send a setpoint command to the IEC 104 server and check for successful processing.

        :param ioa: Information Object Address of the command.
        :param value: The floating-point setpoint value to be sent.
        :return: True if the command was successfully processed, False otherwise.
        """
        success = False
        try:
            value = float(value)
        except ValueError:
            print(f"Invalid setpoint value: {value}. Must be a floating-point number.")
            return False

        self.send(SET_POINT_CMD, ACT_COT, CASDU, ioa, value)
        response = self.receive()
        if not response:
            print("No valid response received.")

        success = self.process_cot(SET_POINT_CMD, response)

        return success


    def api_request_data(self):
        """
        Request data for all information objects from the server and process the responses.

        :return: A tuple containing a boolean indicating overall success, and a dictionary with IOA numbers as keys
                 and their corresponding values if successful, None otherwise.
        """
        overall_success = True
        data = {}

        self.send_interrogation_command()
        responses = self.receive_multiple()

        if not responses:
            print("No responses received.")
            return False, None

        for response in responses:
            success, ioa, value = self.decode_iec104_response(response)
            if success:
                data[ioa] = value
            else:
                overall_success = False

        return overall_success, data


def check_port_number(value):
    decimal_pattern = re.compile(r'^\d{1,5}$')
    hex_pattern = re.compile(r'^0x[a-fA-F0-9]{1,4}$')

    if decimal_pattern.match(value):
        int_value = int(value)
        if 1 <= int_value <= MAX_UINT16:
            return int_value
    elif hex_pattern.match(value):
        int_value = int(value, HEX_BASE)
        if 1 <= int_value <= MAX_UINT16:
            return int_value

    raise argparse.ArgumentTypeError("port_number must be between 1 and 65535, either in decimal or hexadecimal format")


def check_timeout(value):
    pattern = re.compile(r'^\d{1,3}$')

    if pattern.match(value):
        int_value = int(value)
        if 0 < int_value < MAX_TIMEOUT:
            return int_value

    raise argparse.ArgumentTypeError("timeout must be a positive integer less than 120 seconds")


def check_ipv4_or_hostname(value):
    ipv4_pattern = re.compile(r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
    hostname_pattern = re.compile(r'^[a-z][a-z0-9\.\-]+$')

    if ipv4_pattern.match(value) or hostname_pattern.match(value):
        return value

    raise argparse.ArgumentTypeError("Invalid IPv4 address or hostname")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Client IEC 60870-5-104 command line', add_help=False)
    parser.add_argument('ip_address', type=check_ipv4_or_hostname, help='IP address or hostname of the IEC 104 server', nargs='?', default='localhost')
    parser.add_argument('-h', '--help', action='store_true', help='show this help message')
    parser.add_argument('-v', '--version', action='store_true', help='show version')
    parser.add_argument('-d', '--dump', action='store_true', help='set dump mode (show tx/rx frame in hex)')
    parser.add_argument('-p', '--port', metavar='port_number', type=check_port_number, help='set TCP port (default 2404)', default=IEC104_PORT)
    parser.add_argument('-t', '--timeout', metavar='timeout', type=check_timeout, help='set timeout seconds (default is 5s)', default=5)

    # IEC 104 specific commands
    parser.add_argument('-w45','--single-command', metavar='ioa_value', help='Format: IOA,value - send single bool command (C_SC_NA_1)')
    parser.add_argument('-w50','--setpoint-command', metavar='ioa_value', help='Format: IOA,value - send setpoint command (C_SE_NA_1)')
    parser.add_argument('-r100', '--request-data', action='store_true', help='request data for all information objects (General Interrogation)')

    args = parser.parse_args()

    if args.help:
        parser.print_help()
        sys.exit()

    if args.version:
        print(VERSION)
        sys.exit()

    # Set options based on arguments
    opt_server = args.ip_address
    opt_port = args.port
    opt_timeout = args.timeout
    opt_dump = args.dump

    # IEC 104 client initialization
    client = IEC104Client(opt_server, port=opt_port, timeout=opt_timeout, print_debug=opt_dump)
    client.connect()

    try:
        if args.single_command:
            ioa, value = map(int, args.single_command.split(','))
            client.send(SINGLE_CMD, ACT_COT, CASDU, ioa, value)
            response = client.receive()
            if response:
                # Process the COT from the response to check if command was accepted
                client.process_cot(SINGLE_CMD, response)
            else:
                print("No valid response received.")

        if args.setpoint_command:
            ioa, value = args.setpoint_command.split(',')
            ioa = int(ioa)
            value = float(value)
            client.send(SET_POINT_CMD, ACT_COT, CASDU, ioa, value)
            response = client.receive()
            if response:
                client.process_cot(SET_POINT_CMD, response)
            else:
                print("No valid response received.")

        if args.request_data:
            client.send_interrogation_command()
            # Receive multiple responses within a timeout
            responses = client.receive_multiple()
            for response in responses:
                client.decode_iec104_response(response)

    except Exception as e:
        print("Error:", str(e))

    client.close()