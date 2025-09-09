# Connections

The information about how to interface with equipment for computer control is defined in the eXtensible Markup Language (XML) file format. You specify the XML file that contains the connection information as a `<connections>` element in your [configuration file][configuration-files]. When the configuration file is loaded, it links a [Connection][] instance with the corresponding [Equipment][] instance. You may also define the connection information directly in a [Python module][non-iso-labs], instead of in XML files.

## XML {: #connections-xml}

### Schema {: #connections-xml-schema}

### Example {: #connections-xml-example}

## Address Syntax

The following are examples of VISA-style addresses that may be used to connect to equipment.

<table>
  <tr>
    <th>Interface</th>
    <th>Address</th>
    <th>Description</th>
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

## Interfaces {: #connections-interfaces}

The following interface classes are available

* [SDK][msl.equipment.interfaces.sdk.SDK] &mdash; Use the Software Development Kit (SDK) provided by the manufacturer

### Backends {: #connections-backend}

When a [Connection][] instance is created, the `backend` keyword argument decides which backend to use when interfacing with the equipment. There are different [Backends][msl.equipment.enumerations.Backend] to choose from: `MSL` (default), `PyVISA` or `NIDAQ`.

The [interface class][connections-interfaces] can be used if the `backend` is `MSL`. The corresponding interface classes for the external backends are [PyVISA][msl.equipment.interfaces.pyvisa.PyVISA] and [NIDAQ][msl.equipment.interfaces.nidaq.NIDAQ].

## Python Example {: #connections-python-example}
