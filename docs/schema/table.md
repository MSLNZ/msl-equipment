# Table

<!--
>>> from xml.etree.ElementTree import XML
>>> import numpy as np
>>> from msl.equipment import Table
>>> text = """
... <table comment="Spectral">
...   <type>   int       ,    double ,    double     </type>
...   <unit>   nm        ,    W/m^2  ,    W/m^2      </unit>
...   <header> Wavelength, Irradiance, u(Irradiance) </header>
...   <data>   250       ,    0.01818,   0.02033
...            300       ,    0.18478,   0.01755
...            350       ,    0.80845,   0.01606
...            400       ,    2.21355,   0.01405
...            450       ,    4.49004,   0.01250
...            500       ,    7.45135,   0.01200
...            550       ,   10.75753,   0.01152
...            600       ,   14.03809,   0.01102
...            650       ,   16.99469,   0.01103
...            700       ,   19.44093,   0.01077
...   </data>
... </table>
... """
>>> table = Table.from_xml(XML(text))

-->

Suppose you have a variable named `table` (which is an instance of [Table][msl.equipment.schema.Table]) that represents the following information in an equipment register for equipment that measures spectral irradiance

```xml
<table comment="Spectral">
  <type>   int       ,    double ,    double     </type>
  <unit>   nm        ,    W/m^2  ,    W/m^2      </unit>
  <header> Wavelength, Irradiance, u(Irradiance) </header>
  <data>   250       ,    0.01818,   0.02033
           300       ,    0.18478,   0.01755
           350       ,    0.80845,   0.01606
           400       ,    2.21355,   0.01405
           450       ,    4.49004,   0.01250
           500       ,    7.45135,   0.01200
           550       ,   10.75753,   0.01152
           600       ,   14.03809,   0.01102
           650       ,   16.99469,   0.01103
           700       ,   19.44093,   0.01077
  </data>
</table>
```

The `table` instance is a numpy [structured array][structured_arrays]{:target="_blank"} that has the *header* values as the *field name* of each column

```pycon
>>> table.header
array(['Wavelength', 'Irradiance', 'u(Irradiance)'], dtype='<U13')
>>> table["Wavelength"]
Table([250, 300, 350, 400, 450, 500, 550, 600, 650, 700])
>>> table.types["Wavelength"]
array(dtype('int64'), dtype=object)
>>> assert table.units["Wavelength"] == "nm"

```

Since `table` is a numpy array, you can index it

```pycon
>>> print(table[0])
(250, 0.01818, 0.02033)
>>> sliced=table[:3]
>>> sliced
Table([(250, 0.01818, 0.02033), (300, 0.18478, 0.01755),
       (350, 0.80845, 0.01606)],
      dtype=[('Wavelength', '<i8'), ('Irradiance', '<f8'), ('u(Irradiance)', '<f8')])

```

and notice that the returned instance fo `sliced` is another [Table][msl.equipment.schema.Table] instance, so the attributes of [Table][msl.equipment.schema.Table] are available

```pycon
>>> sliced.comment
'Spectral'

```

as well as perform mathematical operations and call numpy functions directly with the `table` instance

```pycon
>>> np.cos(1 + table["Irradiance"])
Table([ 0.52491592,  0.37650087, -0.2354229 , -0.99741219,  0.70160756,
       -0.56246854,  0.6903377 , -0.78390036,  0.65631968, -0.0205763 ])

```

Suppose you wanted to get all Irradiance values in the table that are for UV light (i.e., wavelengths &lt; 400 nm)

```pycon
>>> table["Irradiance"][ table["Wavelength"] < 400 ]
Table([0.01818, 0.18478, 0.80845])

```

If you prefer to work with *unstructured* data, you can convert the `table` by calling the [unstructured][msl.equipment.schema.Table.unstructured] method

```pycon
>>> unstructured = table.unstructured()
>>> unstructured
Table([[2.500000e+02, 1.818000e-02, 2.033000e-02],
       [3.000000e+02, 1.847800e-01, 1.755000e-02],
       [3.500000e+02, 8.084500e-01, 1.606000e-02],
       [4.000000e+02, 2.213550e+00, 1.405000e-02],
       [4.500000e+02, 4.490040e+00, 1.250000e-02],
       [5.000000e+02, 7.451350e+00, 1.200000e-02],
       [5.500000e+02, 1.075753e+01, 1.152000e-02],
       [6.000000e+02, 1.403809e+01, 1.102000e-02],
       [6.500000e+02, 1.699469e+01, 1.103000e-02],
       [7.000000e+02, 1.944093e+01, 1.077000e-02]])
>>> print(unstructured[0, 0])
250.0

```

::: msl.equipment.schema
    options:
        filters: ["Table", "from_xml", "to_xml", "__new__", "types", "units", "header", "comment", "unstructured"]
