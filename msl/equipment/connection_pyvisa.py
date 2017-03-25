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
    PYVISA_ERROR_MESSAGE = 'Could not open the VISA library that is required for PyVISA'

from msl.equipment.connection import Connection


class ConnectionPyVISA(Connection):

    def __init__(self, record):
        """
        Use PyVISA_ to establish a connection to the equipment.

        Do not instantiate this class directly. Use :func:`msl.equipment.factory.connect`
        or :meth:`EquipmentRecord.connect() <msl.equipment.record_types.EquipmentRecord.connect>`
        to connect to the equipment.

        The :data:`EquipmentRecord.connection.backend <msl.equipment.record_types.ConnectionRecord.backend>`
        value must be equal to :data:`Backend.PyVISA <msl.equipment.constants.Backend.PyVISA>` to use this
        class for the communication system.

        Args:
            record (:class:`~msl.equipment.record_types.EquipmentRecord`): An
                equipment record (a row) from the :class:`~msl.equipment.database.Database`.

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

    def read(self, termination=None, encoding=None):
        """
        Use PyVISA_ to read_ the response from the equipment.

        .. _PyVISA: http://pyvisa.readthedocs.io/en/stable/index.html
        .. _read: http://pyvisa.readthedocs.io/en/stable/api/resources.html#pyvisa.resources.MessageBasedResource.read
        """
        return self._backend.read(termination, encoding)

    def write(self, message, termination=None, encoding=None):
        """
        Use PyVISA_ to write_ a message to the equipment.

        .. _PyVISA: http://pyvisa.readthedocs.io/en/stable/index.html
        .. _write: http://pyvisa.readthedocs.io/en/stable/api/resources.html#pyvisa.resources.MessageBasedResource.write
        """
        return self._backend.write(message, termination, encoding)
