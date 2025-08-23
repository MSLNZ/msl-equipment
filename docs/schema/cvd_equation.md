# CVDEquation

The Callendar-Van Dusen (CVD) equation describes the relationship between resistance, $R$, and temperature, $t$, of platinum resistance thermometers (PRT). It is defined in two temperature ranges

$$
\frac{R(t)}{R_0} = \begin{cases}
    1 + A \cdot t + B \cdot t^2 + D \cdot t^3 & R(t) \geq R_0 \\
    1 + A \cdot t + B \cdot t^2 + C \cdot t^3 \cdot (t-100) & R(t) \lt R_0 \\
\end{cases}
$$

where, $R_0 = R(0~^{\circ}\text{C})$ is the resistance at $t=0~^{\circ}\text{C}$ and $A$, $B$, $C$ and $D$ are the CVD coefficients. The $D$ coefficient is typically zero but may be non-zero if $t \gtrsim 200~^{\circ}\text{C}$.

<!--
>>> from msl.equipment import CVDEquation, Evaluable, Range
>>> cvd = CVDEquation(
...     R0=100.0189,
...     A=3.913e-3,
...     B=-6.056e-7,
...     C=1.372e-12,
...     D=0.0,
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
  <D>0</D>
  <uncertainty variables="">0.0056/2</uncertainty>
  <range>
    <minimum>-10</minimum>
    <maximum>70</maximum>
  </range>
</cvdCoefficients>
```

You can access the *CVD coefficients*, *degrees of freedom* and *comment* as attributes of `cvd`,

```pycon
>>> cvd.R0
100.0189
>>> cvd.A
0.003913
>>> cvd.B
-6.056e-07
>>> cvd.C
1.372e-12
>>> cvd.D
0.0
>>> cvd.degree_freedom
inf
>>> cvd.comment
''

```

evaluate the uncertainty,

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

A number or any sequence of numbers, i.e., a [list][]{:target="_blank"}, [tuple][]{:target="_blank"} or [ndarray][numpy.ndarray]{:target="_blank"} may be used to calculate the temperature or resistance *(tip: using [ndarray][numpy.ndarray]{:target="_blank"} will improve performance since a copy of the values is not required)*.

When calculating resistance or temperature, the values of the inputs are checked to ensure that the values are within the range that the CVD coefficients are valid for. The XML data above shows that the temperature must be in the range $-10~^\circ\text{C}$ to $70~^\circ\text{C}$, which has a corresponding resistance range of $96.099~\Omega$ to $127.118~\Omega$ from the equation above. If you calculate resistance from $t=-10.2~^\circ\text{C}$ or temperature from $R=96.0~\Omega$ a [ValueError][]{:target="_blank"} is raised, since the value is outside the range.

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

::: msl.equipment.schema.CVDEquation
    options:
        show_root_full_path: false
        show_root_heading: true
