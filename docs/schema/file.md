# File

<!--
>>> from msl.equipment import File
>>> file = File(
...     url="tests/resources/irradiance.xlsx",
...     sha256="7a91267cfb529388a99762b891ee4b7a12463e83b5d55809f76a0c8e76c71886",
...     attributes={"sheet": "2024-May", "cells": "A1:C11"},
...     comment="FEL T647",
... )

-->

Suppose you have a variable named `file` (which is an instance of [File][msl.equipment.schema.File]) that represents the following information in an equipment register for data that is stored in a Spreadsheet

```xml
<file comment="FEL T647">
  <url sheet="2024-May" cells="A1:C11">tests\resources\irradiance.xlsx</url>
  <sha256>7a91267cfb529388a99762b891ee4b7a12463e83b5d55809f76a0c8e76c71886</sha256>
</file>
```

You can access *sha256* and *comment* as attributes of `file`

```pycon
>>> file.sha256
'7a91267cfb529388a99762b891ee4b7a12463e83b5d55809f76a0c8e76c71886'
>>> file.comment
'FEL T647'

```

The *url* and *attributes* attributes of `file` can be used with the [read_table][msl.io.tables.read_table]{:target="_blank"} function of [msl-io](https://mslnz.github.io/msl-io/latest/){:target="_blank"} to read the Spreadsheet data

```pycon
>>> from msl.io import read_table
>>> table = read_table(file.url, **file.attributes)
>>> print(table.metadata.header)
['Wavelength' 'Irradiance' 'u(Irradiance)']
>>> table
<Dataset 'irradiance.xlsx' shape=(10, 3) dtype='<f8' (1 metadata)>
>>> print(table)
array([[2.500000e+02, 1.818000e-02, 2.033000e-02],
       [3.000000e+02, 1.847800e-01, 1.755000e-02],
       [3.500000e+02, 8.084500e-01, 1.606000e-02],
       [4.000000e+02, 2.213550e+00, 1.405000e-02],
       [4.500000e+02, 4.490040e+00, 1.250000e-02],
       [5.000000e+02, 7.451350e+00, 1.200000e-02],
       [5.500000e+02, 1.075753e+01, 1.152000e-02],
       [6.000000e+02, 1.403809e+01, 1.102000e-02],
       [6.500000e+02, 1.699469e+01, 1.103000e-02],
       [7.000000e+02, 1.944093e+01, 1.077000e-02]])

```

!!! note
    Passing `**file.attributes` to [read_table][msl.io.tables.read_table]{:target="_blank"} works as expected provided that the XML attributes of the `<url>` element are valid keyword arguments to [read_table][msl.io.tables.read_table]{:target="_blank"}. See [Read a table](https://mslnz.github.io/msl-io/latest/#read-a-table){:target="_blank"} for more examples from [msl-io](https://mslnz.github.io/msl-io/latest/){:target="_blank"}, in particular, specifying `dtype="header"` will return a structured dataset which would behave similar to the [Table][table] example in `msl-equipment` (i.e., accessing columns by header name).

::: msl.equipment.schema
    options:
        filters: ["File", "from_xml", "to_xml", "url", "sha256", "attributes", "comment"]
