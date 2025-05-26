# IEC-104 Interactive Shell Client

A command‐line interactive client for IEC-104. Only some operations are supported for now.

## Features

- **Dynamic point registration**: register single or ranges of IOAs at any time  
- **Single-point reads** and **writes** (`M_SP_NA_1`, `C_SC_NA_1`)  
- **Floating-point reads** (`M_ME_NC_1`) via single-command reads  
- **Batch interrogation** of ranges (`interrogate <start> <end> <TypeName>`)

## Usage

``python iec104_client.py [--host HOST] [--port PORT] [--ca CASDU] [-d]``

* `--host`: the host IP address (default is `127.0.0.1`)
* `--port`: the port number (default is `2404`)
* `--ca`: CASDU common address (default is `1`)
* `-d`, `--debug`: enable printing of debug messages (default is `off`)

## Examples

Start client and connect (with 5 s timeout)

``python iec104_client.py --host 192.168.1.50 --port 2404 --ca 10 -d``

Register IOAs 10010–10013 as float measurement points

``iec104> register 10010 10013 M_ME_NC_1``

Read a single float point

``iec104> read 10010 M_ME_NC_1``

Write a single-point command

``iec104> write 15105 C_SC_NA_1 1``

Interrogate a range of digital points

``iec104> interrogate 1100 1106 M_SP_NA_1``

## Supported operations

| Short       | Enum                       | Usage                |
| ----------- | -------------------------- | -------------------- |
| `M_SP_NA_1` | Single-point measurement   | digital status read  |
| `M_ME_NC_1` | Floating-point measurement | analog read (float)  |
| `C_SC_NA_1` | Single-point command       | digital on/off write |
| `C_SE_NC_1` | Set-point command          | analog float write   |
