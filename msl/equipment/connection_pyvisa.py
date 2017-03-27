"""
Use PyVISA_ as the backend to communicate with the equipment.

.. _PyVISA: http://pyvisa.readthedocs.io/en/stable/index.html
"""
import logging

logger = logging.getLogger(__name__)

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
        value must be equal to :data:`Backend.PyVISA <msl.equipment.constants.Backend.PyVISA>` to use 
        this class for the communication system. This is achieved by setting the value in the **Backend** 
        field for a connection record in the **Connections** database to be **PyVISA**.

        If you want to change the ``read_termination``, ``write_termination`` and/or the ``encoding`` 
        value for communication with the equipment then you can define, for example, 
        ``read_termination=\\n; write_termination=\\n; encoding=utf-8`` in the 
        **Properties** field for a connection record in the **Connections** database.

        Args:
            record (:class:`~.record_types.EquipmentRecord`): An equipment 
                record (a row) from the :class:`~.database.Database`.

        .. _PyVISA: http://pyvisa.readthedocs.io/en/stable/index.html
        """
        if PYVISA_RESOURCE_MANAGER is None:
            raise ImportError(PYVISA_ERROR_MESSAGE)

        # use PyVISA to connect to the equipment
        self._resource = PYVISA_RESOURCE_MANAGER.open_resource(record.connection.address,
                                                               **record.connection.properties)

        # update the address to be the VISA resource name
        record._connection._address = self._resource.resource_info[0].resource_name

        # expose all of the PyVISA Resource methods for this connection
        for method in dir(self._resource):
            if not method.startswith('_'):
                setattr(self, method, getattr(self._resource, method))

        Connection.__init__(self, record)

    def disconnect(self):
        """
        Close_ the PyVISA_ connection.

        .. _Close: http://pyvisa.readthedocs.io/en/stable/api/resources.html#pyvisa.resources.RegisterBasedResource.close
        .. _PyVISA: http://pyvisa.readthedocs.io/en/stable/index.html        
        """
        self._resource.close()
        logger.debug('Disconnected from {}'.format(self.equipment_record.connection))
