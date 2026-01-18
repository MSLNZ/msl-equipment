# Configuration Files

A configuration file is useful when you want to perform a measurement. You can use it to specify

* equipment that is required to perform the measurement
* locations of the [equipment registers][] and [connections][] that the equipment can be found in
* user-specific information that the measurement procedure requires for data acquisition.

A configuration file uses the eXtensible Markup Language (XML) file format to specify this information.

## XML Example {: #config-xml-example}

The following illustrates an example configuration file.

```xml
<?xml version="1.0" encoding="utf-8"?>
<config> <!-- The name of the root tag can be anything you want. -->

  <!-- OPTIONAL: Set the path to the D2XX library file (for FTDI communication).

    This creates/overwrites the value of the D2XX_LIBRARY environment variable.
    Specifying this element is only necessary if the D2XX library is not
    automatically found. You could also include the directory to the D2XX
    library file as a <path> element in the configuration file (see below).
  -->
  <d2xx_library>C:\Users\username\ftd2xx64.dll</d2xx_library>

  <!-- OPTIONAL: Set the path to a GPIB library file (for GPIB communication).

    This creates/overwrites the value of the GPIB_LIBRARY environment variable.
    Specifying this element is only necessary if the default file location is
    not automatically found or if you want to use a different GPIB library
    instead of the default library.
  -->
  <gpib_library>/opt/gpib/libgpib.so.0</gpib_library>

  <!-- OPTIONAL: Set the PyVISA backend library to use for PyVISA communication.

    This creates/overwrites the value of the PYVISA_LIBRARY environment
    variable. Possible values are:
      @ivi (PyVISA >=1.11, default)
      @ni  (PyVISA < 1.11)
      @py  (PyVISA-py)
      @sim (PyVISA-sim)
  -->
  <pyvisa_library>@py</pyvisa_library>

  <!-- OPTIONAL: Add paths to where library files are located.

    The paths are appended to the PATH environment variable. If a
    recursive="true" attribute is included, then recursively adds the
    specified directory and all sub-directories to PATH. Adding <path>
    elements is useful if communication to equipment requires the
    manufacturer's Software Development Kit (SDK). The <path> element
    may be specified multiple times.
  -->
  <path>C:\Program Files\Manufacturer\lib</path>
  <path recursive="true">D:\code\SDKs</path>

  <!-- Specify the equipment that is required to perform the measurement.

    The `eid` attribute (equipment ID from an equipment register) is mandatory,
    and the `name` attribute is optional. If you define a `name`, you can access
    the equipment by its name instead of the index number based on the order
    that <equipment/> elements are defined in the configuration file. You can
    also access the equipment by its `eid` value. All other attributes are
    ignored by msl-equipment. Additional attributes may be helpful for a person
    to know what the equipment is when they read the configuration file.

    Not all <equipment/> elements that are defined need to be for communication
    purposes. Cables, amplifiers, filters and adaptors can all be important
    equipment that may be required to perform a measurement. Defining this kind
    of equipment is useful to have access to during data acquisition since you
    can save the <equipment/> information (or just the equipment IDs) to the
    output file.
   -->
  <equipment eid="MSLE.M.092" name="dmm" comment="borrowed from Kibble lab"/>
  <equipment eid="MSLE.O.103" name="photodiode" manufacturer="MSL" std="B03"/>
  <equipment eid="MSLE.O.061" name="monochromator"/>

  <!-- Equipment registers that the equipment above can be found in.

    The value can be a single XML file or a directory that contains multiple
    XML files (if your register spans multiple files). If a directory, the
    specified directory and all sub-directories will be searched for equipment
    registers.

    The value supports the ~ character to represent the users HOME directory.
    The <register> element can be specified multiple times.
  -->
  <register>~\Equipment\register.xml</register>
  <register>M:\Mass\Register</register>

  <!-- Connection files for equipment that require computer control.

    The value can be a single XML file or a directory that contains multiple
    XML files. If a directory, the specified directory and all sub-directories
    will be searched for connection files.

    The value supports the ~ character to represent the users HOME directory.
    The <connections> element can be specified multiple times.
  -->
  <connections>C:\DATA\Connections\transmittance.xml</connections>

  <!-- USER SPECIFIC: You may define your own elements. -->
  <max_temperature unit="°C">30</max_temperature>
  <auto_zero>true</auto_zero>
  <nd_filter>OD: 2.0</nd_filter>
  <smtp>
    <host>smtp.server.nz</host>
    <port>25</port>
    <recipient>me@measurement.govt.nz</recipient>
    <recipient>you@measurement.govt.nz</recipient>
  </smtp>

</config>
```

## Python Example {: #config-python-example}

The [Config][] class is used to load a configuration file

```pycon
>>> from msl.equipment import Config
>>> cfg = Config("tests/resources/config.xml")

```

You can then access the equipment [registers][msl.equipment.config.Config.registers],

```pycon
>>> for team, register in cfg.registers.items():
...    print(f"{team}:", register)
Mass: Register(team='Mass' (3 equipment))
Light: Register(team='Light' (4 equipment))

```

iterate over and access `<equipment/>` elements that have been defined in the configuration file to access the [Equipment][] instances,

```pycon
>>> for equipment in cfg.equipment:
...     print(equipment.id)
MSLE.M.092
MSLE.O.103
MSLE.O.061
>>> cfg.equipment[0].id  # use the index
'MSLE.M.092'
>>> cfg.equipment["MSLE.M.092"].id  # use the equipment id
'MSLE.M.092'
>>> cfg.equipment["dmm"].id  # use the name attribute
'MSLE.M.092'

```

access XML elements defined in the configuration file by using the tag name or the path to the element,

```pycon
>>> cfg.attrib("max_temperature")
{'unit': '°C'}
>>> cfg.find("max_temperature")
<Element 'max_temperature' at ...>
>>> cfg.findall("smtp/recipient")
[<Element 'recipient' at ...>, <Element 'recipient' at ...>]

```

and if the value of an XML element is a boolean (`true`, `false` case-insensitive) an integer or a floating-point number, you can use the [value][msl.equipment.config.Config.value] method to convert the text value to the appropriate Python data type (otherwise the text value will remain as a string).

```pycon
>>> cfg.value("auto_zero")
True
>>> cfg.value("max_temperature") / 2
15.0
>>> cfg.value("nd_filter")
'OD: 2.0'

```

If the equipment supports computer control, you can call the [connect][msl.equipment.schema.Equipment.connect] method of the [Equipment][msl.equipment.schema.Equipment] instance to establish communication.

```python
dmm = cfg.equipment["dmm"].connect()
print(dmm.query("*IDN?"))
dmm.disconnect()
```

See [this section][connections-python-examples] for more details about communicating with equipment.
