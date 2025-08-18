# Schema Classes

Class representations of the [XML Schema Definition](https://mslnz.github.io/equipment-register-schema/latest/){:target="_blank"} for an equipment register.

The primary class is [Register][] which contains a sequence of [Equipment][] classes that are each composed of the following classes:

* [AcceptanceCriteria][]
* [Accessories][]
* [Adjustment][]
* [Alteration][]
* [Component][]
* [Competency][]
* [CompletedTask][]
* [Conditions][]
* [CVDEquation][] (Callendar-Van Dusen equation, uses the [cvdCoefficients][type_cvdCoefficients]{:target="_blank"})
* [Deserialised][] (opposite of [serialised][type_serialised]{:target="_blank"})
* [DigitalReport][]
* [Equation][]
* [File][]
* [Financial][]
* [Firmware][]
* [Maintenance][]
* [Measurand][]
* [PerformanceCheck][]
* [PlannedTask][]
* [QualityManual][]
* [ReferenceMaterials][]
* [Report][]
* [Specifications][]
* [SpecifiedRequirements][]
* [Status][]
* [Table][]

The [Any][] class is used as a base class for elements that are currently represented by the [any][type_any]{:target="_blank"} type in the XML Schema Definition.
