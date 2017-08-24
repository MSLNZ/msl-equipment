=============
MSL-Equipment
=============

This package is used to help manage and connect to equipment in the laboratory.

Three items are used by **MSL-Equipment** to help organise (and share) equipment that is available in the laboratory to
perform a measurement:

1. A :ref:`configuration`
2. An :ref:`equipment_database`
3. A :ref:`connection_database`

The following example illustrates a configuration file that specifies a database containing 6 Digital Multimeter's
that are available in a lab which can be used to measure a voltage. The person performing the measurement specifies
which of the Multimeter's they are using as an **<equipment>** XML tag in the configuration file.

The `configuration file`_ that specifies the example database_ to load and the Digital Multimeter to use for the voltage
measurement is as follows:

.. literalinclude:: ../msl/examples/equipment/example.xml
   :language: xml

Load the example database_ from the `configuration file`_:

.. code-block:: python

  >>> from msl.equipment import Config
  >>> cfg = Config('msl/examples/equipment/example.xml')
  >>> db = cfg.database()

Access the **Keysight 34465A** equipment record in the database_ (known by the *dmm* alias that is specified in the
`configuration file`_) which is an :class:`~msl.equipment.record_types.EquipmentRecord` object:

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

Since the equipment that the person is using to perform the measurement is specified in a configuration file, if the
they decide that they need to use a Digital Multimeter with more precision then they do not modify their code, but
update the *model* number of the **<equipment>** tag in the `configuration file`_ to select the appropriate Digital
Multimeter from the database_.

For more examples of what a configuration file or a database can look like see the :ref:`examples`.

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
   API <api>
   License <license>
   Authors <authors>
   Release Notes <changelog>

=====
Index
=====

* :ref:`modindex`

.. _configuration file: https://github.com/MSLNZ/msl-equipment/tree/master/msl/examples/equipment/example.xml
.. _database: https://github.com/MSLNZ/msl-equipment/tree/master/msl/examples/equipment/example.xlsx
