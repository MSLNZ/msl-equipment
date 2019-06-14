.. _database:

================
Database Formats
================
Databases are used by **MSL-Equipment** to store :class:`~msl.equipment.record_types.EquipmentRecord`\'s in an
:ref:`equipment_database` and :class:`~msl.equipment.record_types.ConnectionRecord`\'s in a
:ref:`connections_database`. The database file formats that are currently supported are **.txt** (``\t`` delimited),
**.csv** (``,`` delimited) and **.xls[x]**.

A database is composed of *fields* (columns) and *records* (rows).

.. _equipment_database:

Equipment-Register Database
---------------------------

.. attention::

   The design of the Equipment-Register database is in active development and it can be unstable
   until an official release of MSL-Equipment is made.

The information about the equipment that is used to perform a measurement must be known and it must be kept up to date.
Keeping a central and official (hence the word *Register*) database of the equipment that is available in the laboratory
allows for easily managing this information and for helping to ensure that the equipment that is being used for a
task meets the calibration requirements needed to obtain the desired measurement uncertainty.

**MSL-Equipment** does not require that a *single* database is used for all equipment records. However, it is vital
that each equipment record can only be uniquely found in one :ref:`equipment_database`. The records in a database must
never be copied from one database to another database *(keeping a backup copy of the database is encouraged)*.
Rather, if you are borrowing equipment from another team you simply specify the path to that teams
:ref:`equipment_database` as a ``<register>`` element in your :ref:`configuration_file`. The owner of the equipment
is responsible for ensuring that the information about the equipment is kept up to date in their
:ref:`equipment_database` and the user of the equipment defines an ``<equipment>`` element in the
:ref:`configuration_file` to access this information. Therefore, an :ref:`equipment_database` is to be considered as
a *global* database that can be accessed (with read permission only) by anyone.

Each record in an :ref:`equipment_database` is converted into an :class:`~msl.equipment.record_types.EquipmentRecord`.

The following is an example of an :ref:`equipment_database` (additional *fields* can also be added to a database,
see :ref:`register_field_names`).

+-----------------+---------+--------+--------------+---------------+---------------------------------------+
| Manufacturer    | Model   | Serial | Date         | Calibration   | Description                           |
|                 | Number  | Number | Calibrated   | Cycle [Years] |                                       |
+=================+=========+========+==============+===============+=======================================+
| Keysight        | 34465A  | MY5450 | 4 April 2014 | 5             | 6.5 digital multimeter                |
+-----------------+---------+--------+--------------+---------------+---------------------------------------+
| Hewlett Packard | HP8478B | BCD024 | 17 June 2017 | 3             | Dual element thermistor power sensors |
+-----------------+---------+--------+--------------+---------------+---------------------------------------+
| Agilent         | 53230A  | 49e39f | 9 Sept 2015  | 7             | Universal counter/timer               |
+-----------------+---------+--------+--------------+---------------+---------------------------------------+

.. tip::
   Not all records in the :ref:`equipment_database` need to have the ability to be interfaced with a computer. For
   example, cables, amplifiers, filters and adaptors can all be important equipment that may be used to perform a
   measurement and should be included in the :ref:`equipment_database` and specified as ``<equipment>`` elements in the
   :ref:`configuration_file`.

.. _register_field_names:

Field Names
+++++++++++
The supported *fields* for an :ref:`equipment_database` are:

* **Calibration Cycle** -- The number of years that can pass before the equipment must be re-calibrated.
* **Category** -- The category (e.g., Laser, DMM) that the equipment belongs to.
* **Date Calibrated** -- The date that the equipment was last calibrated.
* **Description** -- A description of the equipment.
* **Location** -- The location where the equipment can usually be found.
* **Manufacturer** -- The name of the manufacturer of the equipment.
* **Model** -- The model number of the equipment.
* **Latest Report Number** -- The report number for the last time that the equipment was calibrated.
* **Serial** -- The serial number, or engraved unique ID, of the equipment.

The text in the header of each *field* is not too particular for what it must be. The header text is parsed for one
of the specific *field* names listed above and if the header contains one of these *field* names then that
column is assigned to be that *field*.

.. role:: blue

For example, the following headers are valid (the :blue:`blue` text is what is important in the header)

* Headers can contain many words. For a *field* to be assigned to the
  :attr:`~msl.equipment.record_types.EquipmentRecord.manufacturer` attribute the header can be written as:

  +------------------------------------------------------------------------------+
  | *This column is used to specify the* :blue:`Manufacturer` *of the equipment* |
  +------------------------------------------------------------------------------+

* Text is case insensitive. For a *field* to be assigned to the
  :attr:`~msl.equipment.record_types.EquipmentRecord.model` attribute the header can be written as any of the following:

  +---------------------+-------------------+-----------------------------------------------+---------------+
  | :blue:`MODEL` *No.* | :blue:`Model` *#* | *The* :blue:`model` *number of the equipment* | :blue:`MoDeL` |
  +---------------------+-------------------+-----------------------------------------------+---------------+

  Although using the following header will not raise an exception, you should not use the following header because
  either the :attr:`~msl.equipment.record_types.EquipmentRecord.manufacturer` or the
  :attr:`~msl.equipment.record_types.EquipmentRecord.model` attribute will be assigned for this *field* depending on the
  order in which the *fields* appear in the database:

  +----------------------------------------------------------------+
  | *The* :blue:`model` *number given by the* :blue:`manufacturer` |
  +----------------------------------------------------------------+

* Whitespace is replaced by an underscore. For a *field* to be assigned to the
  :attr:`~msl.equipment.record_types.EquipmentRecord.calibration_cycle` attribute the header can be written as:

  +---------------------------------------+
  | :blue:`Calibration cycle`, *in years* |
  +---------------------------------------+

* If the header does not contain any of the specific *field* names that are being searched for then the values
  in that column are silently ignored.

Equipment records should be defined in a properly-managed :ref:`equipment_database` (especially if the equipment is
used within a Quality Management System, such as `ISO/IEC 17025`_) and accessed via the
:meth:`~msl.equipment.config.Config.database` method; however, for those not bound to a rigorous Quality Management
System you can also store your equipment records in a Python module, for example:

.. code-block:: python

    from datetime import date
    from msl.equipment import EquipmentRecord, ConnectionRecord, Backend

    equipment = {
        'dmm':
            EquipmentRecord(
                manufacturer='HP',
                model='34401A',
                serial='3146A34467',
                date_calibrated=date(2016, 7, 12),
                calibration_cycle=5,
                connection=ConnectionRecord(
                    backend=Backend.MSL,
                    address='COM3',
                    properties=dict(
                        baud_rate=19200,
                    )
                )
            ),
        'scope':
            EquipmentRecord(
                manufacturer='Pico Technology',
                model='5244B',
                serial='DY135/055',
                description='Oscilloscope -- 2 Channel, 200 MHz, 1 GSPS, 512 Mpts, 5.8 ns',
                connection=ConnectionRecord(
                    backend=Backend.MSL,
                    address='SDK::ps5000a.dll',
                    properties=dict(
                        resolution='16bit',
                    )
                )
            ),
        '1ohm':
            EquipmentRecord(
                manufacturer='Tinsley',
                model='64750',
                serial='03246836',
                description='1.0 Ohm Resistor 3A',
                date_calibrated=date(2018, 8, 2),
                calibration_cycle=5,
            ),
    }

.. _connections_database:

Connections Database
--------------------
A :ref:`connections_database` is used to store the information that is required to establish communication with the
equipment.

You specify the :ref:`connections_database` that you what to use as a ``<connection>`` element in your
:ref:`configuration_file`. Each record in an :ref:`connections_database` is converted into a
:class:`~msl.equipment.record_types.ConnectionRecord`.

.. _connections_field_names:

Field Names
+++++++++++
The supported *fields* for a :ref:`connections_database` are:

* **Address** -- The address to use for the connection (see :ref:`address_syntax`).
* **Backend** -- The :class:`~msl.equipment.constants.Backend` to use to communicate with the equipment.
* **Manufacturer** -- The name of the manufacturer of the equipment.
* **Model** -- The model number of the equipment.
* **Properties** -- Additional properties that may be required to establish a connection to the equipment as key-value
  pairs separated by a semi-colon. For example, for a :class:`~msl.equipment.connection_serial.ConnectionSerial`
  connection the baud rate and parity might need to be defined -- ``baud_rate=11920; parity=even``. The value (as in a
  key-*value* pair) gets cast to the appropriate data type (e.g., :class:`int`, :class:`float`, :class:`str`) so the
  baud rate value would be ``11920`` as an :class:`int` and the parity value would be
  :data:`Parity.EVEN <msl.equipment.constants.Parity.EVEN>`.
* **Serial** -- The serial number, or engraved unique ID, of the equipment.

A record in a :ref:`connections_database` gets matched with the appropriate record in an :ref:`equipment_database`
by the unique combination of the ``manufacturer + model + serial`` values, which when combined act as the primary key
in each database.

The following is an example of a :ref:`connections_database`. The header of each *field* also follows the same
:ref:`register_field_names` format used in an :ref:`equipment_database` and so *MODEL#* would also be
an acceptable header for *Model Number*.

+-----------------+---------+--------+---------+---------------------------+-------------------------------+
| Manufacturer    | Model   | Serial | Backend | Address                   | Properties                    |
|                 | Number  | Number |         |                           |                               |
+=================+=========+========+=========+===========================+===============================+
| OMEGA           | iTHX-W3 | 458615 | MSL     | \TCP::192.168.1.100::2000 | termination="\\r"; timeout=10 |
+-----------------+---------+--------+---------+---------------------------+-------------------------------+
| Hewlett Packard | 3468A   | BCD024 | PyVISA  | GPIB::7                   |                               |
+-----------------+---------+--------+---------+---------------------------+-------------------------------+
| Agilent         | 53230A  | 49e39f | MSL     | COM2                      | baud_rate=119200; parity=even |
+-----------------+---------+--------+---------+---------------------------+-------------------------------+

Unlike an :ref:`equipment_database` each person can maintain their own :ref:`connections_database`. The reason being
that since equipment can be shared between people some Connection *fields*, like the COM address, can vary depending on
which computer the equipment is connected to and what other equipment is also connected to that computer. Therefore,
everyone could have their own :ref:`connections_database` and connection records can be copied from one
:ref:`connections_database` to another. If you are using someone else's equipment and if none of the Connection *fields*
need to be changed to be able to communicate with the equipment then it is recommended to add their
:ref:`connections_database` as a ``<connection>`` element in your :ref:`configuration_file`.

.. _address_syntax:

Address Syntax
++++++++++++++
The following are examples of an **Address** syntax (see more examples from `National Instruments`_).

+------------------------------------------------+-----------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+
| :class:`~msl.equipment.constants.MSLInterface` | Syntax Example                                      |  Notes                                                                                                                                         |
+================================================+=====================================================+================================================================================================================================================+
| SDK                                            | SDK::C:/Program Files/Manufacturer/bin/filename.dll | Specify the full path to the SDK                                                                                                               |
+------------------------------------------------+-----------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+
| SDK                                            | SDK::filename.dll                                   | Specify only the filename if the path to where the SDK file is located has been added as a ``<path>`` element in the :ref:`configuration_file` |
+------------------------------------------------+-----------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+
| SERIAL                                         | COM2                                                |                                                                                                                                                |
+------------------------------------------------+-----------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+
| SERIAL                                         | ASRL7::INSTR                                        | Compatible with `National Instruments`_ syntax                                                                                                 |
+------------------------------------------------+-----------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+
| SERIAL                                         | ASRLCOM4                                            | Compatible with PyVISA-py_ syntax                                                                                                              |
+------------------------------------------------+-----------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+
| SERIAL                                         | SERIAL::/dev/pts/12                                 |                                                                                                                                                |
+------------------------------------------------+-----------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+
| SOCKET                                         | \TCP::192.168.1.100::5000                           | Creates the connection as a :data:`socket.SOCK_STREAM` to host=192.168.1.100, port=5000                                                        |
+------------------------------------------------+-----------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+
| SOCKET                                         | UDP::192.168.1.100::5000                            | Creates the connection as a :data:`socket.SOCK_DGRAM`                                                                                          |
+------------------------------------------------+-----------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+
| SOCKET                                         | TCPIP::192.168.1.100::5000::SOCKET                  | Compatible with `National Instruments`_ syntax                                                                                                 |
+------------------------------------------------+-----------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+
| SOCKET                                         | SOCKET::192.168.1.100::5000                         | Generic socket type. You can specify the connection type in the **Properties** *field* (i.e., type=RAW)                                        |
+------------------------------------------------+-----------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+

.. _National Instruments: https://zone.ni.com/reference/en-XX/help/370131S-01/ni-visa/visaresourcesyntaxandexamples/
.. _PyVISA-py: https://pyvisa-py.readthedocs.io/en/latest/
.. _ISO/IEC 17025: https://www.iso.org/standard/66912.html
