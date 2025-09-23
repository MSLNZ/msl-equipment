# interfaces

Interface classes for computer control.

Generic interface classes

* [Interface][msl.equipment.schema.Interface] &mdash; Base class for all interfaces
* [MessageBased][msl.equipment.interfaces.message_based.MessageBased] &mdash; Base class for all message-based interfaces

Specific interfaces

* [GPIB][msl.equipment.interfaces.gpib.GPIB] &mdash; Base class for GPIB communication
* [HiSLIP][msl.equipment.interfaces.hislip.HiSLIP] &mdash; Base class for the [HiSLIP](https://www.ivifoundation.org/downloads/Protocol%20Specifications/IVI-6.1_HiSLIP-2.0-2020-04-23.pdf) communication protocol
* [Prologix][msl.equipment.interfaces.prologix.Prologix] &mdash; Use [Prologix](https://prologix.biz/) hardware to establish a connection
* [SDK][msl.equipment.interfaces.sdk.SDK] &mdash; Base class for equipment that use the manufacturer's Software Development Kit
* [Serial][msl.equipment.interfaces.serial.Serial] &mdash; Base class for equipment that is connected through a serial port
* [Socket][msl.equipment.interfaces.socket.Socket] &mdash; Base class for equipment that is connected through a socket
* [VXI11][msl.equipment.interfaces.vxi11.VXI11] &mdash; Base class for the [VXI-11](http://www.vxibus.org/specifications.html) communication protocol
* [ZeroMQ][msl.equipment.interfaces.zeromq.ZeroMQ] &mdash; Base class for equipment that use the [ZeroMQ](https://zeromq.org/) communication protocol

Backend (external package) interfaces

* [NIDAQ][msl.equipment.interfaces.nidaq.NIDAQ] &mdash; Use [NI-DAQmx](https://nidaqmx-python.readthedocs.io/en/stable/index.html) as the backend to communicate with the equipment
* [PyVISA][msl.equipment.interfaces.pyvisa.PyVISA] &mdash; Use [PyVISA](https://pyvisa.readthedocs.io/en/stable/) as the backend to communicate with the equipment

::: msl.equipment.schema.Interface
    options:
        show_root_full_path: false
        show_root_heading: true

::: msl.equipment.interfaces.message_based.MessageBased
    options:
        show_root_full_path: false
        show_root_heading: true

::: msl.equipment.interfaces.gpib.GPIB
    options:
        show_root_full_path: false
        show_root_heading: true

::: msl.equipment.interfaces.hislip.HiSLIP
    options:
        show_root_full_path: false
        show_root_heading: true

::: msl.equipment.interfaces.nidaq.NIDAQ
    options:
        show_root_full_path: false
        show_root_heading: true

::: msl.equipment.interfaces.prologix.Prologix
    options:
        show_root_full_path: false
        show_root_heading: true

::: msl.equipment.interfaces.pyvisa.PyVISA
    options:
        show_root_full_path: false
        show_root_heading: true

::: msl.equipment.interfaces.sdk.SDK
    options:
        show_root_full_path: false
        show_root_heading: true

::: msl.equipment.interfaces.serial.Serial
    options:
        show_root_full_path: false
        show_root_heading: true

::: msl.equipment.interfaces.socket.Socket
    options:
        show_root_full_path: false
        show_root_heading: true

::: msl.equipment.interfaces.vxi11.VXI11
    options:
        show_root_full_path: false
        show_root_heading: true

::: msl.equipment.interfaces.zeromq.ZeroMQ
    options:
        show_root_full_path: false
        show_root_heading: true
