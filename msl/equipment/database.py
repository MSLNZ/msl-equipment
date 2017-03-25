"""
Load equipment and connection records (rows) from the database.
"""
import os
import re
import logging
import datetime
from xml.etree import ElementTree

import xlrd

from msl.equipment import constants
from msl.equipment.record_types import EquipmentRecord, ConnectionRecord

logger = logging.getLogger(__name__)


def load(path):
    """
    Load equipment and connection records (rows) from the databases that are
    specified in a configuration file.

    Args:
        path (str): The path to a XML configuration file.

    Returns:
        :class:`Database`: The equipment and connection records in the database.
    """
    return Database(path)


class Database(object):

    def __init__(self, path):
        """
        Loads a configuration file to create :class:`.EquipmentRecord` objects
        from equipment records that are in Equipment-Register databases and
        :class:`.ConnectionRecord` objects from connection records that are in
        Connection databases.

        Args:
            path (str): The path to a XML configuration file.

        Raises:
            IOError: If there was a problem parsing the configuration file.
            AttributeError: If an <equipment> XML element is specified in the configuration
                file and it does not uniquely identify an equipment record in the
                Equipment-Register database.
            ValueError: If any of the values in the Connection database are invalid.
        """
        if not os.path.isfile(path):
            raise IOError('Cannot find the configuration file ' + path)

        if '.xml' != os.path.splitext(path)[1].lower():
            raise IOError('Only XML configuration files are currently supported')

        logger.debug('Loading databases from ' + path)

        self._config_path = path

        self._equipment_attributes = EquipmentRecord.attributes()
        self._connection_attributes = ConnectionRecord.attributes()

        root = ElementTree.parse(path).getroot()

        # create a dictionary of ConnectionRecord objects
        self._connection_records = {}
        for element in root.findall('equipment_connections'):

            header, rows = self._read(element)
            self._make_index_map(header, self._connection_attributes)

            for row in rows:
                if not self._is_row_length_okay(row, header):
                    continue

                key = self._make_key(row)
                if not self._is_key_unique(key, self._connection_records, element):
                    continue

                record = ConnectionRecord()

                # auto set the attributes that are string datatypes
                for attrib in ('address', 'manufacturer', 'model', 'serial'):
                    setattr(record, '_'+attrib, row[self._index_map[attrib]])

                # set the backend to use to communicate with the equipment
                backend = row[self._index_map['backend']]
                if backend in constants.Backend.__members__:
                    record._backend = getattr(constants.Backend, backend)
                else:
                    logger.warning('Unknown Backend "{}"'.format(backend))

                # set the connection interface to use for the MSL backend
                if record.backend == constants.Backend.MSL:

                    # determine the connection interface from the address
                    match = re.match('[+_A-Z]+', record.address.upper())
                    interface = '' if match is None else match.group(0).replace('+', '_')

                    # check if aliases are used for the connection interface
                    for name, values in constants.MSL_INTERFACE_ALIASES.items():
                        for value in values:
                            if value in interface:
                                interface = interface.replace(value, name)
                                record._address = record.address.replace(value, name)

                    # set the interface
                    if interface in constants.MSLInterface.__members__:
                        record._interface = getattr(constants.MSLInterface, interface)
                    else:
                        logger.warning('Unknown MSL Interface "{}"'.format(interface))

                # create the property dictionary
                record._properties = {}
                for item in row[self._index_map['properties']].split(";"):
                    if len(item.strip()) > 1:

                        item_split = item.split('=')
                        k, v = item_split[0].strip(), item_split[1].strip()

                        if 'ASRL' in record.interface.name:
                            if k.lower().startswith('parity'):
                                v = self._check_asrl_property(key, v, constants.Parity)
                            elif k.lower().startswith('flow'):
                                v = self._check_asrl_property(key, v, constants.FlowControl)
                            elif k.lower().startswith('stop'):
                                v = self._check_asrl_property(key, int(10*float(v)), constants.StopBits)
                            elif k.lower().startswith('data'):
                                v = self._check_asrl_property(key, int(v), constants.DataBits)
                            elif k.lower().startswith('baud'):
                                v = int(v)

                        record._properties[k] = v

                self._connection_records[key] = record

        # create a dictionary of all the EquipmentRecord objects that are found in the Equipment Registers
        self._equipment_records = {}
        for registers in root.findall('equipment_registers'):
            for register in registers.findall('register'):

                # the MSL section (e.g., Electrical) that this Equipment Register belongs to
                section = register.attrib.get('section', '')

                header, rows = self._read(register)
                self._make_index_map(header, self._equipment_attributes)

                for row in rows:
                    if not self._is_row_length_okay(row, header):
                        continue

                    key = self._make_key(row)
                    if not self._is_key_unique(key, self._equipment_records, register):
                        continue

                    record = EquipmentRecord()
                    record._section = section

                    if key in self._connection_records:
                        record._connection = self._connection_records[key]
                        if 'alias' in record.connection.properties:
                            record.alias = record.connection.properties['alias']
                            del record.connection.properties['alias']

                    for attrib in self._equipment_attributes:
                        try:
                            value = row[self._index_map[attrib]]
                        except KeyError:
                            continue

                        if attrib == 'date_calibrated' and isinstance(value, str):
                            date_format = register.attrib.get('date_format', '')
                            if date_format:
                                try:
                                    value = datetime.datetime.strptime(value, date_format).date()
                                except ValueError:
                                    # if the date cannot be converted to a datetime.date object then ignore it
                                    continue
                            else:
                                # if the date cannot be converted to a datetime.date object then ignore it
                                continue

                        setattr(record, '_'+attrib, value)

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
                raise AttributeError('No equipment records found with attributes {}'.format(element.attrib))
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
        """
        A :py:class:`dict` of :class:`.EquipmentRecord`\'s that were listed as <equipment> XML elements
        in the configuration file which are being used to perform a measurement in the laboratory.
        """
        return self._equipment_using

    @property
    def path(self):
        """
        :py:class:`str`: The path to the configuration file that contains the information about the
        Equipment-Register and Connection databases.
        """
        return self._config_path

    def connections(self, **kwargs):
        """
        Search the Connections database to find all connection records that
        match the specified criteria.

        Args:
            **kwargs: The keys can be any of the :class:`.ConnectionRecord` property names.
                The comparison for the value is performed by `regex <http://www.pyregex.com/>`_.

        Returns:
            A :py:class:`list` of :class:`.ConnectionRecord`\'s that match the search criteria.

        Examples:
            >>> connections()  # doctest: +SKIP
            will return a list of all connection records

            >>> connections(manufacturer='H*P')  # doctest: +SKIP
            will return a list of all connection records that have Hewlett Packard as the manufacturer

            >>> connections(address='GPIB*')  # doctest: +SKIP
            will return a list of all connection records that use GPIB for the connection bus
        """
        # only use the keys that are ConnectionRecord attributes
        _kwargs = {key: kwargs[key] for key in kwargs if key in self._connection_attributes}
        return [r for r in self._connection_records.values() if self._match(r, _kwargs)]

    def records(self, **kwargs):
        """
        Search the Equipment-Register database to find all equipment records that
        match the specified criteria.

        Args:
            **kwargs: The keys can be any of the :class:`.EquipmentRecord` property names.
                The comparison for the value is performed by `regex <http://www.pyregex.com/>`_.

        Returns:
            A :py:class:`list` of :class:`.EquipmentRecord`\'s that match the search criteria.

        Examples:
            >>> records()  # doctest: +SKIP
            will return a list of all equipment records

            >>> records(manufacturer='H*P')  # doctest: +SKIP
            will return a list of all equipment records that have Hewlett Packard as the manufacturer

            >>> records(manufacturer='Agilent', model='3458A')  # doctest: +SKIP
            will return a list of all equipment records that are from Agilent and that have the model number 3458A

            >>> records(manufacturer='Agilent', model='3458A', serial='MY45046470')  # doctest: +SKIP
            will return a list of only one equipment record

            >>> records(description='I-V Converter')  # doctest: +SKIP
            will return a list of all equipment records that contain the string 'I-V Converter' in the description field
        """
        # only use the keys that are EquipmentRecord attributes
        _kwargs = {key: kwargs[key] for key in kwargs if key in self._equipment_attributes}
        return [r for r in self._equipment_records.values() if self._match(r, _kwargs)]

    def _read(self, element):
        """Read a database file"""
        path = element.findtext('path')
        if path is None:
            raise IOError('You must create a <path> </path> element in {} '
                          'specifying where to find the database'.format(self._config_path))

        if not os.path.isfile(path):
            # check if the path is a relative path (relative to the .XML file path)
            path = os.path.join(os.path.dirname(self._config_path), path)
            if not os.path.isfile(path):
                raise IOError('Cannot find the database ' + path)

        ext = os.path.splitext(path)[1].lower()
        if ext in ('.xls', '.xlsx'):
            header, rows = self._read_excel(path, element.findtext('sheet'))
        elif ext in ('.csv', '.txt'):
            delimiter = ',' if ext == '.csv' else '\t'
            header, rows = self._read_ascii(path, delimiter)
        else:
            raise IOError('Unsupported equipment-registry database format ' + path)

        logger.debug('Read database ' + path)
        return header, rows

    def _read_excel(self, path, sheet_name):
        """Read an Excel database file"""
        self._book = xlrd.open_workbook(path, on_demand=True)

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

        sheet = self._book.sheet_by_name(sheet_name)
        header = [str(val) for val in sheet.row_values(0)]
        rows = [[self._cell_convert(sheet.cell(r, c)) for c in range(sheet.ncols)] for r in range(1, sheet.nrows)]
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

    def _read_ascii(self, path, delimiter):
        """Read an ASCII database file"""
        with open(path, 'r') as fp:
            header = [val for val in fp.readline().split(delimiter)]
            rows = [[val.strip() for val in line.split(delimiter)] for line in fp.readlines() if line.strip()]
        return header, rows

    def _make_index_map(self, header, attributes):
        """Determine the column numbers in the header that the attributes are located in"""
        self._index_map = {}
        h = [item.strip().lower().replace(' ', '_') for item in header]
        for index, label in enumerate(h):
            for attrib in attributes:
                if attrib not in self._index_map and attrib in label:
                    self._index_map[attrib] = index
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
            logger.warning('len(row) != len(header) -> row={}'.format(row))
            return False
        return True

    def _check_asrl_property(self, key, value, enum):
        """Check if the enum property is valid for a Serial communication interface"""
        if isinstance(value, int):
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

    def _match(self, record, kwargs):
        """Check if the kwargs match a database record"""
        for key, value in kwargs.items():
            if not bool(re.search(value, str(getattr(record, key)))):
                return False
        return True
