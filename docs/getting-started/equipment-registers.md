# Equipment Registers

Laboratories that use equipment for traceable calibration measurements are required to manage information about the equipment by following the [ISO/IEC 17025]{:target="_blank"} standard. An equipment register is in the eXtensible Markup Language (XML) file format, and, as such, it may be parsed by many programming languages.

An equipment register may be defined in a single XML file or distributed across multiple XML files (for the same _team_). You can also define the information directly in a [Python module][non-iso-labs] instead of in XML files.

The [Schema Classes][] section of the documentation shows how each of the XML elements that are contained in an equipment register can be used in a Python program.

## XML Schema

The documentation for the equipment-register schema is available [here](https://mslnz.github.io/equipment-register-schema/latest/){:target="_blank"} and development of the schema is performed in the [repository](https://github.com/MSLNZ/equipment-register-schema){:target="_blank"}.

Currently, the schema is targeting equipment that is located at the Measurement Standards Laboratory of New Zealand (in particular, enumeration values and pattern-string matches). If you work at a calibration laboratory and are interested in using the schema within your quality system, please [contact us](https://www.measurement.govt.nz/contact-us){:target="_blank"} or open an [issue](https://github.com/MSLNZ/equipment-register-schema/issues){:target="_blank"}.

### Validation

You may use any XML-validating tool to validate an equipment register against the schema; however, some of the values of the XML elements are not _completely_ validated by the schema alone. For example, the value of an element in an equipment register could be the SHA256 checksum of a file. The schema will validate that the SHA256 checksum value has the correct string length and that the checksum only contains the allowed alphanumeric characters, but, the schema does not validate that the checksum value is correct for the associated file. For these additional validation steps, another tool must be used.

To validate _all_ elements within an equipment register, you can install `msl-equipment-validate`

=== "pip"
    ```console
    pip install msl-equipment-validate
    ```

=== "pipx"
    ```console
    pipx install msl-equipment-validate
    ```

=== "uv"
    ```console
    uv tool install msl-equipment-validate
    ```

This will install a command-line tool that you can use to validate the content in an equipment register.

TODO show how to use tool...

## Non ISO/IEC 17025 labs {: #non-iso-labs }

If your laboratory is not bound to the [ISO/IEC 17025]{:target="_blank"} standard and you are primarily interested in interfacing with equipment, you can define [Equipment][] classes in a Python module to connect to the equipment

```python
from msl.equipment import Connection, Equipment

equipment = {
    "dmm": Equipment(
        manufacturer="HP",
        model="34401A",
        serial="123456789",
        connection=Connection(
            address="COM3",
        ),
    ),
    "scope": Equipment(
        manufacturer="Pico Technology",
        model="5244B",
        serial="XY135/001",
        connection=Connection(
            address="SDK::ps5000a.dll",
            resolution="16bit",
        ),
    ),
}

# Connect to the digital multimeter
dmm = equipment["dmm"].connect()
identity = dmm.query("*IDN?")
```

[ISO/IEC 17025]: https://www.iso.org/ISO-IEC-17025-testing-and-calibration-laboratories.html
