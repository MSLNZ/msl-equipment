.. _equipment-api:

=================
API Documentation
=================

The main entryway in to **MSL-Equipment** is achieved by loading a :ref:`configuration-file` and that is achieved by
creating a :class:`~msl.equipment.config.Config` object. This example loads the `example.xml`_ file.

.. code-block:: pycon

    >>> from msl.equipment import Config
    >>> cfg = Config('config.xml')

Once a :class:`~msl.equipment.config.Config` object exists you can access of all the
:class:`~msl.equipment.record_types.EquipmentRecord`\'s and :class:`~msl.equipment.record_types.ConnectionRecord`\'s
that are contained within the :ref:`Databases <database-formats>` as well as all of the
:attr:`~msl.equipment.database.Database.equipment` that is being used to perform the measurement by calling the
:meth:`~msl.equipment.config.Config.database` method to create an instance of the
:class:`~msl.equipment.database.Database`.

.. code-block:: pycon

    >>> db = cfg.database()
    >>> for record in db.records():
    ...    print(record)
    ...
    EquipmentRecord<Fluke|8506A|A10008>
    EquipmentRecord<Oriel|66087|B10009>
    EquipmentRecord<Kepco|JQE|C10010>
    EquipmentRecord<Hewlett Packard|34401A|D10011>
    EquipmentRecord<Arlunya|Milli Gauss|E10012>
    EquipmentRecord<Toledo|1000|F10013>
    EquipmentRecord<Stanford Research Systems|SR850 DSP|G10014>
    EquipmentRecord<Hewlett Packard|3478A|D10015>
    >>> for record in db.records(manufacturer='H.*P'):
    ...    print(record)
    ...
    EquipmentRecord<Hewlett Packard|34401A|D10011>
    EquipmentRecord<Hewlett Packard|3478A|D10015>
    >>> for conn in db.connections():
    ...    print(conn)
    ...
    ConnectionRecord<Fluke|8506A|A10008>
    ConnectionRecord<Hewlett Packard|34401A|D10011>
    ConnectionRecord<Stanford Research Systems|SR850 DSP|G10014>
    ConnectionRecord<Hewlett Packard|3478A|D10011>
    >>> for conn in db.connections(address='GPIB'):
    ...     print(conn)
    ...
    ConnectionRecord<Fluke|8506A|A10008>
    ConnectionRecord<Hewlett Packard|3478A|D10011>
    >>> db.equipment
    {'dmm': EquipmentRecord<Hewlett Packard|34401A|D10011>}
    >>> db.equipment['dmm'].connection
    ConnectionRecord<Hewlett Packard|34401A|D10011>

Establishing a connection to the equipment is achieved by calling the
:meth:`~msl.equipment.record_types.EquipmentRecord.connect` method of an
:class:`~msl.equipment.record_types.EquipmentRecord`. This call will return a specific
:class:`~msl.equipment.connection.Connection` subclass that contains the necessary properties and methods for
communicating with the equipment.

.. code-block:: pycon

    >>> dmm = db.equipment['dmm'].connect()
    >>> dmm.query('*IDN?')
    'Hewlett Packard,34401A,D10011,A.02.14-02.40-02.14-00.49-03-01'

In addition, the :mod:`~msl.equipment.constants` module contains the package constants.

.. _connection-classes:

Connection Classes
------------------
The following :class:`~msl.equipment.connection.Connection` classes are available to communicate
with the equipment *(although you should never need to instantiate these classes directly):*

+-------------------------------------------------------------------------+--------------------------------------------------------------------------+
| :class:`~msl.equipment.connection_demo.ConnectionDemo`                  | Simulate a connection to the equipment                                   |
+-------------------------------------------------------------------------+--------------------------------------------------------------------------+
| :class:`~msl.equipment.connection_message_based.ConnectionMessageBased` | Equipment that use message-based communication                           |
+-------------------------------------------------------------------------+--------------------------------------------------------------------------+
| :class:`~msl.equipment.connection_prologix.ConnectionPrologix`          | Equipment that is connected through a Prologix_ Controller               |
+-------------------------------------------------------------------------+--------------------------------------------------------------------------+
| :class:`~msl.equipment.connection_sdk.ConnectionSDK`                    | Equipment that use the manufacturer's SDK for the connection             |
+-------------------------------------------------------------------------+--------------------------------------------------------------------------+
| :class:`~msl.equipment.connection_serial.ConnectionSerial`              | Equipment that is connected through a Serial port                        |
+-------------------------------------------------------------------------+--------------------------------------------------------------------------+
| :class:`~msl.equipment.connection_socket.ConnectionSocket`              | Equipment that is connected through a Socket                             |
+-------------------------------------------------------------------------+--------------------------------------------------------------------------+
| :class:`~msl.equipment.connection_tcpip_vxi11.ConnectionTCPIPVXI11`     | Equipment that use the VXI-11 protocol                                   |
+-------------------------------------------------------------------------+--------------------------------------------------------------------------+
| :class:`~msl.equipment.connection_tcpip_hislip.ConnectionTCPIPHiSLIP`   | Equipment that use the HiSLIP protocol                                   |
+-------------------------------------------------------------------------+--------------------------------------------------------------------------+

and the :class:`~msl.equipment.connection.Connection` classes that are available from external Python libraries are:

+---------------------------------------------------------------+---------------------------------------------------------+
| :class:`~msl.equipment.connection_pyvisa.ConnectionPyVISA`    | Uses PyVISA_ to establish a connection to the equipment |
+---------------------------------------------------------------+---------------------------------------------------------+
| :class:`~msl.equipment.connection_nidaq.ConnectionNIDAQ`      | Uses NI-DAQ_ to establish a connection to the equipment |
+---------------------------------------------------------------+---------------------------------------------------------+

Package Structure
-----------------

.. toctree::
   :maxdepth: 1

   msl.equipment <_api/msl.equipment>
   msl.equipment.config <_api/msl.equipment.config>
   msl.equipment.connection <_api/msl.equipment.connection>
   msl.equipment.connection_demo <_api/msl.equipment.connection_demo>
   msl.equipment.connection_message_based <_api/msl.equipment.connection_message_based>
   msl.equipment.connection_nidaq <_api/msl.equipment.connection_nidaq>
   msl.equipment.connection_prologix <_api/msl.equipment.connection_prologix>
   msl.equipment.connection_pyvisa <_api/msl.equipment.connection_pyvisa>
   msl.equipment.connection_sdk <_api/msl.equipment.connection_sdk>
   msl.equipment.connection_serial <_api/msl.equipment.connection_serial>
   msl.equipment.connection_socket <_api/msl.equipment.connection_socket>
   msl.equipment.connection_tcpip_hislip <_api/msl.equipment.connection_tcpip_hislip>
   msl.equipment.connection_tcpip_vxi11 <_api/msl.equipment.connection_tcpip_vxi11>
   msl.equipment.constants <_api/msl.equipment.constants>
   msl.equipment.database <_api/msl.equipment.database>
   msl.equipment.dns_service_discovery <_api/msl.equipment.dns_service_discovery>
   msl.equipment.exceptions <_api/msl.equipment.exceptions>
   msl.equipment.factory <_api/msl.equipment.factory>
   msl.equipment.hislip <_api/msl.equipment.hislip>
   msl.equipment.record_types <_api/msl.equipment.record_types>
   msl.equipment.resources <_api/msl.equipment.resources>
   msl.equipment.utils <_api/msl.equipment.utils>
   msl.equipment.vxi11 <_api/msl.equipment.vxi11>

.. _PyVISA: https://pyvisa.readthedocs.io/en/stable/index.html
.. _NI-DAQ: https://nidaqmx-python.readthedocs.io/en/stable/index.html
.. _example.xml: https://github.com/MSLNZ/msl-equipment/blob/main/msl/examples/equipment/example.xml
.. _Prologix: https://prologix.biz/
