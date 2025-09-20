# API Overview

Although this package contains many classes and functions, the classes that you may typically create instances of are

* [Config][]
* [Connection][]
* [Equipment][] &mdash; possibly a [Register][] if you only want to load an equipment register (i.e., you don't need to create [Connection][]s)

The following interfaces are available to communicate with equipment,

* [GPIB][msl.equipment.interfaces.gpib.GPIB] &mdash; Base class for GPIB communication
* [Prologix][msl.equipment.interfaces.prologix.Prologix] &mdash; Use [Prologix](https://prologix.biz/) hardware to establish a connection
* [SDK][msl.equipment.interfaces.sdk.SDK] &mdash; Use the Software Development Kit (SDK) provided by the manufacturer
* [Serial][msl.equipment.interfaces.serial.Serial] &mdash; Base class for equipment that is connected through a serial port
* [Socket][msl.equipment.interfaces.socket.Socket] &mdash; Base class for equipment that is connected through a socket
* [VXI11][msl.equipment.interfaces.vxi11.VXI11] &mdash; Base class for equipment that use the VXI-11 communication protocol
* [ZeroMQ][msl.equipment.interfaces.zeromq.ZeroMQ] &mdash; Base class for equipment that use the [ZeroMQ](https://zeromq.org/) communication protocol

and the following classes may be used to interface with equipment using external packages

* [NIDAQ][msl.equipment.interfaces.nidaq.NIDAQ] &mdash; Use the [NIDAQmx](https://nidaqmx-python.readthedocs.io/en/stable/index.html) package to establish a connection to the equipment
* [PyVISA][msl.equipment.interfaces.pyvisa.PyVISA] &mdash; Use the [PyVISA](https://pyvisa.readthedocs.io/en/stable/index.html) package to establish a connection to the equipment
