# Getting Started

Three concepts are used by `msl-equipment`

1. [Equipment registers][] &mdash; to comply with the [ISO/IEC 17025](https://www.iso.org/ISO-IEC-17025-testing-and-calibration-laboratories.html){:target="_blank"} standard
2. [Connections][] &mdash; to interface with equipment for computer control
3. [Configuration files][] &mdash; define requirements for a measurement (links items 1 and 2 together)

You do not need to use all three concepts for your application. You can choose to only use the [equipment-register classes][schema-classes] to help manage information about the equipment in your laboratory and use a different Python package to communicate with the equipment. Similarly, you can choose to use one of the supported [backends][connections-backend] for communication. You do not need to use `msl-equipment` at all. Since an equipment register is written in the eXtensible Markup Language (XML) file format, it may be parsed by many programming languages. This allows people to share a common equipment register and use different programming languages to read information from the same equipment register.
