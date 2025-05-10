This is a Python implementation of a simplified IEC 104 outstation device (server) simulating a hydropower plant.

# IEC 104 IOAs in use

## SP (single-point) Measurements (type = M_SP_NA_1)
- **Water Inlet Valve** (IOA 1100): BOOL — Controls the water inlet valve to the turbine  
- **Excite Switch** (IOA 1101): BOOL — Switch to excite generator voltage  
- **Transformer Switch** (IOA 1102): BOOL — Switch between generator and transformer  
- **Grid Switch** (IOA 1103): BOOL — Connects/disconnects transformer to power grid  
- **Cooling Switch** (IOA 1104): BOOL — Enables cooling fluid system for bearings  
- **Start Process** (IOA 1105): BOOL — Initiates plant startup sequence  
- **Shutdown Process** (IOA 1106): BOOL — Initiates plant shutdown sequence  

## SP Commands (type = C_SC_NA_1)
- **Water Inlet Valve Command** (IOA 15100): BOOL — Command to open/close water inlet valve  
- **Excite Switch Command** (IOA 15101): BOOL — Command to toggle generator excite circuit  
- **Transformer Switch Command** (IOA 15102): BOOL — Command to switch generator–transformer coupling  
- **Grid Switch Command** (IOA 15103): BOOL — Command to connect/disconnect grid switch  
- **Cooling Switch Command** (IOA 15104): BOOL — Command to enable/disable bearing cooling  
- **Start Process Command** (IOA 15105): BOOL — Command to start plant sequence  
- **Shutdown Process Command** (IOA 15106): BOOL — Command to shut down plant sequence  

## Analog (float) Measurements (type = M_ME_NC_1)
- **Turbine Speed** (IOA 15010): Float — RPM of turbine  
- **Generator Voltage** (IOA 15011): Float — Voltage output of generator  
- **Grid Power** (IOA 15012): Float — Estimated kW produced by turbine  
- **Bearing Temperature** (IOA 15013): Float — Temperature of turbine bearings  

# Command Line Arguments

The following command line arguments are available when running the IEC 104 server script:

* `--host`: the host IP address (default is `127.0.0.1`)
* `-p`, `--port`: the port number (default is `2404`)
* `-d`, `--debug`: enable printing of debug messages (default is `off`)

# Starting the Simulator

To start the simulator, run the program with the desired command line arguments. For example, to start the simulator on a specific IP address and port with debugging information enabled, run the following command:

``python3 iec104_hydropower.py --host 192.168.1.100 --port 2404 -d``

The program will print out the IP address, port, and debug information settings to the console. The simulator will then listen for incoming IEC 104 requests, if they are supported by the server, on the specified IP address and port.