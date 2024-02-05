#!/usr/bin/env python3

from .py104get import IEC104Client

class IEC104ClientAPI:
    def __init__(self, ip_address, port=2404, timeout=5):
        """
        Initialize the IEC104Client and establish a connection to the server.
        """
        self.client = IEC104Client(ip_address, port, timeout, False)
        self.client.connect()


    def write_single_command(self, ioa, value):
        """
        Send a single command to the server.

        :param ioa: Information Object Address.
        :param value: The value to be sent (True or False).
        :return: 1 on success, 0 on failure.
        """
        success = self.client.api_single_command(ioa, value)
        return 1 if success else 0


    def write_setpoint_command(self, ioa, value):
        """
        Send a setpoint command to the server.

        :param ioa: Information Object Address.
        :param value: The setpoint value to be sent.
        :return: 1 on success, 0 on failure.
        """
        success = self.client.api_setpoint_command(ioa, value)
        return 1 if success else 0

    def request_data(self):
        """
        Request data for all IOA defined in use for the server.

        :return: A dictionary with IOA numbers as keys and current values as values if successful, None otherwise.
        """
        success, data = self.client.api_request_data()
        if success:
            # Optionally, process the data dictionary as needed or return it directly
            return data
        else:
            print("Failed to retrieve or process data.")
            return None


    def close(self):
        """
        Close the connection to the server.
        """
        self.client.close()


# Unit tests of API
if __name__ == "__main__":
    ip_address = "127.0.0.1"
    port = 2404
    timeout = 5

    # Initialize flags for each test
    write_single_success = False
    write_set_point_success = False
    write_set_point_success_overwrite = False
    read_success = True  # Assume reading success until proven otherwise

    # Initialize the IEC104 client API with the provided parameters
    client = IEC104ClientAPI(ip_address, port, timeout)

    # Write a single command to IOA 105 with value 1 (ON)
    if client.write_single_command(105, 1):
        write_single_success = True
        print("Single command to IOA 105 successful.")
    else:
        print("Single command to IOA 105 failed.")
        read_success = False

    # Write a setpoint command to IOA 120 with the floating-point value 123.45
    if client.write_setpoint_command(120, 123.45):
        write_set_point_success = True
        print("Setpoint command to IOA 120 (123.45) successful.")
    else:
        print("Setpoint command to IOA 120 (123.45) failed.")
        read_success = False

    # Request data from all information objects from the server
    data = client.request_data()

    if data is None:
        read_success = False
        print("Failed to read data after first set of commands.")

    # Write a setpoint command to IOA 120 with the integer value 12345 (for testing overwrite)
    if client.write_setpoint_command(120, 12345):
        write_set_point_success_overwrite = True
        print("Overwrite setpoint command to IOA 120 (12345) successful.")
    else:
        print("Overwrite setpoint command to IOA 120 (12345) failed.")
        read_success = False

    # Request data again from all information objects from the server
    data = client.request_data()

    if data:
        if 105 in data and data[105] == 1 and 120 in data and data[120] == 12345:
            print("Success: Read matches written values.")
        else:
            print("Error: Final data check failed.")
            read_success = False
    else:
        print("Error: No data received from the server after second set of commands.")
        read_success = False

    # Close the client connection
    client.close()

    # Check if all tests passed
    if write_single_success and write_set_point_success and write_set_point_success_overwrite and read_success:
        print("All tests passed successfully.")
    else:
        print("Some tests failed.")
