========================
Welcome to MSL-Equipment
========================

|docs|

Purpose
-------

The purpose of **MSL-Equipment** is to help facilitate the management and the control of equipment in the laboratory.
It aims to achieve this by requiring that information about the equipment that is used in the laboratory is kept in
a centralized (and ideally updated) database. It allows for easily sharing equipment between research teams without
any downtime in learning how to establish communication to the borrowed equipment. Therefore, you can be confident
whether the equipment that was used for a project meets the calibration requirements needed to obtain the desired
measurement uncertainty and you can spend your time acquiring and analysing data rather than figuring out how to
query, for example, a ``*IDN?`` command from the equipment.

Install
-------

To install **MSL-Equipment** run:

.. code-block:: console

   pip install https://github.com/MSLNZ/msl-equipment/archive/main.zip

Alternatively, using the `MSL Package Manager`_ run:

.. code-block:: console

   msl install equipment

Compatibility
-------------
**MSL-Equipment** is tested with Python 2.7, 3.5+. However, some of the resources_ might not work in your
application because the resource might depend on an external dependency (e.g., the SDK provided by a manufacturer)
and this external dependency might not be available for your operating system.

Documentation
-------------
The documentation for **MSL-Equipment** can be found
`here <https://msl-equipment.readthedocs.io/en/latest/index.html>`_.

.. |docs| image:: https://readthedocs.org/projects/msl-equipment/badge/?version=latest
   :target: https://msl-equipment.readthedocs.io/en/latest/
   :alt: Documentation Status
   :scale: 100%

.. _MSL Package Manager: https://msl-package-manager.readthedocs.io/en/latest/
.. _resources: https://msl-equipment.readthedocs.io/en/latest/resources.html
