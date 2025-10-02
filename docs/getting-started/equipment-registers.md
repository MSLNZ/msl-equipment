# Equipment Registers

Laboratories that use equipment for traceable calibration measurements are required to manage information about the equipment by following the [ISO/IEC 17025](https://www.iso.org/ISO-IEC-17025-testing-and-calibration-laboratories.html){:target="_blank"} standard. This information is saved in files that are referred to as *equipment registers*.

An equipment register is based on the definitions in the [Schema][er-schema] and may either be saved in the eXtensible Markup Language (XML) file format or in a [Python module][er-python-module]. Using the XML format is the preferred way to save the information since XML files can be easily [validated][validate] against the [Schema][er-schema] to ensure data integrity and it allows for equipment registers to be parsed by many programming languages. An equipment register can be saved in a single XML file or distributed across multiple XML files.

The [Schema Classes][] section of the documentation shows how an equipment register can be used in a Python program.

## XML Schema {: #er-schema }

The documentation for the equipment-register schema is available [here](https://mslnz.github.io/equipment-register-schema/latest/){:target="_blank"} and development of the schema is performed in the [repository](https://github.com/MSLNZ/equipment-register-schema){:target="_blank"}.

Currently, the schema is targeting equipment that is located at the Measurement Standards Laboratory of New Zealand (in particular, enumeration values and pattern-string matches). If you work at a calibration laboratory and are interested in using the schema within your Quality Management System, please [contact us](https://www.measurement.govt.nz/contact-us){:target="_blank"} or open an [issue](https://github.com/MSLNZ/equipment-register-schema/issues){:target="_blank"}.

See [this section][validate] for details on how to validate the contents of an equipment register against the schema.

## Python Module {: #er-python-module }

You may save the information about the equipment you are using in Python modules instead of in XML files.

```python
from datetime import date

from msl.equipment import (
    CompletedTask,
    Component,
    Connection,
    Equation,
    Equipment,
    Evaluable,
    Maintenance,
    Measurand,
    Range,
    Report,
)

equipment = Equipment(
    manufacturer="HP",
    model="3458A",
    connection=Connection("GPIB::22"),
    maintenance=Maintenance(
        completed=(
            CompletedTask(
                task="Clean fan",
                due_date=date(2025, 3, 4),
                completed_date=date(2025, 3, 5),
                performed_by="John",
            ),
        )
    ),
    calibrations=(
        Measurand(
            quantity="Voltage DC",
            calibration_interval=1,
            components=(
                Component(
                    reports=(
                        Report(
                            id="Report No.",
                            report_issue_date=date(2024, 8, 13),
                            measurement_start_date=date(2024, 8, 5),
                            measurement_stop_date=date(2024, 8, 6),
                            equations=(
                                Equation(
                                    value=Evaluable(
                                        equation="0.9999862*v + 1.0241e-5",
                                        variables=("v",),
                                        ranges={"v": Range(1, 10)}
                                    ),
                                    uncertainty=Evaluable(equation="3.2e-7"),
                                    unit="V",
                                ),
                            ),
                        ),
                    )
                ),
            ),
        ),
    ),
)

# # Connect to the digital multimeter to query its identity
dmm = equipment.connect()
print(dmm.query("ID?"))

# You can fetch DC voltage readings from the multimeter
voltages = ...

# and apply the calibration equation to correct the voltages
correction = equipment.latest_report().equations[0]
print(correction.value(v=voltages))
print(correction.uncertainty(v=voltages))
```
