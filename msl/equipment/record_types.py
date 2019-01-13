"""
Records from :ref:`equipment_database`\'s or :ref:`connections_database`\'s.
"""
from __future__ import unicode_literals
import re
import logging
import datetime
from enum import Enum
from xml.etree.cElementTree import Element

from dateutil.relativedelta import relativedelta

from .utils import convert_to_enum
from .constants import (
    Parity,
    StopBits,
    DataBits,
    Backend,
    MSLInterface,
    MSL_INTERFACE_ALIASES,
    LF,
    CR,
)

logger = logging.getLogger(__name__)

_interface_regex = re.compile(r'[+_A-Z]+')


class EquipmentRecord(object):

    # Valid property names for an EquipmentRecord
    _NAMES = ['alias', 'calibration_cycle', 'category', 'connection',
             'date_calibrated', 'description', 'latest_report_number',
             'location', 'manufacturer', 'model', 'serial', 'team', 'user_defined']

    def __init__(self, **kwargs):
        """Contains the information about an equipment record in an :ref:`equipment_database`.

        Parameters
        ----------
        **kwargs
            The argument names can be any of the :class:`EquipmentRecord` attribute names.
            Any kwargs that are not one of the *standard* attribute names gets added to the
            :attr:`.user_defined` :class:`dict`.
        """

        # The following attributes are NOT defined as fields in the equipment-register database
        self._alias = kwargs.get('alias', '')
        self._connection = None
        self._team = kwargs.get('team', '')
        self._user_defined = {}

        # The following attributes can be defined as fields in the equipment-register database
        # IMPORTANT: When a new attribute is added below remember to include it in
        #            "Field Names" section in docs/database.rst
        self._calibration_cycle = 0.0
        self._category = kwargs.get('category', '')
        self._date_calibrated = datetime.date(datetime.MINYEAR, 1, 1)
        self._description = kwargs.get('description', '')
        self._latest_report_number = kwargs.get('latest_report_number', '')
        self._location = kwargs.get('location', '')
        self._manufacturer = kwargs.get('manufacturer', '')
        self._model = kwargs.get('model', '')
        self._serial = kwargs.get('serial', '')

        # date_calibrated
        try:
            date = kwargs['date_calibrated']
        except KeyError:
            pass
        else:
            if isinstance(date, datetime.date):
                self._date_calibrated = date
            else:
                raise TypeError('The "date_calibrated" must be a datetime.date object')

        # calibration_cycle
        try:
            cc = kwargs['calibration_cycle']
        except KeyError:
            pass
        else:
            self._calibration_cycle = max(0.0, float(cc))

        for name in kwargs:
            if name not in EquipmentRecord._NAMES:
                self._user_defined[name] = kwargs[name]

        if 'connection' in kwargs:
            self.connection = kwargs['connection']

        # the manufacturer, model and serial cannot change once an EquipmentRecord is created
        self._str = u'EquipmentRecord<{}|{}|{}>'.format(self._manufacturer, self._model, self._serial)

    def __repr__(self):
        # the alias and the connection can be updated so we cannot cache the __repr__
        out = []
        for name in EquipmentRecord._NAMES:
            if name == 'connection':
                if not self._connection:
                    out.append('connection: None')
                else:
                    out.append('connection:')
                    for line in repr(self._connection).splitlines():
                        out.append('  ' + line)
            elif name == 'user_defined':
                if not self._user_defined:
                    out.append('user_defined: {}')
                else:
                    out.append('user_defined:')
                    for key in sorted(self._user_defined):
                        out.append('  {}: {!r}'.format(key, self._user_defined[key]))
            else:
                out.append('{}: {!r}'.format(name, getattr(self, name)))
        return '\n'.join(out)

    def __str__(self):
        return self._str

    @property
    def alias(self):
        """:class:`str`: An alias to use to reference this equipment by.

        The `alias` can be defined in different in 3 ways:

        * in the **<equipment>** XML tag in a :ref:`configuration_file`
        * in the **Properties** field in a :ref:`connections_database`
        * by redefining the `alias` value after the :class:`EquipmentRecord` has been instantiated

        """
        return self._alias

    @alias.setter
    def alias(self, text):
        self._alias = text

    @property
    def calibration_cycle(self):
        """:class:`float`: The number of years that can pass before the equipment must be re-calibrated."""
        return self._calibration_cycle

    @property
    def category(self):
        """:class:`str`: The category (e.g., Laser, DMM) that the equipment belongs to."""
        return self._category

    @property
    def connection(self):
        """:class:`ConnectionRecord` or :data:`None`: The information necessary to
        establish a connection to the equipment."""
        return self._connection

    @connection.setter
    def connection(self, record):
        """Set the information necessary to establish a connection to the equipment.

        Parameters
        ----------
        record : :class:`ConnectionRecord`
            A connection record.

        Raises
        ------
        TypeError
            If `connection_record` is not of type :class:`ConnectionRecord`.
        ValueError
            If any of the `manufacturer`, `model`, `serial` values in `record`
            are defined and they do not match those values in this :class:`EquipmentRecord`.
        """
        if not isinstance(record, ConnectionRecord):
            raise TypeError('Must pass in a ConnectionRecord object')

        # ensure that the manufacturer, model and serial match
        for attrib in ('_manufacturer', '_model', '_serial'):
            if not getattr(record, attrib):
                # then it was not set in the connection_record
                setattr(record, attrib, getattr(self, attrib))
            elif getattr(record, attrib) != getattr(self, attrib):
                msg = 'ConnectionRecord.{0} ({1}) != EquipmentRecord.{0} ({2})'\
                    .format(attrib[1:], getattr(record, attrib), getattr(self, attrib))
                raise ValueError(msg)

        self._connection = record

    @property
    def date_calibrated(self):
        """:class:`datetime.date`: The date that the equipment was last calibrated.

        If the equipment has never been calibrated then the date is defined as
        year=1, month=1, day=1.
        """
        return self._date_calibrated

    @property
    def description(self):
        """:class:`str`: A description of the equipment."""
        return self._description

    @property
    def latest_report_number(self):
        """:class:`str`: The report number for the last time that the equipment was calibrated."""
        return self._latest_report_number

    @property
    def location(self):
        """:class:`str`: The location where the equipment can usually be found."""
        return self._location

    @property
    def manufacturer(self):
        """:class:`str`: The name of the manufacturer of the equipment."""
        return self._manufacturer

    @property
    def model(self):
        """:class:`str`: The model number of the equipment."""
        return self._model

    @property
    def serial(self):
        """:class:`str`: The serial number, or engraved unique ID, of the equipment."""
        return self._serial

    @property
    def team(self):
        """:class:`str`: The team (e.g., Light Standards) that the equipment belongs to."""
        return self._team

    @property
    def user_defined(self):
        """:class:`dict`: User-defined, key-value pairs for the :class:`EquipmentRecord`.

        All \*\*kwargs that are passed to the :class:`EquipmentRecord` when it is instantiated
        that are not part of the *standard* attributes for an :class:`EquipmentRecord`
        are added to the *user_defined* :class:`dict`.

        Examples
        --------
        ::

            >>> from msl.equipment import EquipmentRecord
            >>> record = EquipmentRecord(manufacturer='ABC', model='XYZ', chocolate='sugar', one=1)
            >>> record.manufacturer  # doctest: +SKIP
            'ABC'
            >>> record.model  # doctest: +SKIP
            'XYZ'
            >>> record.user_defined  # doctest: +SKIP
            {'chocolate': 'sugar', 'one': 1}

        """
        return self._user_defined

    def connect(self, demo=None):
        """Establish a connection to the equipment.

        Calls the :func:`~msl.equipment.factory.connect` function.

        Parameters
        ----------
        demo : :class:`bool`, optional
            Whether to simulate a connection to the equipment by opening
            a connection in demo mode. This allows you to test your code
            if the equipment is not physically connected to a computer.

            If :data:`None` then the `demo` value is determined from the
            :attr:`~.config.Config.DEMO_MODE` attribute.

        Returns
        -------
        A :class:`~msl.equipment.connection.Connection` subclass.
        """
        from msl.equipment import factory  # import here to avoid circular imports
        return factory.connect(self, demo)

    def is_calibration_due(self, months=0):
        """Whether the equipment needs to be re-calibrated.

        Parameters
        ----------
        months : :class:`int`
            The number of months to add to today's date to determine if
            the equipment needs to be re-calibrated within a certain amount
            of time. For example, if ``months = 6`` then that is a way of
            asking *"is a re-calibration due within the next 6 months?"*.

        Returns
        -------
        :class:`bool`
            :data:`True` if the equipment needs to be re-calibrated, :data:`False`
            if it does not need to be re-calibrated (or it has never been calibrated).
        """
        if self._date_calibrated.year == datetime.MINYEAR or self._calibration_cycle == 0.0:
            return False
        date = datetime.date.today() + relativedelta(months=max(0, int(months)))
        return date > self.next_calibration_date()

    def next_calibration_date(self):
        """The date that the next calibration is due.

        Returns
        -------
        :class:`datetime.date`
            The next calibration date (or :data:`None` it has never been calibrated)."""
        if self._date_calibrated.year == datetime.MINYEAR:
            return None
        years = int(self._calibration_cycle)
        months = int(round(12 * (self._calibration_cycle - years)))
        return self._date_calibrated + relativedelta(years=years, months=months)

    def to_dict(self):
        """Convert this :class:`EquipmentRecord` to a :class:`dict`.

        Returns
        -------
        :class:`dict`
            The :class:`EquipmentRecord` as a :class:`dict`.
        """
        return {
            'alias': self._alias,
            'calibration_cycle': self._calibration_cycle,
            'category': self._category,
            'connection': None if self._connection is None else self._connection.to_dict(),
            'date_calibrated': self._date_calibrated,
            'description': self._description,
            'latest_report_number': self._latest_report_number,
            'location': self._location,
            'manufacturer': self._manufacturer,
            'model': self._model,
            'serial': self._serial,
            'team': self._team,
            'user_defined': self._user_defined,
        }

    def to_xml(self):
        """Convert this :class:`EquipmentRecord` to an XML :class:`~xml.etree.ElementTree.Element`.

        All values of the :class:`EquipmentRecord` are converted to a :class:`str`.

        Returns
        -------
        :class:`~xml.etree.ElementTree.Element`
            The :class:`EquipmentRecord` as an XML element.
        """
        root = Element('EquipmentRecord')
        for name in EquipmentRecord._NAMES:
            element = Element(name)
            if name == 'connection':
                if self._connection is None:
                    element.text = ''
                else:
                    for sub_element in self._connection.to_xml():
                        element.append(sub_element)
            elif name == 'date_calibrated':
                date = self._date_calibrated
                element.text = '' if date.year == datetime.MINYEAR else date.isoformat()
                element.attrib['format'] = 'YYYY-MM-DD'
            elif name == 'calibration_cycle':
                if self._calibration_cycle == 0:
                    element.text = ''
                elif int(self._calibration_cycle) == self._calibration_cycle:
                    element.text = str(int(self._calibration_cycle))
                else:
                    element.text = str(self._calibration_cycle)
                element.attrib['units'] = 'years'
            elif name == 'user_defined':
                if not self._user_defined:
                    element.text = ''
                else:
                    for prop_key in sorted(self._user_defined):
                        prop = Element(prop_key)
                        prop.text = '{}'.format(self._user_defined[prop_key])
                        element.append(prop)
            else:
                element.text = getattr(self, name)
            root.append(element)
        return root


class ConnectionRecord(object):

    # Valid property names for a ConnectionRecord
    _NAMES = ['address', 'backend', 'interface', 'manufacturer', 'model', 'properties', 'serial']

    _LF = ['\\n', "'\\n'", '"\\n"']
    _CR = ['\\r', "'\\r'", '"\\r"']
    _CRLF = ['\\r\\n', "'\\r\\n'", '"\\r\\n"']

    def __init__(self, **kwargs):
        """Contains the information about a connection record in a :ref:`connections_database`.

        Parameters
        ----------
        **kwargs
            The argument names can be any of the :class:`ConnectionRecord` attribute names.
            Any kwargs that are not one of the *standard* attribute names gets added to the
            :attr:`.properties` :class:`dict`.
        """

        # The following attributes are NOT defined as fields in the connection database
        self._interface = MSLInterface.NONE

        # The following attributes can be defined as fields in the connection database
        # IMPORTANT: When a new attribute is added below remember to include it in
        #            "Field Names" section in docs/database.rst
        self._address = kwargs.get('address', '')
        self._backend = Backend.UNKNOWN
        self._manufacturer = kwargs.get('manufacturer', '')
        self._model = kwargs.get('model', '')
        self._properties = {}
        self._serial = kwargs.get('serial', '')

        # update the backend
        try:
            backend = kwargs['backend']
        except KeyError:
            pass
        else:
            if isinstance(backend, int):
                self._backend = Backend(backend)
            else:
                self._backend = Backend.__members__.get(backend)
                if self._backend is None:
                    raise ValueError('{!r} is not a valid Backend'.format(backend))

        # update the interface
        try:
            interface = kwargs['interface']
        except KeyError:
            pass
        else:
            if isinstance(interface, int):
                self._interface = MSLInterface(interface)
            else:
                self._interface = MSLInterface.__members__.get(interface)
                if self._interface is None:
                    raise ValueError('{!r} is not a valid MSLInterface'.format(interface))

        if self._backend == Backend.MSL and self._interface == MSLInterface.NONE:
            self._interface = self._get_interface_from_address()

        # use the setter method to set the properties
        try:
            self.properties = kwargs['properties']
        except KeyError:
            pass

        if self._address.startswith('UDP'):
            self._properties['socket_type'] = 'SOCK_DGRAM'

        for name in kwargs:
            if name not in ConnectionRecord._NAMES:
                self._properties[name] = kwargs[name]

        # the manufacturer, model and serial cannot change once a ConnectionRecord is created
        self._str = 'ConnectionRecord<{}|{}|{}>'.format(self._manufacturer, self._model, self._serial)

    def __repr__(self):
        # the properties can be updated so we cannot cache the __repr__
        # (and sometimes the interface can change if there is an MSL Resource defined for the
        # EquipmentRecord, for example, the Resource uses an SDK but the address=COM5)
        out = []
        for name in ConnectionRecord._NAMES:
            if name == 'properties':
                if not self._properties:
                    out.append('properties: {}')
                else:
                    out.append('properties:')
                    for key in sorted(self._properties):
                        out.append('  {}: {!r}'.format(key, self._properties[key]))
            else:
                out.append('{}: {!r}'.format(name, getattr(self, name)))
        return '\n'.join(out)

    def __str__(self):
        return self._str

    @property
    def address(self):
        """:class:`str`: The address to use for the connection (see :ref:`address_syntax` for examples)."""
        return self._address

    @property
    def backend(self):
        """:class:`~.constants.Backend`: The backend to use to communicate with the equipment."""
        return self._backend

    @property
    def interface(self):
        """:class:`~.constants.MSLInterface`: The interface that is used for the
        communication system that transfers data between a computer and the equipment
        (only used if the :attr:`.backend` is equal to :attr:`~.constants.Backend.MSL`).
        """
        return self._interface

    @property
    def manufacturer(self):
        """:class:`str`: The name of the manufacturer of the equipment."""
        return self._manufacturer

    @property
    def model(self):
        """:class:`str`: The model number of the equipment."""
        return self._model

    @property
    def properties(self):
        """
        :class:`dict`: Additional properties that may be required to connect to the equipment.

        For example, communicating via RS-232 may require::

            {'baud_rate': 19200, 'parity': 'even'}

        See the :ref:`connections_database` for examples on how to set the `properties`.
        """
        return self._properties

    @properties.setter
    def properties(self, props):
        if not isinstance(props, dict):
            raise TypeError('The "properties" must be a dictionary')
        self._properties = props.copy()

        # update the Enums for a SERIAL connection
        is_serial = self._interface == MSLInterface.SERIAL
        if not is_serial:
            for alias in MSL_INTERFACE_ALIASES['SERIAL']:
                if self._address.startswith(alias):
                    is_serial = True
                    break

        for key, value in props.items():
            if is_serial:
                k_lower = key.lower()
                if k_lower == 'parity':
                    self._properties[key] = convert_to_enum(value, Parity, to_upper=True)
                elif k_lower.startswith('stop'):
                    self._properties[key] = convert_to_enum(value, StopBits, to_upper=True)
                elif k_lower.startswith('data'):
                    self._properties[key] = convert_to_enum(value, DataBits, to_upper=True)
            if key.endswith('termination'):
                if value in ConnectionRecord._CRLF:  # must check before LR and CR checks
                    self._properties[key] = CR + LF
                elif value in ConnectionRecord._LF:
                    self._properties[key] = LF
                elif value in ConnectionRecord._CR:
                    self._properties[key] = CR

    @property
    def serial(self):
        """:class:`str`: The serial number, or engraved unique ID, of the equipment."""
        return self._serial

    def to_dict(self):
        """Convert this :class:`ConnectionRecord` to a :class:`dict`.

        Returns
        -------
        :class:`dict`
            The :class:`ConnectionRecord` as a :class:`dict`.
        """
        return {
            'address': self._address,
            'backend': self._backend,
            'interface': self._interface,
            'manufacturer': self._manufacturer,
            'model': self._model,
            'properties': self._properties,
            'serial': self._serial,
        }

    def to_xml(self):
        """Convert this :class:`ConnectionRecord` to an XML :class:`~xml.etree.ElementTree.Element`.

        Note
        ----
        All values of the :class:`ConnectionRecord` are converted to a :class:`str`.

        Returns
        -------
        :class:`~xml.etree.ElementTree.Element`
            The :class:`ConnectionRecord` as a XML :class:`~xml.etree.ElementTree.Element`.
        """
        root = Element('ConnectionRecord')
        for name in ConnectionRecord._NAMES:
            value = getattr(self, name)
            element = Element(name)
            if name == 'properties':
                if not self._properties:
                    element.text = ''
                else:
                    for prop_key in sorted(self._properties):
                        prop_value = self._properties[prop_key]
                        prop = Element(prop_key)
                        if isinstance(prop_value, Enum):
                            prop.text = prop_value.name
                        elif prop_key.endswith('termination'):
                            prop.text = repr(prop_value)
                        elif isinstance(prop_value, bytes):
                            prop.text = repr(prop_value)
                        else:
                            prop.text = '{}'.format(prop_value)
                        element.append(prop)
            elif isinstance(value, Enum):
                element.text = value.name
            else:
                element.text = '{}'.format(value)
            root.append(element)
        return root

    def _get_interface_from_address(self):
        """Get the interface based on the address value.

        Returns
        -------
        :class:`MSLInterface`
            The interface.

        Raises
        ------
        ValueError
            If the interface cannot be determined from the value of address.
        """
        if not self._address:
            return MSLInterface.NONE

        address_upper = self._address.upper()

        # checks for equivalent PyVISA addresses
        if address_upper.startswith('TCPIP') and address_upper.endswith('SOCKET'):
            return MSLInterface.SOCKET

        # determine the name of the interface
        match = _interface_regex.match(address_upper)
        interface_name = '' if match is None else match.group(0).replace('+', '_')

        try:
            return MSLInterface[interface_name]
        except KeyError:
            pass

        # check if an alias is used for the name of the interface
        for name, values in MSL_INTERFACE_ALIASES.items():
            for value in values:
                if interface_name.startswith(value):
                    return MSLInterface[name]

        raise ValueError('Cannot determine the MSLInterface from address {!r}'.format(self._address))
