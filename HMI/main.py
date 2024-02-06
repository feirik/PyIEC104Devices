#!/usr/bin/env python3

import argparse  
import tkinter as tk
import re
from hmi_view import HMIView
from hmi_controller import HMIController

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_TITLE = "HMI - IEC104 Hydropower Plant"

DEFAULT_HOST_IP = '127.0.0.1'
DEFAULT_PORT = 2404
DEFAULT_TIMEOUT = 5

MAX_TIMEOUT = 120
MAX_UINT8 = 255
MAX_UINT16 = 65535
HEX_BASE = 16

def check_ipv4_or_hostname(value):
    ipv4_pattern = re.compile(r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
    hostname_pattern = re.compile(r'^[a-z][a-z0-9\.\-]+$')

    if ipv4_pattern.match(value) or hostname_pattern.match(value):
        return value

    raise argparse.ArgumentTypeError("Invalid IPv4 address or hostname")


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


def main():
    # Argument parsing
    parser = argparse.ArgumentParser(description="HMI - IEC104 Hydropower Plant")
    
    parser.add_argument('--host', type=check_ipv4_or_hostname, 
                        default=DEFAULT_HOST_IP, help=f'Host IP address or hostname (default: {DEFAULT_HOST_IP})')
    parser.add_argument('-p', '--port', metavar='port_number', type=check_port_number, 
                        default=DEFAULT_PORT, help=f'set TCP port (default: {DEFAULT_PORT})')
    parser.add_argument('-t', '--timeout', metavar='timeout', type=check_timeout, 
                        default=DEFAULT_TIMEOUT, help=f'set timeout in seconds (default: {DEFAULT_TIMEOUT}s)')
    parser.add_argument('--os', default='', help='Specify the operating system (e.g., "PIOS" for Raspberry Pi OS)')

    args = parser.parse_args()

    # Instantiate a Tkinter root window
    root = tk.Tk()

    # Set window title
    root.title(WINDOW_TITLE)

    # Set window size
    root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")

    # Instantiate view and controller
    view = HMIView(master=root)
    
    # Pass the parsed arguments to HMIController
    controller = HMIController(view=view, host=args.host, port=args.port, timeout=args.timeout, os=args.os)

    # Start the GUI event loop
    root.mainloop()

# Entry point for the application
if __name__ == "__main__":
    main()