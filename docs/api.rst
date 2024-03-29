.. _equipment-api:

=================
API Documentation
=================
Although this package contains many classes and functions, the only object
that you must initialize in your application is :class:`~msl.equipment.config.Config`
and perhaps :class:`~msl.equipment.record_types.EquipmentRecord`'s (depending on the
format that is chosen to store the :ref:`Databases <database-formats>`).

.. _find-equipment:

Find Equipment
--------------
To find equipment that can be connected to, you may either call the
:func:`~msl.equipment.find_equipment` function or run the ``find-equipment``
executable from a terminal. To see the help for the executable, run

.. code-block:: console

    find-equipment --help

Running either the function or the executable will return/display a description
about the equipment and the address(es) that may be used to connect to the equipment.

.. _connection-classes:

Connection Classes
------------------
The following :class:`~msl.equipment.connection.Connection` classes are available to communicate
with the equipment *(although you should never need to instantiate these classes directly):*

+-------------------------------------------------------------------------+--------------------------------------------------------------------------+
| :class:`~msl.equipment.connection_demo.ConnectionDemo`                  | Simulate a connection to the equipment                                   |
+-------------------------------------------------------------------------+--------------------------------------------------------------------------+
| :class:`~msl.equipment.connection_gpib.ConnectionGPIB`                  | Equipment that use the IEEE-488 bus (GPIB)                               |
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
| :class:`~msl.equipment.connection_tcpip_vxi11.ConnectionTCPIPVXI11`     | Equipment that use the VXI-11_ protocol                                  |
+-------------------------------------------------------------------------+--------------------------------------------------------------------------+
| :class:`~msl.equipment.connection_tcpip_hislip.ConnectionTCPIPHiSLIP`   | Equipment that use the HiSLIP_ protocol                                  |
+-------------------------------------------------------------------------+--------------------------------------------------------------------------+
| :class:`~msl.equipment.connection_zeromq.ConnectionZeroMQ`              | Equipment that use the ZeroMQ_ protocol                                  |
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
   msl.equipment.connection_gpib <_api/msl.equipment.connection_gpib>
   msl.equipment.connection_message_based <_api/msl.equipment.connection_message_based>
   msl.equipment.connection_nidaq <_api/msl.equipment.connection_nidaq>
   msl.equipment.connection_prologix <_api/msl.equipment.connection_prologix>
   msl.equipment.connection_pyvisa <_api/msl.equipment.connection_pyvisa>
   msl.equipment.connection_sdk <_api/msl.equipment.connection_sdk>
   msl.equipment.connection_serial <_api/msl.equipment.connection_serial>
   msl.equipment.connection_socket <_api/msl.equipment.connection_socket>
   msl.equipment.connection_tcpip_hislip <_api/msl.equipment.connection_tcpip_hislip>
   msl.equipment.connection_tcpip_vxi11 <_api/msl.equipment.connection_tcpip_vxi11>
   msl.equipment.connection_zeromq <_api/msl.equipment.connection_zeromq>
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
.. _Prologix: https://prologix.biz/
.. _ZeroMQ: https://zeromq.org/
.. _VXI-11: https://www.vxibus.org/specifications.html
.. _HiSLIP: https://www.ivifoundation.org/downloads/Protocol%20Specifications/IVI-6.1_HiSLIP-2.0-2020-04-23.pdf