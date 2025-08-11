# CVDEquation

The Callendar-Van Dusen (CVD) equation describes the relationship between resistance, $R$, and temperature, $T$, of platinum resistance thermometers (PRT). It is typically defined in two temperature ranges

$$
\frac{R(T)}{R_0} = \begin{cases}
    1 + A \cdot T + B \cdot T^2 & 0~^{\circ}\text{C} \leq T \lt 661~^{\circ}\text{C} \\
    1 + A \cdot T + B \cdot T^2 + C \cdot (T-100) \cdot T^3 & -200~^{\circ}\text{C} \lt T \lt 0~^{\circ}\text{C} \\
\end{cases}
$$

<!--
>>> from msl.equipment import CVDEquation, Evaluable, Range
>>> cvd = CVDEquation(
...     R0=100.0189,
...     A=3.913e-3,
...     B=-6.056e-7,
...     C=1.372e-12,
...     uncertainty=Evaluable(equation="0.0026"),
...     ranges={"t": Range(-10, 70), "r": Range(96.099, 127.118)},
... )

-->

Suppose you have a variable named `cvd` (which is an instance of [CVDEquation][msl.equipment.schema.CVDEquation]) that represents the following information in an equipment register for a PRT

```xml
<cvdCoefficients>
  <R0>100.0189</R0>
  <A>3.913e-3</A>
  <B>-6.056e-7</B>
  <C>1.372e-12</C>
  <uncertainty variables="">0.0056/2</uncertainty>
  <range>
    <minimum>-10</minimum>
    <maximum>70</maximum>
  </range>
</cvdCoefficients>
```

You can access the *CVD coefficients*, *degrees of freedom* and *comment* as attributes of `cvd`

```pycon
>>> cvd.R0
100.0189
>>> cvd.A
0.003913
>>> cvd.B
-6.056e-07
>>> cvd.C
1.372e-12
>>> cvd.degree_freedom
inf
>>> cvd.comment
''

```

You can evaluate the uncertainty,

```pycon
>>> print(cvd.uncertainty())
0.0026

```

calculate resistance from temperature,

```pycon
>>> print(cvd.resistance(12.4))
104.86262358516764
>>> cvd.resistance([-5, 0, 5, 10, 15, 20, 25])
array([ 98.06051774, 100.0189    , 101.97425549, 103.92658241,
       105.87588076, 107.82215054, 109.76539174])

```

and calculate temperature from resistance

```pycon
>>> print(cvd.temperature(109.1))
23.287055698724505
>>> cvd.temperature([98.7, 99.2, 100.4, 101.7, 103.8])
array([-3.36816839, -2.09169544,  0.9738958 ,  4.29823964,  9.67558125])

```

Any sequence of numbers, i.e., a [list][]{:target="_blank"}, [tuple][]{:target="_blank"}, [ndarray][numpy.ndarray]{:target="_blank"}, etc., may be used to calculate the temperature or resistance *(tip: using [ndarray][numpy.ndarray]{:target="_blank"} will improve performance since a copy of the values is not required)*.

When calculating resistance or temperature, the value(s) of the inputs are checked to ensure that the value(s) are within the ranges that the CVD coefficients are valid for. The XML data above shows that the temperature must be in the range $-10~^\circ\text{C}$ to $70~^\circ\text{C}$, which has a corresponding resistance range of $96.099~\Omega$ to $127.118~\Omega$ from the equation above. If you calculate resistance from $T=-10.2~^\circ\text{C}$ or temperature from $R=96.0~\Omega$ a [ValueError][]{:target="_blank"} is raised

```pycon
>>> cvd.ranges
{'t': Range(minimum=-10, maximum=70), 'r': Range(minimum=96.099, maximum=127.118)}

>>> cvd.resistance(-10.2)
Traceback (most recent call last):
...
ValueError: The value -10.2 is not within the range [-10, 70]

>>> cvd.temperature(96)
Traceback (most recent call last):
...
ValueError: The value 96.0 is not within the range [96.099, 127.118]

```

You can bypass range checking by including a `check_range=False` keyword argument

```pycon
>>> print(cvd.resistance(-10.2, check_range=False))
96.02059984653798
>>> print(cvd.temperature(96, check_range=False))
-10.252469261526016

```

::: msl.equipment.schema
    options:
        filters: ["CVDEquation", "from_xml", "to_xml", "R0", "^A$", "^B$", "^C$", "uncertainty", "ranges", " degree_freedom", "comment", "^resistance$", "temperature"]
