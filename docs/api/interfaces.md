# interfaces

Interface classes for computer control.

* [Interface][msl.equipment.schema.Interface] &mdash; Base class for all interfaces
* [MessageBased][msl.equipment.interfaces.message_based.MessageBased] &mdash; Base class for all message-based interfaces
* [NIDAQ][msl.equipment.interfaces.nidaq.NIDAQ] &mdash; Use [NI-DAQmx](https://nidaqmx-python.readthedocs.io/en/stable/index.html) as the backend to communicate with the equipment
* [PyVISA][msl.equipment.interfaces.pyvisa.PyVISA] &mdash; Use [PyVISA](https://pyvisa.readthedocs.io/en/stable/) as the backend to communicate with the equipment
* [SDK][msl.equipment.interfaces.sdk.SDK] &mdash; Base class for equipment that use the manufacturer's Software Development Kit
* [ZeroMQ][msl.equipment.interfaces.zeromq.ZeroMQ] &mdash; Base class for equipment that use the [ZeroMQ](https://zeromq.org/) communication protocol

::: msl.equipment.schema.Interface
    options:
        show_root_full_path: false
        show_root_heading: true

::: msl.equipment.interfaces.message_based.MessageBased
    options:
        show_root_full_path: false
        show_root_heading: true

::: msl.equipment.interfaces.nidaq.NIDAQ
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

::: msl.equipment.interfaces.zeromq.ZeroMQ
    options:
        show_root_full_path: false
        show_root_heading: true
