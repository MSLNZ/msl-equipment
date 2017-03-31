"""
Records (rows) from the equipment-register database and the connection database.
"""
import datetime

from msl.equipment.constants import Backend, MSLInterface
from msl.equipment import factory


class EquipmentRecord(object):

    _alias = ''
    _asset_number = ''
    _category = ''
    _connection = None
    _date_calibrated = datetime.date(datetime.MINYEAR, 1, 1)
    _description = ''
    _location = ''
    _manufacturer = ''
    _model = ''
    _register = ''
    _section = ''
    _serial = ''

    def __init__(self, **kwargs):
        """
        Contains the information about an equipment record (a row) in an 
        Equipment-Register database.
        
        Args:
            **kwargs: The argument names can be any of the :class:`EquipmentRecord` 
                attribute names. Silently ignores all invalid argument names.

        Raises:
            ValueError: If the value of ``connection`` or ``date_calibrated`` is 
            invalid.
        """
        for attrib in EquipmentRecord.attributes():
            if attrib in kwargs:
                if attrib == 'connection' and not isinstance(kwargs[attrib], ConnectionRecord):
                    raise ValueError('The connection value must be a ConnectionRecord object')
                if attrib == 'date_calibrated' and not isinstance(kwargs[attrib], datetime.date):
                    raise ValueError('The date_calibrated value must be a datetime.date object')
                setattr(self, '_'+attrib, kwargs[attrib])

    @property
    def alias(self):
        """:py:class:`str`: An alias to use to associate with this equipment."""
        return self._alias

    @alias.setter
    def alias(self, text):
        self._alias = str(text)

    @property
    def asset_number(self):
        """:py:class:`str`: The IRL/CI asset number of the equipment."""
        return self._asset_number

    @property
    def category(self):
        """:py:class:`str`: The category (e.g., Laser, DMM) that the equipment belongs to."""
        return self._category

    @property
    def connection(self):
        """:class:`ConnectionRecord`: The information necessary to establish a connection to the equipment."""
        return self._connection

    @connection.setter
    def connection(self, connection_record):
        """
        Set the information necessary to establish a connection to the equipment.
        
        Args:
            connection_record (:class:`ConnectionRecord`): A connection record.
        """
        if not isinstance(connection_record, ConnectionRecord):
            raise TypeError('The connection type must be a ConnectionRecord object')
        self._connection = connection_record

    @property
    def date_calibrated(self):
        """:py:class:`datetime.date`: The date that the equipment was last calibrated."""
        return self._date_calibrated

    @property
    def description(self):
        """:py:class:`str`: A description of the equipment."""
        return self._description

    @property
    def location(self):
        """:py:class:`str`: The location where the equipment can usually be found."""
        return self._location

    @property
    def manufacturer(self):
        """:py:class:`str`: The name of the manufacturer of the equipment."""
        return self._manufacturer

    @property
    def model(self):
        """:py:class:`str`: The model number of the equipment."""
        return self._model

    @property
    def register(self):
        """:py:class:`str`: The value assigned, as in MSL Policy and Procedures, for any equipment
        that requires calibration or maintenance for projects."""
        return self._register

    @property
    def section(self):
        """:py:class:`str`: The MSL section (e.g., Light) that the equipment belongs to."""
        return self._section

    @property
    def serial(self):
        """:py:class:`str`: The serial number, or engraved unique ID, of the equipment."""
        return self._serial

    @staticmethod
    def attributes():
        """
        Returns:
            :py:class:`list`\[:py:class:`str`\]: A list of all the attribute names for an
            :class:`EquipmentRecord` object.
        """
        return [item for item in dir(EquipmentRecord) if not (item.startswith('_')
                                                              or item == 'attributes'
                                                              or item == 'connect'
                                                              )]

    def connect(self, demo=False):
        """
        Establish a connection to this equipment.

        Args:
            demo (bool): Whether to simulate a connection to the equipment by opening 
                a connection in demo mode. This allows you to call :meth:`~.Connection.write` 
                and :meth:`~.Connection.read` methods even if the equipment is not connected 
                to the computer. 

        Returns:
            A :class:`~msl.equipment.connection.Connection` object.

        Raises:
            ValueError: If any of the attribute values in :data:`connection` are invalid.
        """
        return factory.connect(self, demo)

    def __repr__(self):
        return '{}{}'.format(self.__class__.__name__,
                             {a: getattr(self, a) if a != 'connection' else self.connection
                              for a in self.attributes()})

    def __str__(self):
        return '{}<{}|{}|{}>'.format(self.__class__.__name__,
                                     self.manufacturer,
                                     self.model,
                                     self.serial)


class ConnectionRecord(object):

    _address = ''
    _backend = Backend.UNKNOWN
    _interface = MSLInterface.NONE
    _manufacturer = ''
    _model = ''
    _properties = {}
    _serial = ''

    def __init__(self, **kwargs):
        """
        Contains the information about a connection record (a row) in a connection 
        database.

        Args:
            **kwargs: The argument names can be any of the :class:`ConnectionRecord` 
                attribute names. Silently ignores all invalid argument names.
        
        Raises:
            ValueError: If the value of ``backend``, ``interface`` or ``properties`` 
            is invalid.
        """
        for attrib in ConnectionRecord.attributes():
            if attrib in kwargs:
                if attrib == 'backend':
                    self._backend = Backend(kwargs[attrib])
                elif attrib == 'interface':
                    self._interface = MSLInterface(kwargs[attrib])
                elif attrib == 'properties':
                    if isinstance(kwargs[attrib], dict):
                        self._properties = kwargs[attrib]
                    else:
                        raise ValueError('The properties value must be a dictionary.')
                else:
                    setattr(self, '_'+attrib, kwargs[attrib])

    @property
    def address(self):
        """
        :py:class:`str`: The address to use for the connection (see here_ for examples from PyVISA_).

        .. _here: https://pyvisa.readthedocs.io/en/stable/names.html#visa-resource-syntax-and-examples
        .. _PyVISA: http://pyvisa.readthedocs.io/en/stable/index.html
        """
        return self._address

    @property
    def backend(self):
        """:class:`~.constants.Backend`: The backend to use to communicate with the equipment."""
        return self._backend

    @property
    def interface(self):
        """
        :class:`~.constants.MSLInterface`: The interface to use for the communication 
        system that transfers data between a computer and the equipment
        (only used if the ``backend`` is :data:`Backend.MSL <msl.equipment.constants.Backend.MSL>`).
        """
        return self._interface

    @property
    def manufacturer(self):
        """:py:class:`str`: The name of the manufacturer of the equipment."""
        return self._manufacturer

    @property
    def model(self):
        """:py:class:`str`: The model number of the equipment."""
        return self._model

    @property
    def properties(self):
        """
        :py:class:`dict`: Additional properties that are required to establish
        a connection to the equipment, e.g., for a Serial connection 
        {'baud_rate': 11920, 'data_bits': 8}
        """
        return self._properties

    @property
    def serial(self):
        """:py:class:`str`: The serial number, or engraved unique ID, of the equipment."""
        return self._serial

    @staticmethod
    def attributes():
        """
        Returns:
            :py:class:`list`\[:py:class:`str`\]: A list of all the attribute names for a
            :class:`ConnectionRecord` object.
        """
        return [item for item in dir(ConnectionRecord) if not (item.startswith('_')
                                                               or item == 'attributes'
                                                               )]

    def __str__(self):
        return '{}<{}|{}|{}>'.format(self.__class__.__name__,
                                     self.manufacturer,
                                     self.model,
                                     self.serial)

    def __repr__(self):
        return '{}{}'.format(self.__class__.__name__,
                             {a: getattr(self, a) for a in self.attributes()})
