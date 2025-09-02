# Overview

!!! info
    The docs are being rewritten. See [here](https://msl-equipment.readthedocs.io/en/latest/index.html) for the old docs.

The purpose of `msl-equipment` is to manage information about equipment and to interface with equipment for computer control. The information that is managed is focused on testing and calibration laboratories that are accredited for the [ISO/IEC 17025]{:target="_blank"} standard.

[ISO/IEC 17025]: https://www.iso.org/ISO-IEC-17025-testing-and-calibration-laboratories.html

# Registers

## Equipment Register

## Connection Register

# Configuration File

A configuration file is useful when you want to perform a measurement. You can use it to specify

1. equipment that is being used to perform the measurement
2. locations of the equipment and connection registers that the equipment can be found in
3. additional information that the measurement procedure requires for data acquisition.

The configuration file uses the XML file format to specify this information.

The following illustrates an example configuration file.

```xml
<?xml version="1.0" encoding="utf-8"?>
<msl>

  <!-- OPTIONAL: Set the path to the GPIB library file to use for GPIB communication.

    This will create/overwrite the value of the GPIB_LIBRARY environment variable.
    Specifying this element is only necessary only if the default file location is not
    automatically found or if you want to use a different file instead of the default file.
  -->
  <gpib_library>/opt/gpib/libgpib.so.0</gpib_library>

  <!-- OPTIONAL: Set the PyVISA backend library to use for PyVISA communication.

    This will create/overwrite the value of the PYVISA_LIBRARY environment variable.
    Possible values are:
      @ivi (PyVISA >=1.11)
      @ni  (PyVISA < 1.11)
      @py  (PyVISA-py)
      @sim (PyVISA-sim)
  -->
  <pyvisa_library>@py</pyvisa_library>

  <!-- OPTIONAL: Add paths to where external resource files are located.

    The paths are appended to the PATH environment variable. If a recursive="true"
    attribute is included, then recursively adds the specified directory all
    sub-directories to PATH. This is useful if communication to the equipment
    uses the manufacturer's SDK. The <path> element may be specified multiple times.
  -->
  <path>D:\code\SDKs</path>
  <path recursive="true">C:\Program Files\Manufacturer</path>

  <!-- OPTIONAL: You may define your own elements. -->
  <max_temperature units="C">60</max_temperature>
  <smtp>
    <file>settings.ini</file>
    <recipients>me@measurement.govt.nz</recipients>
  </smtp>

  <!-- Specify the equipment that is being used to perform the measurement.

    The `eid` attribute (the equipment ID from an equipment register) is mandatory,
    all other attributes are optional. If you define an "alias" then you can access the
    equipment by the alias value instead of by the index in which it is defined in the
    configuration file. Defining the `manufacturer`, `model` or `serial` are helpful for
    a person to know what the equipment is when they read the configuration file,
    since the equipment ID does not provide "helpful" information for a person.
   -->
  <equipment eid="MSLE.O.231" alias="dmm" manufacturer="Keysight" model="34465A" serial="123456789" />
  <equipment eid="MSLE.O.086" alias="amplifier" manufacturer="MSL" model="PA1039" />
  <equipment eid="MSLE.O.086" alias="photodiode"  manufacturer="MSL" />
  <equipment eid="MSLE.O.142" alias="shutter" />
  <equipment eid="MSLE.O.061" alias="laser" manufacturer="Coherent" />

  <!-- Specify the Equipment Registers that the equipment above can be found in. -->
  <registers>
    <!-- The equipment register is defined in a single file. -->
    <register>R:\Equipment\Equipment Register.xml</register>
    <!-- The equipment register spans multiple files, specify the parent directory. -->
    <register>L:\Register\</register>
  </registers>

  <!-- Specify the Connection Registers to load connection information from. -->
  <connections>
    <!-- The connection register is defined in a single file. -->
    <connection>R:\Equipment\Connection Register.xml</connection>
    <!-- The connection register spans multiple files, specify the parent directory. -->
    <connection>L:\Register\</connection>
  </connections>

</msl>
```

The [Config][] class is used to load a configuration file

```pycon
>>> from msl.equipment import Config
>>> cfg = Config("tests/resources/config.xml")
>>> cfg.registers
{'Mass': <Register team='Mass' (3 equipment)>}
>>> assert cfg.value("max_temperature") == 60

```