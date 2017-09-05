"""
Load equipment and connection records from :ref:`Databases <database>`.
"""
from __future__ import unicode_literals
import os
import re
import ast
import codecs
import logging
import datetime
from xml.etree import ElementTree

import xlrd

from msl.equipment import constants
from msl.equipment.record_types import EquipmentRecord, ConnectionRecord

logger = logging.getLogger(__name__)


class Database(object):

    def __init__(self, path):
        """Create :class:`.EquipmentRecord`'s and :class:`.ConnectionRecord`'s 
        from :ref:`Databases <database>` that are specified in a :ref:`configuration`.

        This class should be accessed through the :meth:`~.config.Config.database` method
        after a :class:`~.config.Config` object has been created.

        Parameters
        ----------
        path : :obj:`str`
            The path to a XML :ref:`configuration`.

        Raises
        ------
        IOError
            If `path` does not exist.
        :exc:`~xml.etree.ElementTree.ParseError`
            If the :ref:`configuration` is invalid.
        UnicodeError
            For all errors that are related to encoding problems.
        AttributeError
            If an ``<equipment>`` XML tag is specified in the :ref:`configuration`
            and it does not uniquely identify an equipment record in an
            :ref:`equipment_database`.
        ValueError
            If multiple :obj:`~.record_types.EquipmentRecord.alias`\es are specified
            for the same :obj:`~.record_types.EquipmentRecord`.
        """
        logger.debug('Loading databases from {}'.format(path))

        root = ElementTree.parse(path).getroot()

        self._config_path = path
        self._equipment_property_names = [k for k in EquipmentRecord().to_dict()]
        self._connection_property_names = [k for k in ConnectionRecord().to_dict()]

        # create a dictionary of ConnectionRecord objects
        self._connection_records = {}
        for element in root.findall('equipment_connections'):

            header, rows = self._read(element)
            self._make_index_map(header, self._connection_property_names)

            for row in rows:
                if not self._is_row_length_okay(row, header):
                    continue

                key = self._make_key(row)
                if not self._is_key_unique(key, self._connection_records, element):
                    continue

                conn_record = ConnectionRecord()

                # auto set the attributes that are string data types
                for name in ('address', 'manufacturer', 'model', 'serial'):
                    setattr(conn_record, '_'+name, row[self._index_map[name]])

                # set the backend to use to communicate with the equipment
                backend = row[self._index_map['backend']]
                try:
                    conn_record._backend = constants.Backend[backend]
                except ValueError:
                    logger.warning('Unknown Backend "{}"'.format(backend))

                # set the MSL connection interface to use for the MSL backend
                if conn_record.backend == constants.Backend.MSL:
                    try:
                        interface_name = conn_record._get_interface_name_from_address()
                        conn_record._interface = constants.MSLInterface[interface_name]
                    except KeyError:
                        logger.warning('Unknown MSL Interface for "{}"'.format(conn_record))

                # create the property dictionary
                conn_record._properties = {}
                for item in row[self._index_map['properties']].split(';'):
                    item_split = item.split('=')
                    if len(item_split) < 2:
                        continue

                    k, v = item_split[0].strip(), str(item_split[1].strip())

                    if 'ASRL' in conn_record.interface.name or conn_record.address.startswith('COM'):
                        k_lower = k.lower()
                        if k_lower.startswith('parity'):
                            v = self._to_enum(key, v, constants.Parity)
                        elif k_lower.startswith('stop'):
                            v = self._to_enum(key, float(v), constants.StopBits)
                        elif k_lower.startswith('data'):
                            v = self._to_enum(key, int(v), constants.DataBits)

                    if isinstance(v, str):
                        # try to convert 'v' to a Python bool, int or float
                        if v.upper() == 'TRUE':
                            v = True
                        elif v.upper() == 'FALSE':
                            v = False
                        else:
                            try:
                                v = ast.literal_eval(v)
                            except:
                                pass  # keep the value as a string

                    conn_record._properties[k] = v

                self._connection_records[key] = conn_record

        # create a dictionary of all the EquipmentRecord objects that are found in the Equipment Registers
        self._equipment_records = {}
        for registers in root.findall('equipment_registers'):
            for register in registers.findall('register'):

                # the MSL team (e.g., Electrical) that this Equipment Register belongs to
                team = register.attrib.get('team', u'')

                header, rows = self._read(register)
                self._make_index_map(header, self._equipment_property_names)

                for row in rows:
                    if not self._is_row_length_okay(row, header):
                        continue

                    key = self._make_key(row)
                    if not self._is_key_unique(key, self._equipment_records, register):
                        continue

                    record = EquipmentRecord()
                    record._team = team

                    if key in self._connection_records:
                        record._connection = self._connection_records[key]
                        if 'alias' in record.connection.properties:
                            record.alias = record.connection.properties['alias']
                            del record.connection.properties['alias']

                    for name in self._equipment_property_names:
                        try:
                            value = row[self._index_map[name]]
                        except KeyError:
                            continue

                        if name == 'date_calibrated' and not isinstance(value, datetime.date):
                            date_format = register.attrib.get('date_format', '%d/%m/%Y')
                            try:
                                value = datetime.datetime.strptime(value, date_format).date()
                            except ValueError:
                                if len(value) > 0:
                                    logger.error('The date "{}" cannot be converted to a datetime.date object in {}'
                                                 .format(value, register.findtext('path')))
                                continue

                        if name == 'calibration_cycle' and value:
                            try:
                                value = float(value)
                            except ValueError:
                                logger.error('The calibration_cycle must be a number for {}'.format(record))
                                continue

                        setattr(record, '_'+name, value)

                    self._equipment_records[key] = record

        # create a dictionary of all the EquipmentRecord objects that are being used for the measurement
        self._equipment_using = {}
        for element in root.findall('equipment'):

            # check if an alias attribute was defined in the configuration file
            alias = None
            if 'alias' in element.attrib:
                alias = element.attrib['alias']
                del element.attrib['alias']

            # search for the equipment in the database
            equipment = self.records(**element.attrib)
            if len(equipment) == 0:
                raise AttributeError('No equipment record found with attributes {}'.format(element.attrib))
            if len(equipment) > 1:
                raise AttributeError('The equipment specified is not unique. There are {} equipment '
                                     'records for {}'.format(len(equipment), element.attrib))
            equip = equipment[0]

            # determine the dictionary key to use as the name of this equipment object
            if alias is not None:
                if equip.alias and alias != equip.alias:
                    raise ValueError('Multiple aliases set for {}: "{}" and "{}"'.format(equip, alias, equip.alias))
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
        """:obj:`dict` of :class:`.EquipmentRecord`: Equipment records that were listed 
        as ``<equipment>`` XML tags in the :ref:`configuration`.
        """
        return self._equipment_using

    @property
    def path(self):
        """:obj:`str`: The path to the :ref:`configuration`.
        """
        return self._config_path

    def connections(self, **kwargs):
        """Search the :ref:`connection_database` to find all :class:`.ConnectionRecord`\'s that
        match the specified criteria.

        Parameters
        ----------
        **kwargs
            The argument names can be any of the :class:`.ConnectionRecord` property names or
            a ``flags`` argument of type :obj:`int`, see :obj:`re.search`, for performing the search.
            For testing regex expressions online you can use `this <https://pythex.org/>`_ website.

        Examples
        --------
        >>> connections()  # doctest: +SKIP
        a list of all ConnectionRecords
        >>> connections(manufacturer='H*P')  # doctest: +SKIP
        a list of all ConnectionRecords that have Hewlett Packard as the manufacturer
        >>> connections(manufacturer='^Ag', model='34*')  # doctest: +SKIP
        a list of all ConnectionRecords that have Agilent as the manufacturer and a model number beginning with '34'
        >>> connections(interface=MSLInterface.GPIB)  # doctest: +SKIP
        a list of all ConnectionRecords that use GPIB for the connection bus
        >>> connections(interface='USB')  # doctest: +SKIP
        a list of all ConnectionRecords that use USB for the connection bus
        >>> connections(backend=Backend.PyVISA)  # doctest: +SKIP
        a list of all ConnectionRecords that use PyVISA as the backend
        >>> connections(backend='MSL')  # doctest: +SKIP
        a list of all ConnectionRecords that use MSL as the backend

        Returns
        -------
        :obj:`list` of :class:`.ConnectionRecord`
            The connection records that match the search criteria.

        Raises
        ------
        NameError
            If the name of an input argument is not a :class:`.ConnectionRecord`
            property name or ``flags``.
        """
        flags = int(kwargs.pop('flags', 0))  # used by re.search
        for name in kwargs:
            if name not in self._connection_property_names:
                raise NameError('Invalid argument name "{}" for a {}'.format(name, ConnectionRecord.__name__))
        return [r for r in self._connection_records.values() if self._search(r, kwargs, flags)]

    def records(self, **kwargs):
        """Search the :ref:`equipment_database` to find all :class:`.EquipmentRecord`\'s that
        match the specified criteria.

        Parameters
        ----------
        **kwargs
            The argument names can be any of the :class:`.EquipmentRecord` property names or
            a ``flags`` argument of type :obj:`int`, see :obj:`re.search`, for performing the search.
            For testing regex expressions online you can use `this <https://pythex.org/>`_ website.

            If a `kwarg` is ``connection`` then the value will be used to test which
            :class:`.EquipmentRecord`\'s have a :obj:`~.EquipmentRecord.connection` value that
            is either :obj:`None` or :class:`.ConnectionRecord`. See the examples below.

            If a `kwarg` is ``date_calibrated`` then the value must be a callable function that
            takes 1 input argument (a :obj:`datetime.date` object) and the function must return
            a :obj:`bool`. See the examples below.

        Examples
        --------
        >>> records()  # doctest: +SKIP
        a list of all EquipmentRecords
        >>> records(manufacturer='H*P')  # doctest: +SKIP
        a list of all EquipmentRecords that have Hewlett Packard as the manufacturer
        >>> records(manufacturer='Agilent', model='3458A')  # doctest: +SKIP
        a list of all EquipmentRecords that are from Agilent and that have the model number 3458A
        >>> records(manufacturer='Agilent', model='3458A', serial='MY45046470')  # doctest: +SKIP
        a list of only one EquipmentRecord (if the equipment record exists, otherwise an empty list)
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
        :obj:`list` of :class:`.EquipmentRecord`
            The equipment records that match the search criteria.

        Raises
        ------
        NameError
            If the name of an input argument is not a :class:`.EquipmentRecord`
            property name or ``flags``.
        """
        flags = int(kwargs.pop('flags', 0))  # used by re.search
        for name in kwargs:
            if name not in self._equipment_property_names:
                raise NameError('Invalid argument name "{}" for an {}'.format(name, EquipmentRecord.__name__))
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
            header, rows = self._read_text_based(path, delimiter, element.attrib.get('encoding', 'utf8'))
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
                      'You must create a sheet element in {config}\n' \
                      'The text between the <sheet> </sheet> tag must be one of: {sheets}\n' \
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
            raise IOError('There is no Sheet named "{}" in {}'.format(sheet_name, path))

        header = [val for val in sheet.row_values(0)]
        rows = [[self._cell_convert(sheet.cell(r, c)) for c in range(sheet.ncols)] for r in range(1, sheet.nrows)]
        logger.debug('Loading Sheet <{}> in {}'.format(sheet_name, path))
        return header, rows

    def _cell_convert(self, cell):
        """Convert an Excel cell to the appropriate value and data type"""
        t = cell.ctype
        if t == xlrd.XL_CELL_NUMBER or t == xlrd.XL_CELL_BOOLEAN:
            if int(cell.value) == cell.value:
                return str(int(cell.value))
            else:
                return str(cell.value)
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
        self._index_map = {}
        h = [val.strip().lower().replace(' ', '_') for val in header]
        for index, label in enumerate(h):
            for name in field_names:
                if name not in self._index_map and name in label:
                    self._index_map[name] = index
                    break

    def _make_key(self, row):
        """Make a new Manufacturer|Model|Serial key for a dictionary"""
        return '{}|{}|{}'.format(row[self._index_map['manufacturer']],
                                 row[self._index_map['model']],
                                 row[self._index_map['serial']])

    def _is_key_unique(self, key, dictionary, element):
        """Returns whether the dictionary key is unique"""
        if key in dictionary:
            msg = 'Manufacturer|Model|Serial is not unique -> ' \
                  '{} in {}'.format(key, element.findtext('path'))
            logger.warning(msg)
            return False
        return True

    def _is_row_length_okay(self, row, header):
        """Check if the row and the header have the same length"""
        if not len(row) == len(header):
            logger.warning('len(row) [{}] != len(header) [{}] -> row={}'.format(len(row), len(header), row))
            return False
        return True

    def _to_enum(self, key, value, enum):
        """Convert the value to an enum value"""
        if isinstance(value, (int, float)):
            for item in enum:
                if value == item.value:
                    return item
            members = [str(item.value) for item in enum]
        else:
            if value.upper() in enum.__members__:
                return getattr(enum, value.upper())
            members = enum.__members__

        msg = 'Unknown {} value of "{}" for "{}". Must be one of: {}'
        raise ValueError(msg.format(enum.__name__, value, key, ', '.join(members)))

    def _search(self, record, kwargs, flags):
        """Check if the kwargs match a database record"""
        for key, value in kwargs.items():
            if key == 'backend' or key == 'interface':
                enum = constants.Backend if key == 'backend' else constants.MSLInterface
                try:
                    if self._to_enum(key, value, enum) != getattr(record, key):
                        return False
                except ValueError:
                    return False
            elif key == 'connection':
                conn = getattr(record, key)
                if bool(value):
                    # then want equipment records with a connection
                    if conn is None:
                        return False
                else:
                    if conn is not None:
                        return False
            elif key == 'date_calibrated':
                if not value(getattr(record, key)):
                    return False
            else:
                if not bool(re.search(value, getattr(record, key), flags)):
                    return False
        return True
