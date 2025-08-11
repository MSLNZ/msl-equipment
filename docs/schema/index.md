# Schema Classes

Class representations of the [XML Schema Definition](https://mslnz.github.io/equipment-register-schema/latest/){:target="_blank"} for an equipment register.

The primary class is [Equipment][msl.equipment.schema.Equipment] which may contain the following classes:

* [AcceptanceCriteria][msl.equipment.schema.AcceptanceCriteria]
* [Accessories][msl.equipment.schema.Accessories]
* [Adjustment][msl.equipment.schema.Adjustment]
* [Alteration][msl.equipment.schema.Alteration]
* [Competency][msl.equipment.schema.Competency]
* [CompletedTask][msl.equipment.schema.CompletedTask]
* [Conditions][msl.equipment.schema.Conditions]
* [CVDEquation][cvdequation] (Callendar-Van Dusen equation, uses the [cvdCoefficients][type_cvdCoefficients]{:target="_blank"})
* [Deserialised][msl.equipment.schema.Deserialised] (opposite of [serialised][type_serialised]{:target="_blank"})
* [DigitalReport][digitalreport]
* [Equation][equation]
* [File][msl.equipment.schema.File]
* [Financial][msl.equipment.schema.Financial]
* [Firmware][msl.equipment.schema.Firmware]
* [Maintenance][msl.equipment.schema.Maintenance]
* [Measurand][msl.equipment.schema.Measurand]
* [PlannedTask][msl.equipment.schema.PlannedTask]
* [QualityManual][msl.equipment.schema.QualityManual]
* [ReferenceMaterials][msl.equipment.schema.ReferenceMaterials]
* [Specifications][msl.equipment.schema.Specifications]
* [SpecifiedRequirements][msl.equipment.schema.SpecifiedRequirements]
* [Status][msl.equipment.schema.Status]
* [Table][table]

The [Any][msl.equipment.schema.Any] class is used as a base class for elements that are currently represented by the [any][type_any]{:target="_blank"} type in the XML Schema Definition.
