# Equation

<!--
>>> from msl.equipment import Equation, Evaluable, Range
>>> equation = Equation(
...     value=Evaluable(
...         equation="r-0.71-0.04*r+3.4e-4*pow(r,2)+2.4e-3*t+1.3e-3*r*t",
...         variables=("r", "t"),
...         ranges={"r": Range(30, 80), "t": Range(15, 25)},
...     ),
...     uncertainty=Evaluable(equation="0.355"),
...     unit="%rh",
... )

-->

Suppose you have a variable named `equation` (which is an instance of [Equation][msl.equipment.schema.Equation]) that represents the following information in an equipment register for equipment that measures relative humidity. The corrected value depends on two variables (`r` and `t`) and the standard uncertainty is a constant.

```xml
<equation>
  <value variables="r t">r-0.71-0.04*r+3.4e-4*pow(r,2)+2.4e-3*t+1.3e-3*r*t</value>
  <uncertainty variables="">0.355</uncertainty>
  <unit>%rh</unit>
  <ranges>
    <range variable="r">
      <minimum>30</minimum>
      <maximum>80</maximum>
    </range>
    <range variable="t">
      <minimum>15</minimum>
      <maximum>25</maximum>
    </range>
  </ranges>
</equation>
```

You can access the *unit*, *degrees of freedom* and *comment* as attributes of `equation`

```pycon
>>> equation.unit
'%rh'
>>> equation.degree_freedom
inf
>>> equation.comment
''

```

To evaluate an equation, call the appropriate attribute with the variable(s) that are required to evaluate the equation with

```pycon
>>> equation.value.variables
('r', 't')
>>> equation.uncertainty.variables
()
>>> assert equation.value(r=50.3, t=20.4) == 49.8211466
>>> assert equation.uncertainty() == 0.355

```

A variable can have multiple values. Any sequence of numbers, i.e., a [list][]{:target="_blank"}, [tuple][]{:target="_blank"}, [ndarray][numpy.ndarray]{:target="_blank"}, etc., may be used *(tip: using [ndarray][numpy.ndarray]{:target="_blank"} will improve performance since a copy of the values is not required)*,

```pycon
>>> equation.value(r=[50.3, 52.1, 48.7], t=[20.4, 19.7, 20.0])
array([49.8211466, 51.6104604, 48.1625746])

```

the values of the variables do not need to be 1-dimensional arrays,

```pycon
>>> equation.value(r=[(50.3, 52.1), (48.7, 47.9)], t=[(20.4, 19.7), (20.0, 19.6)])
array([[49.8211466, 51.6104604],
       [48.1625746, 47.3216314]])

```

and the array broadcasting rules of numpy also apply, i.e., multiple `r` values and a single `t` value

```pycon
>>> equation.value(r=(50.3, 52.1, 48.7), t=20.4)
array([49.8211466, 51.6595514, 48.1888586])

```

If you forget to specify a variable (in the following case, `t`) a [NameError][]{:target="_blank"} will be raised,

```pycon
>>> equation.value(r=50.3)
Traceback (most recent call last):
...
NameError: name 't' is not defined

```

however, if you specify more variables than are required to evaluate the equation, the additional variables are ignored
```pycon
>>> equation.uncertainty(r=50.3, t=20.4)
array(0.355)

```

Notice in the last returned value that the result was printed as `array(0.355)` even though a single `r` and `t` value was specified *(although these variables were ignored in this particular example, since the standard uncertainty is a constant, the principle remains the same if they were not ignored)*. All evaluated returned types are an instance of a numpy [ndarray][numpy.ndarray]{:target="_blank"} even if a single value is specified. These particular returned array instances are referred to as 0-dimensional [array scalars][arrays.scalars]{:target="_blank"} in numpy terminology.

When evaluating an equation, the value(s) of the input variables are checked to ensure that the value(s) are within the ranges that the equation is valid for. The XML data above shows that the temperature, `t`, value must be in the range `15` to `25`. If you evaluate the corrected value at `t=30` a [ValueError][]{:target="_blank"} is raised

```pycon
>>> equation.value.ranges
{'r': Range(minimum=30, maximum=80), 't': Range(minimum=15, maximum=25)}
>>> equation.value(r=50.3, t=30)
Traceback (most recent call last):
...
ValueError: The value 30.0 is not within the range [15, 25]

```

You can bypass range checking by including a `check_range=False` keyword argument

```pycon
>>> equation.value(r=50.3, t=30, check_range=False)
array(50.4719306)

```

::: msl.equipment.schema.Equation
    options:
        show_root_full_path: false
        show_root_heading: true

::: msl.equipment.schema.Evaluable
    options:
        show_root_full_path: false
        show_root_heading: true

::: msl.equipment.schema.Range
    options:
        show_root_full_path: false
        show_root_heading: true
