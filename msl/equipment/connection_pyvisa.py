"""
Use PyVISA_ as the backend to communicate with the equipment.

.. _PyVISA: http://pyvisa.readthedocs.io/en/stable/index.html
"""
from .config import Config
from .connection import Connection
from .record_types import EquipmentRecord, ConnectionRecord

_VisaIOError = None
_pyvisa_resource_classes = {}
_pyvisa_resource_manager = None
_pyvisa_constants = None


class ConnectionPyVISA(Connection):

    def __init__(self, record):
        """Use PyVISA_ to establish a connection to the equipment.
        
        The :data:`record.connection.backend <msl.equipment.record_types.ConnectionRecord.backend>`
        value must be equal to :data:`Backend.PyVISA <msl.equipment.constants.Backend.PyVISA>` 
        to use this class for the communication system. This is achieved by setting the value 
        in the **Backend** field for a connection record in the **Connections** database 
        to be **PyVISA**.

        If you want to change the ``read_termination``, ``write_termination`` and/or the 
        ``encoding`` value for communication with the equipment then you can define, 
        for example, ``read_termination=\\n; write_termination=\\n; encoding=utf-8`` in the 
        **Properties** field for a connection record in the **Connections** database.

        Do not instantiate this class directly. Use the factory method, 
        :obj:`msl.equipment.factory.connect`, or the `record` object itself, 
        :obj:`record.connect() <.record_types.EquipmentRecord.connect>`,
        to connect to the equipment.

        .. _PyVISA: http://pyvisa.readthedocs.io/en/stable/index.html

        Parameters
        ----------
        record : :class:`~.record_types.EquipmentRecord`
            An equipment record from an **Equipment-Register** :class:`~.database.Database`.
        """
        Connection.__init__(self, record)

        self._resource = None

        rm = ConnectionPyVISA.resource_manager()

        props = record.connection.properties

        try:
            props['parity'] = self.convert_to_enum(props['parity'], _pyvisa_constants.Parity)
        except KeyError:
            pass

        try:
            props['stop_bits'] = self.convert_to_enum(int(float(props['stop_bits'])*10), _pyvisa_constants.StopBits)
        except KeyError:
            pass

        self._resource = rm.open_resource(record.connection.address, **props)

        # expose all of the PyVISA Resource methods to ConnectionPyVISA
        for method in dir(self._resource):
            if not method.startswith('_'):
                try:
                    setattr(self, method, getattr(self._resource, method))
                except _VisaIOError:
                    pass

        self.log_debug('Connected to {}'.format(record.connection))

    def disconnect(self):
        """Calls :meth:`~pyvisa.resources.Resource.close`."""
        if self._resource is not None:
            self._resource.close()
            self.log_debug('Disconnected from {}'.format(self.equipment_record.connection))
            self._resource = None

    @staticmethod
    def resource_manager(visa_library=None):
        """Return the PyVISA :class:`~pyvisa.highlevel.ResourceManager`. 
    
        Only **one** Resource Manager session is created per Python runtime 
        and therefore multiple calls to this function will return the same 
        :class:`~pyvisa.highlevel.ResourceManager` object.

        .. _NI-VISA:
            https://www.ni.com/visa/
        .. _PyVISA-py:
            http://pyvisa-py.readthedocs.io/en/latest/    
        .. _PyVISA-sim:
            https://pyvisa-sim.readthedocs.io/en/latest/    
    
        Parameters
        ----------
        visa_library : :class:`~pyvisa.highlevel.VisaLibraryBase`, :obj:`str` or :obj:`None`
            The library to use for PyVISA. For example:
    
                * ``@ni`` to use NI-VISA_        
                * ``@py`` to use PyVISA-py_
                * ``@sim`` to use PyVISA-sim_
    
            If :data:`None` then the `visa_library` value is read from a 
            :obj:`~.config.CONFIG` variable. See :obj:`msl.equipment.config.load` 
            for more details.
        
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
        global _pyvisa_resource_manager, _VisaIOError, _pyvisa_resource_classes, _pyvisa_constants
        if _pyvisa_resource_manager is not None:
            return _pyvisa_resource_manager

        import pyvisa

        _VisaIOError = pyvisa.errors.VisaIOError
        _pyvisa_constants = pyvisa.constants

        for item in dir(pyvisa.resources):
            if item.endswith('Instrument'):
                key = item[:-len('Instrument')]
                _pyvisa_resource_classes[key] = getattr(pyvisa.resources, item)
            elif item == 'GPIBInterface':
                _pyvisa_resource_classes['GPIB_INTFC'] = getattr(pyvisa.resources, item)
            elif item == 'VXIBackplane':
                _pyvisa_resource_classes['VXI_BACKPLANE'] = getattr(pyvisa.resources, item)
            elif item == 'VXIMemory':
                _pyvisa_resource_classes['VXI_MEMACC'] = getattr(pyvisa.resources, item)

        if visa_library is None:
            visa_library = Config.PyVISA_LIBRARY

        _pyvisa_resource_manager = pyvisa.ResourceManager(visa_library)
        return _pyvisa_resource_manager

    @staticmethod
    def resource_pyclass(record):
        """Find the PyVISA :class:`~pyvisa.resources.Resource` that can open the `record`.
         
        Parameters
        ----------
        record : :class:`~.record_types.EquipmentRecord` or :class:`~.record_types.ConnectionRecord`
            An equipment or connection record from the :class:`~.database.Database`.

        Returns
        -------
        :class:`~pyvisa.resources.Resource`
            The appropriate PyVISA Resource class that can open the `record`.        
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

        try:
            rm = ConnectionPyVISA.resource_manager()
            info = rm.resource_info(address, extended=True)
            return rm._resource_classes[(info.interface_type, info.resource_class)]
        except _VisaIOError:
            # try to figure out the resource class...
            a = address.upper()

            if a.startswith('GPIB') and a.endswith('INTFC'):
                return _pyvisa_resource_classes['GPIB_INTFC']

            if a.startswith('VXI') and a.endswith('BACKPLANE'):
                return _pyvisa_resource_classes['VXI_BACKPLANE']

            if a.startswith('VXI') and a.endswith('MEMACC'):
                return _pyvisa_resource_classes['VXI_MEMACC']

            for key, value in _pyvisa_resource_classes.items():
                if a.startswith(key):
                    return value

            raise ValueError('Cannot find PyVISA resource class for {}'.format(address))
