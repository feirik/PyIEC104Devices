This is a Python implementation of a simplified IEC 104 outstation device (server) simulating a hydropower plant.

# IEC 104 IOAs in use
The following Information Object Addresses (IOAs) from IEC104 are used in the server:

- Water Inlet Valve (IOA 100): Controls the water inlet valve to the turbine. BOOL
- Excite Switch (IOA 101): Manages the switch to excite the generator voltage. BOOL
- Transformer Switch (IOA 102): Switches between the generator and the transformer. BOOL
- Grid Switch (IOA 103): Controls the connection between the transformer and the power grid. BOOL
- Cooling Switch (IOA 104): Activates the cooling fluid system for bearings when temperature exceeds a set limit. BOOL
- Start Process (IOA 105): Initiates the plant startup sequence. BOOL
- Shutdown Process (IOA 106): Initiates the plant shutdown sequence. BOOL

- Turbine Speed (IOA 110): Represents the RPM of the turbine. Float
- Generator Voltage (IOA 111): Voltage output produced by the generator. Float
- Grid Power (IOA 112): Estimated power (kW) produced; demand will fluctuate. Float
- Bearing Temperature (IOA 113): Temperature of the turbine bearings. Float
- Float Test (IOA 120): Used for testing float value write and read operations. Float

# Command Line Arguments

The following command line arguments are available when running the IEC 104 server script:

* `--host`: the host IP address (default is `127.0.0.1`)
* `-p`, `--port`: the port number (default is `2404`)
* `-d`, `--debug`: enable printing of debug messages (default is `off`)

# Starting the Simulator

To start the simulator, run the program with the desired command line arguments. For example, to start the simulator on a specific IP address and port with debugging information enabled, run the following command:

``python3 -  --host 192.168.1.100 --port 2404 -d``

The program will print out the IP address, port, and debug information settings to the console. The simulator will then listen for incoming IEC 104 requests, if they are supported by the server, on the specified IP address and port.