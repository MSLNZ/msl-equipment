.. _api:

=================
API Documentation
=================

The main gateway into **MSL-Equipment** is by loading a :ref:`configuration` and that is achieved by using the
:class:`~msl.equipment.config.Config` class.

Once a :ref:`configuration` has been loaded you can access the :class:`~msl.equipment.database.Database` records by
calling the :meth:`~msl.equipment.config.Config.database` method. The records are define as

+-------------------------------------------------------+---------------------------------------------------------------------------+
| :class:`~msl.equipment.record_types.EquipmentRecord`  | The information about an equipment record in an :ref:`equipment_database` |
+-------------------------------------------------------+---------------------------------------------------------------------------+
| :class:`~msl.equipment.record_types.ConnectionRecord` | The information about a connection record in a :ref:`connection_database` |
+-------------------------------------------------------+---------------------------------------------------------------------------+

In addition, the :mod:`~msl.equipment.constants` module contains the package constants.

That pretty much summarizes all the classes and modules that a typical user will need to use.

.. _connection_classes:

Connection Classes
------------------
The following classes are available which allow for communicating with the equipment *(although you will never need to*
*instantiate these classes directly):*

+---------------------------------------------------------------+--------------------------------------------------------------------------------------------+
| :class:`~msl.equipment.connection_msl.ConnectionMessageBased` | Base class for equipment that use message based communication.                             |
+---------------------------------------------------------------+--------------------------------------------------------------------------------------------+
| :class:`~msl.equipment.connection_msl.ConnectionSDK`          | Base class for equipment that use the SDK provided by the manufacturer for the connection. |
+---------------------------------------------------------------+--------------------------------------------------------------------------------------------+
| :class:`~msl.equipment.connection_msl.ConnectionSerial`       | Base class for equipment that is connected through a Serial port.                          |
+---------------------------------------------------------------+--------------------------------------------------------------------------------------------+
| :class:`~msl.equipment.connection_demo.ConnectionDemo`        | Simulate a connection to the equipment.                                                    |
+---------------------------------------------------------------+--------------------------------------------------------------------------------------------+

and the connection classes that are available from external Python libraries are:

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