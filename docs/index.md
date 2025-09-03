# Overview

!!! info
    The docs are being rewritten. See [here](https://msl-equipment.readthedocs.io/en/latest/index.html) for the old docs.

The purpose of `msl-equipment` is to manage information about equipment and to interface with equipment for computer control. The information that is managed is focused on testing and calibration laboratories that are accredited for the [ISO/IEC 17025]{:target="_blank"} standard.

[ISO/IEC 17025]: https://www.iso.org/ISO-IEC-17025-testing-and-calibration-laboratories.html

## Registers

### Equipment Register

### Connection Register

## Configuration File

A configuration file is useful when you want to perform a measurement. You can use it to specify

1. equipment that is required to perform the measurement,
2. locations of the [equipment][equipment-register] and [connection][connection-register] registers that the equipment can be found in, and
3. additional information that the measurement procedure requires for data acquisition.

The configuration file uses the XML file format to specify this information.

The following illustrates an example configuration file.

```xml
<?xml version="1.0" encoding="utf-8"?>
<msl>

  <!-- OPTIONAL: Set the path to a GPIB library file (for GPIB communication).

    This creates/overwrites the value of the GPIB_LIBRARY environment variable.
    Specifying this element is only necessary if the default file location is
    not automatically found or if you want to use a different file instead of
    the default file.
  -->
  <gpib_library>/opt/gpib/libgpib.so.0</gpib_library>

  <!-- OPTIONAL: Set the PyVISA backend library to use for PyVISA communication.

    This creates/overwrites the value of the PYVISA_LIBRARY environment
    variable. Possible values are:
      @ivi (PyVISA >=1.11)
      @ni  (PyVISA < 1.11)
      @py  (PyVISA-py)
      @sim (PyVISA-sim)
  -->
  <pyvisa_library>@py</pyvisa_library>

  <!-- OPTIONAL: Add paths to where external resource files are located.

    Paths are appended to the PATH environment variable. If a recursive="true"
    attribute is included, then recursively adds the specified directory and
    all sub-directories to PATH. This is useful if communication to the
    equipment uses an SDK. The <path> element may be specified multiple times.
  -->
  <path>D:\code\SDKs</path>
  <path recursive="true">C:\Program Files\Manufacturer</path>

  <!-- OPTIONAL: You may define your own elements. -->
  <max_temperature unit="°C">60</max_temperature>
  <smtp>
    <file>settings.ini</file>
    <recipient>me@measurement.govt.nz</recipient>
    <recipient>you@measurement.govt.nz</recipient>
  </smtp>

  <!-- Specify the equipment that is being used to perform the measurement.

    The `eid` attribute (equipment ID from an equipment register) is mandatory,
    all other attributes are optional. If you define an "alias" then you can
    access the equipment by the alias value instead of the index number based
    on the order that it is defined in the configuration file. Defining the
    `manufacturer`, `model` or `serial` are helpful for a person to know what
    the equipment is when they read the configuration file, since the equipment
    ID does not provide "helpful" information for a person.
   -->
  <equipment eid="MSLE.O.231" alias="dmm" model="3458A" serial="0123456789"/>
  <equipment eid="MSLE.O.103" alias="photodiode" manufacturer="MSL"/>
  <equipment eid="MSLE.O.061" alias="monochromator"/>

  <!-- The Equipment Registers that the equipment above can be found in. -->
  <registers>
    <!-- Equipment register is defined in a single file. -->
    <register>C:\Equipment\register.xml</register>
    <!-- Equipment register spans multiple files, specify parent directory. -->
    <register>L:\Register</register>
  </registers>

  <!-- The Connection Registers to load connection information from. -->
  <connections>
    <!-- Connection register is defined in a single file. -->
    <connection>C:\Connection\register.xml</connection>
    <!-- Connection register spans multiple files, specify parent directory. -->
    <connection>L:\Register</connection>
  </connections>

</msl>
```

The [Config][] class is used to load a configuration file

```pycon
>>> from msl.equipment import Config
>>> cfg = Config("tests/resources/config.xml")

```

You can then access the equipment registers

```pycon
>>> for key, value in cfg.registers.items():
...    print(f"{key}:", value)
Mass: <Register team='Mass' (3 equipment)>
Light: <Register team='Light' (4 equipment)>

```

iterate over and access `<equipment/>` elements that have been defined in the configuration file

```pycon
>>> for equipment in cfg.equipment:
...     print(equipment.id)
MSLE.O.231
MSLE.O.103
MSLE.O.061
>>> cfg.equipment[0].id  # using the index in the configuration file
'MSLE.O.231'
>>> cfg.equipment["MSLE.O.231"].id  # using the equipment id
'MSLE.O.231'
>>> cfg.equipment["dmm"].id  # using the alias defined in the configuration file
'MSLE.O.231'

```

access XML elements defined in the configuration file by using the tag name or the path to the element

```pycon
>>> cfg.attrib("max_temperature")
{'unit': '°C'}
>>> cfg.find("max_temperature")
<Element 'max_temperature' at ...>
>>> cfg.findall("smtp/recipient")
[<Element 'recipient' at ...>, <Element 'recipient' at ...>]

```

and if the value of an XML element is a boolean (`true`, `false` case-insensitive) an integer or a float, it will be converted to the appropriate Python data type

```pycon
>>> cfg.value("max_temperature") / 2
30.0

```

otherwise the value will remain a string.
