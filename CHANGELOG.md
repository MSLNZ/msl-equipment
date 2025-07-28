# Release Notes

---

## 0.2.0 (2025-03-28)

***Added:***

- support for Python 3.12 and 3.13
- `find-equipment` console script
- `msl.equipment.connection_gpib.ConnectionGPIB` class
- `msl.equipment.resources.greisinger.gmh3000.GMH3000` resource
- `msl.equipment.resources.isotech.millik.MilliK` resource
- `msl.equipment.resources.vaisala.ptu300.PTU300` resource
- `msl.equipment.resources.vaisala.ptb330.PTB330` resource

***Fixed:***

- issue [#9](https://github.com/MSLNZ/msl-equipment/issues/9) &mdash; Missing functions from Avantes AvaSpec DLL
- issue [#8](https://github.com/MSLNZ/msl-equipment/issues/8) &mdash; Invalid URL for LXI XML identification document

***Removed:***

- support for Python 2.7, 3.5, 3.6 and 3.7

## 0.1.0 (2023-06-18)

Initial release.

It is also the last release to support Python 2.7, 3.5, 3.6 and 3.7
