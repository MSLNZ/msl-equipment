"""
A record from an **Equipment-Register** database or a **Connections** database.
"""
import re
import logging
import datetime

from dateutil.relativedelta import relativedelta

from msl.equipment import factory
from msl.equipment.constants import Backend, MSLInterface, MSL_INTERFACE_ALIASES

logger = logging.getLogger(__name__)


class EquipmentRecord(object):

    def __init__(self, **kwargs):
        """Contains the information about an equipment record in an 
        **Equipment-Register** database.
        
        Parameters
        ----------
        **kwargs
            The argument names can be any of the :class:`EquipmentRecord` attribute names.

        Raises
        ------
        ValueError
            If an argument name is `calibration_period` and the value cannot be converted
            to an :obj:`float`.
        TypeError
            If an argument name is `connection` or `date_calibrated` and the data type of
            the value is invalid.
        AttributeError
            If an argument name is not an :class:`EquipmentRecord` attribute.
        
        Examples
        --------
        Equipment records **should** be defined in a database and instantiated by 
        calling :obj:`msl.equipment.config.load`; however, you can still
        manually create an equipment record.
        
        >>> from msl.equipment import EquipmentRecord, ConnectionRecord, Backend
        >>> record = EquipmentRecord(
        ...              manufacturer='Pico Technology',
        ...              model='5244B',
        ...              serial='DY135/055',
        ...              connection=ConnectionRecord(
        ...                  backend=Backend.MSL,
        ...                  address='SDK::PicoScope5000A::ps5000a',
        ...                  properties={
        ...                      'resolution': '14bit',  # only used for ps5000a series PicoScope's
        ...                      'auto_select_power': True,  # for PicoScopes that can be powered by an AC adaptor or by a USB cable
        ...                  },
        ...              )
        ...          )
        
        """
        self._alias = ''
        self._asset_number = ''
        self._calibration_period = 0.0
        self._category = ''
        self._connection = None
        self._date_calibrated = datetime.date(datetime.MINYEAR, 1, 1)
        self._description = ''
        self._location = ''
        self._manufacturer = ''
        self._model = ''
        self._register = ''
        self._section = ''
        self._serial = ''

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
                        raise TypeError('The date_calibrated value must be a datetime.date object')
                elif attrib == 'calibration_period':
                    try:
                        self._calibration_period = max(0.0, float(kwargs[attrib]))
                        err = ''
                    except ValueError:
                        err = 'The calibration_period must be a number.'
                    if err:
                        raise ValueError(err)
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
        """:obj:`str`: An alias to use to associate with this equipment."""
        return self._alias

    @alias.setter
    def alias(self, text):
        self._alias = str(text)

    @property
    def asset_number(self):
        """:obj:`str`: The IRL/CI asset number of the equipment."""
        return self._asset_number

    @property
    def calibration_period(self):
        """:obj:`float`: The number of years that can pass before the equipment must be re-calibrated."""
        return self._calibration_period

    @property
    def category(self):
        """:obj:`str`: The category (e.g., Laser, DMM) that the equipment belongs to."""
        return self._category

    @property
    def connection(self):
        """:class:`ConnectionRecord`: The information necessary to establish a connection to the equipment."""
        return self._connection

    @connection.setter
    def connection(self, connection_record):
        """Set the information necessary to establish a connection to the equipment.
        
        Parameters
        ----------
        connection_record : :class:`ConnectionRecord`
            A connection record.
        
        Raises
        ------
        TypeError
            If `connection_record` is not of type :class:`ConnectionRecord`.            
        ValueError
            If any of the `manufacturer`, `model`, `serial` values in the `connection_record` 
            are set and they do not match those values in this :class:`EquipmentRecord`.
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
        """:class:`datetime.date`: The date that the equipment was last calibrated."""
        return self._date_calibrated

    @property
    def description(self):
        """:obj:`str`: A description of the equipment."""
        return self._description

    @property
    def location(self):
        """:obj:`str`: The location where the equipment can usually be found."""
        return self._location

    @property
    def manufacturer(self):
        """:obj:`str`: The name of the manufacturer of the equipment."""
        return self._manufacturer

    @property
    def model(self):
        """:obj:`str`: The model number of the equipment."""
        return self._model

    @property
    def register(self):
        """:obj:`str`: The value assigned, as in MSL Policy and Procedures, for any equipment
        that requires calibration or maintenance for projects."""
        return self._register

    @property
    def section(self):
        """:obj:`str`: The MSL section (e.g., P&R) that the equipment belongs to."""
        return self._section

    @property
    def serial(self):
        """:obj:`str`: The serial number, or engraved unique ID, of the equipment."""
        return self._serial

    @staticmethod
    def attributes():
        """:obj:`list` of :obj:`str`: A list of all the attribute names for an 
        :class:`EquipmentRecord` object.
        """
        return [item for item in dir(EquipmentRecord) if not (item.startswith('_')
                                                              or item == 'attributes'
                                                              or item == 'connect'
                                                              or item == 'is_calibration_due'
                                                              or item == 'next_calibration_date'
                                                              )]

    def connect(self, demo=None):
        """Establish a connection to the equipment.

        Parameters
        ----------
        demo : :obj:`bool` or :obj:`None`
            Whether to simulate a connection to the equipment by opening
            a connection in demo mode. This allows you run your code if the 
            equipment is not physically connected to the computer.
            
            If :data:`None` then the `demo` value is read from a :obj:`~.config.CONFIG`
            variable. See :obj:`msl.equipment.config.load` for more details.

        Returns
        -------
        :class:`~msl.equipment.connection.Connection`
            A :class:`~msl.equipment.connection.Connection`-type object.

        Raises
        ------
        ValueError
            If any of the property values in
            :obj:`record.connection.properties <.ConnectionRecord.properties>`
            are invalid.
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

    def is_calibration_due(self, months=0):
        """Whether the equipment needs to be re-calibrated.

        Parameters
        ----------
        months : :obj:`int`
            The number of months to add to today's date to determine if
            the equipment needs to be re-calibrated within a certain amount
            of time. For example, if `months` = ``6`` then that is a way of
            asking "is a re-calibration due within the next 6 months?".

        Returns
        -------
        :obj:`bool`
            :obj:`True` if the equipment needs to be re-calibrated, :obj:`False`
            if it does not need to be re-calibrated.
        """
        if self.date_calibrated.year == datetime.MINYEAR or self.calibration_period == 0.0:
            return False
        ask_date = datetime.date.today() + relativedelta(months=max(0, months))
        return ask_date >= self.next_calibration_date()

    def next_calibration_date(self):
        """:obj:`datetime.date`: The next date that a re-calibration is due."""
        years = int(self.calibration_period)
        months = round(12*(self.calibration_period - years))
        return self.date_calibrated + relativedelta(years=years, months=months)


class ConnectionRecord(object):

    def __init__(self, **kwargs):
        """Contains the information about a connection record in a **Connections** 
        database.

        Parameters
        ----------
        **kwargs
            The argument names can be any of the :class:`ConnectionRecord` attribute names.
        
        Raises
        ------
        ValueError
            If an argument name is `backend`, `interface` or `properties` and the 
            value is invalid.
        AttributeError
            If a named argument is not an :class:`ConnectionRecord` attribute name.
        
        Examples
        --------
        Connection records **should** be defined in a database and instantiated by 
        calling :obj:`msl.equipment.config.load`; however, you can still
        manually create a connection record.
        
        >>> from msl.equipment import ConnectionRecord, Backend
        >>> record = ConnectionRecord(
        ...              manufacturer='Pico Technology',
        ...              model='5244B',
        ...              serial='DY135/055',
        ...              backend=Backend.MSL,
        ...              address='SDK::PicoScope5000A::ps5000a',
        ...              properties={
        ...                  'resolution': '14bit',  # only used for ps5000a series PicoScope's
        ...                  'auto_select_power': True,  # for PicoScopes that can be powered by an AC adaptor or by a USB cable
        ...              }
        ...          )
        
        """
        self._address = ''
        self._backend = Backend.UNKNOWN
        self._interface = MSLInterface.NONE
        self._manufacturer = ''
        self._model = ''
        self._properties = {}
        self._serial = ''

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
        """:obj:`str`: The address to use for the connection (see here_ for examples
        from National Instruments).

        .. _here: http://zone.ni.com/reference/en-XX/help/370131S-01/ni-visa/visaresourcesyntaxandexamples/
        """
        return self._address

    @property
    def backend(self):
        """:class:`~.constants.Backend`: The backend to use to communicate with the equipment."""
        return self._backend

    @property
    def interface(self):
        """:class:`~.constants.MSLInterface`: The interface to use for the communication 
        system that transfers data between a computer and the equipment
        (only used if the `backend` is :data:`Backend.MSL <msl.equipment.constants.Backend.MSL>`).
        """
        return self._interface

    @property
    def manufacturer(self):
        """:obj:`str`: The name of the manufacturer of the equipment."""
        return self._manufacturer

    @property
    def model(self):
        """:obj:`str`: The model number of the equipment."""
        return self._model

    @property
    def properties(self):
        """:obj:`dict`: Additional properties that may be used to establish
        a connection to the equipment, e.g., for a Serial connection 
        ``{'baud_rate': 11920, 'data_bits': 8}``.
        """
        return self._properties

    @property
    def serial(self):
        """:obj:`str`: The serial number, or engraved unique ID, of the equipment."""
        return self._serial

    @staticmethod
    def attributes():
        """:obj:`list` of :obj:`str`: A list of all the attribute names for a
        :class:`ConnectionRecord` object.
        """
        return [item for item in dir(ConnectionRecord) if not (item.startswith('_') or item == 'attributes')]

    def _set_msl_interface(self):
        """Set the `interface` based on the `address`"""

        # determine the MSLInterface
        match = re.match('[+_A-Z]+', self._address.upper())
        interface = '' if match is None else match.group(0).replace('+', '_')

        # check if aliases are used for the MSL interface
        for name, values in MSL_INTERFACE_ALIASES.items():
            for value in values:
                if value in interface:
                    interface = interface.replace(value, name)

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
