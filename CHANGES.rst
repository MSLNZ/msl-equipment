=============
Release Notes
=============

Version 0.2.0 (in development)
==============================

* Added

  - support for Python 3.12
  - ``find-equipment`` console script
  - :class:`~msl.equipment.connection_gpib.ConnectionGPIB` class
  - :class:`~msl.equipment.resources.greisinger.gmh3000.GMH3000` resource
  - :class:`~msl.equipment.resources.isotech.millik.MilliK` resource
  - :class:`~msl.equipment.resources.vaisala.ptu300.PTU300` resource
  - :class:`~msl.equipment.resources.vaisala.ptb330.PTB330` resource

* Fixed

  - issue `#9 <https://github.com/MSLNZ/msl-equipment/issues/9>`_ - Missing functions
    from Avantes AvaSpec DLL
  - issue `#8 <https://github.com/MSLNZ/msl-equipment/issues/8>`_ - Invalid URL
    for LXI XML identification document

* Removed

  - support for Python 2.7, 3.5, 3.6 and 3.7

Version 0.1.0 (2023-06-18)
==========================
Initial release.

It is also the last release to support Python 2.7, 3.5, 3.6 and 3.7
