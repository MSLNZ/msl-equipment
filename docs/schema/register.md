# Register

An equipment register can be stored in a single XML file or distributed across multiple XML files. In this example we load a single XML file.

```pycon
>>> from msl.equipment import Register
>>> register = Register("tests/resources/mass/register.xml")

```

Printing the `register` object shows the name of the [team][msl.equipment.schema.Register.team] that is responsible for the equipment register and the number of [Equipment][] items that are in the register.

```pycon
>>> register
Register(team='Mass' (2 equipment))
>>> register.team
'Mass'

```

A register behaves like a sequence of [Equipment][] items. You can get the number of items in the sequence and iterate over the sequence,

```pycon
>>> len(register)
2
>>> for equipment in register:
...     print(equipment.id)
...
MSLE.M.001
MSLE.M.092

```

access equipment by its index, its equipment [id][msl.equipment.schema.Equipment.id] or its [alias][msl.equipment.schema.Equipment.alias].

```pycon
>>> register[1].id  # index
'MSLE.M.092'
>>> register["MSLE.M.092"].id  # equipment id
'MSLE.M.092'
>>> register["Bob"].id  # alias
'MSLE.M.092'

```

The [get][msl.equipment.schema.Register.get] method will attempt to get the [Equipment][] at the specified index, [id][msl.equipment.schema.Equipment.id] or [alias][msl.equipment.schema.Equipment.alias], but will return `None` (instead of raising an exception) if the [Equipment][] cannot be found in the register.

```pycon
>>> assert register.get(4) is None  # invalid index
>>> assert register.get("MSLE.M.999") is None  # invalid equipment id
>>> register.get("Bob")  # valid alias
Equipment(id='MSLE.M.092', manufacturer='XYZ', model='A', serial='b' (4 reports))

```

The [find][msl.equipment.schema.Register.find] method searches the register to find equipment that contain certain text. You may use a [regular-expression pattern](https://regexr.com/) to find matching equipment items. Here we find all equipment that have the text `Hygrometer` in one of the [Equipment][] attribute values that are considered in the search.

```pycon
>>> for hygrometer in register.find("Hygrometer"):
...    print(hygrometer)
Equipment(id='MSLE.M.092', manufacturer='XYZ', model='A', serial='b' (4 reports))

```

We see that one equipment was found and that there are four calibration reports associated with the equipment. From the [Equipment][] instance, we can get the latest calibration report for a certain [Component][msl.equipment.schema.Component] [name][msl.equipment.schema.Component.name] and [Measurand][msl.equipment.schema.Measurand] [quantity][msl.equipment.schema.Measurand.quantity].

!!! tip
    If the equipment contains only one [Measurand][msl.equipment.schema.Measurand] and one [Component][msl.equipment.schema.Component] you do not need to specify the *name* and *quantity* keyword arguments.

```pycon
>>> report = hygrometer.latest_report(name="Probe 1", quantity="Humidity")
>>> report
LatestReport(name='Probe 1', quantity='Humidity', id='Humidity/2023/583' (1 equation))

```

We see that the calibration report contains one [Equation][]. We can use the equation to apply a correction to measured values and to calculate the uncertainty.

```pycon
>>> value = report.equation.value
>>> value.equation
'R - 7.131e-2 - 3.951e-2*R + 3.412e-4*pow(R,2) + 2.465e-3*t + 1.034e-3*R*t - 5.297e-6*pow(R,2)*t'
>>> value(R=[45.5, 46.1], t=[20.1, 20.0])
array([45.1121266, 45.7099039])
>>> report.equation.uncertainty(R=[45.5, 46.1], t=[20.1, 20.0])
array([0.355, 0.355])
>>> report.equation.unit
'%rh'

```

From the [LatestReport][msl.equipment.schema.LatestReport] instance, we can, for example, get the date when the next calibration is due.

```pycon
>>> report.next_calibration_date
datetime.date(2028, 8, 14)

```

::: msl.equipment.schema.Register
    options:
        show_root_full_path: false
        show_root_heading: true
