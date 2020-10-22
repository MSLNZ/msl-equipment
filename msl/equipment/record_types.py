"""
Records from :ref:`equipment-database`\'s or :ref:`connections-database`\'s.
"""
from __future__ import unicode_literals
import json
import datetime
from enum import Enum
from xml.etree.cElementTree import Element
from collections import OrderedDict
try:
    from collections.abc import Mapping
except ImportError:
    from collections import Mapping  # Python 2.7

from dateutil.relativedelta import relativedelta

from .utils import (
    convert_to_enum,
    convert_to_date,
)
from .constants import (
    Parity,
    StopBits,
    DataBits,
    Backend,
    MSLInterface,
    LF,
    CR,
)
from .factory import (
    connect,
    find_interface,
)


class RecordDict(Mapping):

    __slots__ = '_mapping'

    def __delattr__(self, item):
        # override to raise TypeError and to control the error message
        self._raise('item deletion')

    def __getattr__(self, item):
        return self._mapping[item]

    def __getitem__(self, item):
        return self._mapping[item]

    def __init__(self, dictionary):
        """A read-only dictionary that supports attribute access via a key lookup."""

        if not isinstance(dictionary, dict):
            raise TypeError("Can only create a 'RecordDict' from a dict")

        # recursively make all values that are a dict a RecordDict
        for k, v in dictionary.items():
            if isinstance(v, dict):
                dictionary[k] = RecordDict(v)
            if isinstance(v, (list, tuple)):
                def deep_tuple(a):
                    return tuple(map(deep_tuple, a)) if isinstance(a, (list, tuple)) else a
                dictionary[k] = deep_tuple(v)

        super(RecordDict, self).__setattr__('_mapping', dictionary)

    def __iter__(self):
        return iter(self._mapping)

    def __len__(self):
        return len(self._mapping)

    def __repr__(self):
        return 'RecordDict<{}>'.format(self._mapping)

    def __setattr__(self, key, value):
        # override to raise TypeError and to control the error message
        self._raise('item assignment')

    def _raise(self, message):
        raise TypeError('A {!r} object does not support {}'.format(self.__class__.__name__, message))

    def clear(self):
        self._raise('clearing')

    def copy(self):
        """:class:`RecordDict`: Return a copy of the :class:`RecordDict`."""
        return RecordDict(self._mapping.copy())

    def fromkeys(self, *args, **kwargs):
        self._raise('fromkeys')

    def pop(self, *args, **kwargs):
        self._raise('popping')

    def popitem(self):
        self._raise('popitem')

    def setdefault(self, *args, **kwargs):
        self._raise('setdefault')

    def update(self, *args, **kwargs):
        self._raise('updating')

    def to_xml(self, tag='RecordDict'):
        """Convert the :class:`RecordDict` to an XML :class:`~xml.etree.ElementTree.Element`

        Parameters
        ----------
        tag : :class:`str`
            The name of the :class:`~xml.etree.ElementTree.Element`.

        Returns
        -------
        :class:`~xml.etree.ElementTree.Element`
            The :class:`RecordDict` as an XML :class:`~xml.etree.ElementTree.Element`.
        """
        root = Element(tag)
        for k, v in self._mapping.items():
            if isinstance(v, RecordDict):
                element = v.to_xml(tag=k)
            else:
                element = Element(k)
                element.text = repr(v)
            root.append(element)
        return root

    def to_json(self):
        """:class:`dict`: Convert the :class:`RecordDict` to be JSON_ serializable.

        .. _JSON: https://www.json.org/
        """
        root = dict()
        for k, v in self._mapping.items():
            if isinstance(v, RecordDict):
                root[k] = v.to_json()
            elif isinstance(v, Enum):
                root[k] = v.name
            else:
                try:
                    json.dumps(v)
                except TypeError:
                    root[k] = str(v)  # cannot be serialized
                else:
                    root[k] = v  # can be serialized
        return root


class Record(object):

    def to_dict(self):
        """:class:`dict`: Convert the Record to a :class:`dict`."""
        return dict((name, getattr(self, name)) for name in self.__slots__)

    def to_json(self):
        """:class:`dict`: Convert the Record to be JSON_ serializable.

        This differs from :meth:`to_dict` such that all values that are not
        JSON_ serializable, like :class:`datetime.date` objects, are
        converted to a :class:`str`.

        .. _JSON: https://www.json.org/
        """
        raise NotImplementedError

    def to_xml(self):
        """:class:`~xml.etree.ElementTree.Element`: Convert the Record to an XML
        :class:`~xml.etree.ElementTree.Element`."""
        raise NotImplementedError

    @staticmethod
    def _dict_to_str(dict_):
        if dict_:
            return '\n' + '\n'.join('    {}: {!r}'.format(k, v) for k, v in sorted(dict_.items()))
        else:
            return 'None'

    @staticmethod
    def _list_to_str(list_):
        if list_:
            return '\n' + '\n'.join(['    {}'.format(line) for c in list_
                                     for line in repr(c).splitlines()])
        else:
            return 'None'


class EquipmentRecord(Record):

    __slots__ = ('alias', 'calibrations', 'category', 'connection', 'description',
                 'is_operable', 'maintenances', 'manufacturer', 'model',
                 'serial', 'team', 'unique_key', 'user_defined')

    def __init__(self, alias='', calibrations=None, category='', connection=None,
                 description='', is_operable=False, maintenances=None,
                 manufacturer='', model='', serial='', team='', unique_key='', **user_defined):
        """Contains the information about an equipment record in an :ref:`equipment-database`.

        Parameters
        ----------
        alias : :class:`str`
            An alias to use to reference this equipment by.
        calibrations : :class:`list` of :class:`.CalibrationRecord`
            The calibration history of the equipment.
        category : :class:`str`
            The category (e.g., Laser, DMM) that the equipment belongs to.
        connection : :class:`.ConnectionRecord`
            The information necessary to communicate with the equipment.
        description : :class:`str`
            A description about the equipment.
        is_operable : :class:`bool`
            Whether the equipment is able to be used.
        maintenances : :class:`list` of :class:`.MaintenanceRecord`
            The maintenance history of the equipment.
        manufacturer : :class:`str`
            The name of the manufacturer of the equipment.
        model : :class:`str`
            The model number of the equipment.
        serial : :class:`str`
            The serial number (or unique identifier) of the equipment.
        team : :class:`str`
            The team (e.g., Light Standards) that the equipment belongs to.
        unique_key : :class:`str`
            The key that uniquely identifies the equipment record in a database.
        **user_defined
            All additional key-value pairs are added to the :attr:`.user_defined` attribute.
        """

        self.alias = alias  # the alias should be of type str, but this is up to the user
        """:class:`str`: An alias to use to reference this equipment by.
        
        The `alias` can be defined in 4 ways:
        
            * by specifying it when the EquipmentRecord is created
            * by setting the value after the EquipmentRecord has been created 
            * in the **<equipment>** XML tag in a :ref:`configuration-file`
            * in the **Properties** field in a :ref:`connections-database`
        
        """

        self.calibrations = self._set_calibrations(calibrations)
        """:class:`tuple` of :class:`.CalibrationRecord`: The calibration history of the equipment."""

        self.category = '{}'.format(category)
        """:class:`str`: The category (e.g., Laser, DMM) that the equipment belongs to."""

        self.description = '{}'.format(description)
        """:class:`str`: A description about the equipment."""

        self.is_operable = bool(is_operable)
        """:class:`bool`: Whether the equipment is able to be used."""

        self.maintenances = self._set_maintenances(maintenances)
        """:class:`tuple` of :class:`.MaintenanceRecord`: The maintenance history of the equipment."""

        self.manufacturer = '{}'.format(manufacturer)
        """:class:`str`: The name of the manufacturer of the equipment."""

        self.model = '{}'.format(model)
        """:class:`str`: The model number of the equipment."""

        self.serial = '{}'.format(serial)
        """:class:`str`: The serial number (or unique identifier) of the equipment."""

        # requires self.manufacturer, self.model and self.serial to be already defined
        self.connection = self._set_connection(connection)
        """:class:`.ConnectionRecord`: The information necessary to communicate with the equipment."""

        # cache this value because __str__ is called a lot during logging
        self._str = 'EquipmentRecord<{}|{}|{}>'.format(self.manufacturer, self.model, self.serial)

        self.team = '{}'.format(team)
        """:class:`str`: The team (e.g., Light Standards) that the equipment belongs to."""

        self.unique_key = '{}'.format(unique_key)
        """:class:`str`: The key that uniquely identifies the equipment record in a database."""

        try:
            # a 'user_defined' kwarg was explicitly defined
            ud = user_defined.pop('user_defined')
        except KeyError:
            ud = user_defined
        else:
            ud.update(**user_defined)  # the user_defined dict might still contain other key-value pairs

        self.user_defined = RecordDict(ud)
        """:class:`.RecordDict`: User-defined, key-value pairs."""

    def __repr__(self):
        calibrations = self._list_to_str(self.calibrations)
        maintenances = self._list_to_str(self.maintenances)
        user_defined = self._dict_to_str(self.user_defined)

        if self.connection:
            connection = '\n    ' + '\n    '.join(repr(self.connection).splitlines())
        else:
            connection = 'None'

        return 'EquipmentRecord\n' \
               '  alias: {!r}\n' \
               '  calibrations: {}\n' \
               '  category: {!r}\n' \
               '  connection: {}\n' \
               '  description: {!r}\n' \
               '  is_operable: {}\n' \
               '  maintenances: {}\n' \
               '  manufacturer: {!r}\n' \
               '  model: {!r}\n' \
               '  serial: {!r}\n' \
               '  team: {!r}\n' \
               '  unique_key: {!r}\n' \
               '  user_defined: {}'.format(self.alias, calibrations, self.category, connection,
                                           self.description, self.is_operable, maintenances,
                                           self.manufacturer, self.model, self.serial,
                                           self.team, self.unique_key, user_defined)

    def __str__(self):
        return self._str

    def __setattr__(self, name, value):
        try:
            # once the `user_defined` attribute is created the class becomes read only
            # (except for the `alias` attribute which can be changed at any time)
            self.user_defined
        except AttributeError:
            super(EquipmentRecord, self).__setattr__(name, value)
        else:
            if name == 'alias':  # only allow the alias to be modified
                super(EquipmentRecord, self).__setattr__(name, value)
            else:
                raise TypeError("An 'EquipmentRecord' cannot be modified. "
                                "Cannot set {!r} to {!r}".format(name, value))

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
        return connect(self, demo=demo)

    def is_calibration_due(self, months=0):
        """Whether the equipment needs to be re-calibrated.

        Parameters
        ----------
        months : :class:`int`, optional
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
        next_date = self.next_calibration_date()
        if next_date is None:
            return False

        ask_date = datetime.date.today() + relativedelta(months=max(0, int(months)))
        return ask_date > next_date

    @property
    def latest_calibration(self):
        """:class:`.CalibrationRecord`: The latest calibration or :data:`None`
        if the equipment has never been calibrated."""
        latest = None
        date = datetime.date(datetime.MINYEAR, 1, 1)
        for report in self.calibrations:
            # the calibration date gets precedence over the report date
            if report.calibration_date > date:
                date = report.calibration_date
                latest = report
            elif report.report_date > date:
                date = report.report_date
                latest = report
        return latest

    def next_calibration_date(self):
        """The date that the next calibration is due.

        Returns
        -------
        :class:`datetime.date`
            The next calibration date (or :data:`None` if the equipment has
            never been calibrated or if it is no longer in operation).
        """
        if not self.is_operable:
            return None

        report = self.latest_calibration
        if report is None or report.calibration_cycle <= 0:
            return None

        # the calibration date gets precedence over the report date
        if report.calibration_date.year != datetime.MINYEAR:
            date = report.calibration_date
        elif report.report_date.year != datetime.MINYEAR:
            date = report.report_date
        else:
            return None

        years = int(report.calibration_cycle)
        months = int(round(12 * (report.calibration_cycle - years)))
        return date + relativedelta(years=years, months=months)

    def to_dict(self):
        """Convert this :class:`EquipmentRecord` to a :class:`dict`.

        Returns
        -------
        :class:`dict`
            The :class:`EquipmentRecord` as a :class:`dict`.
        """
        return {
            'alias': self.alias,
            'calibrations': tuple(cr.to_dict() for cr in self.calibrations),
            'category': self.category,
            'connection': None if self.connection is None else self.connection.to_dict(),
            'description': self.description,
            'is_operable': self.is_operable,
            'maintenances': tuple(mh.to_dict() for mh in self.maintenances),
            'manufacturer': self.manufacturer,
            'model': self.model,
            'serial': self.serial,
            'team': self.team,
            'unique_key': self.unique_key,
            'user_defined': self.user_defined,
        }

    def to_json(self):
        """Convert this :class:`EquipmentRecord` to be JSON_ serializable.

        .. _JSON: https://www.json.org/

        Returns
        -------
        :class:`dict`
            The :class:`EquipmentRecord` as a JSON_\\-serializable object.
        """
        return {
            'alias': self.alias,
            'calibrations': tuple(cr.to_json() for cr in self.calibrations),
            'category': self.category,
            'connection': None if self.connection is None else self.connection.to_json(),
            'description': self.description,
            'is_operable': self.is_operable,
            'maintenances': tuple(mh.to_json() for mh in self.maintenances),
            'manufacturer': self.manufacturer,
            'model': self.model,
            'serial': self.serial,
            'team': self.team,
            'unique_key': self.unique_key,
            'user_defined': self.user_defined.to_json(),
        }

    def to_xml(self):
        """Convert this :class:`EquipmentRecord` to an XML :class:`~xml.etree.ElementTree.Element`.

        Returns
        -------
        :class:`~xml.etree.ElementTree.Element`
            The :class:`EquipmentRecord` as an XML element.
        """
        root = Element('EquipmentRecord')
        for name in EquipmentRecord.__slots__:
            element = Element(name)
            if name == 'connection':
                if self.connection is not None:
                    element.append(self.connection.to_xml())
            elif name == 'maintenances':
                for mh in self.maintenances:
                    element.append(mh.to_xml())
            elif name == 'calibrations':
                for cr in self.calibrations:
                    element.append(cr.to_xml())
            elif name == 'user_defined':
                for key, value in sorted(self.user_defined.items()):
                    prop = Element(key)
                    prop.text = '{}'.format(value)
                    element.append(prop)
            else:
                element.text = '{}'.format(getattr(self, name))
            root.append(element)
        return root

    def _set_connection(self, record):
        if not record:
            return None

        if not isinstance(record, ConnectionRecord):
            if isinstance(record, dict):
                record = ConnectionRecord(**record)
            else:
                raise TypeError('Must pass in a ConnectionRecord object. Got {!r}'.format(record))

        # ensure that the manufacturer, model and serial match
        for item in ('manufacturer', 'model', 'serial'):
            r, s = getattr(record, item), getattr(self, item)
            if not r:  # then it was not set in the ConnectionRecord
                setattr(record, item, s)
            elif r != s:
                raise ValueError('ConnectionRecord.{0} ({1}) != EquipmentRecord.{0} ({2})'.format(item, r, s))

        return record

    @staticmethod
    def _set_calibrations(calibrations):
        if calibrations is None:
            return tuple()

        reports = []
        for report in calibrations:
            if isinstance(report, CalibrationRecord):
                reports.append(report)
            elif isinstance(report, dict):
                report['measurands'] = [MeasurandRecord(**m) for m in report['measurands']]
                reports.append(CalibrationRecord(**report))
            else:
                raise TypeError("Invalid data type {!r} for creating a 'CalibrationRecord'".format(type(report)))
        return tuple(reports)

    @staticmethod
    def _set_maintenances(maintenances):
        if maintenances is None:
            return tuple()

        history = []
        for maintenance in maintenances:
            if isinstance(maintenance, MaintenanceRecord):
                history.append(maintenance)
            elif isinstance(maintenance, dict):
                history.append(MaintenanceRecord(**maintenance))
            else:
                raise TypeError("Invalid data type {!r} for creating a 'MaintenanceRecord'".format(type(maintenance)))
        return tuple(history)


class ConnectionRecord(Record):

    __slots__ = ('address', 'backend', 'interface', 'manufacturer', 'model', 'properties', 'serial')

    _LF = ['\\n', "'\\n'", '"\\n"', "b'\\n'", b'\n', b'\\n', b"b'\\n'"]
    _CR = ['\\r', "'\\r'", '"\\r"', "b'\\r'", b'\r', b'\\r', b"b'\\r'"]
    _CRLF = ['\\r\\n', "'\\r\\n'", '"\\r\\n"', "b'\\r\\n'", b'\r\n', b'\\r\\n', b"b'\r\n'", b"b'\\r\\n'"]

    def __init__(self, address='', backend=Backend.MSL, interface=None, manufacturer='',
                 model='', serial='', **properties):
        """Contains the information about a connection record in a :ref:`connections-database`.

        Parameters
        ----------
        address : :class:`str`
            The address to use for the connection (see :ref:`address-syntax` for examples).
        backend : :class:`str`, :class:`int`, or :class:`.Backend`
            The backend to use to communicate with the equipment. The value must be able to
            be converted to a :class:`.Backend` enum.
        interface : :class:`str`, :class:`int`, or :class:`.MSLInterface`
            The interface to use to communicate with the equipment. If :data:`None` then
            determines the `interface` based on the value of `address`. If specified then
            the value must be able to be converted to a :class:`.MSLInterface` enum.
        manufacturer : :class:`str`
            The name of the manufacturer of the equipment.
        model : :class:`str`
            The model number of the equipment.
        serial : :class:`str`
            The serial number (or unique identifier) of the equipment.
        properties
            Additional key-value pairs that are required to communicate with the equipment.
        """
        self.address = '{}'.format(address)
        """:class:`str`: The address to use for the connection (see :ref:`address-syntax` for examples)."""

        self.backend = convert_to_enum(backend, Backend)
        """:class:`.Backend`: The backend to use to communicate with the equipment."""

        if interface:
            self.interface = convert_to_enum(interface, MSLInterface, to_upper=True)
        elif not address or self.backend != Backend.MSL:
            self.interface = MSLInterface.NONE
        else:
            self.interface = find_interface(address)
        """:class:`.MSLInterface`: The interface that is used for the communication system that
        transfers data between a computer and the equipment (only used if the :attr:`.backend`
        is equal to :attr:`~.Backend.MSL`)."""

        self.manufacturer = '{}'.format(manufacturer)
        """:class:`str`: The name of the manufacturer of the equipment."""

        self.model = '{}'.format(model)
        """:class:`str`: The model number of the equipment."""

        self.properties = self._set_properties(properties)
        """:class:`dict`: Additional key-value pairs that are required to communicate with the equipment.
        
        For example, communicating via RS-232 may require::
        
            {'baud_rate': 19200, 'parity': 'even'}
        
        See the :ref:`connections-database` for examples on how to set the `properties`.
        """

        self.serial = '{}'.format(serial)
        """:class:`str`: The serial number (or unique identifier) of the equipment."""

    def __repr__(self):
        props = self._dict_to_str(dict((k, self.properties[k]) for k in sorted(self.properties)))
        return 'ConnectionRecord\n' \
               '  address: {!r}\n' \
               '  backend: {!r}\n' \
               '  interface: {!r}\n' \
               '  manufacturer: {!r}\n' \
               '  model: {!r}\n' \
               '  properties: {}\n' \
               '  serial: {!r}'.format(self.address, self.backend, self.interface,
                                       self.manufacturer, self.model, props, self.serial)

    def __str__(self):
        return 'ConnectionRecord<{}|{}|{}>'.format(self.manufacturer, self.model, self.serial)

    def to_json(self):
        """Convert this :class:`ConnectionRecord` to be JSON_ serializable.

        .. _JSON: https://www.json.org/

        Returns
        -------
        :class:`dict`
            The :class:`ConnectionRecord` as a JSON_\\-serializable object.
        """
        props = dict()
        for k, v in self.properties.items():
            if isinstance(v, Enum):
                props[k] = v.name
            else:
                try:
                    json.dumps(v)
                except TypeError:
                    props[k] = repr(v)  # cannot be serialized
                else:
                    props[k] = v  # can be serialized

        return {
            'address': self.address,
            'backend': self.backend.name,
            'interface': self.interface.name,
            'manufacturer': self.manufacturer,
            'model': self.model,
            'properties': props,
            'serial': self.serial,
        }

    def to_xml(self):
        """Convert this :class:`ConnectionRecord` to an XML :class:`~xml.etree.ElementTree.Element`.

        Returns
        -------
        :class:`~xml.etree.ElementTree.Element`
            The :class:`ConnectionRecord` as a XML :class:`~xml.etree.ElementTree.Element`.
        """
        root = Element('ConnectionRecord')
        for name, value in self.to_dict().items():
            element = Element(name)
            if name == 'properties':
                for prop_key in sorted(self.properties):
                    prop_value = self.properties[prop_key]
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

    def _set_properties(self, kwargs):
        try:
            # a 'properties' kwarg was explicitly defined
            properties = kwargs.pop('properties')
        except KeyError:
            properties = kwargs
        else:
            if not properties:
                properties = {}
            elif not isinstance(properties, dict):
                raise TypeError('The properties kwarg for a ConnectionRecord must be of type dict. '
                                'Got {!r} -> {!r}'.format(type(properties), properties))
            properties.update(kwargs)

        if self.address.startswith('UDP'):
            properties['socket_type'] = 'SOCK_DGRAM'

        is_serial = self.interface == MSLInterface.SERIAL
        if not is_serial and self.backend == Backend.PyVISA:
            for alias in ('COM', 'ASRL', 'ASRLCOM'):
                if self.address.startswith(alias):
                    is_serial = True
                    break

        for key, value in properties.items():
            if is_serial:
                if key == 'parity':
                    properties[key] = convert_to_enum(value, Parity, to_upper=True)
                elif key == 'stop_bits' or key == 'stopbits':
                    properties[key] = convert_to_enum(value, StopBits, to_upper=True)
                elif key == 'data_bits' or key == 'bytesize':
                    properties[key] = convert_to_enum(value, DataBits, to_upper=True)
            if key.endswith('termination'):
                if value in ConnectionRecord._CRLF:  # must check before LR and CR checks
                    properties[key] = CR + LF
                elif value in ConnectionRecord._LF:
                    properties[key] = LF
                elif value in ConnectionRecord._CR:
                    properties[key] = CR
                elif not isinstance(value, bytes) and value is not None:
                    properties[key] = value.encode()

        return properties


class MaintenanceRecord(Record):

    __slots__ = ('comment', 'date')

    def __init__(self, comment='', date=None):
        """Contains the information about a maintenance record in an :ref:`equipment-database`.

        Parameters
        ----------
        comment : :class:`str`
            A description of the maintenance that was performed.
        date : :class:`datetime.date`, :class:`datetime.datetime` or :class:`str`
            An object that can be converted to a :class:`datetime.date` object.
            If a :class:`str` then in the format ``'YYYY-MM-DD'``.
        """
        self.comment = '{}'.format(comment)
        """:class:`str`: A description of the maintenance that was performed."""

        self.date = convert_to_date(date)
        """:class:`datetime.date`: The date that the maintenance was performed."""

    def __setattr__(self, name, value):
        try:
            self.date  # once the `date` is defined the class becomes read only
        except AttributeError:
            super(MaintenanceRecord, self).__setattr__(name, value)
        else:
            raise TypeError("A 'MaintenanceRecord' cannot be modified. Cannot set {!r} to {!r}".format(name, value))

    def __repr__(self):
        return 'MaintenanceRecord\n' \
               '  comment: {!r}\n' \
               '  date: {}'.format(self.comment, self.date)

    def __str__(self):
        return 'MaintenanceRecord<{}>'.format(self.date)

    def to_json(self):
        """Convert this :class:`MaintenanceRecord` to be JSON_ serializable.

        .. _JSON: https://www.json.org/

        Returns
        -------
        :class:`dict`
            The :class:`MaintenanceRecord` as a JSON_\\-serializable object.
        """
        return {
            'comment': self.comment,
            'date': self.date.isoformat(),
        }

    def to_xml(self):
        """Convert this :class:`MaintenanceRecord` to an XML :class:`~xml.etree.ElementTree.Element`.

        Returns
        -------
        :class:`~xml.etree.ElementTree.Element`
            The :class:`MaintenanceRecord` as a XML :class:`~xml.etree.ElementTree.Element`.
        """
        root = Element('MaintenanceRecord')

        comment_element = Element('comment')
        comment_element.text = self.comment
        root.append(comment_element)

        date_element = Element('date')
        date_element.text = self.date.isoformat()
        date_element.attrib['format'] = 'YYYY-MM-DD'
        root.append(date_element)

        return root


class MeasurandRecord(Record):

    __slots__ = ('calibration', 'conditions', 'type', 'unit')

    def __init__(self, calibration=None, conditions=None, type='', unit=''):
        """Contains the information about a measurement for a calibration.

        Parameters
        ----------
        calibration : :class:`dict`
            The information about the calibration.
        conditions : :class:`dict`
            The information about the conditions under which the measurement was performed.
        type : :class:`str`
            The type of measurement (e.g., voltage, temperature, transmittance, ...).
        unit : :class:`str`
            The unit that is associated with the measurement (e.g., V, deg C, %, ...).
        """
        if calibration is None:
            calibration = {}
        elif not isinstance(calibration, dict):
            raise TypeError("the 'calibration' parameter must be a dict")

        if conditions is None:
            conditions = {}
        elif not isinstance(conditions, dict):
            raise TypeError("the 'conditions' parameter must be a dict")

        self.calibration = RecordDict(calibration)
        """:class:`.RecordDict`: The information about calibration."""

        self.conditions = RecordDict(conditions)
        """:class:`.RecordDict`: The information about the measurement conditions."""

        self.type = '{}'.format(type)
        """:class:`str`: The type of measurement (e.g., voltage, temperature, transmittance, ...)."""

        self.unit = '{}'.format(unit)
        """:class:`str`: The unit that is associated with the measurement (e.g., V, deg C, %, ...)."""

    def __setattr__(self, name, value):
        try:
            self.unit  # once the `unit` is defined the class becomes read only
        except AttributeError:
            super(MeasurandRecord, self).__setattr__(name, value)
        else:
            raise TypeError("A 'MeasurandRecord' cannot be modified. Cannot set {!r} to {!r}".format(name, value))

    def __repr__(self):
        cal = self._dict_to_str(self.calibration)
        con = self._dict_to_str(self.conditions)
        return 'MeasurandRecord\n' \
               '  calibration: {}\n' \
               '  conditions: {}\n' \
               '  type: {!r}\n' \
               '  unit: {!r}'.format(cal, con, self.type, self.unit)

    def __str__(self):
        return 'MeasurandRecord<{}>'.format(self.type)

    def to_json(self):
        """Convert this :class:`MeasurandRecord` to be JSON_ serializable.

        .. _JSON: https://www.json.org/

        Returns
        -------
        :class:`dict`
            The :class:`MeasurandRecord` as a JSON_\\-serializable object.
        """
        return {
            'calibration': self.calibration.to_json(),
            'conditions': self.conditions.to_json(),
            'type': self.type,
            'unit': self.unit,
        }

    def to_xml(self):
        """Convert this :class:`MeasurandRecord` to an XML :class:`~xml.etree.ElementTree.Element`.

        Returns
        -------
        :class:`~xml.etree.ElementTree.Element`
            The :class:`MeasurandRecord` as a XML :class:`~xml.etree.ElementTree.Element`.
        """
        root = Element('MeasurandRecord')

        for name in ('calibration', 'conditions'):
            root.append(getattr(self, name).to_xml(tag=name))

        for name in ('type', 'unit'):
            element = Element(name)
            element.text = getattr(self, name)
            root.append(element)

        return root


class CalibrationRecord(Record):

    __slots__ = ('calibration_cycle', 'calibration_date', 'measurands', 'report_date', 'report_number')

    def __init__(self, calibration_cycle=0, calibration_date=None, measurands=None,
                 report_date=None, report_number=''):
        """Contains the information about a calibration record in an :ref:`equipment-database`.

        Parameters
        ----------
        calibration_cycle : :class:`int` or :class:`float`
            The number of years that can pass before the equipment must be re-calibrated.
        calibration_date : :class:`datetime.date`, :class:`datetime.datetime` or :class:`str`
            The date that the calibration was performed. If a :class:`str` then in the
            format ``'YYYY-MM-DD'``.
        measurands : :class:`list` of :class:`.MeasurandRecord`
            The quantities that were measured.
        report_date : :class:`datetime.date`, :class:`datetime.datetime` or :class:`str`
            The date that the report was issued. If a :class:`str` then in the
            format ``'YYYY-MM-DD'``.
        report_number : :class:`str`
            The report number.
        """
        if measurands is None:
            measurands = []

        measures = []
        for m in measurands:
            if isinstance(m, MeasurandRecord):
                measures.append(m)
            elif m and isinstance(m, dict):
                measures.append(MeasurandRecord(**m))

        self.calibration_cycle = float(calibration_cycle)
        """:class:`float`: The number of years that can pass before the equipment must be re-calibrated."""

        self.calibration_date = convert_to_date(calibration_date)
        """:class:`datetime.date`: The date that the calibration was performed."""

        self.measurands = RecordDict(OrderedDict((m.type, m) for m in measures))
        """:class:`.RecordDict`: The quantities that were measured."""

        self.report_date = convert_to_date(report_date)
        """:class:`datetime.date`: The date that the report was issued."""

        self.report_number = '{}'.format(report_number)
        """:class:`str`: The report number."""

    def __setattr__(self, name, value):
        try:
            self.report_number  # once the `report_number` is defined the class becomes read only
        except AttributeError:
            super(CalibrationRecord, self).__setattr__(name, value)
        else:
            raise TypeError("A 'CalibrationRecord' cannot be modified. Cannot set {!r} to {!r}".format(name, value))

    def __repr__(self):
        if self.measurands:
            measurands = '\n' + '\n'.join('    {}'.format(line) for value in self.measurands.values()
                                          for line in repr(value).splitlines())
        else:
            measurands = 'None'

        return 'CalibrationRecord\n' \
               '  calibration_cycle: {}\n' \
               '  calibration_date: {}\n' \
               '  measurands: {}\n' \
               '  report_date: {}\n' \
               '  report_number: {!r}'.format(self.calibration_cycle, self.calibration_date,
                                              measurands, self.report_date, self.report_number)

    def __str__(self):
        return 'CalibrationRecord<{}>'.format(self.report_number)

    def to_json(self):
        """Convert this :class:`CalibrationRecord` to be JSON_ serializable.

        .. _JSON: https://www.json.org/

        Returns
        -------
        :class:`dict`
            The :class:`CalibrationRecord` as a JSON_\\-serializable object.
        """
        return {
            'calibration_cycle': self.calibration_cycle,
            'calibration_date': self.calibration_date.isoformat(),
            'measurands': tuple(m.to_json() for m in self.measurands.values()),
            'report_date': self.report_date.isoformat(),
            'report_number': self.report_number
        }

    def to_xml(self):
        """Convert this :class:`CalibrationRecord` to an XML :class:`~xml.etree.ElementTree.Element`.

        Returns
        -------
        :class:`~xml.etree.ElementTree.Element`
            The :class:`CalibrationRecord` as a XML :class:`~xml.etree.ElementTree.Element`.
        """
        root = Element('CalibrationRecord')

        calibration_date = Element('calibration_date')
        calibration_date.text = self.calibration_date.isoformat()
        calibration_date.attrib['format'] = 'YYYY-MM-DD'
        root.append(calibration_date)

        calibration_cycle = Element('calibration_cycle')
        calibration_cycle.text = str(self.calibration_cycle)
        calibration_cycle.attrib['unit'] = 'years'
        root.append(calibration_cycle)

        measurands = Element('measurands')
        for measurand in self.measurands.values():
            measurands.append(measurand.to_xml())
        root.append(measurands)

        report_number = Element('report_number')
        report_number.text = self.report_number
        root.append(report_number)

        report_date = Element('report_date')
        report_date.text = self.report_date.isoformat()
        report_date.attrib['format'] = 'YYYY-MM-DD'
        root.append(report_date)

        return root
