"""
Use PyVISA_ as the backend to communicate with the equipment.

.. _PyVISA: http://pyvisa.readthedocs.io/en/stable/index.html
"""
from msl.equipment.connection import Connection
from msl.equipment.record_types import EquipmentRecord, ConnectionRecord

_pyvisa_resource_manager = None
_VisaIOError = None
_pyvisa_class_resources = {}


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
        self._resource = None

        rm = ConnectionPyVISA.resource_manager()
        self._resource = rm.open_resource(record.connection.address, **record.connection.properties)

        # expose all of the PyVISA Resource methods for this connection object
        for method in dir(self._resource):
            if not method.startswith('_'):
                setattr(self, method, getattr(self._resource, method))

        Connection.__init__(self, record)
        self.log_debug('Connected to {}'.format(record.connection))

    def disconnect(self):
        """Close_ the PyVISA_ connection.

        .. _Close: http://pyvisa.readthedocs.io/en/stable/api/resources.html#pyvisa.resources.RegisterBasedResource.close
        .. _PyVISA: http://pyvisa.readthedocs.io/en/stable/index.html        
        """
        if self._resource is not None:
            self._resource.close()
            self.log_debug('Disconnected from {}'.format(self.equipment_record.connection))
            self._resource = None

    @staticmethod
    def resource_manager(pyvisa_backend=None):
        """Return the PyVISA `Resource Manager`_. 
    
        Only **one** `Resource Manager`_ session is created per Python runtime and therefore 
        multiple calls to this function returns the same `Resource Manager`_ object.
    
        .. _Resource Manager:
            http://pyvisa.readthedocs.io/en/stable/api/resourcemanager.html#pyvisa.highlevel.ResourceManager
        .. _NI-VISA:
            https://www.ni.com/visa/
        .. _PyVISA-py:
            http://pyvisa-py.readthedocs.io/en/latest/    
        .. _PyVISA-sim:
            https://pyvisa-sim.readthedocs.io/en/latest/    
    
        Parameters
        ----------
        pyvisa_backend : :obj:`str` or :obj:`None`
            The backend to use for PyVISA. For example:
    
                * ``@ni`` to use NI-VISA_        
                * ``@py`` to use PyVISA-py_
                * ``@sim`` to use PyVISA-sim_
    
            If :data:`None` then the `pyvisa_backend` value is read from an 
            :obj:`os.environ` variable. See :func:`msl.equipment.config.load` 
            for more details.
        
        Returns
        -------
        `Resource Manager`_
            The PyVISA Resource Manager.
        
        Raises
        ------
        ValueError
            If the PyVISA backend cannot be found.
        """
        global _pyvisa_resource_manager, _VisaIOError, _pyvisa_class_resources
        if _pyvisa_resource_manager is not None:
            return _pyvisa_resource_manager

        import os
        import pyvisa

        _VisaIOError = pyvisa.errors.VisaIOError

        for item in dir(pyvisa.resources):
            if item.endswith('Instrument'):
                key = item.replace('Instrument', '')
                _pyvisa_class_resources[key] = getattr(pyvisa.resources, item)

        if pyvisa_backend is None:
            pyvisa_backend = os.environ.get('PyVISA-backend', '@ni')

        _pyvisa_resource_manager = pyvisa.ResourceManager(pyvisa_backend)
        return _pyvisa_resource_manager

    @staticmethod
    def resource_pyclass(record):
        """Finds the PyVISA `resource class`_ that can be used to open the `record`.
         
        .. _resource class: http://pyvisa.readthedocs.io/en/stable/api/resources.html
        
        Parameters
        ----------
        record : :class:`~.record_types.EquipmentRecord` or :class:`~.record_types.ConnectionRecord`
            An equipment or connection record from the :class:`~.database.Database`.

        Returns
        -------
        `resource class`_
            The appropriate PyVISA resource class.        
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
            # try to figure it out manually...
            for key, value in _pyvisa_class_resources.items():
                if address.startswith(key):
                    return value
