.. _api:

=================
API Documentation
=================

The main gateway into **MSL-Equipment** is achieved by loading a :ref:`configuration` and that is achieved by
creating a :class:`~msl.equipment.config.Config` object.

.. code-block:: python

  >>> from msl.equipment import Config
  >>> cfg = Config('msl/examples/equipment/example.xml')

Once a :class:`~msl.equipment.config.Config` object exists you can access of all the
:class:`~msl.equipment.record_types.EquipmentRecord`\'s and :class:`~msl.equipment.record_types.ConnectionRecord`\'s
that are contained within the :ref:`Databases <database>` as well as all of the
:obj:`~msl.equipment.database.Database.equipment` that is being used to perform the measurement by calling the
:meth:`~msl.equipment.config.Config.database` method to create an instance of the
:class:`~msl.equipment.database.Database`.

.. code-block:: python

  >>> db = cfg.database()
  >>> for r in db.records():
  ...     print(r)
  EquipmentRecord<Agilent|34420A|D7D59860>
  EquipmentRecord<Keysight|34465A|MY54506462>
  EquipmentRecord<Hewlett Packard|3468A|8BB438A7>
  EquipmentRecord<BK Precision|5492BGPIB|51957DB9>
  EquipmentRecord<Keithley|2002|2CAD4BC6>
  EquipmentRecord<Keysight|3458A|MY24339283>
  >>> for r in db.records(manufacturer='Keysight'):
  ...     print(r)
  EquipmentRecord<Keysight|34465A|MY54506462>
  EquipmentRecord<Keysight|3458A|MY24339283>
  >>> for c in db.connections():
  ...     print(c)
  ConnectionRecord<Agilent|34420A|D7D59860>
  ConnectionRecord<Keysight|34465A|MY54506462>
  ConnectionRecord<Hewlett Packard|3468A|8BB438A7>
  ConnectionRecord<BK Precision|5492BGPIB|51957DB9>
  ConnectionRecord<Keithley|2002|2CAD4BC6>
  ConnectionRecord<Keysight|3458A|MY24339283>
  >>> for c in db.connections(address='USB*'):
  ...     print(c)
  ConnectionRecord<Agilent|34420A|D7D59860>
  ConnectionRecord<Keysight|34465A|MY54506462>
  ConnectionRecord<Keysight|3458A|MY24339283>
  >>> db.equipment
  {'dmm': EquipmentRecord<Keysight|34465A|MY54506462>}
  >>> db.equipment['dmm'].connection
  ConnectionRecord<Keysight|34465A|MY54506462>

Establishing a connection to the :obj:`~msl.equipment.database.Database.equipment` is achieved by calling the
:meth:`~msl.equipment.record_types.EquipmentRecord.connect` method of an
:class:`~msl.equipment.record_types.EquipmentRecord`. This call will return a specific
:class:`~msl.equipment.connection.Connection` subclass that contains the necessary properties and methods for
communicating with the :obj:`~msl.equipment.database.Database.equipment`.

.. code-block:: python

  >>> dmm = db.equipment['dmm'].connect()
  >>> dmm.query('*IDN?')
  'Keysight Technologies,34465A,MY54506462,A.02.14-02.40-02.14-00.49-03-01\n'

In addition, the :mod:`~msl.equipment.constants` module contains the package constants.

That pretty much summarizes all of the classes and modules that a typical user will need to access in their
application.

.. _connection_classes:

Connection Classes
------------------
The following :class:`~msl.equipment.connection.Connection` classes are available which allow for communicating with the
:obj:`~msl.equipment.database.Database.equipment` *(although you should never need to instantiate these classes directly):*

+---------------------------------------------------------------+--------------------------------------------------------------------------------------------+
| :class:`~msl.equipment.connection_demo.ConnectionDemo`        | Simulate a connection to the equipment.                                                    |
+---------------------------------------------------------------+--------------------------------------------------------------------------------------------+
| :class:`~msl.equipment.connection_msl.ConnectionMessageBased` | Base class for equipment that use message based communication.                             |
+---------------------------------------------------------------+--------------------------------------------------------------------------------------------+
| :class:`~msl.equipment.connection_msl.ConnectionSDK`          | Base class for equipment that use the SDK provided by the manufacturer for the connection. |
+---------------------------------------------------------------+--------------------------------------------------------------------------------------------+
| :class:`~msl.equipment.connection_msl.ConnectionSerial`       | Base class for equipment that is connected through a Serial port.                          |
+---------------------------------------------------------------+--------------------------------------------------------------------------------------------+

and the :class:`~msl.equipment.connection.Connection` classes that are available from external Python libraries are:

+---------------------------------------------------------------+--------------------------------------------------------------------------------------------+
| :class:`~msl.equipment.connection_pyvisa.ConnectionPyVISA`    | Uses PyVISA_ to establish a connection to the equipment.                                   |
+---------------------------------------------------------------+--------------------------------------------------------------------------------------------+

Package Structure
-----------------

.. toctree::
   :maxdepth: 1

   msl.equipment <_api/msl.equipment>
   msl.equipment.config <_api/msl.equipment.config>
   msl.equipment.connection <_api/msl.equipment.connection>
   msl.equipment.connection_demo <_api/msl.equipment.connection_demo>
   msl.equipment.connection_msl <_api/msl.equipment.connection_msl>
   msl.equipment.connection_pyvisa <_api/msl.equipment.connection_pyvisa>
   msl.equipment.constants <_api/msl.equipment.constants>
   msl.equipment.database <_api/msl.equipment.database>
   msl.equipment.exceptions <_api/msl.equipment.exceptions>
   msl.equipment.factory <_api/msl.equipment.factory>
   msl.equipment.record_types <_api/msl.equipment.record_types>
   msl.equipment.resources <_api/msl.equipment.resources>

.. _PyVISA: http://pyvisa.readthedocs.io/en/stable/index.html