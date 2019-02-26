# -*- coding: utf8 -*-
import os
import sys
import datetime
import tempfile
from xml.etree.ElementTree import ElementTree

import pytest

from msl.equipment.config import Config
from msl.equipment import EquipmentRecord, ConnectionRecord, Backend
from msl.equipment.constants import MSLInterface, DataBits, Parity, StopBits, LF, CR

PY2 = sys.version_info.major == 2
if not PY2:
    unicode = str


def test_equipment_record():

    temp = os.path.join(tempfile.gettempdir(), 'msl-equipment-record.xml')

    # the default values
    record = EquipmentRecord()
    print(record)  # make sure it is printable
    print(repr(record))
    assert record.alias == ''
    assert record.calibration_cycle == 0.0
    assert record.category == ''
    assert record.connection is None
    assert record.date_calibrated == datetime.date(datetime.MINYEAR, 1, 1)
    assert record.description == ''
    assert record.latest_report_number == ''
    assert record.location == ''
    assert record.manufacturer == ''
    assert record.model == ''
    assert record.serial == ''
    assert record.team == ''
    assert record.user_defined == {}

    a = record.to_dict()
    assert len(a) == 13
    assert a['alias'] == ''
    assert a['calibration_cycle'] == 0.0
    assert a['category'] == ''
    assert a['connection'] is None
    assert a['date_calibrated'] == datetime.date(datetime.MINYEAR, 1, 1)
    assert a['description'] == ''
    assert a['latest_report_number'] == ''
    assert a['location'] == ''
    assert a['manufacturer'] == ''
    assert a['model'] == ''
    assert a['serial'] == ''
    assert a['team'] == ''
    assert a['user_defined'] == {}

    tree = ElementTree(record.to_xml())
    tree.write(temp)
    a = ElementTree().parse(temp)
    assert len(a) == 13
    assert a.find('alias').text is None
    assert a.find('calibration_cycle').text is None
    assert a.find('category').text is None
    assert a.find('connection').text is None
    assert a.find('date_calibrated').text is None
    assert a.find('description').text is None
    assert a.find('latest_report_number').text is None
    assert a.find('location').text is None
    assert a.find('manufacturer').text is None
    assert a.find('model').text is None
    assert a.find('serial').text is None
    assert a.find('team').text is None
    assert a.find('user_defined').text is None

    a = repr(record).splitlines()
    assert len(a) == 13
    assert a[0] == "alias: u''" if PY2 else "alias: ''"
    assert a[1] == 'calibration_cycle: 0.0'
    assert a[2] == "category: u''" if PY2 else "category: ''"
    assert a[3] == 'connection: None'
    assert a[4] == 'date_calibrated: datetime.date(1, 1, 1)'
    assert a[5] == "description: u''" if PY2 else "description: ''"
    assert a[6] == "latest_report_number: u''" if PY2 else "latest_report_number: ''"
    assert a[7] == "location: u''" if PY2 else "location: ''"
    assert a[8] == "manufacturer: u''" if PY2 else "manufacturer: ''"
    assert a[9] == "model: u''" if PY2 else "model: ''"
    assert a[10] == "serial: u''" if PY2 else "serial: ''"
    assert a[11] == "team: u''" if PY2 else "team: ''"
    assert a[12] == "user_defined: {}"

    # populate the EquipmentRecord
    record = EquipmentRecord(
        alias='my alias',
        calibration_cycle=5,
        category='DMM',
        connection=ConnectionRecord(
            address='GPIB::15',
            backend=Backend.PyVISA,
            manufacturer=u'uñicödé',
            model='XYZ',
            serial='ABC123',
            properties={
                'none': None,
                'bytes': b'\x02\x19\x08',
                'string': 'string',
                'unicode': u'uñicödé',
                'termination': '\r\n',
                'boolean': True,
                'integer': 77,
                'float': 12.34,
                'complex': -2-3j,
                'enum': StopBits.ONE_POINT_FIVE,
            },
        ),
        date_calibrated=datetime.date(2018, 8, 20),
        description=u'Sométhing uséful',
        latest_report_number='Report:12-3/4',
        location='the lab',
        manufacturer=u'uñicödé',
        model='XYZ',
        serial='ABC123',
        team='P&R',
        a='a',  # goes into the user_defined dict
        b=8,  # goes into the user_defined dict
        c=[1, 2, 3],  # goes into the user_defined dict
    )
    print(unicode(record))  # make sure it is printable
    print(unicode(repr(record)))
    assert record.alias == 'my alias'
    assert record.calibration_cycle == 5
    assert record.category == 'DMM'
    assert record.connection.address == 'GPIB::15'
    assert record.connection.backend == Backend.PyVISA
    assert record.connection.interface == MSLInterface.NONE  # using PyVISA as the backend
    assert record.connection.manufacturer == u'uñicödé'
    assert record.connection.model == 'XYZ'
    assert record.connection.properties['none'] is None
    assert record.connection.properties['bytes'] == b'\x02\x19\x08'
    assert record.connection.properties['string'] == 'string'
    assert record.connection.properties['unicode'] == u'uñicödé'
    assert record.connection.properties['termination'] == b'\r\n'
    assert record.connection.properties['boolean'] is True
    assert record.connection.properties['integer'] == 77
    assert record.connection.properties['float'] == 12.34
    assert record.connection.properties['complex'] == -2-3j
    assert record.connection.properties['enum'] == StopBits.ONE_POINT_FIVE
    assert record.connection.serial == 'ABC123'
    assert record.date_calibrated == datetime.date(2018, 8, 20)
    assert record.description == u'Sométhing uséful'
    assert record.latest_report_number == 'Report:12-3/4'
    assert record.location == 'the lab'
    assert record.manufacturer == u'uñicödé'
    assert record.model == 'XYZ'
    assert record.serial == 'ABC123'
    assert record.team == 'P&R'
    assert record.user_defined['a'] == 'a'
    assert record.user_defined['b'] == 8
    assert record.user_defined['c'] == [1, 2, 3]

    a = record.to_dict()
    assert len(a) == 13
    assert a['alias'] == 'my alias'
    assert a['calibration_cycle'] == 5
    assert a['category'] == 'DMM'
    assert a['connection']['address'] == 'GPIB::15'
    assert a['connection']['backend'] == Backend.PyVISA
    assert a['connection']['interface'] == MSLInterface.NONE  # using PyVISA as the backend
    assert a['connection']['manufacturer'] == u'uñicödé'
    assert a['connection']['model'] == 'XYZ'
    assert a['connection']['properties']['none'] is None
    assert a['connection']['properties']['bytes'] == b'\x02\x19\x08'
    assert a['connection']['properties']['string'] == 'string'
    assert a['connection']['properties']['unicode'] == u'uñicödé'
    assert a['connection']['properties']['termination'] == b'\r\n'
    assert a['connection']['properties']['boolean'] is True
    assert a['connection']['properties']['integer'] == 77
    assert a['connection']['properties']['float'] == 12.34
    assert a['connection']['properties']['complex'] == -2-3j
    assert a['connection']['properties']['enum'] == StopBits.ONE_POINT_FIVE
    assert a['connection']['serial'] == 'ABC123'
    assert a['date_calibrated'] == datetime.date(2018, 8, 20)
    assert a['description'] == u'Sométhing uséful'
    assert a['latest_report_number'] == 'Report:12-3/4'
    assert a['location'] == 'the lab'
    assert a['manufacturer'] == u'uñicödé'
    assert a['model'] == 'XYZ'
    assert a['serial'] == 'ABC123'
    assert a['team'] == 'P&R'
    assert a['user_defined']['a'] == 'a'
    assert a['user_defined']['b'] == 8
    assert a['user_defined']['c'] == [1, 2, 3]

    tree = ElementTree(record.to_xml())
    tree.write(temp)
    a = ElementTree().parse(temp)
    assert len(a) == 13
    assert a.find('alias').text == 'my alias'
    assert a.find('calibration_cycle').text == '5'
    assert a.find('category').text == 'DMM'
    assert a.find('connection').find('address').text == 'GPIB::15'
    assert a.find('connection/backend').text == 'PyVISA'
    assert a.find('connection/interface').text == 'NONE'  # using PyVISA as the backend
    assert a.find('connection/manufacturer').text == u'uñicödé'
    assert a.find('connection/model').text == 'XYZ'
    assert a.find('connection/properties').text is None
    assert a.find('connection/properties/none').text == 'None'
    assert a.find('connection/properties/bytes').text == "'\\x02\\x19\\x08'" if PY2 else "b'\x02\x19\x08'"
    assert a.find('connection/properties/string').text == "'string'" if PY2 else 'string'
    assert a.find('connection/properties/unicode').text == u'u\xf1ic\xf6d\xe9' if PY2 else 'uñicödé'
    assert a.find('connection/properties/termination').text == "'\\r\\n'" if PY2 else "b'\\r\\n'"
    assert a.find('connection/properties/boolean').text == 'True'
    assert a.find('connection/properties/integer').text == '77'
    assert a.find('connection/properties/float').text == '12.34'
    assert a.find('connection/properties/complex').text == '(-2-3j)'
    assert a.find('connection/properties/enum').text == 'ONE_POINT_FIVE'
    assert a.find('connection/serial').text == 'ABC123'
    assert a.find('date_calibrated').text == '2018-08-20'
    assert a.find('description').text == u'Sométhing uséful'
    assert a.find('latest_report_number').text == 'Report:12-3/4'
    assert a.find('location').text == 'the lab'
    assert a.find('manufacturer').text == u'u\xf1ic\xf6d\xe9' if PY2 else 'uñicödé'
    assert a.find('model').text == 'XYZ'
    assert a.find('serial').text == 'ABC123'
    assert a.find('team').text == 'P&R'
    assert a.find('user_defined').text is None
    assert a.find('user_defined/a').text == 'a'
    assert a.find('user_defined/b').text == '8'
    assert a.find('user_defined/c').text == '[1, 2, 3]'

    a = repr(record).splitlines()
    assert len(a) == 33
    assert a[0] == "alias: 'my alias'"
    assert a[1] == 'calibration_cycle: 5.0'
    assert a[2] == "category: 'DMM'"
    assert a[3] == 'connection:'
    assert a[4] == "  address: 'GPIB::15'"
    assert a[5] == '  backend: <Backend.PyVISA: 2>'
    assert a[6] == '  interface: <MSLInterface.NONE: 0>'
    assert a[7] == "  manufacturer: u'u\\xf1ic\\xf6d\\xe9'" if PY2 else "manufacturer: 'uñicödé'"
    assert a[8] == "  model: 'XYZ'"
    assert a[9] == '  properties:'
    assert a[10] == '    boolean: True'
    assert a[11] == "    bytes: '\\x02\\x19\\x08'" if PY2 else "    bytes: b'\x02\x19\x08'"
    assert a[12] == '    complex: (-2-3j)'
    assert a[13] == '    enum: <StopBits.ONE_POINT_FIVE: 1.5>'
    assert a[14] == '    float: 12.34'
    assert a[15] == '    integer: 77'
    assert a[16] == '    none: None'
    assert a[17] == "    string: 'string'"
    assert a[18] == "    termination: '\\r\\n'" if PY2 else "    termination: b'\\r\\n'"
    assert a[19] == "    unicode: u'u\\xf1ic\\xf6d\\xe9'" if PY2 else "    unicode: 'uñicödé'"
    assert a[20] == "  serial: 'ABC123'"
    assert a[21] == 'date_calibrated: datetime.date(2018, 8, 20)'
    assert a[22] == "description: u'Som\\xe9thing us\\xe9ful'" if PY2 else "description: 'Sométhing uséful'"
    assert a[23] == "latest_report_number: 'Report:12-3/4'"
    assert a[24] == "location: 'the lab'"
    assert a[25] == "manufacturer: u'u\\xf1ic\\xf6d\\xe9'" if PY2 else "manufacturer: 'uñicödé'"
    assert a[26] == "model: 'XYZ'"
    assert a[27] == "serial: 'ABC123'"
    assert a[28] == "team: 'P&R'"
    assert a[29] == 'user_defined:'
    assert a[30] == "  a: 'a'"
    assert a[31] == '  b: 8'
    assert a[32] == '  c: [1, 2, 3]'

    #
    # Check specifying date_calibrated and/or calibration_cycle
    #

    today = datetime.date.today()
    record = EquipmentRecord(date_calibrated=today, calibration_cycle=5)
    assert record.calibration_cycle == 5.0
    assert record.date_calibrated.year == today.year
    assert record.date_calibrated.month == today.month
    assert record.date_calibrated.day == today.day

    EquipmentRecord(calibration_cycle='5')

    r = EquipmentRecord(calibration_cycle='5.7')
    assert r.calibration_cycle == 5.7

    r = EquipmentRecord(calibration_cycle='-5.7')
    assert r.calibration_cycle == 0.0

    with pytest.raises(ValueError):
        EquipmentRecord(calibration_cycle='is not an number')

    with pytest.raises(TypeError):
        EquipmentRecord(date_calibrated='2017-08-15')

    #
    # Check setting the ConnectionRecord
    #

    for item in [None, 1, 6j, 'hello', True, object, 7.7, b'\x00']:
        with pytest.raises(TypeError):
            EquipmentRecord(connection=item)

    record = EquipmentRecord(manufacturer='ABC def', model='ZZZ', serial='DY135/055')

    # check that the manufacturer, model and serial values all match
    record.connection = ConnectionRecord(manufacturer='ABC def', model='ZZZ', serial='DY135/055')

    # one of the manufacturer, model or serial values do not match
    with pytest.raises(ValueError) as err:
        record.connection = ConnectionRecord(manufacturer='XYZ')
    assert '.manufacturer' in str(err.value)
    with pytest.raises(ValueError) as err:
        record.connection = ConnectionRecord(manufacturer='ABC def', model='AAA')
    assert '.model' in str(err.value)
    with pytest.raises(ValueError) as err:
        record.connection = ConnectionRecord(manufacturer='ABC def', model='ZZZ', serial='AAA')
    assert '.serial' in str(err.value)

    # check that the manufacturer, model and serial values for the ConnectionRecord get updated
    record = EquipmentRecord(manufacturer='Company', model='ABC', serial='XYZ', connection=ConnectionRecord())
    assert record.connection.manufacturer == 'Company'
    assert record.connection.model == 'ABC'
    assert record.connection.serial == 'XYZ'

    #
    # Specifying a kwarg that is not expected goes into the self._user_defined dictionary
    #
    record = EquipmentRecord(unknown_attribute='AAA', dictionary={'a': 1, 'b': 2})
    assert record.user_defined['unknown_attribute'] == 'AAA'
    assert record.user_defined['dictionary'] == dict(a=1, b=2)

    os.remove(temp)


def test_connection_record():
    temp = os.path.join(tempfile.gettempdir(), 'msl-connection-record.xml')

    # The default values
    record = ConnectionRecord()
    print(record)  # make sure it is printable
    print(repr(record))
    assert record.address == ''
    assert record.backend == Backend.UNKNOWN
    assert record.interface == MSLInterface.NONE
    assert record.manufacturer == ''
    assert record.model == ''
    assert record.properties == {}
    assert record.serial == ''

    a = record.to_dict()
    assert len(a) == 7
    assert a['address'] == ''
    assert a['backend'] == Backend.UNKNOWN
    assert a['interface'] == MSLInterface.NONE
    assert a['manufacturer'] == ''
    assert a['model'] == ''
    assert a['properties'] == {}
    assert a['serial'] == ''

    tree = ElementTree(record.to_xml())
    tree.write(temp, encoding='UTF-8')
    a = ElementTree().parse(temp)
    assert len(a) == 7
    assert a.find('address').text is None
    assert a.find('backend').text == 'UNKNOWN'
    assert a.find('interface').text == 'NONE'
    assert a.find('manufacturer').text is None
    assert a.find('model').text is None
    assert a.find('properties').text is None
    assert a.find('serial').text is None

    a = repr(ConnectionRecord()).splitlines()
    assert len(a) == 7
    assert a[0] == "address: u''" if PY2 else "address: ''"
    assert a[1] == 'backend: <Backend.UNKNOWN: 0>'
    assert a[2] == 'interface: <MSLInterface.NONE: 0>'
    assert a[3] == "manufacturer: u''" if PY2 else "manufacturer: ''"
    assert a[4] == "model: u''" if PY2 else "model: ''"
    assert a[5] == 'properties: {}'
    assert a[6] == "serial: u''" if PY2 else "serial: ''"

    # create a new ConnectionRecord
    record = ConnectionRecord(
        address='GPIB::15',
        backend=Backend.PyVISA,
        manufacturer=u'uñicödé',
        model='XYZ',
        serial='ABC123',
        properties={
            'none': None,
            'bytes': b'\x02\x19\x08',
            'string': 'string',
            'unicode': u'uñicödé',
            'termination': '\r\n',
            'boolean': True,
            'integer': 77,
            'float': 12.34,
            'complex': -2-3j,
            'enum': StopBits.ONE_POINT_FIVE,
        },
    )
    print(unicode(record))  # make sure it is printable
    print(unicode(repr(record)))
    assert record.address == 'GPIB::15'
    assert record.backend == Backend.PyVISA
    assert record.interface == MSLInterface.NONE  # using PyVISA as the backend
    assert record.manufacturer == u'uñicödé'
    assert record.model == 'XYZ'
    assert record.properties['none'] is None
    assert record.properties['bytes'] == b'\x02\x19\x08'
    assert record.properties['string'] == 'string'
    assert record.properties['unicode'] == u'uñicödé'
    assert record.properties['termination'] == b'\r\n'
    assert record.properties['boolean'] is True
    assert record.properties['integer'] == 77
    assert record.properties['float'] == 12.34
    assert record.properties['complex'] == -2-3j
    assert record.properties['enum'] == StopBits.ONE_POINT_FIVE
    assert record.serial == 'ABC123'

    a = record.to_dict()
    assert len(a) == 7
    assert a['address'] == 'GPIB::15'
    assert a['backend'] == Backend.PyVISA
    assert a['interface'] == MSLInterface.NONE  # using PyVISA as the backend
    assert a['manufacturer'] == u'uñicödé'
    assert a['model'] == 'XYZ'
    assert a['properties']['none'] is None
    assert a['properties']['bytes'] == b'\x02\x19\x08'
    assert a['properties']['string'] == 'string'
    assert a['properties']['unicode'] == u'uñicödé'
    assert a['properties']['termination'] == b'\r\n'
    assert a['properties']['boolean'] is True
    assert a['properties']['integer'] == 77
    assert a['properties']['float'] == 12.34
    assert a['properties']['complex'] == -2-3j
    assert a['properties']['enum'] == StopBits.ONE_POINT_FIVE
    assert a['serial'] == 'ABC123'

    tree = ElementTree(record.to_xml())
    tree.write(temp, encoding='UTF-8')
    a = ElementTree().parse(temp)
    assert len(a) == 7
    assert a.find('address').text == 'GPIB::15'
    assert a.find('backend').text == 'PyVISA'
    assert a.find('interface').text == 'NONE'
    assert a.find('manufacturer').text == u'uñicödé'
    assert a.find('model').text == 'XYZ'
    props = a.find('properties')
    assert props.find('none').text == 'None'
    assert props.find('bytes').text == "'\\x02\\x19\\x08'" if PY2 else "b'\x02\x19\x08'"
    assert props.find('string').text == "'string'" if PY2 else 'string'
    assert props.find('unicode').text == u'u\xf1ic\xf6d\xe9' if PY2 else 'uñicödé'
    assert props.find('termination').text == "'\\r\\n'" if PY2 else "b'\\r\\n'"
    assert props.find('boolean').text == 'True'
    assert props.find('integer').text == '77'
    assert props.find('float').text == '12.34'
    assert props.find('complex').text == '(-2-3j)'
    assert props.find('enum').text == 'ONE_POINT_FIVE'
    assert a.find('serial').text == 'ABC123'

    a = repr(record).splitlines()
    assert len(a) == 17
    assert a[0] == "address: 'GPIB::15'"
    assert a[1] == 'backend: <Backend.PyVISA: 2>'
    assert a[2] == 'interface: <MSLInterface.NONE: 0>'
    assert a[3] == "manufacturer: u'u\\xf1ic\\xf6d\\xe9'" if PY2 else "manufacturer: 'uñicödé'"
    assert a[4] == "model: 'XYZ'"
    assert a[5] == 'properties:'
    assert a[6] == '  boolean: True'
    assert a[7] == "  bytes: '\\x02\\x19\\x08'" if PY2 else "  bytes: b'\\x02\\x19\\x08'"
    assert a[8] == '  complex: (-2-3j)'
    assert a[9] == '  enum: <StopBits.ONE_POINT_FIVE: 1.5>'
    assert a[10] == '  float: 12.34'
    assert a[11] == '  integer: 77'
    assert a[12] == '  none: None'
    assert a[13] == "  string: 'string'"
    assert a[14] == "  termination: '\\r\\n'" if PY2 else "  termination: b'\\r\\n'"
    assert a[15] == "  unicode: u'u\\xf1ic\\xf6d\\xe9'" if PY2 else "  unicode: 'uñicödé'"
    assert a[16] == "serial: 'ABC123'"

    #
    # The following are interface checks
    #

    # unknown address value does not raise an exception because the backend is not MSL
    c = ConnectionRecord(address='XXXXXX')
    assert c.interface == MSLInterface.NONE

    # invalid address for an MSL Backend -> cannot determine the MSLInterface
    with pytest.raises(ValueError) as err:
        ConnectionRecord(address='XXXXXX', backend=Backend.MSL)
    assert str(err.value).startswith('Cannot determine the MSLInterface')

    # if the user specifies the interface then this interface is used regardless of the value of address
    for interface in [MSLInterface.SDK, 'SDK', u'SDK', 1]:
        c = ConnectionRecord(address='XXXXXX', backend=Backend.MSL, interface=interface)
        assert c.interface == MSLInterface.SDK

    # setting the interface to something that cannot be converted to an MSLInterface
    for interface in [None, -1, -9.9, 'XXXXX']:
        with pytest.raises(ValueError) as err:
            ConnectionRecord(address='COM1', backend=Backend.MSL, interface=interface)
        assert str(err.value).endswith('not a valid MSLInterface')

    # MSLInterface.SDK
    record = ConnectionRecord(address='SDK::whatever.dll', backend=Backend.MSL)
    assert record.interface == MSLInterface.SDK

    record = ConnectionRecord(address='SDK::/path/to/whatever.dll', backend=Backend.MSL)
    assert record.interface == MSLInterface.SDK

    # MSLInterface.SERIAL
    record = ConnectionRecord(address='COM4', backend=Backend.MSL)
    assert record.interface == MSLInterface.SERIAL  # COM is an alias

    record = ConnectionRecord(address='ASRLCOM4', backend=Backend.MSL)
    assert record.interface == MSLInterface.SERIAL   # ASRLCOM is used by PyVISA

    record = ConnectionRecord(address='LPT5', backend=Backend.MSL)
    assert record.interface == MSLInterface.SERIAL   # LPT is an alias

    record = ConnectionRecord(address='ASRL4', backend=Backend.MSL)
    assert record.interface == MSLInterface.SERIAL  # ASRL is an alias

    # MSLInterface.SOCKET
    record = ConnectionRecord(address='SOCKET::127.0.0.1::1234', backend=Backend.MSL)
    assert record.interface == MSLInterface.SOCKET

    record = ConnectionRecord(address='ENET::127.0.0.1::1234', backend=Backend.MSL)
    assert record.interface == MSLInterface.SOCKET  # ENET is an alias for SOCKET

    record = ConnectionRecord(address='ETHERNET::127.0.0.1::1234', backend=Backend.MSL)
    assert record.interface == MSLInterface.SOCKET  # ETHERNET is an alias for SOCKET

    record = ConnectionRecord(address='LAN::127.0.0.1::1234', backend=Backend.MSL)
    assert record.interface == MSLInterface.SOCKET  # LAN is an alias for SOCKET

    record = ConnectionRecord(address='TCPIP::127.0.0.1::1234::SOCKET', backend=Backend.MSL)
    assert record.interface == MSLInterface.SOCKET  # PyVISA naming scheme

    record = ConnectionRecord(address='TCP::127.0.0.1::1234', backend=Backend.MSL)
    assert record.interface == MSLInterface.SOCKET  # TCP is an alias for SOCKET

    record = ConnectionRecord(address='UDP::127.0.0.1::1234', backend=Backend.MSL, properties=dict(x=1))
    assert record.interface == MSLInterface.SOCKET  # UDP is an alias for SOCKET
    assert record.properties['socket_type'] == 'SOCK_DGRAM'  # gets set automatically
    assert record.properties['x'] == 1  # does not get overwritten

    # TODO enable these tests once we create the TCPIP_ASRL and TCPIP_GPIB IntEnum constants in MSLInterface
    # record = ConnectionRecord(address='ENET+COM::192.168.1.21+3', backend=Backend.MSL)
    # assert record.address == 'ENET+COM::192.168.1.21+3'
    # assert record.backend == Backend.MSL
    # assert record.interface == MSLInterface.TCPIP_ASRL

    # record = ConnectionRecord(address='LAN+GPIB::192.168.1.21+7', backend=Backend.MSL)
    # assert record.address == 'LAN+GPIB::192.168.1.21+7'
    # assert record.backend == Backend.MSL
    # assert record.interface == MSLInterface.TCPIP_GPIB

    #
    # The following are backend checks
    #

    # equivalent ways to define a Backend
    for backend in [Backend.MSL, 'MSL', u'MSL', 1]:
        c = ConnectionRecord(backend=backend)
        assert c.backend == Backend.MSL

    # invalid Backends
    for backend in [None, -1, -9.9, 'XXXXX']:
        with pytest.raises(ValueError) as err:
            ConnectionRecord(backend=backend)
        assert str(err.value).endswith('not a valid Backend')

    #
    # The following are "properties" checks
    #

    # the properties attribute must be a dictionary
    for props in [[], (), set(), 'xxxxxxxx', None, 1, 0j, 9.9]:
        with pytest.raises(TypeError) as err:
            ConnectionRecord(properties=props)
        assert 'dictionary' in str(err.value)

        c = ConnectionRecord(properties={'one': 1, 'two': 2})
        with pytest.raises(TypeError) as err:
            c.properties = props
        assert 'dictionary' in str(err.value)

    # unexpected kwargs get inserted into the "properties" dict
    c = ConnectionRecord(model='ABC', unknown_attribute='AAA', xxxx=7.2)
    assert c.model == 'ABC'
    assert c.properties['unknown_attribute'] == 'AAA'
    assert c.properties['xxxx'] == 7.2

    # data types do not change
    c = ConnectionRecord(properties=dict(a=1, b=True, c={'one': -1, 'two': 2.2}, d=4-9j, e='hey!', f=[0, -1]))
    assert c.properties['a'] == 1
    assert c.properties['b'] is True
    assert c.properties['c']['one'] == -1
    assert c.properties['c']['two'] == 2.2
    assert c.properties['d'] == 4-9j
    assert c.properties['e'] == 'hey!'
    assert c.properties['f'][0] == 0
    assert c.properties['f'][1] == -1

    os.remove(temp)


def test_dbase():

    path = os.path.join(os.path.dirname(__file__), 'db.xml')
    c = Config(path)

    dbase = c.database()

    eq1 = dbase.equipment['712ae']
    assert eq1.manufacturer == 'F D080'
    assert eq1.model == '712ae'
    assert eq1.serial == '49e39f1'
    assert eq1.date_calibrated.year == 2010
    assert eq1.date_calibrated.month == 11
    assert eq1.date_calibrated.day == 1
    assert eq1.category == 'DMM'
    assert eq1.location == 'General'
    assert eq1.description == 'Digital Multimeter'
    assert eq1.connection is None

    eq2 = dbase.equipment['dvm']
    assert eq2.alias == 'dvm'
    assert eq2.calibration_cycle == 5
    assert eq2.category == 'DVM'
    assert eq2.date_calibrated.year == 2009
    assert eq2.date_calibrated.month == 11
    assert eq2.date_calibrated.day == 12
    assert eq2.description == 'Digital nanovoltmeter'
    assert eq2.location == 'Watt Lab'
    assert eq2.manufacturer == 'Agilent'
    assert eq2.model == '34420A'
    assert eq2.team == 'Any'
    assert eq2.serial == 'A00024'

    c = eq2.connection
    assert c.manufacturer == 'Agilent'
    assert c.model == '34420A'
    assert c.serial == 'A00024'
    assert c.address == 'ASRL1::INSTR'
    assert c.backend == Backend.MSL
    assert c.interface == MSLInterface.SERIAL
    assert c.properties['baud_rate'] == 9600
    assert c.properties['read_termination'] == CR + LF
    assert c.properties['write_termination'] == LF

    if PY2:
        string = (str, unicode)
    else:
        string = str

    for r in dbase.records():
        for key, value in r.to_dict().items():
            if key == 'calibration_cycle':
                assert isinstance(value, float)
            elif key == 'date_calibrated':
                if value is not None:
                    assert isinstance(value, datetime.date)
            elif key == 'user_defined':
                assert isinstance(value, dict)
            elif key == 'connection':
                if isinstance(value, dict):
                    for k, v in value.items():
                        if k == 'backend':
                            assert isinstance(v, Backend)
                        elif k == 'interface':
                            assert isinstance(v, MSLInterface)
                        elif k == 'properties':
                            assert isinstance(v, dict)
                        else:
                            assert isinstance(v, string)
                else:
                    assert value is None
            else:
                assert isinstance(value, string)


def test_asrl():
    c = Config(os.path.join(os.path.dirname(__file__), 'db_asrl.xml'))

    dbase = c.database()

    pyvisa = dbase.equipment['pyvisa'].connection
    msl = dbase.equipment['msl'].connection

    assert pyvisa.address == 'COM1'
    assert msl.address == 'COM1'

    assert pyvisa.properties['baud_rate'] == 119200
    assert msl.properties['baud_rate'] == 119200

    assert pyvisa.properties['data_bits'] == DataBits.SEVEN
    assert msl.properties['data_bits'] == DataBits.SEVEN

    assert pyvisa.properties['parity'] == Parity.ODD
    assert msl.properties['parity'] == Parity.ODD

    assert pyvisa.properties['stop_bits'] == StopBits.ONE_POINT_FIVE
    assert msl.properties['stop_bits'] == StopBits.ONE_POINT_FIVE


def test_calibration_check_methods():
    today = datetime.date.today()

    record = EquipmentRecord()
    assert not record.is_calibration_due()  # the date_calibrated value has not been set

    record = EquipmentRecord(date_calibrated=today)
    assert not record.is_calibration_due()  # the calibration_cycle value has not been set

    record = EquipmentRecord(date_calibrated=today, calibration_cycle=5)
    assert not record.is_calibration_due()

    record = EquipmentRecord(date_calibrated=datetime.date(2000, 1, 1), calibration_cycle=1)
    assert record.is_calibration_due()

    record = EquipmentRecord(date_calibrated=datetime.date(2000, 1, 1), calibration_cycle=999)
    assert not record.is_calibration_due()

    date = datetime.date(today.year-1, today.month, today.day)
    record = EquipmentRecord(date_calibrated=date, calibration_cycle=1.5)
    assert not record.is_calibration_due()  # not due for another 6 months
    assert record.is_calibration_due(12)

    record = EquipmentRecord(date_calibrated=datetime.date(2000, 1, 1))
    d = record.next_calibration_date()
    assert d.year == 2000
    assert d.month == 1
    assert d.day == 1

    record = EquipmentRecord(date_calibrated=datetime.date(2000, 8, 4), calibration_cycle=1)
    d = record.next_calibration_date()
    assert d.year == 2001
    assert d.month == 8
    assert d.day == 4

    record = EquipmentRecord(date_calibrated=datetime.date(2000, 12, 30), calibration_cycle=5.0)
    d = record.next_calibration_date()
    assert d.year == 2005
    assert d.month == 12
    assert d.day == 30

    record = EquipmentRecord(date_calibrated=datetime.date(2000, 8, 4), calibration_cycle=1.5)
    d = record.next_calibration_date()
    assert d.year == 2002
    assert d.month == 2
    assert d.day == 4

    record = EquipmentRecord(date_calibrated=datetime.date(2000, 3, 14), calibration_cycle=0.7)
    d = record.next_calibration_date()
    assert d.year == 2000
    assert d.month == 11
    assert d.day == 14
