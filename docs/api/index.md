# API Overview

## Overview {: #api-overview-toc }

Although this package contains many classes and functions, the classes that you may typically create instances of are

* [Config][] &mdash; if you want to load equipment registers and communicate with equipment
* [Connection][] &mdash; if you are only interested in communicating with equipment
* [Register][] &mdash; if you only want to load an equipment register

and there are [enumeration][enumerations] classes and a [Readings][] class.

[Interfaces][] are available to communicate with equipment, [Backends][] may be used to interface with equipment using external packages and possibly [Resources][] may be available.

!!! tip
    You do not need to create instances of these communication classes. Calling the [Equipment.connect()][msl.equipment.schema.Equipment.connect] or [Connection.connect()][msl.equipment.schema.Connection.connect] method will automatically use the correct object for communication.

    If you are using type annotations and/or an editor that supports code completion, you can annotate the type of the returned object to get support for these features, for example,

    ```python
    from msl.equipment import GPIB, Connection

    device: GPIB = Connection("GPIB::22").connect()
    ```

The [MSLConnectionError][msl.equipment.interfaces.message.MSLConnectionError] and [MSLTimeoutError][msl.equipment.interfaces.message.MSLTimeoutError] classes are raised if there are issues when communicating with equipment.

## Equipment Server

If you would like to allow equipment that has a non-Ethernet interface (e.g., GPIB, RS-232, USB) to be connectable from any computer that is on the network, you can use a client-server protocol using the [ZeroMQ][msl.equipment.interfaces.zeromq.ZeroMQ] and [ZeroMQServer][msl.equipment.interfaces.zeromq.ZeroMQServer] classes. The following examples illustrate the concept. Run `server.py` on the computer that is physically connected to the equipment and `client.py` can be run on any computer on the network.

When using the [REQ][zmq.SocketType.REQ] (client) and [REP][zmq.SocketType.REP] (server) socket types, a client must always read the response after sending a request. This means that a client cannot perform a [write][msl.equipment.interfaces.zeromq.ZeroMQ.write] and/or a [write_multipart][msl.equipment.interfaces.zeromq.ZeroMQ.write_multipart] sequentially.

By default, the server will process requests that are sent by *any* computer on the network (example 1 below). If you want to control which client(s) the server will process requests for, you can take guidance from example 2, 3 or 4.

1. Allow requests from any client (see [Allow any][1-allow-any] below). This example uses the [REQ][zmq.SocketType.REQ] (client) and [REP][zmq.SocketType.REP] (server) socket types so the client must always read a response, even if the action is only to write a message to the equipment.
2. Specify the IP address(es), or hostname(s), of the clients that are allowed to send requests to the server when the server is instantiated (see [Allow specific][2-allow-specific] below). The [handle_request][msl.equipment.interfaces.zeromq.ZeroMQServer.handle_request] method on the server is also implemented in a different way than in example 1.
3. Use a [PAIR][zmq.SocketType.PAIR] socket type when creating an instance of the client and server (see [Use a PAIR][3-use-a-pair] below). When using a [PAIR][zmq.SocketType.PAIR] socket, the client can send multiple *writes* without performing a *read* and the server can return `None` from the [handle_request][msl.equipment.interfaces.zeromq.ZeroMQServer.handle_request] method.
4. Include a unique and privately known (between the client and server) *identity* as the first item in a multipart message that the client sends. The server verifies the *identity* before processing the request (see [Use an identity][4-use-an-identity] below). Note, this is not a form of secure network communication since messages are sent across the network in plain text. This example assumes that you have trustworthy people on your network and you simply do not want someone to accidentally take control of your equipment. The ZeroMQ protocol has a way to encrypt messages, but that is not of interest here.

### 1. Allow any

=== "client.py"
    ```python
    # The server has an IP address of 192.168.1.8 and is running on port 5555
    from msl.equipment import Connection, ZeroMQ

    client: ZeroMQ
    with Connection("ZMQ::192.168.1.8::5555").connect() as client:
        # The client performs a query
        print(client.query("*IDN?"))

        # The client only wants to write a message to the equipment
        # But the client must still read a response for the REQ-REP protocol
        _ = client.query_multipart([b"ignored", b"*RST"])

        # The client only wants to read a message from the equipment
        # The server knows that an empty request is for a read only
        print(client.query(b""))
    ```

=== "server.py"
    ```python
    from __future__ import annotations

    from msl.equipment import Connection, GPIB, ZeroMQServer
    from msl.equipment.typing import ZMQServerResponse

    class DMM(ZeroMQServer):
        """Allow for a digital multimeter to be available on the network."""

        def __init__(self, port: int) -> None:
            super().__init__(port=port)

            # Create the connection to the digital multimeter
            self.dmm: GPIB = Connection("GPIB::18").connect()

        def handle_request(self, msg_parts: list[bytes]) -> ZMQServerResponse:
            """Handle a request and return the response."""
            if len(msg_parts) == 1:
                message = msg_parts[0]
                if not message:
                    return self.dmm.read(decode=False)
                return self.dmm.query(message, decode=False)

            # Otherwise, only write a message (the message is the second item)
            _ = self.dmm.write(msg_parts[1])
            return b""  # Cannot return None

        def shutdown_handler(self) -> None:
            """Disconnect from the digital multimeter when the server shuts down."""
            self.dmm.disconnect()

    if __name__ == "__main__":
        server = DMM(port=5555)
        server.start()
    ```

### 2. Allow specific

=== "client.py"
    ```python
    # The client sends the action to perform in a multipart message
    # The client always gets a list[bytes] as a response (with a length of 1)
    # The server has an IP address of 192.168.1.8 and is running on port 5555
    from msl.equipment import Connection, ZeroMQ

    client: ZeroMQ
    with Connection("ZMQ::192.168.1.8::5555").connect() as client:
        # The client wants to query the equipment
        print(client.query_multipart([b"query", b"*IDN?"]))

        # The client only wants to write a message to the equipment
        _ = client.query_multipart([b"write", b"*RST"])

        # The client only wants to read a message from the equipment
        print(client.query_multipart([b"read"]))
    ```

=== "server.py"
    ```python
    # The client sends the action to perform as the first item in `msg_parts`
    # The server includes an `allow` keyword argument of the client's IP address
    from __future__ import annotations

    from msl.equipment import Connection, GPIB, ZeroMQServer
    from msl.equipment.typing import ZMQServerResponse

    class DMM(ZeroMQServer):
        """Allow for a digital multimeter to be available on the network."""

        def __init__(self, port: int, allow: str) -> None:
            super().__init__(port=port, allow=allow)

            # Create the connection to the digital multimeter
            self.dmm: GPIB = Connection("GPIB::18").connect()

        def handle_request(self, msg_parts: list[bytes]) -> ZMQServerResponse:
            """Handle a request and return the response."""
            action, *message = msg_parts
            if action == b"query":
                return self.dmm.query(message[0], decode=False)

            if action == b"write":
                _ = self.dmm.write(message[0])
                return b""  # Cannot return None

            # Otherwise, perform a read
            return self.dmm.read(decode=False)

        def shutdown_handler(self) -> None:
            """Disconnect from the digital multimeter when the server shuts down."""
            self.dmm.disconnect()

    if __name__ == "__main__":
        # The client has an IP address of 192.168.1.58
        # You can also specify a sequence of IP addresses to allow
        server = DMM(port=5555, allow="192.168.1.58")
        server.start()
    ```

### 3. Use a [PAIR][zmq.SocketType.PAIR]

=== "client.py"
    ```python
    # The connection is created using the `socket_type="PAIR"` keyword argument
    # The server has an IP address of 192.168.1.8 and is running on port 5555
    from msl.equipment import Connection, ZeroMQ

    client: ZeroMQ
    with Connection("ZMQ::192.168.1.8::5555", socket_type="PAIR").connect() as client:
        # The client performs a query
        print(client.query("*IDN?"))

        # The client can perform multiple writes without needing to perform a read
        client.write_multipart([b"ignored", b"*RST"])
        client.write_multipart([b"ignored", b"*CLS"])

        # The client only wants to read a message from the equipment
        # The server knows that an empty request is for a read only
        print(client.query(b""))
    ```

=== "server.py"
    ```python
    # The server is instantiated using the `socket_type="PAIR"` keyword argument
    # The server can return `None` to not send a response
    from __future__ import annotations

    from msl.equipment import Connection, GPIB, ZeroMQServer
    from msl.equipment.typing import ZMQServerResponse

    class DMM(ZeroMQServer):
        """Allow for a digital multimeter to be available on the network."""

        def __init__(self, port: int, socket_type: str) -> None:
            super().__init__(port=port, socket_type=socket_type)

            # Create the connection to the digital multimeter
            self.dmm: GPIB = Connection("GPIB::18").connect()

        def handle_request(self, msg_parts: list[bytes]) -> ZMQServerResponse:
            """Handle a request and return the response."""
            if len(msg_parts) == 1:
                message = msg_parts[0]
                if not message:
                    return self.dmm.read(decode=False)
                return self.dmm.query(message, decode=False)

            # Otherwise, only write a message (the message is the second item)
            _ = self.dmm.write(msg_parts[1])
            return None  # Return None to not send a response

        def shutdown_handler(self) -> None:
            """Disconnect from the digital multimeter when the server shuts down."""
            self.dmm.disconnect()

    if __name__ == "__main__":
        server = DMM(port=5555, socket_type="PAIR")
        server.start()
    ```

### 4. Use an identity

=== "client.py"
    ```python
    # The client must include its identity in every request message
    # The server has an IP address of 192.168.1.8 and is running on port 5555
    from msl.equipment import Connection, ZeroMQ

    identity = b"let me in!"

    client: ZeroMQ
    with Connection("ZMQ::192.168.1.8::5555").connect() as client:
        # The client makes an unauthorised query
        # Response is "PermissionError: ..."
        print(client.query("*IDN?"))

        # The client makes a successful authenticated query
        print(client.query_multipart([identity, b"*IDN?"]))

        # The client only wants to write a message to the equipment
        # But the client must still read a response for the REQ-REP protocol
        _ = client.query_multipart([identity, b"ignored", b"*RST"])

        # The client only wants to read a message from the equipment
        # The server knows that an empty request is for a read only
        print(client.query_multipart([identity, b""]))
    ```

=== "server.py"
    ```python
    # The client must include its identity in every request message
    # The server verifies the identity before processing the request
    from __future__ import annotations

    from msl.equipment import Connection, GPIB, ZeroMQServer
    from msl.equipment.typing import ZMQServerResponse

    class DMM(ZeroMQServer):
        """Allow for a digital multimeter to be available on the network."""

        def __init__(self, port: int) -> None:
            super().__init__(port=port)

            # Create the connection to the digital multimeter
            self.dmm: GPIB = Connection("GPIB::18").connect()

        def handle_request(self, msg_parts: list[bytes]) -> ZMQServerResponse:
            """Handle a request and return the response."""
            identity, *request = msg_parts

            # Check the identity of the client
            if identity != b"let me in!":
                return b"PermissionError: You are not allowed to do this"

            if len(request) == 1:
                message = request[0]
                if not message:
                    return self.dmm.read(decode=False)
                return self.dmm.query(message, decode=False)

            # Otherwise, only write a message (the second item in `request`)
            _ = self.dmm.write(request[1])
            return b""  # Cannot return None

        def shutdown_handler(self) -> None:
            """Disconnect from the digital multimeter when the server shuts down."""
            self.dmm.disconnect()

    if __name__ == "__main__":
        server = DMM(port=5555)
        server.start()
    ```

## Command Line Interface

A command-line interface is also available to find equipment, [validate][] XML files against the schema or start the [web application][]. Validation and the web application require that the `msl-equipment-validate` and `msl-equipment-webapp` packages are installed.

To see the help, run

```console
msl-equipment help
```

or to display the help for a specific command

```console
msl-equipment help find
```

### find {: #cli-find }

Run the `find` command to find equipment (and serial ports) that are available.

```console
msl-equipment find
```

This will display a description about the type of interface, the equipment that was found for each interface and the address(es) that may be used to connect to the equipment.

!!! tip
    If USB devices are attached to the computer and none are found, make sure you have followed the [USB prerequisites][usb] and/or the [GPIB prerequisites][gpib] for your operating system.

```console
ASRL Ports
  COM1 [Intel PCI\VEN_8086&DEV_A13D&SYS_72141043&REV_31\3&14588619&1&B4]
  COM2 [PI 18071105A VID:PID=0647:0100 SER=18071105A]
  COM3 [Prolific VID:PID=067B:2303 LOCATION=1-8]
FTDI Devices
  FTDI2::0x0403::0xfaf0::40874293 [APT Stepper Motor Controller]
  FTDI2::0x0403::0xfaf0::27259213 [Brushed Motor Controller]
  FTDI2::0x0403::0xfaf0::26007245 [Stepper Controller]
GPIB Devices
  GPIB0::5::INSTR
LXI Devices
  315W Multi Range Triple Output PSU [webserver: http://169.254.100.2]
    TCPIP::169.254.100.2::9221::SOCKET
    TCPIP::169.254.100.2::inst0::INSTR
  34465A Digital Multimeter [webserver: http://169.254.100.3]
    TCPIP::169.254.100.3::5025::SOCKET
    TCPIP::169.254.100.3::hislip0::INSTR
    TCPIP::169.254.100.3::inst0::INSTR
VXI11 Devices
  34972A Data Acquisition / Switch Unit [webserver: http://10.12.102.15]
    TCPIP::10.12.102.15::5025::SOCKET
    TCPIP::10.12.102.15::inst0::INSTR
  E5810 (00-21-B3-1F-01-CD) [webserver: http://10.12.102.31]
    TCPIP::10.12.102.31::inst0::INSTR
  E5810 (43:8E:5A:06:23:EE) [webserver: http://10.12.102.2]
    TCPIP::10.12.102.2::inst0::INSTR
```

### validate {: #cli-validate }

Validate [equipment registers][] and [connection][connections] files against the schema.

Requires the [msl-equipment-validate][validate] package to be installed.

The following command shows how to validate an equipment register

```console
msl-equipment validate path/to/register.xml
```

See [here][validate-usage] for more examples.
