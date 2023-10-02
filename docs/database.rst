.. _database-formats:

================
Database Formats
================
Databases are used by MSL-Equipment to store
:class:`~msl.equipment.record_types.EquipmentRecord`\'s in an
:ref:`equipment-database` and :class:`~msl.equipment.record_types.ConnectionRecord`\'s
in a :ref:`connections-database`. The database file formats that are currently
supported are **xml**, **json**, **txt** (``\t`` delimited),
**csv** (``,`` delimited) and **xls[x]**.

The **txt**, **csv** and **xls[x]** formats are simple databases that are
composed of *fields* (columns) and *records* (rows). The **xml** and **json**
formats allow for storing more complex data structures, such as
:class:`~msl.equipment.record_types.MaintenanceRecord`\'s
:class:`~msl.equipment.record_types.CalibrationRecord`\'s and
:class:`~msl.equipment.record_types.MeasurandRecord`\'s for each
:class:`~msl.equipment.record_types.EquipmentRecord`. For example **xml**
and **json** formats, see `equipment_register.xml`_ and `equipment_register.json`_
respectively.

.. _equipment-database:

Equipment-Register Database
---------------------------

.. attention::

   The design of the Equipment-Register database is in active development and it will be unstable
   until an official release of MSL-Equipment is made.

The information about the equipment that is used to perform a measurement must be known and it must be kept up to date.
Keeping a central and official (hence the word *Register*) database of the equipment that is available in the laboratory
allows for easily managing this information and for helping to ensure that the equipment that is being used for a
measurement meets the calibration requirements needed to obtain the desired measurement uncertainty.

MSL-Equipment does not require that a *single* database is used for all equipment records. However, it is vital
that each equipment record can only be uniquely found in one :ref:`equipment-database`. The records in a database must
never be copied from one database to another database *(keeping a backup copy of the database is encouraged)*.
Rather, if you are borrowing equipment from another team you simply specify the path to that teams
:ref:`equipment-database` as a ``<register>`` element in your :ref:`configuration-file`. The owner of the equipment
is responsible for ensuring that the information about the equipment is kept up to date in their
:ref:`equipment-database` and the user of the equipment defines an ``<equipment>`` element in the
:ref:`configuration-file` to access this information. Therefore, an :ref:`equipment-database` is to be considered as
a *global* database that can be accessed (with read permission only) by anyone.

Each record in an :ref:`equipment-database` is converted into an :class:`~msl.equipment.record_types.EquipmentRecord`.

The following is an example of an :ref:`equipment-database` (additional *fields* can also be added to a database,
see :ref:`register-field-names`).

+-----------------+---------+--------+---------------------------------------+
| Manufacturer    | Model   | Serial | Description                           |
|                 | Number  | Number |                                       |
+=================+=========+========+=======================================+
| Keysight        | 34465A  | MY5450 | 6.5 digit digital multimeter          |
+-----------------+---------+--------+---------------------------------------+
| Hewlett Packard | HP8478B | BCD024 | Dual element thermistor power sensors |
+-----------------+---------+--------+---------------------------------------+
| Agilent         | 53230A  | 49e39f | Universal counter/timer               |
+-----------------+---------+--------+---------------------------------------+

.. tip::
   Not all records in the :ref:`equipment-database` need to have the ability to be interfaced with a computer. For
   example, cables, amplifiers, filters and adaptors can all be important equipment that may be used to perform a
   measurement and should be included in the :ref:`equipment-database` and specified as ``<equipment>`` elements in the
   :ref:`configuration-file`.

.. _register-field-names:

Field Names
+++++++++++
Some of the supported *fields* for an :ref:`equipment-database` are:

* **Category** -- The category (e.g., Laser, DMM) that the equipment belongs to.
* **Description** -- A description of the equipment.
* **Location** -- The location where the equipment can usually be found.
* **Manufacturer** -- The name of the manufacturer of the equipment.
* **Model** -- The model number of the equipment.
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
  :attr:`~msl.equipment.record_types.EquipmentRecord.is_operable` attribute the header can be written as:

  +--------------------------------------+
  | :blue:`Is Operable`, *True or False* |
  +--------------------------------------+

* If the header does not contain any of the specific *field* names that are being searched for then the values
  in that column are silently ignored.

Equipment records should be defined in an :ref:`equipment-database` and accessed via the
:meth:`~msl.equipment.config.Config.database` method; however, you can also define equipment
records in a Python module, for example:

.. code-block:: python

    from msl.equipment import EquipmentRecord, ConnectionRecord, Backend

    equipment = {
        'dmm':
            EquipmentRecord(
                manufacturer='HP',
                model='34401A',
                serial='123456789',
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
                serial='XY135/001',
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
                serial='5672413',
                description='1.0 Ohm Resistor 3A',
            ),
    }

.. _connections-database:

Connections Database
--------------------
A :ref:`connections-database` is used to store the information that is required to establish communication with the
equipment.

You specify the :ref:`connections-database` that you what to use as a ``<connection>`` element in your
:ref:`configuration-file`. Each record in an :ref:`connections-database` is converted into a
:class:`~msl.equipment.record_types.ConnectionRecord`.

.. _connections-field-names:

Field Names
+++++++++++
The supported *fields* for a :ref:`connections-database` are:

* **Address** -- The address to use for the connection (see :ref:`address-syntax`).
* **Backend** -- The :class:`~msl.equipment.constants.Backend` to use to communicate with the equipment.
* **Manufacturer** -- The name of the manufacturer of the equipment.
* **Model** -- The model number of the equipment.
* **Properties** -- Additional properties that may be required to establish a connection to the equipment as key-value
  pairs separated by a semi-colon. For example, for a :class:`~msl.equipment.connection_serial.ConnectionSerial`
  connection the baud rate and parity might need to be defined -- ``baud_rate=11920; parity=even``. The value (as in a
  key-*value* pair) gets cast to the appropriate data type (e.g., :class:`int`, :class:`float`, :class:`str`) so the
  baud rate value would be ``11920`` as an :class:`int` and the parity value becomes
  :data:`Parity.EVEN <msl.equipment.constants.Parity.EVEN>`.
* **Serial** -- The serial number, or unique ID, of the equipment.

A record in a :ref:`connections-database` gets matched with the appropriate record in an :ref:`equipment-database`
by the unique combination of the ``manufacturer + model + serial`` values, which when combined act as the primary key
in each database.

The following is an example of a :ref:`connections-database`. The header of each *field* also follows the same
:ref:`register-field-names` format used in an :ref:`equipment-database` and so *MODEL#* would also be
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

Unlike an :ref:`equipment-database` each person can maintain their own :ref:`connections-database`. The reason being
that since equipment can be shared between people some Connection *fields*, like the COM address, can vary depending on
which computer the equipment is connected to and what other equipment is also connected to that computer. Therefore,
everyone could have their own :ref:`connections-database` and connection records can be copied from one
:ref:`connections-database` to another. If you are using someone else's equipment and if none of the Connection *fields*
need to be changed to be able to communicate with the equipment then it is recommended to add their
:ref:`connections-database` as a ``<connection>`` element in your :ref:`configuration-file`.

.. _address-syntax:

Address Syntax
++++++++++++++
The following are examples of an **Address** syntax (see more examples from `National Instruments`_).

+------------------------------------------------+-----------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+
| :class:`~msl.equipment.constants.Interface`    | Syntax Example                                      |  Notes                                                                                                                                         |
+================================================+=====================================================+================================================================================================================================================+
| PROLOGIX                                       | Prologix::192.168.1.110::1234::6                    | The GPIB-ETHERNET Controller: host=192.168.1.110, port=1234, primary-GPIB-address=6                                                            |
+------------------------------------------------+-----------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+
| PROLOGIX                                       | Prologix::192.168.1.70::1234::6::112                | The GPIB-ETHERNET Controller: host=192.168.1.70, port=1234, primary-GPIB-address=6, secondary-GPIB-address=112                                 |
+------------------------------------------------+-----------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+
| PROLOGIX                                       | Prologix::192.168.1.70::1234::GPIB::6::112          | The GPIB-ETHERNET Controller: host=192.168.1.70, port=1234, primary-GPIB-address=6, secondary-GPIB-address=112                                 |
+------------------------------------------------+-----------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+
| PROLOGIX                                       | Prologix::COM3::6                                   | The GPIB-USB Controller: port=COM3, primary-GPIB-address=6                                                                                     |
+------------------------------------------------+-----------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+
| PROLOGIX                                       | Prologix::/dev/ttyS0::4::96                         | The GPIB-USB Controller: port=/dev/ttyS0, primary-GPIB-address=4, secondary-GPIB-address=96                                                    |
+------------------------------------------------+-----------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+
| SDK                                            | SDK::C:/Program Files/Manufacturer/bin/filename.dll | Specify the full path to the SDK                                                                                                               |
+------------------------------------------------+-----------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+
| SDK                                            | SDK::filename.dll                                   | Specify only the filename if the path to where the SDK file is located has been added as a ``<path>`` element in the :ref:`configuration-file` |
+------------------------------------------------+-----------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+
| SERIAL                                         | COM2                                                | A serial port on Windows                                                                                                                       |
+------------------------------------------------+-----------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+
| SERIAL                                         | ASRL/dev/ttyS1                                      | A serial port on Linux                                                                                                                         |
+------------------------------------------------+-----------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+
| SERIAL                                         | ASRL2::INSTR                                        | Compatible with `National Instruments`_ syntax                                                                                                 |
+------------------------------------------------+-----------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+
| SERIAL                                         | ASRLCOM2                                            | Compatible with PyVISA-py_ syntax                                                                                                              |
+------------------------------------------------+-----------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+
| SOCKET                                         | \TCP::192.168.1.100::5000                           | Creates the connection as a :data:`socket.SOCK_STREAM` to the IP address **192.168.1.100** at port **5000**                                    |
+------------------------------------------------+-----------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+
| SOCKET                                         | UDP::192.168.1.100::5000                            | Creates the connection as a :data:`socket.SOCK_DGRAM`                                                                                          |
+------------------------------------------------+-----------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+
| SOCKET                                         | TCPIP::192.168.1.100::5000::SOCKET                  | Compatible with `National Instruments`_ syntax                                                                                                 |
+------------------------------------------------+-----------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+
| SOCKET                                         | SOCKET::192.168.1.100::5000                         | Generic socket type. You can specify the connection type in the **Properties** *field* (i.e., type=RAW)                                        |
+------------------------------------------------+-----------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+
| TCPIP HiSLIP                                   | TCPIP::dev.company.com::hislip0                     | A HiSLIP LAN instrument at the hostname **dev.company.com**.                                                                                   |
+------------------------------------------------+-----------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+
| TCPIP HiSLIP                                   | TCPIP::10.12.114.50::hislip0,5000::INSTR            | A HiSLIP LAN instrument whose IP address is **10.12.114.50** with the server listening at port **5000**                                        |
+------------------------------------------------+-----------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+
| TCPIP VXI-11                                   | TCPIP::dev.company.com::INSTR                       | A VXI-11.3 LAN instrument at the hostname **dev.company.com**. This uses the default LAN Device Name **inst0**                                 |
+------------------------------------------------+-----------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+
| TCPIP VXI-11                                   | TCPIP::10.6.56.21::gpib0,2::INSTR                   | A VXI-11.2 GPIB device whose IP address is **10.6.56.21**                                                                                      |
+------------------------------------------------+-----------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+
| TCPIP VXI-11                                   | TCPIP::192.168.1.100                                | A VXI-11.3 LAN instrument at IP address **192.168.1.100**. Note that default values for board **0** and LAN device name **inst0** will be used |
+------------------------------------------------+-----------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+
| ZMQ                                            | ZMQ::192.168.20.90::5555                            | Use the ZeroMQ_ messaging library to connect to a device at IP address **192.168.20.90** and port **5555**                                     |
+------------------------------------------------+-----------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------+

.. _National Instruments: https://www.ni.com/docs/en-US/bundle/ni-visa/page/ni-visa/visaresourcesyntaxandexamples.html
.. _PyVISA-py: https://pyvisa.readthedocs.io/projects/pyvisa-py/en/stable/
.. _equipment_register.json: https://github.com/MSLNZ/msl-equipment/blob/main/tests/db_files/equipment_register.json
.. _equipment_register.xml: https://github.com/MSLNZ/msl-equipment/blob/main/tests/db_files/equipment_register.xml
.. _ZeroMQ: https://zeromq.org/