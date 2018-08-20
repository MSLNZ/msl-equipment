"""
Uses PyVISA_ as the backend to communicate with the equipment.

.. _PyVISA: http://pyvisa.readthedocs.io/en/stable/index.html
"""
try:
    import pyvisa
except IOError:
    pyvisa = None

from .config import Config
from .connection import Connection
from .record_types import EquipmentRecord, ConnectionRecord


class ConnectionPyVISA(Connection):

    _resource_classes = {}

    def __init__(self, record):
        """Uses PyVISA_ to establish a connection to the equipment.

        The :data:`~msl.equipment.record_types.ConnectionRecord.backend`
        value must be equal to :data:`~msl.equipment.constants.Backend.PyVISA`
        to use this class for the communication system. This is achieved by setting the
        value in the **Backend** field for a connection record in the :ref:`connections_database`
        to be ``PyVISA``.

        Do not instantiate this class directly. Use the
        :meth:`~.EquipmentRecord.connect` method to connect to the equipment.

        .. _PyVISA: http://pyvisa.readthedocs.io/en/stable/index.html

        Parameters
        ----------
        record : :class:`.EquipmentRecord`
            A record from an :ref:`equipment_database`.
        """
        super(ConnectionPyVISA, self).__init__(record)

        self._resource = None

        rm = ConnectionPyVISA.resource_manager()

        props = record.connection.properties

        try:
            val = props['parity'].name.lower()
        except KeyError:
            pass
        else:
            props['parity'] = self.convert_to_enum(val, pyvisa.constants.Parity)

        try:
            val = int(props['stop_bits'].value*10)
        except KeyError:
            pass
        else:
            props['stop_bits'] = self.convert_to_enum(val, pyvisa.constants.StopBits)

        self._resource = rm.open_resource(record.connection.address, **props)

        # expose all of the PyVISA Resource functions and properties to ConnectionPyVISA
        # NOTE: the 'setter' function of the @property does NOT get called. If you want
        # it to be called you would have to deal with it in the same manner as 'timeout'
        for attr in dir(self._resource):
            if attr.startswith('_') or attr == 'timeout':
                continue
            setattr(self, attr, getattr(self._resource, attr, None))

        self.log_debug('Connected to {}'.format(record.connection))

    @property
    def timeout(self):
        """Calls :attr:`~pyvisa.resources.Resource.timeout`."""
        return self._resource.timeout

    @timeout.setter
    def timeout(self, value):
        self._resource.timeout = value

    @timeout.deleter
    def timeout(self):
        del self._resource.timeout

    def disconnect(self):
        """Calls :meth:`~pyvisa.resources.Resource.close`."""
        if self._resource is not None:
            self._resource.close()
            self.log_debug('Disconnected from {}'.format(self.equipment_record.connection))
            self._resource = None

    @staticmethod
    def resource_manager(visa_library=None):
        """Return the PyVISA :class:`~pyvisa.highlevel.ResourceManager`. 

        Parameters
        ----------
        visa_library : :class:`~pyvisa.highlevel.VisaLibraryBase` or :class:`str`, optional
            The library to use for PyVISA. For example:
    
                * ``@ni`` to use `NI-VISA <https://www.ni.com/visa/>`_
                * ``@py`` to use `PyVISA-py <http://pyvisa-py.readthedocs.io/en/latest/>`_
                * ``@sim`` to use `PyVISA-sim <https://pyvisa-sim.readthedocs.io/en/latest/>`_
    
            If :data:`None` then `visa_library` is read from the
            :attr:`~.config.Config.PyVISA_LIBRARY` variable.

        Returns
        -------
        :class:`~pyvisa.highlevel.ResourceManager`
            The PyVISA Resource Manager.

        Raises
        ------
        ValueError
            If the PyVISA backend wrapper cannot be found.
        OSError
            If the VISA library cannot be found.
        """
        if pyvisa is None:
            raise ImportError('pyvisa is not installed. Run: pip install pyvisa')

        if not ConnectionPyVISA._resource_classes:
            for item in dir(pyvisa.resources):
                if item.endswith('Instrument'):
                    key = item[:-len('Instrument')]
                    ConnectionPyVISA._resource_classes[key] = getattr(pyvisa.resources, item)
                elif item == 'GPIBInterface':
                    ConnectionPyVISA._resource_classes['GPIB_INTFC'] = pyvisa.resources.GPIBInterface
                elif item == 'VXIBackplane':
                    ConnectionPyVISA._resource_classes['VXI_BACKPLANE'] = pyvisa.resources.VXIBackplane
                elif item == 'VXIMemory':
                    ConnectionPyVISA._resource_classes['VXI_MEMACC'] = pyvisa.resources.VXIMemory
                elif item == 'TCPIPSocket':
                    ConnectionPyVISA._resource_classes['TCPIP_SOCKET'] = pyvisa.resources.TCPIPSocket
                elif item == 'USBRaw':
                    ConnectionPyVISA._resource_classes['USB_RAW'] = pyvisa.resources.USBRaw
                elif item == 'PXIMemory':
                    ConnectionPyVISA._resource_classes['PXI_MEMACC'] = getattr(pyvisa.resources, item)
            for item in ('COM', 'ASRL', 'LPT1', 'ASRLCOM'):
                ConnectionPyVISA._resource_classes[item] = pyvisa.resources.SerialInstrument

        if visa_library is None:
            visa_library = Config.PyVISA_LIBRARY

        return pyvisa.ResourceManager(visa_library)

    @staticmethod
    def resource_class(record):
        """Find the specific_ PyVISA Resource class that can open the `record`.

        .. _specific: http://pyvisa.readthedocs.io/en/stable/api/resources.html
         
        Parameters
        ----------
        record : :class:`~.record_types.EquipmentRecord` or :class:`~.record_types.ConnectionRecord`
            An equipment or connection record from a :ref:`Database <database>`.

        Returns
        -------
        A :class:`~pyvisa.resources.Resource` subclass
            The PyVISA Resource class that can open the `record`.
        """
        if isinstance(record, EquipmentRecord):
            if record.connection is None:
                raise ValueError('The connection object has not been set for {}'.format(record))
            address = record.connection.address
        elif isinstance(record, ConnectionRecord):
            address = record.address
        else:
            msg = 'Invalid record type. Must be of type {} or {}'.format(
                EquipmentRecord.__name__, ConnectionRecord.__name__)
            raise TypeError(msg)

        if not address:
            raise ValueError('The connection address for {} has not been set'.format(record))

        rm = ConnectionPyVISA.resource_manager()
        try:
            info = rm.resource_info(address, extended=True)
            return rm._resource_classes[(info.interface_type, info.resource_class)]
        except:
            # try to figure out the resource class...
            a = address.upper()

            if a.startswith('GPIB') and a.endswith('INTFC'):
                return ConnectionPyVISA._resource_classes['GPIB_INTFC']

            if a.startswith('VXI') and a.endswith('BACKPLANE'):
                return ConnectionPyVISA._resource_classes['VXI_BACKPLANE']

            if a.startswith('VXI') and a.endswith('MEMACC'):
                return ConnectionPyVISA._resource_classes['VXI_MEMACC']

            if a.startswith('TCPIP') and a.endswith('SOCKET'):
                return ConnectionPyVISA._resource_classes['TCPIP_SOCKET']

            if a.startswith('USB') and a.endswith('RAW'):
                return ConnectionPyVISA._resource_classes['USB_RAW']

            if a.startswith('PXI') and a.endswith('MEMACC'):
                return ConnectionPyVISA._resource_classes['PXI_MEMACC']

            for key, value in ConnectionPyVISA._resource_classes.items():
                if a.startswith(key):
                    return value

            raise ValueError('Cannot find PyVISA resource class for {}'.format(address))
