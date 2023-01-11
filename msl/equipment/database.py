"""
Load equipment and connection records from :ref:`Databases <database-formats>`.
"""
from __future__ import unicode_literals
import os
import re
import ast
import json
import codecs
from xml.etree import cElementTree

from msl.io import read_table_excel

from . import constants
from .record_types import (
    EquipmentRecord,
    ConnectionRecord,
)
from .utils import (
    logger,
    convert_to_primitive,
    convert_to_enum,
)


class Database(object):

    def __init__(self, path):
        """Create :class:`.EquipmentRecord`'s and :class:`.ConnectionRecord`'s
        from :ref:`Databases <database-formats>` that are specified in a :ref:`configuration-file`.

        This class should be accessed through the :meth:`~.config.Config.database` method
        after a :class:`~.config.Config` object has been created.

        Parameters
        ----------
        path : :class:`str`
            The path to an XML :ref:`configuration-file`.

        Raises
        ------
        OSError
            If `path` does not exist or if the :ref:`configuration-file` is invalid.
        AttributeError
            If an ``<equipment>`` XML tag is specified in the :ref:`configuration-file`
            and it does not uniquely identify an equipment record in an
            :ref:`equipment-database`.
        ValueError
            If an :attr:`~.EquipmentRecord.alias` has been specified multiple times
            for the same :class:`~.EquipmentRecord` or if the name of the Sheet in an Excel
            spreadsheet is invalid.
        """
        logger.debug('Loading databases from %s', path)

        try:
            root = cElementTree.parse(path).getroot()
        except cElementTree.ParseError as err:
            parse_err = str(err)  # want to raise OSError not ParseError
        else:
            parse_err = None

        if parse_err:
            raise OSError(parse_err)

        self._config_path = path

        # create a dictionary of all ConnectionRecord's
        self._connection_records = {}
        easy_names = ('address', 'backend', 'manufacturer', 'model', 'serial')
        for connections in root.iterfind('connections'):
            for element in connections.iterfind('connection'):
                data = self._read(element)
                if isinstance(data, tuple):  # then the information is stored as a table of rows and columns
                    header, rows = self._read(element)
                    index_map = self._make_index_map(header, ConnectionRecord.__slots__)
                    for row in rows:
                        if not self._is_row_length_okay(row, header):
                            continue
                        key = self._make_key(row, self._connection_records, element, index_map=index_map)
                        if not key:
                            continue
                        kwargs = {}
                        for name in easy_names:
                            kwargs[name] = row[index_map[name]]
                        kwargs['properties'] = {}
                        props = row[index_map['properties']]
                        if props:
                            for item in props.split(';'):
                                s = item.split('=')
                                if len(s) != 2:
                                    continue
                                kwargs['properties'][s[0].strip()] = convert_to_primitive(s[1])
                        self._connection_records[key] = ConnectionRecord(**kwargs)
                elif isinstance(data, dict):  # loaded a json or xml file
                    for record in data['connection_records']:
                        key = self._make_key(record, self._connection_records, element)
                        if not key:
                            continue
                        self._connection_records[key] = ConnectionRecord(**record)
                else:
                    assert False, 'Not a tuple or dict'

        # create a dictionary of EquipmentRecord's
        self._equipment_records = {}
        for registers in root.iterfind('registers'):
            for register in registers.iterfind('register'):
                team = register.attrib.get('team', '')
                data = self._read(register)
                if isinstance(data, tuple):  # then the information is stored as a table of rows and columns
                    header, rows = data
                    index_map = self._make_index_map(header, EquipmentRecord.__slots__)

                    # prepare the user_defined list
                    temp = register.attrib.get('user_defined', [])
                    user_defined = []
                    index_map_user_defined = {}
                    if temp:
                        temp = [t.strip().lower().replace(' ', '_') for t in temp.split(',') if t.strip()]
                        for name in temp:
                            if name in EquipmentRecord.__slots__:
                                logger.warning('The "user_defined" parameter %r is already an '
                                               'EquipmentRecord attribute', name)
                            else:
                                user_defined.append(name)
                        if user_defined:
                            index_map_user_defined = self._make_index_map(header, user_defined)

                    for row in rows:
                        if not self._is_row_length_okay(row, header):
                            continue

                        key = self._make_key(row, self._equipment_records, register, index_map=index_map)
                        if not key:
                            continue

                        kwargs = {'team': team}

                        # find the corresponding ConnectionRecord (if it exists)
                        try:
                            kwargs['connection'] = self._connection_records[key]
                        except KeyError:
                            pass
                        else:
                            alias = kwargs['connection'].properties.pop('alias', None)
                            if alias:
                                kwargs['alias'] = alias

                        for name in EquipmentRecord.__slots__:
                            try:
                                value = row[index_map[name]]
                            except KeyError:
                                continue

                            kwargs[name] = value

                        for name in user_defined:
                            try:
                                s = row[index_map_user_defined[name]]
                            except KeyError:
                                pass
                            else:
                                kwargs[name] = convert_to_primitive(s)

                        self._equipment_records[key] = EquipmentRecord(**kwargs)

                elif isinstance(data, dict):  # loaded a json or xml file
                    team = data.get('team', team)
                    for record in data['equipment_records']:
                        key = self._make_key(record, self._equipment_records, register)
                        if not key:
                            continue

                        record['team'] = team

                        # find the corresponding ConnectionRecord (if it exists)
                        try:
                            record['connection'] = self._connection_records[key]
                        except KeyError:
                            pass
                        else:
                            alias = record['connection'].properties.pop('alias', None)
                            if alias:
                                record['alias'] = alias

                        self._equipment_records[key] = EquipmentRecord(**record)
                else:
                    assert False, 'Not a tuple or dict'

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
        the :ref:`configuration-file`.
        """
        return self._equipment_using

    @property
    def path(self):
        """:class:`str`: The path to the :ref:`configuration-file`.
        """
        return self._config_path

    def connections(self, **kwargs):
        """Search the :ref:`connections-database` to find all :class:`.ConnectionRecord`\'s that
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
        * `connections()` :math:`\\rightarrow`
          a list of all ConnectionRecord's

        * `connections(manufacturer='Keysight')` :math:`\\rightarrow`
          a list of all ConnectionRecord's that have Keysight as the manufacturer

        * `connections(manufacturer='Agilent|Keysight')` :math:`\\rightarrow`
          a list of all ConnectionRecord's that are from Agilent or Keysight

        * `connections(manufacturer='H.*P')` :math:`\\rightarrow`
          a list of all ConnectionRecord's that have Hewlett Packard (or HP) as
          the manufacturer

        * `connections(manufacturer='Agilent', model='^34')` :math:`\\rightarrow`
          a list of all ConnectionRecord's that have Agilent as the manufacturer
          and a model number beginning with '34'

        * `connections(interface=MSLInterface.SERIAL)` :math:`\\rightarrow`
          a list of all ConnectionRecord's that use SERIAL for the connection bus

        * `connections(interface='SDK')` :math:`\\rightarrow`
          a list of all ConnectionRecord's that use the manufacturers SDK to
          control the equipment

        * `connections(backend=Backend.PyVISA)` :math:`\\rightarrow`
          a list of all ConnectionRecord's that use PyVISA as the backend

        * `connections(backend='MSL')` :math:`\\rightarrow`
          a list of all ConnectionRecord's that use MSL as the backend

        * `connections(properties={'baud_rate': 115200})` :math:`\\rightarrow`
          a list of all ConnectionRecord's that specify a baud rate equal to
          115200 in the Properties field

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
            if name not in ConnectionRecord.__slots__:
                raise NameError('Invalid argument name {!r} for a {}'.format(name, ConnectionRecord.__name__))
        return [r for r in self._connection_records.values() if self._search(r, kwargs, flags)]

    def records(self, **kwargs):
        """Search the :ref:`equipment-database` to find all :class:`.EquipmentRecord`\'s that
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

        Examples
        --------
        * `records()` :math:`\\rightarrow`
          a list of all EquipmentRecord's

        * `records(manufacturer='Agilent')` :math:`\\rightarrow`
          a list of all EquipmentRecord's that are from Agilent

        * `records(manufacturer='Agilent|Keysight')` :math:`\\rightarrow`
          a list of all EquipmentRecord's that are from Agilent or Keysight

        * `records(manufacturer='Agilent', model='3458A')` :math:`\\rightarrow`
          a list of all EquipmentRecords that are from Agilent and that have the model number 3458A

        * `records(manufacturer='Agilent', model='3458A', serial='MY45046470')` :math:`\\rightarrow`
          a list of only one EquipmentRecord (if the equipment record exists, otherwise an empty list)

        * `records(manufacturer=r'H.*P')` :math:`\\rightarrow`
          a list of all EquipmentRecord's that have Hewlett Packard (or HP) as the manufacturer

        * `records(description='I-V Converter')` :math:`\\rightarrow`
          a list of all EquipmentRecords that contain 'I-V Converter' in the description field

        * `records(connection=True)` :math:`\\rightarrow`
          a list of all EquipmentRecords that can be connected to

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
            if name not in EquipmentRecord.__slots__:
                raise NameError('Invalid argument name {!r} for an {}'.format(name, EquipmentRecord.__name__))
        return [r for r in self._equipment_records.values() if self._search(r, kwargs, flags)]

    def _read(self, element):
        """Read the allowed database file types."""
        path = element.findtext('path')
        if path is None:
            raise OSError('You must create a <path> </path> element in {!r} '
                          'specifying where to find the database'.format(self._config_path))

        logger.debug('Reading database file %s', path)
        ext = os.path.splitext(path)[1].lower()

        # also check if the path is a relative path (relative to the XML file path)
        relative_path = os.path.join(os.path.dirname(self._config_path), path)
        for p in [path, relative_path]:
            try:
                if ext in ('.xls', '.xlsx'):
                    encoding = element.attrib.get('encoding')
                    dset = read_table_excel(p, sheet=element.findtext('sheet'), encoding=encoding)
                    if dset.ndim == 1:
                        return dset.metadata.header, [dset.data]
                    return dset.metadata.header, dset.data
                elif ext in ('.csv', '.txt'):
                    delimiter = ',' if ext == '.csv' else '\t'
                    encoding = element.attrib.get('encoding', 'utf-8')
                    with codecs.open(p, mode='r', encoding=encoding) as fp:
                        header = [val for val in fp.readline().split(delimiter)]
                        rows = [[val.strip() for val in line.split(delimiter)]
                                for line in fp.readlines() if line.strip()]
                    return header, rows
                elif ext == '.json':
                    encoding = element.attrib.get('encoding', 'utf-8')
                    with codecs.open(p, mode='r', encoding=encoding) as fp:
                        return json.load(fp)
                elif ext == '.xml':
                    return self._read_xml(p)
                else:
                    raise OSError('Unsupported equipment-registry database file {!r}'.format(p))
            except (IOError, OSError) as err:
                if str(err).startswith('Unsupported equipment-registry'):
                    raise
        raise OSError('Cannot find the database {!r}'.format(path))

    def _read_xml(self, path):
        """Read an XML database."""
        def value(item):
            if item.tag.endswith('date'):
                return item.text
            try:
                return ast.literal_eval(item.text)
            except:
                return item.text

        def get(element, tag, default=None):
            e = element.find(tag) if tag else element
            if e is None:
                return default
            if len(e) == 0:
                return default if e.text is None else value(e)
            return dict((item.tag, get(item, None) if len(item) > 0 else value(item)) for item in e)

        root = cElementTree.parse(path).getroot()
        _dict = {'team': get(root, 'team', default='')}
        equipment_records = []
        for er in root.iterfind('.//EquipmentRecord'):
            record = {
                'calibrations': [
                    {
                        'report_date': get(cr, 'report_date', default=None),
                        'calibration_date': get(cr, 'calibration_date', default=None),
                        'report_number': get(cr, 'report_number', default=''),
                        'calibration_cycle': get(cr, 'calibration_cycle', default=0),
                        'measurands': [
                            {
                                'type': get(mr, 'type', default=''),
                                'unit': get(mr, 'unit', default=''),
                                'conditions': get(mr, 'conditions'),
                                'calibration': get(mr, 'calibration'),
                            } for mr in cr.iterfind('.//MeasurandRecord')
                        ]
                    } for cr in er.iterfind('.//CalibrationRecord')
                ],
                'category': get(er, 'category', default=''),
                'description': get(er, 'description', default=''),
                'is_operable': get(er, 'is_operable', default=False),
                'maintenances': [
                    {
                        'date': get(mr, 'date', default=None),
                        'comment': get(mr, 'comment', default=''),
                    } for mr in er.iterfind('.//MaintenanceRecord')
                ],
                'manufacturer': get(er, 'manufacturer', default=''),
                'model': get(er, 'model', default=''),
                'serial': get(er, 'serial', default=''),
                'unique_key': get(er, 'unique_key', default=''),
            }

            # add the user_defined kwargs
            for child in er:
                if child.tag not in record:
                    record[child.tag] = value(child)

            equipment_records.append(record)

        _dict['equipment_records'] = equipment_records

        _dict['connection_records'] = [
            dict((child.tag, get(child, None, default='')) for child in cr)
            for cr in root.iterfind('.//ConnectionRecord')
        ]

        return _dict

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

    def _make_key(self, obj, records, element, index_map=None):
        """Make a new Manufacturer|Model|Serial key."""
        if index_map is not None:
            manufacturer = obj[index_map['manufacturer']]
            model = obj[index_map['model']]
            serial = obj[index_map['serial']]
        else:
            manufacturer = obj.get('manufacturer', '')
            model = obj.get('model', '')
            serial = obj.get('serial', '')

        key = '{}|{}|{}'.format(manufacturer, model, serial)
        if key in records:
            logger.error('Manufacturer|Model|Serial is not unique -> %s in %r',
                         key, element.findtext('path'))
            return ''
        return key

    def _is_key_unique(self, key, dictionary, element):
        """Returns whether the dictionary key is unique"""
        if key in dictionary:
            logger.error('Manufacturer|Model|Serial is not unique -> %s in %r',
                         key, element.findtext('path'))
            return False
        return True

    def _is_row_length_okay(self, row, header):
        """Check if the row and the header have the same length"""
        if not len(row) == len(header):
            logger.error('len(row) [%d] != len(header) [%d] -> row: %s', len(row), len(header), row)
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
            elif key == 'properties':
                if not isinstance(value, dict):
                    raise TypeError('The "properties" value must be a dict, got {}'.format(type(value)))
                for k, v in value.items():
                    if k not in record.properties:
                        return False
                    if v != record.properties[k]:
                        return False
            elif key == 'is_operable':
                return getattr(record, key) is bool(value)
            else:
                if not bool(re.search(value, getattr(record, key), flags)):
                    return False
        return True
