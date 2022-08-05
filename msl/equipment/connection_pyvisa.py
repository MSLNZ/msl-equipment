"""
Uses PyVISA_ as the backend to communicate with the equipment.

.. _PyVISA: https://pyvisa.readthedocs.io/en/stable/
"""
try:
    import pyvisa
except ImportError:
    pyvisa = None

from .config import Config
from .connection import Connection


class ConnectionPyVISA(Connection):

    _resource_classes = {}

    def __init__(self, record):
        """Uses PyVISA_ to establish a connection to the equipment.

        The :data:`~msl.equipment.record_types.ConnectionRecord.backend`
        value must be equal to :data:`~msl.equipment.constants.Backend.PyVISA`
        to use this class for the communication system. This is achieved by setting the
        value in the **Backend** field for a connection record in the :ref:`connections-database`
        to be ``PyVISA``.

        Do not instantiate this class directly. Use the
        :meth:`~.EquipmentRecord.connect` method to connect to the equipment.

        Parameters
        ----------
        record : :class:`.EquipmentRecord`
            A record from an :ref:`equipment-database`.
        """
        self._resource = None
        super(ConnectionPyVISA, self).__init__(record)

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

        # PyVISA requires the read/write termination data type to be str not bytes
        def ensure_term(term):
            try:
                return term.decode()
            except AttributeError:
                return term

        # "termination" is a shortcut used by the MSL backend to set both
        # write_termination and read_termination to the same value
        rw_term = props.pop('termination', None)
        r_term = props.pop('read_termination', rw_term)
        w_term = props.pop('write_termination', rw_term)
        if r_term is not None:
            props['read_termination'] = ensure_term(r_term)
        if w_term is not None:
            props['write_termination'] = ensure_term(w_term)

        # the "timeout" value is in seconds for MSL backend
        # PyVISA uses a timeout in milliseconds
        timeout = props.get('timeout')
        if timeout and timeout < 100:
            # if timeout < 100 then it's value is probably in seconds
            props['timeout'] = timeout * 1000

        self._resource = rm.open_resource(record.connection.address, **props)
        self.log_debug('Connected to %s', record.connection)

    def __getattr__(self, item):
        attr = getattr(self._resource, item)
        if callable(attr):
            def wrapper(*args, **kwargs):
                return attr(*args, **kwargs)
            return wrapper
        return attr

    def __setattr__(self, item, value):
        if item[0] == '_':
            # handles all private attributes, like:
            #   self._resource
            #   self._record
            #   self._exception_handler
            #   self._repr
            #   self._str
            self.__dict__[item] = value
        else:
            setattr(self._resource, item, value)

    def __delattr__(self, item):
        delattr(self._resource, item)

    @property
    def resource(self):
        """:class:`~pyvisa.resources.Resource`: The PyVISA_ resource that is used for the connection.

        This is the :class:`~pyvisa.resources.Resource` that would have
        been returned if you did the following in a script::

            import pyvisa
            rm = visa.ResourceManager()
            resource = rm.open_resource('COM6')

        """
        return self._resource

    def disconnect(self):
        """Calls :meth:`~pyvisa.resources.Resource.close`."""
        if self._resource is not None:
            self._resource.close()
            self.log_debug('Disconnected from %s', self.equipment_record.connection)
            self._resource = None

    @staticmethod
    def resource_manager(visa_library=None):
        """Return the PyVISA_ :class:`~pyvisa.highlevel.ResourceManager`.

        Parameters
        ----------
        visa_library : :class:`~pyvisa.highlevel.VisaLibraryBase` or :class:`str`, optional
            The library to use for PyVISA_. For example:

                * ``@ivi`` to use :ref:`IVI <intro-configuring>`
                * ``@ni`` to use `NI-VISA <https://www.ni.com/visa/>`_ (only supported in PyVISA <1.12)
                * ``@py`` to use `PyVISA-py <https://pyvisa-py.readthedocs.io/en/stable/>`_
                * ``@sim`` to use `PyVISA-sim <https://pyvisa-sim.readthedocs.io/en/stable/>`_

            If :data:`None` then :attr:`~.config.Config.PyVISA_LIBRARY` will be used.

        Returns
        -------
        :class:`~pyvisa.highlevel.ResourceManager`
            The PyVISA_ Resource Manager.

        Raises
        ------
        ValueError
            If the PyVISA_ backend wrapper cannot be found.
        OSError
            If an IVI library cannot be found.
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

        try:
            return pyvisa.ResourceManager(visa_library)
        except ValueError as err:
            # as of PyVISA 1.11 the @ni backend became deprecated and it is planned
            # to be removed in 1.12, which is when the @ivi value must be used instead
            if str(err).endswith('pyvisa-ivi'):
                Config.PyVISA_LIBRARY = '@ni'
                return pyvisa.ResourceManager()
            raise

    @staticmethod
    def resource_class(record):
        """Get the PyVISA_ :ref:`Resource class <api_resources>`.

        Parameters
        ----------
        record : :class:`~.record_types.EquipmentRecord` or :class:`~.record_types.ConnectionRecord`
            An equipment or connection record from a :ref:`Database <database-formats>`.

        Returns
        -------
        A :class:`~pyvisa.resources.Resource` subclass
            The PyVISA_ Resource class that can open the `record`.
        """
        try:
            address = record.connection.address
        except AttributeError:
            address = record.address

        if not address:
            raise ValueError('The ConnectionRecord.address for {} has not been set'.format(record))

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

            raise ValueError('Cannot find a PyVISA resource class for {}'.format(address))
