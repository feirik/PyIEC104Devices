# Simplified IEC 104 Command Line client in Python

This script connects to an IEC104 server and performs simple IEC104 read and write operations. It can be use either by CLI or through API.

## Command Line Arguments

The script supports the following command line arguments:

- `ip_address`: The IP address or hostname of the Modbus server.
- `-h`, `--help`: Display the help message.
- `-d`, `--dump`: Enable dump mode (extra debug printing).
- `-v`, `--version`: Display the script version.
- `-w45`, `--single-command`: Write a bool value as single command
- `-w50`, `--setpoint-command`: Write a float to server as a setpoint command
- `-r100`, `--request-data`: Read all IOA values through general interrogation command.
- `-p`, `--port`: Set TCP port (default 2404).
- `-t`, `--timeout`: Set timeout in seconds (default is 5s).

## Running the Script

You can run the script with your desired command line arguments.

Read all IOAs in use from server:

```shell
python3 py104get.py 192.168.1.100 -p 2404 -r100
```

Write bool '1' to server at IOA 105:

```shell
python3 py104get.py 192.168.1.100 -p 2404 -w45 105,1
```

Write float '123' to server at IOA 120:

```shell
python3 py104get.py 192.168.1.100 -p 2404 -w50 120,123
```

## Testing the API and client

Test the API by running the commands below from the **PyIEC104Devices** folder (The folder above this).

```shell
python3 Server/iec104_hydropower.py&
python3 -m Client.api_py104get.py
```

## API Documentation

The `api_py104get.py` file provides a `IEC104ClientAPI` class that wraps around the `IEC104Client` object. It offers methods for simple IEC104 operations. The client is directly using `py104get.py` and will open and close a TCP session for each read or write operation.

### IEC104ClientAPI Class

Initializes a `IEC104ClientAPI` object and connects to the server.

#### Parameters:
- **ip_address** (str): The IP address of the IEC104 server to connect to.
- **port** (int): The port number the client will use to connect to the IEC104 server.
- **timeout** (int): The maximum amount of time (in seconds) to wait for a response from the server before giving up.

#### Methods:

- **write_single_command(ioa: int, value: bool) -> int**:
Sends a single command (e.g., a switch operation) to the IEC 104 server. The ioa parameter specifies the Information Object Address, and the value parameter specifies the command state (True for ON, False for OFF). Returns 1 on success and 0 on failure.

- **write_setpoint_command(ioa: int, value: float) -> int**:
Sends a setpoint command to the IEC 104 server, adjusting a value such as a threshold or setpoint. The ioa parameter specifies the Information Object Address, and the value parameter specifies the setpoint value as a floating-point number. Returns 1 on success and 0 on failure.

- **request_data() -> dict or None**:
Requests the current state or value of all configured Information Object Addresses (IOAs) from the server. Returns a dictionary mapping each ioa to its current value if successful. Returns None if the request fails or if data processing encounters errors.

- **close()**:
Closes the connection to the IEC 104 server.