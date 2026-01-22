# API Overview

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

The [MSLConnectionError][msl.equipment.interfaces.message_based.MSLConnectionError] and [MSLTimeoutError][msl.equipment.interfaces.message_based.MSLTimeoutError] classes are raised if there are issues when communicating with equipment.

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
  COM1 [Communications Port (COM1)]
  COM2 [Communications Port (COM2)]
  COM3 [Intel(R) Active Management Technology - SOL (COM3)]
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
