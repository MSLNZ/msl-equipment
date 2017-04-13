"""
A record (a row) from an **Equipment-Register** database and a **Connections** database.
"""
import re
import logging
import datetime

from msl.equipment.constants import Backend, MSLInterface, MSL_INTERFACE_ALIASES
from msl.equipment import factory

logger = logging.getLogger(__name__)


class EquipmentRecord(object):

    _alias = ''
    _asset_number = ''
    _calibration_period = 0
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
        **Equipment-Register** database.
        
        Args:
            **kwargs: The argument names can be any of the :class:`EquipmentRecord` 
                attribute names.

        Raises:
            ValueError: If an argument name is ``calibration_period``, ``connection`` or 
                ``date_calibrated`` and the value is invalid.
            
            AttributeError: If a named argument is not an :class:`EquipmentRecord` 
                attribute name.
        """
        valid_attribs = EquipmentRecord.attributes()
        for attrib in kwargs:
            if attrib in valid_attribs:
                if attrib == 'connection':
                    # set the connection after the manufacturer, model and serial are all set
                    continue
                elif attrib == 'date_calibrated':
                    if isinstance(kwargs[attrib], datetime.date):
                        self._date_calibrated = kwargs[attrib]
                    else:
                        raise ValueError('The date_calibrated value must be a datetime.date object')
                elif attrib == 'calibration_period':
                    self._calibration_period = int(kwargs[attrib])
                else:
                    setattr(self, '_'+attrib, str(kwargs[attrib]))
            else:
                msg = 'An EquipmentRecord has no "{}" attribute.\nValid attributes are {}'\
                    .format(attrib, valid_attribs)
                raise AttributeError(msg)

        if 'connection' in kwargs:
            self.connection = kwargs['connection']

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
    def calibration_period(self):
        """:py:class:`int`: The number of years that can pass before the equipment must be recalibrated."""
        return self._calibration_period

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
        
        Raises:
            TypeError: If ``connection_record`` is not of type :class:`ConnectionRecord`.
            
            ValueError: If any of the ``manufacturer``, ``model``, ``serial`` values in 
            the ``connection_record`` are set and they do not match those values in this
            :class:`EquipmentRecord`.
        """
        if not isinstance(connection_record, ConnectionRecord):
            raise TypeError('The connection record must be a ConnectionRecord object')

        # check that the manufacturer, model number and serial number match
        for attrib in ('_manufacturer', '_model', '_serial'):
            if not getattr(connection_record, attrib):
                # it was not set in the connection_record
                setattr(connection_record, attrib, getattr(self, attrib))
            elif getattr(connection_record, attrib) != getattr(self, attrib):
                msg = 'ConnectionRecord.{0} ({1}) != EquipmentRecord.{0} ({2})'\
                    .format(attrib[1:], getattr(connection_record, attrib), getattr(self, attrib))
                raise ValueError(msg)

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
        """:py:class:`str`: The MSL section (e.g., P&R) that the equipment belongs to."""
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
                a connection in demo mode. This allows you run your code if the equipment 
                is not connected to the computer. 

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
        Contains the information about a connection record (a row) in a **Connections** 
        database.

        Args:
            **kwargs: The argument names can be any of the :class:`ConnectionRecord` 
                attribute names.
        
        Raises:
            ValueError: If an argument name is ``backend``, ``interface`` or 
                ``properties`` and the value is invalid.

            AttributeError: If a named argument is not an :class:`ConnectionRecord` 
                attribute name.
        """
        valid_attribs = ConnectionRecord.attributes()
        for attrib in kwargs:
            if attrib in valid_attribs:
                if attrib == 'backend':
                    self._backend = Backend(kwargs[attrib])
                elif attrib == 'interface':
                    raise ValueError('Cannot manually set the MSL interface. '
                                     'It is automatically set based on the value of the address.')
                elif attrib == 'address':
                    self._address = str(kwargs[attrib])
                    if 'backend' in kwargs and kwargs['backend'] == Backend.MSL:
                        bad_interface = self._set_msl_interface()
                        if bad_interface:
                            raise ValueError('Unknown MSL Interface "{}"'.format(bad_interface))
                elif attrib == 'properties':
                    if isinstance(kwargs[attrib], dict):
                        self._properties = kwargs[attrib]
                    else:
                        raise ValueError('The properties value must be a dictionary.')
                else:
                    setattr(self, '_'+attrib, str(kwargs[attrib]))
            else:
                msg = 'A ConnectionRecord has no "{}" attribute.\nValid attributes are {}'\
                    .format(attrib, valid_attribs)
                raise AttributeError(msg)

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

    def _set_msl_interface(self):
        """Set the ``interface`` based on the ``address``"""

        # determine the MSLInterface
        match = re.match('[+_A-Z]+', self._address.upper())
        interface = '' if match is None else match.group(0).replace('+', '_')

        # check if aliases are used for the MSL interface
        for name, values in MSL_INTERFACE_ALIASES.items():
            for value in values:
                if value in interface:
                    interface = interface.replace(value, name)
                    self._address = self._address.replace(value, name)

        # set the interface
        if interface in MSLInterface.__members__:
            self._interface = MSLInterface[interface]
            return ''
        return interface

    def __str__(self):
        return '{}<{}|{}|{}>'.format(self.__class__.__name__,
                                     self.manufacturer,
                                     self.model,
                                     self.serial)

    def __repr__(self):
        return '{}{}'.format(self.__class__.__name__,
                             {a: getattr(self, a) for a in self.attributes()})
