.. _msl-equipment-welcome:

=============
MSL-Equipment
=============
The purpose of MSL-Equipment is to manage information about equipment that are
required to perform a measurement and to connect to equipment that support
computer control. Three items are used to achieve this purpose

1. :ref:`configuration-file`
2. :ref:`equipment-database`
3. :ref:`connections-database`

The following example uses a `configuration file`_ that specifies an
`equipment-register database`_ (which contains information about all of
the equipment that is available), a `connections database`_ (which contains
information on how to connect to equipment that support computer control), and
specifies a digital multimeter to use for a measurement (which is defined as
an ``<equipment>`` XML element).

Loading the `configuration file`_ using the :class:`~msl.equipment.config.Config`
class is the main entry point

.. invisible-code-block: pycon

   >>> SKIP_IF_PYTHON_LESS_THAN_3_6()
   >>> import os
   >>> cwd = os.getcwd()
   >>> os.chdir('tests/db_files')

.. code-block:: pycon

   >>> from msl.equipment import Config
   >>> cfg = Config('config.xml')

and loading the :ref:`Databases <database-formats>` is done via the
:meth:`~msl.equipment.config.Config.database` method

.. code-block:: pycon

   >>> db = cfg.database()

.. invisible-code-block: pycon

   >>> os.chdir(cwd)

You can access XML elements, attributes and values in the `configuration file`_

.. code-block:: pycon

   >>> cfg.find('max_voltage')
   <Element 'max_voltage' at ...>
   >>> cfg.attrib('max_voltage')
   {'unit': 'V'}
   >>> cfg.value('max_voltage')
   3.3

and all of the :class:`~msl.equipment.record_types.EquipmentRecord`\'s that are
contained within the :ref:`equipment-database` [#f1]_

.. code-block:: pycon

   >>> for record in db.records():
   ...    print(record)
   ...
   EquipmentRecord<Fluke|8506A|cecf2e0a>
   EquipmentRecord<Oriel|66087|169b71e9>
   EquipmentRecord<Kepco|JQE|baee83d4>
   EquipmentRecord<Hewlett Packard|34401A|15ab8c6c>
   EquipmentRecord<Arlunya|Milli Gauss|890a4c02>
   EquipmentRecord<Toledo|1000|444213b7>
   EquipmentRecord<Stanford Research Systems|SR850 DSP|cec817f5>
   EquipmentRecord<HP|3478A|bd92c887>

To select the records that are from Hewlett Packard [#f1]_, specify the
*manufacturer* as a search criteria (supports regex_, so both *HP* and
*Hewlett Packard* will match)

.. code-block:: pycon

   >>> for record in db.records(manufacturer='H.*P'):
   ...    print(record)
   ...
   EquipmentRecord<Hewlett Packard|34401A|15ab8c6c>
   EquipmentRecord<HP|3478A|bd92c887>

Get the :class:`~msl.equipment.record_types.ConnectionRecord`\'s of the equipment
that can be computer controlled

.. code-block:: pycon

   >>> for conn in db.connections():
   ...    print(conn)
   ...
   ConnectionRecord<Fluke|8506A|cecf2e0a>
   ConnectionRecord<Hewlett Packard|34401A|15ab8c6c>
   ConnectionRecord<Stanford Research Systems|SR850 DSP|cec817f5>
   ConnectionRecord<HP|3478A|bd92c887>

or filter by the equipment that use GPIB as the communication bus and that are
from Hewlett Packard [#f1]_

.. code-block:: pycon

   >>> for conn in db.connections(address='GPIB', manufacturer='H.*P'):
   ...     print(conn)
   ...
   ConnectionRecord<HP|3478A|bd92c887>

Access the :class:`~msl.equipment.record_types.EquipmentRecord` that has the
specified alias ``dmm`` in the `configuration file`_

.. code-block:: pycon

   >>> record = db.equipment['dmm']
   >>> print(record)
   EquipmentRecord<Hewlett Packard|34401A|15ab8c6c>
   >>> record.is_calibration_due()
   False
   >>> print(record.connection)
   ConnectionRecord<Hewlett Packard|34401A|15ab8c6c>

Establishing a connection to the equipment is achieved by calling the
:meth:`~msl.equipment.record_types.EquipmentRecord.connect` method of an
:class:`~msl.equipment.record_types.EquipmentRecord`. This will return a
specific :class:`~msl.equipment.connection.Connection` subclass that contains
the necessary properties and methods for communicating with the equipment.

.. invisible-code-block: pycon

   >>> import pytest
   >>> pytest.skip('do not connect to HP 34401A')

.. code-block:: pycon

   >>> dmm = record.connect()
   >>> dmm.query('*IDN?')
   'Hewlett Packard,34401A,15ab8c6c,A.02.14-02.40-02.14-00.49-03-01\n'

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

.. _configuration file: https://github.com/MSLNZ/msl-equipment/blob/main/tests/db_files/config.xml
.. _equipment-register database: https://github.com/MSLNZ/msl-equipment/blob/main/tests/db_files/equipment-register.csv
.. _connections database: https://github.com/MSLNZ/msl-equipment/blob/main/tests/db_files/connections.csv
.. _regex: https://www.regular-expressions.info/

.. [#f1] Companies that sell equipment that is used for scientific research are identified in this guide in order
         to illustrate how to adequately use MSL-Equipment in your own application. Such identification is not
         intended to imply recommendation or endorsement by the Measurement Standards Laboratory of New Zealand,
         nor is it intended to imply that the companies identified are necessarily the best for the purpose.
