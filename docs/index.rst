.. _msl-equipment-welcome:

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

1. :ref:`configuration-file`

and two different types of :ref:`database-formats`

2. :ref:`equipment-database`
3. :ref:`connections-database`

The following example uses a `configuration file`_ that specifies a `registry database`_ containing
3 digital multimeters that are available in a lab which can be used to measure a voltage. The information
about how to connect to the equipment is found in a `connections database`_.

You specify which of the digital multimeters you are using as an ``<equipment>`` element in the `configuration file`_.

Loading the `configuration file`_ using the :class:`~msl.equipment.config.Config` class is the main entryway
in to the **MSL-Equipment** package:

.. code-block:: pycon

  >>> from msl.equipment import Config
  >>> cfg = Config('/path/to/config.xml') # doctest: +SKIP
  >>> db = cfg.database() # doctest: +SKIP

Once you have a reference to the :meth:`~msl.equipment.config.Config.database` you have access to all the records in
the :ref:`equipment-database` and in the :ref:`connections-database`. To access the **Hewlett Packard 34401A** [#f1]_
:class:`~msl.equipment.record_types.EquipmentRecord` in the `registry database`_ (which is known by the ``dmm``
alias that is specified in the `configuration file`_) use:

.. code-block:: pycon

  >>> db.equipment['dmm'] # doctest: +SKIP
  EquipmentRecord<Hewlett Packard|34401A|D10011>

Connect to the **Hewlett Packard 34401A** [#f1]_ digital multimeter and query the ``*IDN?`` command:

.. code-block:: pycon

  >>> dmm = db.equipment['dmm'].connect() # doctest: +SKIP
  >>> dmm.query('*IDN?') # doctest: +SKIP
  'Hewlett Packard,34401A,D10011,A.02.14-02.40-02.14-00.49-03-01'

For more examples of what a :ref:`configuration-file` or a :ref:`database-formats` can look like or how to use
**MSL-Equipment** in your own application see the :ref:`equipment-examples`. The :ref:`equipment-api` also
shows a more detailed example that loads the same `configuration file`_.

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

.. _configuration file: https://github.com/MSLNZ/msl-equipment/tree/main/msl/examples/equipment/example.xml
.. _registry database: https://github.com/MSLNZ/msl-equipment/tree/main/msl/examples/equipment/equipment-register.csv
.. _connections database: https://github.com/MSLNZ/msl-equipment/tree/main/msl/examples/equipment/connections.csv


.. [#f1] Companies that sell equipment that is used for scientific research are identified in this guide in order
         to illustrate how to adequately use **MSL-Equipment** in your own application. Such identification is not
         intended to imply recommendation or endorsement by the Measurement Standards Laboratory of New Zealand,
         nor is it intended to imply that the companies identified are necessarily the best for the purpose.
