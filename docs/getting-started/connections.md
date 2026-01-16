# Connections

The information about how to interface with equipment for computer control is based on the definitions in the [Schema][connections-xml] and may either be saved in the eXtensible Markup Language (XML) file format or in a [Python module][connections-python-examples]. When using the XML format, you would specify the XML file that contains the connection information as a `<connections>` element in your [configuration file][configuration-files]. When the configuration file is loaded (via [Config][]), it links a [Connection][] instance with the corresponding [Equipment][] instance based on the equipment id.

## XML Schema {: #connections-xml }

Schema definition for connection information. See [this section][validate] for details on how to validate the contents of a connections XML file against the schema.

```xml
--8<-- "packages/validate/src/msl/equipment_validate/schema/connections.xsd"
```

### Example {: #connections-xml-example }

Example XML file to specify connection information. Only the `<eid>` and `<address>` elements are required, all other elements are optional.

```xml
<?xml version="1.0" encoding="utf-8"?>
<connections>
    <connection>
        <eid>MSLE.M.041</eid>
        <address>TCPIP::192.168.1.10::hislip0</address>
    </connection>
    <connection>
        <eid>MSLE.M.023</eid>
        <address>ASRL/dev/ttyS1</address>
        <backend>PyVISA</backend>
        <manufacturer>Manufacturer</manufacturer>
        <model>Model</model>
        <serial>Serial</serial>
        <properties>
            <baud_rate>19200</baud_rate>
            <read_termination>\r</read_termination>
            <write_termination>\r</write_termination>
            <timeout>10</timeout>
        </properties>
    </connection>
</connections>
```

## Address Syntax

The following are examples of VISA-style addresses that may be used to connect to equipment.

<table>
  <tr>
    <th>Interface</th>
    <th>Address</th>
    <th>Description</th>
  </tr>
  <tr>
    <td>FTDI</td>
    <td>FTDI::0x0403::0x6001::abc</td>
    <td>FTDI device using driver=0 (default, libusb), idVendor=0x0403, idProduct=0x6001 (hexadecimal notation), serial number=abc, USB Interface Number=0 (default)</td>
  </tr>
  <tr>
    <td>FTDI</td>
    <td>FTDI0::1027::24577::032165::1</td>
    <td>FTDI device using driver=0 (libusb), idVendor=1027, idProduct=24577 (decimal notation), serial number=032165, USB Interface Number=1</td>
  </tr>
  <tr>
    <td>FTDI</td>
    <td>FTDI2::0x0403::0xfaf0::825192</td>
    <td>FTDI device using driver=2 (d2xx), idVendor=0x0403, idProduct=0xfaf0 (hexadecimal notation), serial number=825192,
    the USB Interface Number is ignored when using the d2xx driver</td>
  </tr>
  <tr>
    <td>GPIB</td>
    <td>GPIB::10</td>
    <td>GPIB device at board=0 (default), primary address=10, no secondary address</td>
  </tr>
  <tr>
    <td>GPIB</td>
    <td>GPIB0::voltmeter</td>
    <td>GPIB device at board=0, interface name="voltmeter" (see <a href="https://linux-gpib.sourceforge.io/doc_html/configuration-gpib-conf.html" target="_blank">gpib.conf</a> for more details about the "name" option)</td>
  </tr>
  <tr>
    <td>GPIB</td>
    <td>GPIB1::6::97::INSTR</td>
    <td>GPIB device at board=1, primary address=6, secondary address=97</td>
  </tr>
  <tr>
    <td>GPIB</td>
    <td>GPIB2::INTFC</td>
    <td>GPIB interface at board=2</td>
  </tr>
  <tr>
    <td>HiSLIP</td>
    <td>TCPIP::dev.company.com::hislip0</td>
    <td>A HiSLIP LAN instrument, host=dev.company.com</td>
  </tr>
  <tr>
    <td>HiSLIP</td>
    <td>TCPIP::10.12.114.50::hislip0,5000::INSTR</td>
    <td>A HiSLIP LAN instrument, host=10.12.114.50, port=5000</td>
  </tr>
  <tr>
    <td>PROLOGIX</td>
    <td>Prologix::192.168.1.110::1234::6</td>
    <td>The GPIB-ETHERNET Controller, host=192.168.1.110, port=1234, primary GPIB address=6</td>
  </tr>
  <tr>
    <td>PROLOGIX</td>
    <td>Prologix::192.168.1.70::1234::6::112</td>
    <td>The GPIB-ETHERNET Controller, host=192.168.1.70, port=1234, primary GPIB address=6, secondary GPIB address=112</td>
  </tr>
  <tr>
    <td>PROLOGIX</td>
    <td>Prologix::192.168.1.70::1234::GPIB::6::112</td>
    <td>The GPIB-ETHERNET Controller, host=192.168.1.70, port=1234, primary GPIB address=6, secondary GPIB address=112</td>
  </tr>
  <tr>
    <td>PROLOGIX</td>
    <td>Prologix::COM3::6</td>
    <td>The GPIB-USB Controller, port=COM3, primary GPIB address=6</td>
  </tr>
  <tr>
    <td>PROLOGIX</td>
    <td>Prologix::COM3::GPIB::6</td>
    <td>The GPIB-USB Controller, port=COM3, primary GPIB address=6</td>
  </tr>
  <tr>
    <td>PROLOGIX</td>
    <td>Prologix::/dev/ttyS0::4::96</td>
    <td>The GPIB-USB Controller, port=/dev/ttyS0, primary GPIB address=4, secondary GPIB address=96</td>
  </tr>
  <tr>
    <td>SDK</td>
    <td>SDK::C:/Manufacturer/library.dll</td>
    <td>Specify the full path to the SDK</td>
  </tr>
  <tr>
    <td>SDK</td>
    <td>SDK::library.dll</td>
    <td>Specify only the filename if the path to where the SDK file is located has been added to the <code>PATH</code> environment variable</td>
  </tr>
  <tr>
    <td>SERIAL</td>
    <td>COM2</td>
    <td>A serial port on Windows</td>
  </tr>
  <tr>
    <td>SERIAL</td>
    <td>ASRL/dev/ttyS1</td>
    <td>A serial port on Linux</td>
  </tr>
  <tr>
    <td>SERIAL</td>
    <td>ASRL2::INSTR</td>
    <td>Compatible with National Instruments syntax</td>
  </tr>
  <tr>
    <td>SERIAL</td>
    <td>ASRLCOM2</td>
    <td>Compatible with PyVISA-py syntax</td>
  </tr>
  <tr>
    <td>SOCKET</td>
    <td>TCP::192.168.1.100::5000</td>
    <td>Use the TCP protocol, host=192.168.1.100, port=5000</td>
  </tr>
  <tr>
    <td>SOCKET</td>
    <td>UDP::192.168.1.100::5000</td>
    <td>Use the UDP protocol, host=192.168.1.100, port=5000</td>
  </tr>
  <tr>
    <td>SOCKET</td>
    <td>TCPIP::192.168.1.100::5000::SOCKET</td>
    <td>Compatible with National Instruments syntax</td>
  </tr>
  <tr>
    <td>USB</td>
    <td>USB::0x2a67::0x0408::abc::RAW</td>
    <td>A (raw) USB device with board=0 (default), idVendor=0x2a67, idProduct=0x0408 (hexadecimal notation), serial number=abc, USB Interface Number=0 (default)</td>
  </tr>
  <tr>
    <td>USB</td>
    <td>USB0::1027::24577::032165::1::RAW</td>
    <td>A (raw) USB device with board=0, idVendor=1027, idProduct=24577 (decimal notation), serial number=032165, USB Interface Number=1</td>
  </tr>
  <tr>
    <td>USB</td>
    <td>USB::0x0381::0x06a2::IGNORE::RAW</td>
    <td>A (raw) USB device with board=0 (default), idVendor=0x0381, idProduct=0x06a2 (hexadecimal notation), serial number=IGNORE (means that the serial number is not used when finding the USB device and the first USB device found that matches idVendor and idProduct is used), USB Interface Number=0 (default)</td>
  </tr>
  <tr>
    <td>VXI-11</td>
    <td>TCPIP::dev.company.com::INSTR</td>
    <td>A VXI-11.3 LAN instrument, host=dev.company.com (uses the default LAN Device Name <i>inst0</i>)</td>
  </tr>
  <tr>
    <td>VXI-11</td>
    <td>TCPIP::10.6.56.21::gpib0,2::INSTR</td>
    <td>A VXI-11.2 GPIB device, host=10.6.56.21, gpib address=2</td>
  </tr>
  <tr>
    <td>VXI-11</td>
    <td>TCPIP::192.168.1.100</td>
    <td>A VXI-11.3 LAN instrument, host=192.168.1.100 (default values for board <i>0</i> and LAN device name <i>inst0</i> are used)</td>
  </tr>
  <tr>
    <td>ZMQ</td>
    <td>ZMQ::192.168.20.90::5555</td>
    <td>Use the ZeroMQ messaging library to connect to a device, host=192.168.20.90, port=5555</td>
  </tr>
</table>

National Instruments also provides [examples](https://www.ni.com/docs/en-US/bundle/ni-visa/page/visa-resource-syntax-and-examples.html){:target="_blank"} if you are using [PyVISA](https://pyvisa.readthedocs.io/en/stable/){:target="_blank"} as the [backend][connections-backend].

## Interfaces {: #connections-interfaces }

The following interface classes are available

* [FTDI][] &mdash; For equipment that use a Future Technology Devices International (FTDI) chip
* [GPIB][] &mdash; For equipment that use the GPIB (IEEE 488) protocol
* [HiSLIP][] &mdash; For equipment that use the [HiSLIP](https://www.ivifoundation.org/downloads/Protocol%20Specifications/IVI-6.1_HiSLIP-2.0-2020-04-23.pdf){:target="_blank"} protocol
* [Prologix][] &mdash; Use [Prologix](https://prologix.biz/){:target="_blank"} hardware to establish a connection to GPIB-compatible equipment
* [SDK][] &mdash; For equipment that use a Software Development Kit (SDK) for communication
* [Serial][] &mdash; For equipment that is connected through a serial port (or a USB-to-Serial adaptor)
* [Socket][] &mdash; For equipment that is connected through a network socket
* [USB][] &mdash; For equipment that use the USB protocol
* [VXI11][] &mdash; For equipment that use the [VXI-11](http://www.vxibus.org/specifications.html){:target="_blank"} protocol
* [ZeroMQ][] &mdash; For equipment that use the [ZeroMQ](https://zeromq.org/){:target="_blank"} protocol

### Backends {: #connections-backend }

When a [Connection][] instance is created, the `backend` keyword argument decides which backend to use when interfacing with the equipment. There are different [Backend][msl.equipment.enumerations.Backend]s to choose from: `MSL` (default), `PyVISA` or `NIDAQ`.

The [interface class][connections-interfaces] can be used if the `backend` is `MSL`. The corresponding interface classes for the external backends are [PyVISA][msl.equipment.interfaces.pyvisa.PyVISA] and [NIDAQ][msl.equipment.interfaces.nidaq.NIDAQ].

## Python Examples {: #connections-python-examples }

If you are primarily interested in using `msl-equipment` to interface with equipment (and not the [Equipment Registers][] aspect), the simplest approach is to create [Connection][] instances in a module and call the [connect][msl.equipment.schema.Connection.connect] method (which is equivalent to calling [Equipment.connect()][msl.equipment.schema.Equipment.connect] if you are using [Equipment Registers][]).

```python
from msl.equipment import Connection

device = Connection("COM3").connect()
print(device.query("*IDN?"))
device.disconnect()
```

All [interfaces][connections-interfaces] can be used as a [context manager][with]{:target="_blank"}, where the [disconnect][msl.equipment.schema.Interface.disconnect] method is called when exiting the code block. The previous example is equivalent to the following.

```python
from msl.equipment import Connection

with Connection("COM3").connect() as device:
  print(device.query("*IDN?"))
```

If you have multiple equipment that you want to interface with and you also want to include some additional metadata so that you can keep track of which device is associated with the corresponding address, you could do something like the following. Also, for some interfaces, such as when using a manufacturer's [SDK][], the serial number must be passed to the [SDK][] when opening the connection and therefore the serial number must be specified as a keyword argument (or as an element in a connections [XML][connections-xml] file).

```python
from msl.equipment import Connection

# Assign custom names to associate with each equipment
connections = {
    "alice": Connection("GPIB::22", model="3458A"),
    "bob": Connection("COM3", manufacturer="HP", model="34401A"),

    # not used below but is available to use for another day
    "eve": Connection("SDK::company.dll", manufacturer="ABC", serial="4621"),
}

# Connect to the equipment using the names that were assigned
alice = connections["alice"].connect()
bob = connections["bob"].connect()

# Query the identity
print(alice.query("ID?"))
print(bob.query("*IDN?"))

# Disconnect when finished
alice.disconnect()
bob.disconnect()
```

The [logging][]{:target="_blank"} module may be used to help debug communication issues, especially when interfacing with multiple equipment. By enabling the `DEBUG` [level][levels]{:target="_blank"} you will be able to capture the bytes that are written to and read from the equipment.

```python
import logging
from msl.equipment import Connection

logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(message)s")

c = Connection("COM3", manufacturer="HP", model="34401A", serial="3146A")
with c.connect() as dmm:
    identity = dmm.query("*IDN?")
```

Running the previous example would display something similar to the following.

```console
DEBUG Connecting to Serial<HP|34401A|3146A at COM3>
DEBUG Serial<HP|34401A|3146A>.write(b'*IDN?\r\n')
DEBUG Serial<HP|34401A|3146A>.read() -> b'Hewlett Packard,34401A,3146A,A03-02\n'
DEBUG Disconnected from Serial<HP|34401A|3146A at COM3>
```
