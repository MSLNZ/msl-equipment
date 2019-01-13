"""
Load equipment and connection records from :ref:`Databases <database>`.
"""
from __future__ import unicode_literals
import os
import re
import codecs
import logging
import datetime
from xml.etree import cElementTree as ET

import xlrd

from . import constants
from .record_types import (
    EquipmentRecord,
    ConnectionRecord,
)
from .utils import (
    string_to_none_bool_int_float_complex,
    convert_to_enum,
)

logger = logging.getLogger(__name__)


class Database(object):

    def __init__(self, path):
        """Create :class:`.EquipmentRecord`'s and :class:`.ConnectionRecord`'s 
        from :ref:`Databases <database>` that are specified in a :ref:`configuration_file`.

        This class should be accessed through the :meth:`~.config.Config.database` method
        after a :class:`~.config.Config` object has been created.

        Parameters
        ----------
        path : :class:`str`
            The path to an XML :ref:`configuration_file`.

        Raises
        ------
        IOError
            If `path` does not exist or if the :ref:`configuration_file` is invalid.
        AttributeError
            If an ``<equipment>`` XML tag is specified in the :ref:`configuration_file`
            and it does not uniquely identify an equipment record in an
            :ref:`equipment_database`.
        ValueError
            If an :attr:`~.EquipmentRecord.alias` has been specified multiple times
            for the same :class:`~.EquipmentRecord`.
        """
        logger.debug('Loading databases from {!r}'.format(path))

        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as err:
            parse_err = str(err)  # want to raise IOError not ParseError
        else:
            parse_err = None

        if parse_err:
            raise IOError(parse_err)

        self._config_path = path

        # create a dictionary of all ConnectionRecord's
        self._connection_records = {}
        easy_names = ('address', 'backend', 'manufacturer', 'model', 'serial')
        for connections in root.findall('connections'):
            for element in connections.findall('connection'):
                header, rows = self._read(element)
                index_map = self._make_index_map(header, ConnectionRecord._NAMES)
                for row in rows:
                    if not self._is_row_length_okay(row, header):
                        continue
                    key = self._make_key(row, index_map)
                    if not self._is_key_unique(key, self._connection_records, element):
                        continue
                    kwargs = {}
                    for name in easy_names:
                        kwargs[name] = row[index_map[name]]
                    kwargs['properties'] = {}
                    for item in row[index_map['properties']].split(';'):
                        s = item.split('=')
                        if len(s) != 2:
                            continue
                        kwargs['properties'][s[0].strip()] = string_to_none_bool_int_float_complex(s[1].strip())
                    self._connection_records[key] = ConnectionRecord(**kwargs)

        # create a dictionary of EquipmentRecord's
        self._equipment_records = {}
        for registers in root.findall('registers'):
            for register in registers.findall('register'):
                register_path = register.findtext('path')
                team = register.attrib.get('team', '')
                date_format = register.attrib.get('date_format', '%d/%m/%Y')

                header, rows = self._read(register)
                index_map = self._make_index_map(header, EquipmentRecord._NAMES)

                # prepare the user_defined list
                temp = register.attrib.get('user_defined', [])
                user_defined = []
                index_map_user_defined = {}
                if temp:
                    temp = [t.strip().lower().replace(' ', '_') for t in temp.split(',') if t.strip()]
                    for name in temp:
                        if name in EquipmentRecord._NAMES:
                            msg = 'The "user_defined" parameter {!r} is already an EquipmentRecord attribute'
                            logger.warning(msg.format(name))
                        else:
                            user_defined.append(name)
                    if user_defined:
                        index_map_user_defined = self._make_index_map(header, user_defined)

                for row in rows:
                    if not self._is_row_length_okay(row, header):
                        continue
                    key = self._make_key(row, index_map)
                    if not self._is_key_unique(key, self._equipment_records, register):
                        continue

                    kwargs = {'team': team}

                    # find the corresponding ConnectionRecord (if it exists)
                    try:
                        kwargs['connection'] = self._connection_records[key]
                    except KeyError:
                        pass
                    else:
                        try:
                            # check if an alias was defined in ConnectionRecord.properties
                            alias = kwargs['connection'].properties['alias']
                        except KeyError:
                            pass
                        else:
                            kwargs['alias'] = alias
                            del kwargs['connection'].properties['alias']

                    for name in EquipmentRecord._NAMES:
                        try:
                            value = row[index_map[name]]
                        except KeyError:
                            continue

                        if name == 'date_calibrated' and not isinstance(value, datetime.date):
                            try:
                                value = datetime.datetime.strptime(value, date_format).date()
                            except ValueError:
                                if value:
                                    msg = '{} -> The date {!r} cannot be converted to a datetime.date object in {!r}'
                                    logger.error(msg.format(key, value, register_path))
                                continue
                        elif name == 'calibration_cycle':
                            if not value or value.upper() == 'N/A':
                                continue
                            try:
                                value = float(value)
                            except ValueError:
                                msg = '{} -> The calibration cycle value, {!r}, must be a number in {!r}'
                                logger.error(msg.format(key, value, register_path))
                                continue

                        kwargs[name] = value

                    for name in user_defined:
                        try:
                            s = row[index_map_user_defined[name]]
                        except KeyError:
                            pass
                        else:
                            kwargs[name] = string_to_none_bool_int_float_complex(s)

                    self._equipment_records[key] = EquipmentRecord(**kwargs)

        # create a dictionary of all the <equipment> tags
        self._equipment_using = {}
        for element in root.findall('equipment'):

            # check if an alias attribute was defined in the configuration file
            try:
                alias = element.attrib['alias']
            except KeyError:
                alias = None
            else:
                del element.attrib['alias']

            # search for the equipment in the database
            equipment = self.records(**element.attrib)
            if len(equipment) == 0:
                raise AttributeError('No equipment record found with attributes {}'.format(element.attrib))
            if len(equipment) > 1:
                raise AttributeError('The equipment specified is not unique. There are {} equipment '
                                     'records for {}'.format(len(equipment), element.attrib))

            equip = equipment[0]

            # the following is all about checking/getting the alias that associates with `equip`
            if alias is not None:
                if equip.alias and alias != equip.alias:
                    raise ValueError('Multiple aliases set for {}: {!r} and {!r}'.format(equip, alias, equip.alias))
            elif alias is None and equip.alias:
                alias = equip.alias
            else:
                if equip.model:
                    alias = equip.model
                elif equip.manufacturer:
                    alias = equip.manufacturer
                elif equip.connection.backend == constants.Backend.MSL:
                    alias = equip.connection.interface.name
                else:
                    alias = 'equipment'
            # if this alias already exists as a dictionary key then append a unique number to the alias
            if alias in self._equipment_using:
                n = sum([1 for key in self._equipment_using if key.startswith(alias)])
                alias += '({})'.format(n + 1)
            equip.alias = alias

            self._equipment_using[alias] = equip

    @property
    def equipment(self):
        """:class:`dict`: :class:`.EquipmentRecord`\'s that were listed as ``<equipment>`` XML tags in
        the :ref:`configuration_file`.
        """
        return self._equipment_using

    @property
    def path(self):
        """:class:`str`: The path to the :ref:`configuration_file`.
        """
        return self._config_path

    def connections(self, **kwargs):
        """Search the :ref:`connections_database` to find all :class:`.ConnectionRecord`\'s that
        match the specified criteria.

        Parameters
        ----------
        **kwargs
            The argument names can be any of the :class:`.ConnectionRecord` property names or
            a ``flags`` argument of type :class:`int` for performing the search, see :func:`re.search`.
            For testing regex expressions online you can use `this <https://pythex.org/>`_ website.

            If a `kwarg` is ``properties`` then the value must be a :class:`dict`. See the examples below.

        Examples
        --------
        >>> connections()  # doctest: +SKIP
        a list of all ConnectionRecords
        >>> connections(manufacturer='Keysight')  # doctest: +SKIP
        a list of all ConnectionRecords that have Keysight as the manufacturer
        >>> records(manufacturer='Agilent|Keysight')  # doctest: +SKIP
        a list of all ConnectionRecords that are from Agilent OR Keysight
        >>> connections(manufacturer=r'H.*P')  # doctest: +SKIP
        a list of all ConnectionRecords that have Hewlett Packard (or HP) as the manufacturer
        >>> connections(manufacturer='Agilent', model='^34')  # doctest: +SKIP
        a list of all ConnectionRecords that have Agilent as the manufacturer AND a model number beginning with '34'
        >>> connections(interface=MSLInterface.SERIAL)  # doctest: +SKIP
        a list of all ConnectionRecords that use SERIAL for the connection bus
        >>> connections(interface='USB')  # doctest: +SKIP
        a list of all ConnectionRecords that use USB for the connection bus
        >>> connections(backend=Backend.PyVISA)  # doctest: +SKIP
        a list of all ConnectionRecords that use PyVISA as the backend
        >>> connections(backend='MSL')  # doctest: +SKIP
        a list of all ConnectionRecords that use MSL as the backend
        >>> connections(properties={'baud_rate': 115200})  # doctest: +SKIP
        a list of all ConnectionRecords that specify a baud rate equal to 115200 in the Properties field

        Returns
        -------
        :class:`list` of :class:`.ConnectionRecord`
            The connection records that match the search criteria.

        Raises
        ------
        NameError
            If the name of an input argument is not a :class:`.ConnectionRecord`
            property name or ``flags``.
        """
        flags = int(kwargs.pop('flags', 0))  # used by re.search
        for name in kwargs:
            if name not in ConnectionRecord._NAMES:
                raise NameError('Invalid argument name {!r} for a {}'.format(name, ConnectionRecord.__name__))
        return [r for r in self._connection_records.values() if self._search(r, kwargs, flags)]

    def records(self, **kwargs):
        """Search the :ref:`equipment_database` to find all :class:`.EquipmentRecord`\'s that
        match the specified criteria.

        Parameters
        ----------
        **kwargs
            The argument names can be any of the :class:`.EquipmentRecord` property names or
            a ``flags`` argument of type :class:`int` for performing the search, see :func:`re.search`.
            For testing regex expressions online you can use `this <https://pythex.org/>`_ website.

            If a `kwarg` is ``connection`` then the value will be used to test which
            :class:`.EquipmentRecord`\'s have a :attr:`~.EquipmentRecord.connection` value that
            is either :data:`None` or :class:`.ConnectionRecord`. See the examples below.

            If a `kwarg` is ``date_calibrated`` then the value must be a callable function that
            takes 1 input argument (a :class:`datetime.date` object) and the function must return
            a :class:`bool`. See the examples below.

        Examples
        --------
        >>> records()  # doctest: +SKIP
        a list of all EquipmentRecords
        >>> records(manufacturer='Agilent')  # doctest: +SKIP
        a list of all EquipmentRecords that are from Agilent
        >>> records(manufacturer='Agilent|Keysight')  # doctest: +SKIP
        a list of all EquipmentRecords that are from Agilent OR Keysight
        >>> records(manufacturer='Agilent', model='3458A')  # doctest: +SKIP
        a list of all EquipmentRecords that are from Agilent AND that have the model number 3458A
        >>> records(manufacturer='Agilent', model='3458A', serial='MY45046470')  # doctest: +SKIP
        a list of only one EquipmentRecord (if the equipment record exists, otherwise an empty list)
        >>> records(manufacturer=r'H.*P')  # doctest: +SKIP
        a list of all EquipmentRecords that have Hewlett Packard (or HP) as the manufacturer
        >>> records(description='I-V Converter')  # doctest: +SKIP
        a list of all EquipmentRecords that contain 'I-V Converter' in the description field
        >>> records(connection=True)  # doctest: +SKIP
        a list of all EquipmentRecords that can be connected to
        >>> records(connection=0)  # doctest: +SKIP
        a list of all EquipmentRecords that cannot be connected to
        >>> records(date_calibrated=lambda date: 1995 < date.year < 2005)  # doctest: +SKIP
        a list of all EquipmentRecords that were calibrated between the years 1995 and 2005
        >>> records(date_calibrated=lambda date: date > datetime.date(2008, 3, 15))  # doctest: +SKIP
        a list of all EquipmentRecords that were calibrated after 15 March 2008

        Returns
        -------
        :class:`list` of :class:`.EquipmentRecord`
            The equipment records that match the search criteria.

        Raises
        ------
        NameError
            If the name of an input argument is not an :class:`.EquipmentRecord`
            property name or ``flags``.
        """
        flags = int(kwargs.pop('flags', 0))  # used by re.search
        for name in kwargs:
            if name not in EquipmentRecord._NAMES:
                raise NameError('Invalid argument name {!r} for an {}'.format(name, EquipmentRecord.__name__))
        return [r for r in self._equipment_records.values() if self._search(r, kwargs, flags)]

    def _read(self, element):
        """Read any allowed database file type"""
        path = element.findtext('path')
        if path is None:
            raise IOError('You must create a <path> </path> element in {} '
                          'specifying where to find the database'.format(self._config_path))

        if not os.path.isfile(path):
            # check if the path is a relative path (relative to the XML file path)
            path = os.path.join(os.path.dirname(self._config_path), path)
            if not os.path.isfile(path):
                raise IOError('Cannot find the database ' + path)

        ext = os.path.splitext(path)[1].lower()
        if ext in ('.xls', '.xlsx'):
            header, rows = self._read_excel(path, element.findtext('sheet'), element.attrib.get('encoding', None))
        elif ext in ('.csv', '.txt'):
            delimiter = ',' if ext == '.csv' else '\t'
            header, rows = self._read_text_based(path, delimiter, element.attrib.get('encoding', 'utf-8'))
        else:
            raise IOError('Unsupported equipment-registry database format ' + path)

        return header, rows

    def _read_excel(self, path, sheet_name, encoding):
        """Read an Excel database file"""
        self._book = xlrd.open_workbook(path, on_demand=True, encoding_override=encoding)

        if sheet_name is None:
            names = self._book.sheet_names()
            if len(names) > 1:
                msg = 'Cannot read the equipment register.\n' \
                      'More than one Sheet is available in {dbase}\n' \
                      'You must create a <sheet></sheet> element in {config}\n' \
                      'The text between the "sheet" tag must be one of: {sheets}\n' \
                      'For example,\n\t<path>{dbase}</path>\n\t<sheet>{first}</sheet>' \
                    .format(dbase=path, config=self._config_path, sheets=', '.join(names), first=names[0])
                raise IOError(msg)
            else:
                sheet_name = names[0]

        try:
            sheet = self._book.sheet_by_name(sheet_name)
        except xlrd.XLRDError:
            sheet = None

        if sheet is None:
            raise IOError('There is no Sheet named {!r} in {}'.format(sheet_name, path))

        header = [val for val in sheet.row_values(0)]
        rows = [[self._cell_convert(sheet.cell(r, c)) for c in range(sheet.ncols)] for r in range(1, sheet.nrows)]
        logger.debug('Loading Sheet <{}> in {!r}'.format(sheet_name, path))
        return header, rows

    def _cell_convert(self, cell):
        """Convert an Excel cell to the appropriate value and data type"""
        t = cell.ctype
        if t == xlrd.XL_CELL_NUMBER or t == xlrd.XL_CELL_BOOLEAN:
            if int(cell.value) == cell.value:
                return '{}'.format(int(cell.value))
            else:
                return '{}'.format(cell.value)
        elif t == xlrd.XL_CELL_DATE:
            date = xlrd.xldate_as_tuple(cell.value, self._book.datemode)
            return datetime.date(date[0], date[1], date[2])
        elif t == xlrd.XL_CELL_ERROR:
            return xlrd.error_text_from_code[cell.value]
        else:
            return cell.value.strip()

    def _read_text_based(self, path, delimiter, encoding):
        """Read a text-based database file"""
        with codecs.open(path, 'r', encoding) as fp:
            header = [val for val in fp.readline().split(delimiter)]
            rows = [[val.strip() for val in line.split(delimiter)] for line in fp.readlines() if line.strip()]
        logger.debug('Loading database ' + path)
        return header, rows

    def _make_index_map(self, header, field_names):
        """Determine the column index in the header that the field_names are located in"""
        index_map = {}
        h = [val.strip().lower().replace(' ', '_') for val in header]
        for index, label in enumerate(h):
            for name in field_names:
                if name not in index_map and name in label:
                    index_map[name] = index
                    break
        return index_map

    def _make_key(self, row, index_map):
        """Make a new Manufacturer|Model|Serial key for a dictionary"""
        return '{}|{}|{}'.format(row[index_map['manufacturer']],
                                 row[index_map['model']],
                                 row[index_map['serial']])

    def _is_key_unique(self, key, dictionary, element):
        """Returns whether the dictionary key is unique"""
        if key in dictionary:
            msg = 'Manufacturer|Model|Serial is not unique -> {} in {!r}'
            logger.error(msg.format(key, element.findtext('path')))
            return False
        return True

    def _is_row_length_okay(self, row, header):
        """Check if the row and the header have the same length"""
        if not len(row) == len(header):
            logger.error('len(row) [{}] != len(header) [{}] -> row={}'.format(len(row), len(header), row))
            return False
        return True

    def _search(self, record, kwargs, flags):
        """Check if the kwargs match a database record"""
        for key, value in kwargs.items():
            if key == 'backend' or key == 'interface':
                enum = constants.Backend if key == 'backend' else constants.MSLInterface
                val = getattr(record, key)
                if isinstance(value, int):
                    if convert_to_enum(value, enum) != val:
                        return False
                else:
                    x = []
                    for s in value.split('|'):
                        try:
                            x.append(convert_to_enum(s.strip(), enum) == val)
                        except ValueError:
                            pass
                    if not any(x):
                        return False
            elif key == 'connection':
                if bool(value):
                    # then want equipment records with a connection
                    if record.connection is None:
                        return False
                else:
                    if record.connection is not None:
                        return False
            elif key == 'date_calibrated':
                if not callable(value):
                    raise TypeError('The "date_calibrated" value must be a callable function')
                if not value(record.date_calibrated):
                    return False
            elif key == 'calibration_cycle':
                if value != record.calibration_cycle:
                    return False
            elif key == 'properties':
                if not isinstance(value, dict):
                    raise TypeError('The "properties" value must be a dict, got {}'.format(type(value)))
                for k, v in value.items():
                    if k not in record.properties:
                        return False
                    if v != record.properties[k]:
                        return False
            else:
                if not bool(re.search(value, getattr(record, key), flags)):
                    return False
        return True
