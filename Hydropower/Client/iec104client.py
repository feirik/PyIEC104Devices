#!/usr/bin/env python3
import cmd
import argparse
import time
import c104

CONNECTION_TIMEOUT = 5

class IEC104Shell(cmd.Cmd):
    intro = "IEC-104 interactive shell.  Type help or ? to list commands.\n"
    prompt = "iec104> "

    def __init__(self, host, port, ca=1, debug=False):
        super().__init__()

        self.host = host
        self.port = port
        self.casdu = ca
        self.debug = debug

        # Set up initial client and connection
        self.client = c104.Client()
        self.conn   = self.client.add_connection(ip=host, port=port, init=c104.Init.NONE)
        self.conn.on_unexpected_message(self._on_unexpected)
        self.station = self.conn.add_station(common_address=ca)

        # map IOA to c104 point object
        self.points = {}
        # map IOA to c104 point for re-registration
        self.point_definitions = {}

        # Flag to check whether we need to rebuild connection
        self.points_added_to_connection = False

        self.client.start()

        start_time = time.time()

        while self.conn.state != c104.ConnectionState.OPEN:
            if time.time() - start_time > CONNECTION_TIMEOUT:
                print(f"Failed to connect to {self.host}:{self.port}")
                exit(1)
            time.sleep(0.05)
        debug_state = "on" if self.debug else "off"
        print(f"Connected to {host}:{port}, CASDU={ca}, debug={debug_state}")


    # handle unexpected incoming messages such as type ID mismatches
    def _on_unexpected(
        self,
        connection: c104.Connection,
        message:    c104.IncomingMessage,
        cause:      c104.Umc
    ) -> None:
        print(f"Unexpected message from server: {cause}")
    

    def do_interrogate(self, line):
        """interrogate <start> <end> <TypeName>
        usage: interrogate 1100 1106 M_SP_NA_1"""
        parts = line.split()
        proceed = True

        # Validate arguments
        if len(parts) != 3:
            print("usage: interrogate <start> <end> <TypeName>")
            proceed = False
        else:
            ioa_start, ioa_end, type_name = parts

        # Parse IOA start and end
        if proceed:
            try:
                start, end = int(ioa_start), int(ioa_end)
            except ValueError:
                print("Start and end must be integers")
                proceed = False

        # Get c104 type name
        if proceed:
            try:
                ptype = getattr(c104.Type, type_name)
            except AttributeError:
                print(f"Unknown type: {type_name}")
                proceed = False

        # Check if there are new IOA points that need to be added
        if proceed:
            new_ioas = []
            for ioa in range(start, end + 1):
                if ioa not in self.points:
                    new_ioas.append(ioa)

        rebuilt = False

        # Rebuild link if needed to register new points
        if proceed and new_ioas and self.points_added_to_connection:
            if self.debug:
                print("[DEBUG] rebuilding connection to register new IOAs…")
            self.client.stop()
            self.client = c104.Client()
            self.conn   = self.client.add_connection(
                ip=self.host, port=self.port, init=c104.Init.NONE
            )
            self.conn.on_unexpected_message(self._on_unexpected)
            self.station = self.conn.add_station(common_address=self.casdu)

            # Add new IOAs to definition
            for ioa in new_ioas:
                self.point_definitions[ioa] = ptype
            
            # Add all points from the definition
            for existing_ioa, existing_type in self.point_definitions.items():
                pt = self.station.add_point(io_address=existing_ioa, type=existing_type)
                if pt is None:
                    print(f"[ERROR] could not add point {existing_ioa} of type {existing_type}")
                else:
                    self.points[existing_ioa] = pt

            self.client.start()
            while self.conn.state != c104.ConnectionState.OPEN:
                time.sleep(0.01)

            if self.debug:
                print("[DEBUG] connection rebuilt and all points registered")

            rebuilt = True

        # Add new IOAs if we did not have to rebuild the connection
        if proceed and not rebuilt and new_ioas:
            for ioa in new_ioas:
                pt = self.station.add_point(io_address=ioa, type=ptype)
                if pt is None:
                    print(f"[ERROR] could not add point {ioa} of type {ptype}")
                else:
                    self.points[ioa]     = pt
                    self.point_definitions[ioa] = ptype
                    if self.debug:
                        print(f"[DEBUG] registered IOA {ioa} as {type_name}")
                    self.points_added_to_connection = True

        # Do interrogation
        if proceed:
            ok = self.conn.interrogation(
                common_address=self.station.common_address,
                cause=c104.Cot.ACTIVATION,
                qualifier=c104.Qoi.STATION,
                wait_for_response=True
            )
            if not ok:
                print("Interrogation failed")
                proceed = False

        # Print results from interrogation
        if proceed:
            for ioa in range(start, end + 1):
                pt = self.points.get(ioa)
                if pt is None:
                    print(f"[IOA {ioa}]: <not registered>")
                else:
                    print(f"[IOA {ioa}]: {pt.value}")


    def do_read(self, line):
        """read <ioa> <TypeName>
        usage: read 10010 M_ME_NC_1"""
        parts = line.split()
        proceed = True
        rebuilt = False

        # Validate arguments
        if len(parts) != 2:
            print("usage: read <ioa> <TypeName>")
            proceed = False
        else:
            ioa_input, type_name = parts
            try:
                ioa = int(ioa_input)
            except ValueError:
                print("IOA must be an integer")
                proceed = False

            if proceed:
                try:
                    ptype = getattr(c104.Type, type_name)
                except AttributeError:
                    print(f"Unknown type: {type_name}")
                    proceed = False

        # If needed - Rebuild link to register new point
        if proceed:
            if ioa not in self.points and self.points_added_to_connection:
                if self.debug:
                    print("[DEBUG] rebuilding connection to register new IOA…")

                self.client.stop()
                self.client = c104.Client()
                self.conn = self.client.add_connection(
                    ip=self.host, port=self.port, init=c104.Init.NONE
                )
                self.conn.on_unexpected_message(self._on_unexpected)
                self.station = self.conn.add_station(common_address=self.casdu)

                # Add new IOA to definition
                self.point_definitions[ioa] = ptype

                # Add previous known points and the new point to rebuilt connection
                for existing_ioa, existing_type in self.point_definitions.items():
                    pt = self.station.add_point(io_address=existing_ioa, type=existing_type)
                    if pt is None:
                        print(f"[ERROR] could not add point {existing_ioa} of type {existing_type}")
                    else:
                        self.points[existing_ioa] = pt

                self.client.start()
                while self.conn.state != c104.ConnectionState.OPEN:
                    time.sleep(0.01)

                if self.debug:
                    print("[DEBUG] connection rebuilt and all points registered")

                self.points_added_to_connection = True
                rebuilt = True

            # If points are not already added, just add the point to be read
            if not rebuilt and ioa not in self.points:
                pt = self.station.add_point(io_address=ioa, type=ptype)
                if pt is None:
                    print(f"[ERROR] could not add point {ioa} of type {ptype}")
                    proceed = False
                else:
                    self.points[ioa] = pt
                    self.point_definitions[ioa] = ptype
                    self.points_added_to_connection = True

        # Read the point
        if proceed:
            pt = self.points.get(ioa)
            ok = pt.read()
            if not ok:
                print("Read failed")
                proceed = False

        # Print result from read
        if proceed:
            print(f"[IOA {ioa}]: {pt.value}")


    def do_write(self, line):
        """write <ioa> <TypeName> <value>
        usage: write 15100 C_SC_NA_1 1"""
        parts = line.split()
        proceed = True
        rebuilt = False

        # Validate arguments
        if len(parts) != 3:
            print("usage: write <ioa> <TypeName> <value>")
            proceed = False
        else:
            ioa_input, type_name, input_value = parts

            # Parse IOA
            try:
                ioa = int(ioa_input)
            except ValueError:
                print("IOA must be an integer")
                proceed = False

            # Map TypeName to enum
            if proceed:
                try:
                    ptype = getattr(c104.Type, type_name)
                except AttributeError:
                    print(f"Unknown type: {type_name}")
                    proceed = False

            # Parse bool or float value for point type
            if proceed:
                if ptype is c104.Type.C_SC_NA_1:
                    if input_value not in ("0", "1"):
                        print("Value for C_SC_NA_1 must be 0 or 1")
                        proceed = False
                    else:
                        value = bool(int(input_value))
                elif ptype is c104.Type.C_SE_NC_1:
                    try:
                        value = float(input_value)
                    except ValueError:
                        print("Value for C_SE_NC_1 must be a float")
                        proceed = False
                else:
                    print(f"Writing to point type {type_name} not supported")
                    proceed = False

        # If needed - Rebuild link to register new point
        if proceed:
            if ioa not in self.points and self.points_added_to_connection:
                if self.debug:
                    print("[DEBUG] rebuilding connection to register new IOA…")

                self.client.stop()
                self.client = c104.Client()
                self.conn = self.client.add_connection(
                    ip=self.host, port=self.port, init=c104.Init.NONE
                )
                self.conn.on_unexpected_message(self._on_unexpected)
                self.station = self.conn.add_station(common_address=self.casdu)

                # Add new IOA to definition
                self.point_definitions[ioa] = ptype

                # Add previous known points and the new point to rebuilt connection
                for existing_ioa, existing_type in self.point_definitions.items():
                    self.station.add_point(io_address=existing_ioa, type=existing_type)

                self.client.start()
                while self.conn.state != c104.ConnectionState.OPEN:
                    time.sleep(0.01)
                
                if self.debug:
                    print("[DEBUG] connection rebuilt and all points registered")
                
                self.points_added_to_connection = True
                rebuilt = True

                # Re-populate actual point objects
                for existing_ioa in self.point_definitions:
                    self.points[existing_ioa] = self.station.get_point(existing_ioa)

            # If no points are previously added, just add the one for this write
            if not rebuilt and ioa not in self.points:
                pt = self.station.add_point(io_address=ioa, type=ptype)
                if pt is None:
                    print(f"[ERROR] could not add point {ioa} of type {ptype}")
                    proceed = False
                else:
                    self.points[ioa] = pt
                    self.point_definitions[ioa] = ptype
                    self.points_added_to_connection = True

        # Perform the write
        if proceed:
            pt = self.points.get(ioa)
            pt.value = value
            ok = pt.transmit(cause=c104.Cot.ACTIVATION)
            if ok:
                print(f"[IOA {ioa}] set to: {value}")
            else:
                print("Write failed")


    def do_register(self, line):
        """
        register <start> <end> <TypeName>
        usage:  register 10010 10013 M_ME_NC_1
        """
        parts = line.split()
        proceed = True
        rebuilt = False

        # Validate arguments
        if len(parts) != 3:
            print("usage: register <start> <end> <TypeName>")
            proceed = False
        else:
            ioa_start, ioa_end, type_name = parts
            # Parse IOA start and end
            try:
                start, end = int(ioa_start), int(ioa_end)
            except ValueError:
                print("Error: start/end must be integers")
                proceed = False

            if proceed:
                try:
                    ptype = getattr(c104.Type, type_name)
                except AttributeError:
                    print(f"Unknown type: {type_name}")
                    proceed = False

        # Rebuild link if needed to register new points
        if proceed and self.points_added_to_connection:
            if self.debug:
                print("[DEBUG] rebuilding connection to register new IOAs…")
            self.client.stop()
            self.client = c104.Client()
            self.conn   = self.client.add_connection(
                ip=self.host, port=self.port, init=c104.Init.NONE
            )
            self.conn.on_unexpected_message(self._on_unexpected)
            self.station = self.conn.add_station(common_address=self.casdu)

            # Overwrite with new definitions and add points
            for ioa in range(start, end + 1):
                self.point_definitions[ioa] = ptype
            for ioa, point_type in self.point_definitions.items():
                self.station.add_point(io_address=ioa, type=point_type)
                print(f"Registered IOA {ioa} as {point_type}")

            self.client.start()
            while self.conn.state != c104.ConnectionState.OPEN:
                time.sleep(0.01)
            
            if self.debug:
                print("[DEBUG] connection rebuilt and all points registered")

            # Repopulate points list with new points
            for ioa in self.point_definitions:
                self.points[ioa] = self.station.get_point(ioa)

            rebuilt = True

        # Add new IOAs if we did not have to rebuild the connection
        if proceed and not rebuilt:
            for ioa in range(start, end + 1):
                if ioa in self.points:
                    print(f"[DEBUG] IOA {ioa} already registered, skipping")
                    continue
                pt = self.station.add_point(io_address=ioa, type=ptype)
                if pt is None:
                    print(f"[ERROR] could not add point {ioa} of type {type_name}")
                else:
                    self.points[ioa] = pt
                    self.point_definitions[ioa] = ptype
                    print(f"Registered IOA {ioa} as {type_name}")

        # Set flag that we now have registered points to connection
        if proceed:
            self.points_added_to_connection = True

    
    def do_list(self, arg):
        """list — show supported IEC-104 TypeNames"""
        rows = [
            ("M_SP_NA_1", "Single-point measurement", "digital status read"),
            ("M_ME_NC_1", "Floating-point measurement", "analog read (float)"),
            ("C_SC_NA_1", "Single-point command", "digital on/off write"),
            ("C_SE_NC_1", "Set-point command", "analog float write"),
        ]
        headers = ("TypeName", "Description", "Use")
        # Determine max width for each column
        col_widths = []
        for col_idx in range(len(headers)):
            max_in_col = max(len(str(r[col_idx])) for r in rows + [headers])
            col_widths.append(max_in_col)
        # Build a format string like "{:<12}  {:<25}  {:<20}"
        fmt = "  ".join(f"{{:<{w}}}" for w in col_widths)

        # Print header, separator, then rows
        print(fmt.format(*headers))
        print(fmt.format(*["─" * w for w in col_widths]))
        for name, desc, use in rows:
            print(fmt.format(name, desc, use))


    # Exit the interactive shell
    def do_exit(self, arg):
        "exit  — quit"
        return True
    # EOF shortcut exit
    do_EOF = do_exit

    def postloop(self):
        self.client.stop()
        print("disconnected.")

if __name__ == "__main__":
    p = argparse.ArgumentParser(prog="iec104_shell")
    p.add_argument("--host",  default="127.0.0.1")
    p.add_argument("--port",  default=2404, type=int, help="IEC-104 TCP port (default: 2404)")
    p.add_argument("--ca",    default=1,    type=int, help="CASDU common address (default: 1)")
    p.add_argument("-d", "--debug", action="store_true", help="enable debug output")
    args = p.parse_args()

    IEC104Shell(args.host, args.port, ca=args.ca, debug=args.debug).cmdloop()
