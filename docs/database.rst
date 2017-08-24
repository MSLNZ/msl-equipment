.. _database:

================
Database Formats
================
Databases are used by **MSL-Equipment** to store :class:`~msl.equipment.record_types.EquipmentRecord`\'s in an
`Equipment-Register Database`_ and :class:`~msl.equipment.record_types.ConnectionRecord`\'s in a `Connection Database`_.
The database file formats that are currently supported are **.txt**, **.csv** and **.xls(x)**. A database is composed of
**fields** (columns) and **records** (rows).

.. _equipment_database:

Equipment-Register Database
---------------------------
The information about the equipment that is used to perform a measurement must be known and it must be kept up to date.
Keeping a central and official (hence the word *Register*) database of the equipment that is available in the lab allows
for easily managing this information and for helping to ensure that the equipment that is being used for a measurement
meets the requirement needed to achieve the measurement uncertainty.

**MSL-Equipment** does not require that a *single* database is used for all equipment **records**. However, it is vital
that each equipment **record** can only be uniquely found in **ONE** Equipment-Register database. The **records** in a
database MUST NEVER be copied from one database to another database *(keeping a backup copy of the database is encouraged)*.
Rather, if you are borrowing equipment from another team you simply specify the path to that teams Equipment-Register
database in your :ref:`configuration`. The owner of the equipment is responsible for ensuring that the information about
the equipment is up to date in their Equipment-Register database and the user of the equipment defines an
**<equipment>** XML tag in the :ref:`configuration`. Therefore, an Equipment-Register database is to be considered as a
**global** database that can be accessed (with read permission only) by all of MSL via the **MSL-Equipment** package.

Each **record** in an Equipment-Register database is converted into an
:class:`~msl.equipment.record_types.EquipmentRecord`.

The following is an example of an Equipment-Register database (additional **fields** can also be added to a database,
see :ref:`field_names`).

+-----------------+---------+--------+--------------+--------------+---------------------------------------+
| Manufacturer    | Model   | Serial | Date         | Calibration  | Description                           |
|                 | Number  | Number | Calibrated   | Cycle [Years]|                                       |
+=================+=========+========+==============+==============+=======================================+
| Keysight        | 34465A  | MY5450 | 4 April 2014 | 5            | 6.5 digital multimeter                |
+-----------------+---------+--------+--------------+--------------+---------------------------------------+
| Hewlett Packard | HP8478B | BCD024 | 17 June 2017 | 3.5          | Dual element thermistor power sensors |
+-----------------+---------+--------+--------------+--------------+---------------------------------------+
| Agilent         | 53230A  | 49e39f | 9 Sept 2015  | 7            | Universal counter/timer               |
+-----------------+---------+--------+--------------+--------------+---------------------------------------+

.. tip::
   Not all equipment **records** in the Equipment-Register database need to have the ability to be connected to.
   For example, cables, filters and adaptors can all be important equipment that may be used for a measurement
   and should be included in the Equipment-Register database and specified as **<equipment>** tags in the
   :ref:`configuration`.

.. _field_names:

Field Names
+++++++++++
The supported **fields** for an Equipment-Register database are:

* **Asset Number** -- The IRL/CI asset number of the equipment
* **Calibration Cycle** -- The number of years that can pass before the equipment must be re-calibrated
* **Category** -- The category (e.g., Laser, DMM) that the equipment belongs to
* **Date Calibrated** -- The date that the equipment was last calibrated
* **Description** -- A description of the equipment
* **Location** -- The location where the equipment can usually be found
* **Manufacturer** -- The name of the manufacturer of the equipment
* **Model** -- The model number of the equipment
* **Register** -- The value assigned, as in MSL Policy and Procedures, for any equipment that requires calibration or
  maintenance for projects
* **Serial** -- The serial number, or engraved unique ID, of the equipment

The text in the header of each **field** is not too particular for what it must be. The header text is parsed for one
of the specific **field** names listed above and if the header contains one of these **field** names then that
column is assigned to be that **field**.

.. role:: blue

For example, the following headers are valid (the :blue:`blue` text is what is important in the header)

* Headers can contain many words.

  For a **field** to be assigned to the :obj:`~msl.equipment.record_types.EquipmentRecord.manufacturer` the header
  can be written as

  *This column is used to specify the* :blue:`Manufacturer` *of the equipment*

* Text is case insensitive.

  For a **field** to be assigned to the :obj:`~msl.equipment.record_types.EquipmentRecord.model` the header
  can be written as any of the following

  - :blue:`MODEL` *No.*
  - :blue:`Model` *#*
  - :blue:`model` *number*
  - :blue:`MoDeL`

  Although using the following header will not raise an exception, you should not use the following header because
  either the :obj:`~msl.equipment.record_types.EquipmentRecord.manufacturer` or the
  :obj:`~msl.equipment.record_types.EquipmentRecord.model` will be assigned for this **field** depending on the
  order in which the **fields** are defined in the database

  *The* :blue:`model` *number from the* :blue:`manufacturer`

* Whitespace is replaced by an underscore.

  For a **field** to be assigned to the :obj:`~msl.equipment.record_types.EquipmentRecord.calibration_cycle` the header
  can be written as

  :blue:`Calibration Cycle`, *in years*

* If the header does not contain any of the specific **field** names that are being searched for then the values
  in that column are silently ignored.

.. _connection_database:

Connection Database
-------------------
A Connection database is used to store the information that is required to establish communication with the equipment.

The supported **fields** for a Connection database are:

* **Address** -- The address to use for the connection (see :ref:`address_syntax`).
* **Backend** -- The :class:`~msl.equipment.constants.Backend` to use to communicate with the equipment
* **Manufacturer** -- The name of the manufacturer of the equipment
* **Model** -- The model number of the equipment
* **Properties** -- Additional properties that may be required to establish a connection to the equipment as key-value
  pairs separated by a semi-colon. For example, for a :class:`~msl.equipment.connection_msl.ConnectionSerial` connection
  the baud rate and parity might need to be defined -- ``baud_rate=11920; parity=even``. The value (as in a key-*value*
  pair) gets cast to the appropriate data type (e.g., :obj:`int`, :obj:`float`, :obj:`str`) so the baud rate
  value would be ``11920`` as an :obj:`int` and the parity value would be
  :obj:`Parity.EVEN <msl.equipment.constants.Parity.EVEN>`.
* **Serial** -- The serial number, or engraved unique ID, of the equipment

A **record** in a Connection database gets matched with the appropriate **record** in an `Equipment-Register Database`_
by the unique combination of the ``Manufacturer + Model + Serial`` values, which when combined act as the primary key
in each database.

The following is an example of a Connection database (the header of each **field** also follows the same
:ref:`field_names` format used in an `Equipment-Register Database`_ and so *Model #* would also be an acceptable
header)

+-----------------+----------+--------+---------+-----------------------------+-------------------------------+
| Manufacturer    | Model    | Serial | Backend | Address                     | Properties                    |
|                 | Number   | Number |         |                             |                               |
+=================+==========+========+=========+=============================+===============================+
| Keysight        | 34465A   | MY5450 | MSL     | USB::0x2A8D::0x0101::MY5450 |                               |
+-----------------+----------+--------+---------+-----------------------------+-------------------------------+
| Hewlett Packard | HP8478B  | BCD024 | PyVISA  | GPIB::7                     |                               |
+-----------------+----------+--------+---------+-----------------------------+-------------------------------+
| Agilent         | 53230A   | 49e39f | MSL     | COM2                        | baud_rate=119200; parity=even |
+-----------------+----------+--------+---------+-----------------------------+-------------------------------+

Unlike an `Equipment-Register Database`_ each person can have their own Connection database. The reason being that since
equipment can be shared between people some Connection values, like the GPIB address, can vary depending on who is using
the equipment and what other equipment they are using. Therefore, everyone could have their own Connection database and
connection **records** can be copied from one Connection database to another. Also, how one establishes a connection to
the equipment is not vital information for the MSL Quality System. What equipment was used during data acquisition and
the metadata associated with each equipment is important. What is not important is, for example, what the value of the
GPIB address was when the equipment was used to acquired the data.

.. _address_syntax:

Address Syntax
++++++++++++++
The following are examples of an **Address** syntax (see more examples from `National Instruments`_).

.. note::

   The text **PythonClassName** that is used in the table below would be replaced with the actual name of the
   Python class that is available in :ref:`resources`. The text **PathToSDK** would be the full path to where
   the SDK file is located or only the filename if the path to where the SDK file is located has been added as
   a **<PATH>** XML tag in the :ref:`configuration`.

+------------------------------------------------+------------------------------------------------------------------+
| :class:`~msl.equipment.constants.MSLInterface` | Syntax                                                           |
+================================================+==================================================================+
| ASRL                                           | COM2                                                             |
+------------------------------------------------+------------------------------------------------------------------+
| ASRL                                           | COM4::INSTR                                                      |
+------------------------------------------------+------------------------------------------------------------------+
| ASRL                                           | COM7::**PythonClassName**                                        |
+------------------------------------------------+------------------------------------------------------------------+
| SDK                                            | SDK::**PythonClassName**::**PathToSDK**                          |
+------------------------------------------------+------------------------------------------------------------------+
| SDK                                            | SDK::Bentham::C:/Program Files/Bentham/lib/benhw32_cdecl.dll     |
+------------------------------------------------+------------------------------------------------------------------+
| SDK                                            | SDK::FilterFlipper::Thorlabs.MotionControl.FilterFlipper.dll     |
+------------------------------------------------+------------------------------------------------------------------+

.. _National Instruments: http://zone.ni.com/reference/en-XX/help/370131S-01/ni-visa/visaresourcesyntaxandexamples/