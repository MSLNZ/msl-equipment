=============
MSL-Equipment
=============

|docs| |github tests|

The purpose of MSL-Equipment is to manage information about equipment that are
required to perform a measurement and to connect to equipment that support
computer control.

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
**MSL-Equipment** is tested with Python 2.7, 3.5+ on Windows, Linux and macOS.
However, some of the resources_ might not work for your application because the
resource may depend on an external dependency (e.g., the SDK provided by a
manufacturer) and this external dependency might not be available for your
operating system.

Documentation
-------------
The documentation for **MSL-Equipment** can be found
`here <https://msl-equipment.readthedocs.io/en/latest/index.html>`_.

.. |docs| image:: https://readthedocs.org/projects/msl-equipment/badge/?version=latest
   :target: https://msl-equipment.readthedocs.io/en/latest/
   :alt: Documentation Status
   :scale: 100%

.. |github tests| image:: https://github.com/MSLNZ/msl-equipment/actions/workflows/run-tests.yml/badge.svg
   :target: https://github.com/MSLNZ/msl-equipment/actions/workflows/run-tests.yml

.. _MSL Package Manager: https://msl-package-manager.readthedocs.io/en/stable/
.. _resources: https://msl-equipment.readthedocs.io/en/latest/resources.html
