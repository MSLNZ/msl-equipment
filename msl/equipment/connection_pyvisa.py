"""
Use PyVISA as the backend to communicate with the equipment.
"""
try:
    import pyvisa
    PYVISA_RESOURCE_MANAGER = pyvisa.ResourceManager()
except ImportError:
    PYVISA_RESOURCE_MANAGER = None

from msl.equipment.connection import Connection


class ConnectionPyVISA(Connection):

    def __init__(self, equipment_record):
        if PYVISA_RESOURCE_MANAGER is None:
            raise ImportError('PyVISA is not installed')

        Connection.__init__(self, equipment_record)
        self._backend = PYVISA_RESOURCE_MANAGER.open_resource(equipment_record.connection.address,
                                                              **equipment_record.connection.properties)

        # update the address to be the VISA resource name
        equipment_record._connection._address = self._backend.resource_info[0].resource_name

    def disconnect(self):
        if self._backend is not None:
            self._backend.close()

    def read(self, termination=None, encoding=None):
        return self._backend.read(termination, encoding)

    def write(self, message, termination=None, encoding=None):
        self._backend.write(message, termination, encoding)
