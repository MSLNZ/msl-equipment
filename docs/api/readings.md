# Readings

The [Readings][msl.equipment.readings.Readings] class may be used after requesting measurement data from equipment. It calculates the mean, standard deviation and the standard deviation of the mean and provides a user-friendly way to display the information.

<!--
>>> class Connection:
...     def query(self, ignore):
...         return " 8.000167847E+00, 8.000164032E+00, 8.000163241E+00, 8.000165864E+00, 8.000164893E+00\r\n"
>>> dmm = Connection()

-->

Suppose we have a [Connection][connections] to a digital multimeter, `dmm`, and we fetch some readings

```pycon
>>> data = dmm.query("FETCH?")
>>> data
' 8.000167847E+00, 8.000164032E+00, 8.000163241E+00, 8.000165864E+00, 8.000164893E+00\r\n'

```

We can create a [Readings][msl.equipment.readings.Readings] instance from the fetched data and then get statistical information about the data

```pycon
>>> from msl.equipment import Readings
>>> r = Readings(data)
>>> r.mean
8.0001651754
>>> r.std
1.784701179552952e-06
>>> r.std_mean
7.981426314008917e-07
>>> len(r)
5

```

We can treat the readings as a numpy [ndarray][numpy.ndarray] and call [ndarray][numpy.ndarray] attributes

```pycon
>>> print(r.max())
8.000167847
>>> print(r.min())
8.000163241

```

or access the numpy [ndarray][numpy.ndarray] directly

```pycon
>>> r.data
array([8.00016785, 8.00016403, 8.00016324, 8.00016586, 8.00016489])

```

Unpacking the [Readings][msl.equipment.readings.Readings] instance returns the mean and the standard deviation of the mean

```pycon
>>> mean, std_mean = r
>>> mean
8.0001651754
>>> std_mean
7.981426314008917e-07

```

When converting the [Readings][msl.equipment.readings.Readings] to a string, the custom [format specification][] is used and it displays the value (mean) with the uncertainty (standard deviation of the mean)

```pycon
>>> f"{r}" # use the default options
'8.00016518(80)'
>>> f"{r:.2B}" # equivalent to previous
'8.00016518(80)'
>>> f"{r:.3PU}"  # retain 3 digits, +/- mode, unicode style
'8.000165175±0.000000798'

```

## Format Specification

The format specification is similar to the built-in Python [specification][formatspec], but with additional options (*mode*, *style* and *si*). The number of significant digits for the value (mean) and the uncertainty (standard deviation of the mean) can be controlled, based on the uncertainty.

The grammar for the format specification is defined as,

```
[[fill]align][sign][z][#][0][width][grouping][.digits][type][mode][style][si]
```

where we note the use of *digits* (not *precision*) and the additional *mode*, *style* and *si* options. *digits* refers to the number of significant digits to retain in the uncertainty. The *mode* option specifies how the value and the uncertainty are separated: `B` (bracket mode, default) or `P` (plus-minus sign). There are two *style* options: `L` ($\LaTeX$) or `U` (unicode). The *si* option can only be `S` and if it is specified the appropriate [SI prefix symbol](https://en.wikipedia.org/wiki/Metric_prefix) replaces the Base-10 component.

We can also create a [Readings][] instance by specifying the mean, standard deviation and size keyword arguments

```pycon
>>> r = Readings(mean=3.4562e-6, std=4.218e-8, size=10)
>>> r.mean
3.4562e-06
>>> r.std
4.218e-08
>>> r.std_mean  # 4.218e-8 / sqrt(10)
1.3338487170590222e-08

```

Here are some examples on how to use the custom format specification

```pycon
>>> f"{r}"  # default is to retain 2 digits with bracket mode
'0.000003456(13)'
>>> f"{r:P}"  # +/- mode
'0.000003456+/-0.000000013'
>>> f"{r:PU}"  # +/- mode, unicode style
'0.000003456±0.000000013'
>>> f"{r:e}"  # exponent form
'3.456(13)e-06'
>>> f"{r:S}" # SI prefix
'3.456(13) u'
>>> f"{r:US}" # unicode style, SI prefix
'3.456(13) µ'
>>> f"{r:.1eU}" # 1 digit, exponent form, unicode style
'3.46(1)×10⁻⁶'
>>> f"{r:eL}" # exponent form, LaTeX style
'3.456\\left(13\\right)\\times10^{-6}'
>>> f"{r:=^+30.4e}"  # fill with '=', align center, include + sign, 30 characters in total, 4 digits, exponent form
'======+3.45620(1334)e-06======'

```

If the standard deviation of the mean is zero, the uncertainty component is not included in the output and the format applies only to the mean

```pycon
>>> r = Readings(mean=3.4562e-6, std=0, size=10)
>>> f"{r}"  # default is 2 decimal places in floating-point, f, notation
'0.00'
>>> f"{r:e}"
'3.46e-06'
>>> f"{r:.4e}"  # 4 decimals (uses built-in specification since no custom options are used)
'3.4562e-06'
>>> f"{r:.4eUS}"  # 4 digits (uses custom specification since custom options are included)
'3.456 µ'

```

::: msl.equipment.readings.Readings
    options:
        show_root_full_path: false
        show_root_heading: true
