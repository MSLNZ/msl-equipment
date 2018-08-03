=============
MSL-Equipment
=============

The purpose of **MSL-Equipment** is to help facilitate the management and the control of equipment in the laboratory.
It aims to achieve this by requiring that information about the equipment that is used in the laboratory is kept in
a centralized (and ideally updated) database. It allows for easily sharing equipment between research teams without
any downtime in learning how to establish communication to the borrowed equipment. Therefore, you can be confident
whether the equipment that was used for a project meets the calibration requirements needed to obtain the desired
measurement uncertainty and you can spend your time acquiring and analysing data rather than figuring out how to
query, for example, a ``*IDN?`` command from the equipment.

Three items are used by **MSL-Equipment** to help organise, share and communicate with equipment that is available
in the laboratory to perform a measurement

1. :ref:`configuration_file`

and two different types of :ref:`database`

2. :ref:`equipment_database`
3. :ref:`connection_database`

The following example illustrates a configuration file that specifies a database containing 6 Digital Multimeter's
that are available in a lab which can be used to measure a voltage. The person performing the measurement specifies
which of the Digital Multimeter's they are using as an **<equipment>** XML tag in the configuration file. They load the
configuration file using the :obj:`~msl.equipment.config.Config` class, which is the main entryway in to the
**MSL-Equipment** package.

The `configuration file`_ that specifies the example_ database to load and the Digital Multimeter to use for the
voltage measurement is as follows:

.. literalinclude:: ../msl/examples/equipment/example.xml
   :language: xml

Load the example_ database from the `configuration file`_:

.. code-block:: pycon

  >>> from msl.equipment import Config
  >>> cfg = Config('msl/examples/equipment/example.xml')
  >>> db = cfg.database()

Once you have a reference to the :obj:`~msl.equipment.config.Config.database` you have access to all the records in
the :ref:`equipment_database` and in the :ref:`connection_database`. To access the **Keysight 34465A** [#f1]_
:class:`~msl.equipment.record_types.EquipmentRecord` in the example_ database (which is known by the ``dmm`` alias that
is specified in the `configuration file`_) use:

.. code-block:: pycon

  >>> db.equipment['dmm']
  EquipmentRecord<Keysight|34465A|MY54506462>

Connect to the **Keysight 34465A** [#f1]_ Digital Multimeter and query the ``*IDN?`` command:

.. code-block:: pycon

  >>> dmm = db.equipment['dmm'].connect()
  >>> dmm.query('*IDN?')
  'Keysight Technologies,34465A,MY54506462,A.02.14-02.40-02.14-00.49-03-01\n'

For more examples of what a :ref:`configuration_file` or the :ref:`database` can look like or how to use
**MSL-Equipment** in your own application see the :ref:`examples`. The :ref:`api` also shows a more detailed
example that loads the same `configuration file`_.

========
Contents
========

.. toctree::
   :maxdepth: 1

   Configuration File <config>
   Database Formats <database>
   Install <install>
   MSL Resources <resources>
   API Documentation <api>
   Examples <examples>
   License <license>
   Authors <authors>
   Release Notes <changelog>

=====
Index
=====

* :ref:`modindex`

.. _configuration file: https://github.com/MSLNZ/msl-equipment/tree/master/msl/examples/equipment/example.xml
.. _example: https://github.com/MSLNZ/msl-equipment/tree/master/msl/examples/equipment/example.xlsx

.. [#f1] Companies that sell equipment that is used for scientific research are identified in this guide in order
         to illustrate how to adequately use **MSL-Equipment** in your own application. Such identification is not
         intended to imply recommendation or endorsement by the Measurement Standards Laboratory of New Zealand,
         nor is it intended to imply that the companies identified are necessarily the best for the purpose.
