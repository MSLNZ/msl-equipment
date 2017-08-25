=============
MSL-Equipment
=============

This package is used to help manage and connect to equipment in the laboratory.

Three items are used by **MSL-Equipment** to help organise (and share) equipment that is available in the laboratory to
perform a measurement

1. :ref:`configuration`

and two different types of :ref:`database`

2. :ref:`equipment_database`
3. :ref:`connection_database`

The following example illustrates a configuration file that specifies a database containing 6 Digital Multimeter's
that are available in a lab which can be used to measure a voltage. The person performing the measurement specifies
which of the Multimeter's they are using as an **<equipment>** XML tag in the configuration file. They load the
configuration file using the :obj:`~msl.equipment.config.Config` class, which is the main gateway into the
**MSL-Equipment** package.

The `configuration file`_ that specifies the example_ database to load and the Digital Multimeter to use for the voltage
measurement is as follows:

.. literalinclude:: ../msl/examples/equipment/example.xml
   :language: xml

Load the example_ database from the `configuration file`_:

.. code-block:: python

  >>> from msl.equipment import Config
  >>> cfg = Config('msl/examples/equipment/example.xml')
  >>> db = cfg.database()

Once you have a reference to the :obj:`~msl.equipment.config.Config.database` you have access to all the records in
the :ref:`equipment_database` and in the :ref:`connection_database`. To access the **Keysight 34465A**
:class:`~msl.equipment.record_types.EquipmentRecord` in the example_ database (which is known by the *dmm* alias that
is specified in the `configuration file`_) use:

.. code-block:: python

  >>> db.equipment['dmm']
  EquipmentRecord<Keysight|34465A|MY54506462>
  >>> db.equipment['dmm'].manufacturer
  'Keysight'

Connect to the Digital Multimeter and query the ``*IDN?`` command:

.. code-block:: python

  >>> dmm = db.equipment['dmm'].connect()
  >>> dmm.query('*IDN?')
  'Keysight Technologies,34465A,MY54506462,A.02.14-02.40-02.14-00.49-03-01\n'

For more examples of what a configuration file or a database can look like or how to use **MSL-Equipment** in your own
application see the :ref:`examples`.

========
Contents
========

.. toctree::
   :maxdepth: 1

   Configuration File <config>
   Database Formats <database>
   Install <install>
   Examples <examples>
   MSL Resources <resources>
   API Documentation <api>
   License <license>
   Authors <authors>
   Release Notes <changelog>

=====
Index
=====

* :ref:`modindex`

.. _configuration file: https://github.com/MSLNZ/msl-equipment/tree/master/msl/examples/equipment/example.xml
.. _example: https://github.com/MSLNZ/msl-equipment/tree/master/msl/examples/equipment/example.xlsx
