"""
Use PyVISA_ as the backend to communicate with the equipment.

.. _PyVISA: http://pyvisa.readthedocs.io/en/stable/index.html
"""
PYVISA_RESOURCE_MANAGER = None

try:
    import pyvisa
    PYVISA_RESOURCE_MANAGER = pyvisa.ResourceManager()
except ImportError:
    PYVISA_ERROR_MESSAGE = 'PyVISA is not installed'
except OSError:
    PYVISA_ERROR_MESSAGE = 'Could not open the VISA library that is required for PyVISA.\n' \
                           'You must download and install NI-VISA from the National Instruments website.'

from msl.equipment.connection import Connection


class ConnectionPyVISA(Connection):

    def __init__(self, record):
        """
        Use PyVISA_ to establish a connection to the equipment.

        Do not instantiate this class directly. Use :func:`msl.equipment.factory.connect`
        or :meth:`record.connect() <msl.equipment.record_types.EquipmentRecord.connect>`
        to connect to the equipment.

        The :data:`record.connection.backend <msl.equipment.record_types.ConnectionRecord.backend>`
        value must be equal to :data:`Backend.PyVISA <msl.equipment.constants.Backend.PyVISA>` to use this
        class for the communication system. This is achieved by setting the value in the **Backend** 
        field for a connection record in the **Connections** database to be **PyVISA**.

        Args:
            record (:class:`~.record_types.EquipmentRecord`): An equipment 
                record (a row) from the :class:`~.database.Database`.

        .. _PyVISA: http://pyvisa.readthedocs.io/en/stable/index.html
        """
        if PYVISA_RESOURCE_MANAGER is None:
            raise ImportError(PYVISA_ERROR_MESSAGE)

        Connection.__init__(self, record)
        self._backend = PYVISA_RESOURCE_MANAGER.open_resource(record.connection.address,
                                                              **record.connection.properties)

        # update the address to be the VISA resource name
        record._connection._address = self._backend.resource_info[0].resource_name

    def disconnect(self):
        """
        Close_ the PyVISA_ connection.

        .. _Close: http://pyvisa.readthedocs.io/en/stable/api/resources.html#pyvisa.resources.RegisterBasedResource.close
        .. _PyVISA: http://pyvisa.readthedocs.io/en/stable/index.html        
        """
        if self._backend is not None:
            self._backend.close()

    def read(self):
        """
        Use PyVISA_ to read_ a response from the equipment.
        
        If you want to change the ``read_termination`` and/or the ``encoding`` value for communication with 
        the equipment then you must define, for example, ``read_termination=\\n; encoding=utf-8`` in the 
        **Properties** field for a connection record in the **Connections** database.        

        Returns:
            :py:class:`str`: The response from the equipment.

        .. _PyVISA: http://pyvisa.readthedocs.io/en/stable/index.html
        .. _read: http://pyvisa.readthedocs.io/en/stable/api/resources.html#pyvisa.resources.MessageBasedResource.read
        """
        return self._backend.read()

    def write(self, message):
        """
        Use PyVISA_ to write_ a message to the equipment.

        If you want to change the ``write_termination`` and/or the ``encoding`` value for communication with 
        the equipment then you must define, for example, ``write_termination=\\n; encoding=utf-8`` in the 
        **Properties** field for a connection record in the **Connections** database.

        Args:
            message (str): The message to write to the equipment.

        Returns:
            :py:class:`int`: The number of bytes written.

        .. _PyVISA: http://pyvisa.readthedocs.io/en/stable/index.html
        .. _write: http://pyvisa.readthedocs.io/en/stable/api/resources.html#pyvisa.resources.MessageBasedResource.write
        """
        return self._backend.write(message)
