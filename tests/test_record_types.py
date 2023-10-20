# -*- coding: utf8 -*-
from __future__ import annotations

import codecs
import datetime
import json
import os
import tempfile
from xml.etree.ElementTree import ElementTree

import pytest

from msl.equipment import Backend
from msl.equipment import CalibrationRecord
from msl.equipment import ConnectionRecord
from msl.equipment import EquipmentRecord
from msl.equipment import MaintenanceRecord
from msl.equipment import MeasurandRecord
from msl.equipment.config import Config
from msl.equipment.constants import CR
from msl.equipment.constants import DataBits
from msl.equipment.constants import Interface
from msl.equipment.constants import LF
from msl.equipment.constants import Parity
from msl.equipment.constants import StopBits
from msl.equipment.record_types import RecordDict
from msl.equipment.utils import convert_to_xml_string

ROOT_DIR = os.path.join(os.path.dirname(__file__), 'db_files')


def teardown_module():
    import cleanup_os_environ
    cleanup_os_environ.cleanup()


def test_equipment_record():

    temp = os.path.join(tempfile.gettempdir(), 'msl-equipment-record.xml')

    # the default values
    record = EquipmentRecord()
    print(record)  # make sure it is printable
    print(repr(record))
    assert record.alias == ''
    assert isinstance(record.calibrations, tuple) and len(record.calibrations) == 0
    assert record.category == ''
    assert record.connection is None
    assert record.description == ''
    assert not record.is_operable
    assert isinstance(record.maintenances, tuple) and len(record.maintenances) == 0
    assert record.manufacturer == ''
    assert record.model == ''
    assert record.serial == ''
    assert record.team == ''
    assert record.unique_key == ''
    assert record.user_defined == {}
    assert record.latest_calibration is None

    a = record.to_dict()
    assert len(a) == len(record.__slots__)
    assert a['alias'] == ''
    assert isinstance(a['calibrations'], tuple) and len(a['calibrations']) == 0
    assert a['category'] == ''
    assert a['connection'] is None
    assert a['description'] == ''
    assert not a['is_operable']
    assert isinstance(a['maintenances'], tuple) and len(a['maintenances']) == 0
    assert a['manufacturer'] == ''
    assert a['model'] == ''
    assert a['serial'] == ''
    assert a['team'] == ''
    assert a['unique_key'] == ''
    assert a['user_defined'] == {}

    a = record.to_json()
    assert len(a) == len(record.__slots__)
    assert a['alias'] == ''
    assert isinstance(a['calibrations'], tuple) and len(a['calibrations']) == 0
    assert a['category'] == ''
    assert a['connection'] is None
    assert a['description'] == ''
    assert not a['is_operable']
    assert isinstance(a['maintenances'], tuple) and len(a['maintenances']) == 0
    assert a['manufacturer'] == ''
    assert a['model'] == ''
    assert a['serial'] == ''
    assert a['team'] == ''
    assert a['unique_key'] == ''
    assert a['user_defined'] == {}
    EquipmentRecord(**json.loads(json.dumps(a)))  # check that this does not raise an error

    with open(temp, mode='wt') as fp:  # no unicode, use builtin open() function
        fp.write(convert_to_xml_string(record.to_xml()))
    a = ElementTree().parse(temp)
    assert len(a) == len(record.__slots__)
    assert a.find('alias').text is None
    assert a.find('calibrations').text is None
    assert a.find('category').text is None
    assert a.find('connection').text is None
    assert a.find('description').text is None
    assert a.find('is_operable').text == 'False'
    assert a.find('maintenances').text is None
    assert a.find('manufacturer').text is None
    assert a.find('model').text is None
    assert a.find('serial').text is None
    assert a.find('team').text is None
    assert a.find('unique_key').text is None
    assert a.find('user_defined').text is None

    a = repr(record).splitlines()
    assert len(a) == len(record.__slots__) + 1
    assert a[0] == 'EquipmentRecord'
    assert a[1] == '  alias: {!r}'.format('')
    assert a[2] == '  calibrations: None'
    assert a[3] == '  category: {!r}'.format('')
    assert a[4] == '  connection: None'
    assert a[5] == '  description: {!r}'.format('')
    assert a[6] == '  is_operable: False'
    assert a[7] == '  maintenances: None'
    assert a[8] == '  manufacturer: {!r}'.format('')
    assert a[9] == '  model: {!r}'.format('')
    assert a[10] == '  serial: {!r}'.format('')
    assert a[11] == '  team: {!r}'.format('')
    assert a[12] == '  unique_key: {!r}'.format('')
    assert a[13] == '  user_defined: None'

    # populate the EquipmentRecord
    record = EquipmentRecord(
        alias='my alias',
        calibrations=[
            CalibrationRecord(
                calibration_cycle=2,
                calibration_date='2018-8-20',
                report_date='2018-8-20',
                report_number='Report:12-3/4',
                measurands=[
                    MeasurandRecord(calibration={'min': 0, 'max': 10, 'coeff': [1, 2, 3]}, type='A', unit='B'),
                    MeasurandRecord(calibration={'range': [0, 10], 'coeff': [0.2, 11]}, type='X', unit='Y'),
                ]
            ),
        ],
        category='DMM',
        connection=ConnectionRecord(
            address='GPIB::15',
            backend=Backend.PyVISA,
            manufacturer='uñicödé',
            model='XYZ',
            serial='ABC123',
            properties={
                'none': None,
                'bytes': b'\x02\x19\x08',
                'string': 'string',
                'unicode': 'uñicödé',
                'termination': '\r\n',
                'boolean': True,
                'integer': 77,
                'float': 12.34,
                'complex': -2-3j,
                'enum': StopBits.ONE_POINT_FIVE,
            },
        ),
        description='Sométhing uséful',
        is_operable=True,
        maintenances=[
            MaintenanceRecord(date='2019-01-01', comment='fixed it'),
        ],
        manufacturer='uñicödé',
        model='XYZ',
        serial='ABC123',
        team='P&R',
        unique_key='keykeykey',
        a='a',  # goes into the user_defined dict
        b=8,  # goes into the user_defined dict
        c=[1, 2, 3],  # goes into the user_defined dict
    )
    print(str(record))  # make sure it is printable
    print(str(repr(record)))
    assert record.alias == 'my alias'
    assert len(record.calibrations) == 1
    assert record.calibrations[0].calibration_cycle == 2
    assert record.calibrations[0].calibration_date == datetime.date(2018, 8, 20)
    assert record.calibrations[0].report_date == datetime.date(2018, 8, 20)
    assert record.calibrations[0].report_number == 'Report:12-3/4'
    assert len(record.calibrations[0].measurands) == 2
    assert record.calibrations[0].measurands.A.calibration.min == 0
    assert record.calibrations[0].measurands.A.calibration.max == 10
    assert record.calibrations[0].measurands.A.calibration.coeff == (1, 2, 3)
    assert record.calibrations[0].measurands.A.type == 'A'
    assert record.calibrations[0].measurands.A.unit == 'B'
    assert record.calibrations[0].measurands['X'].calibration.range == (0, 10)
    assert record.calibrations[0].measurands['X'].calibration.coeff == (0.2, 11)
    assert record.calibrations[0].measurands['X'].type == 'X'
    assert record.calibrations[0].measurands['X'].unit == 'Y'
    assert record.category == 'DMM'
    assert record.connection.address == 'GPIB::15'
    assert record.connection.backend == Backend.PyVISA
    assert record.connection.interface == Interface.NONE  # using PyVISA as the backend
    assert record.connection.manufacturer == 'uñicödé'
    assert record.connection.model == 'XYZ'
    assert record.connection.properties['none'] is None
    assert record.connection.properties['bytes'] == b'\x02\x19\x08'
    assert record.connection.properties['string'] == 'string'
    assert record.connection.properties['unicode'] == 'uñicödé'
    assert record.connection.properties['termination'] == b'\r\n'
    assert record.connection.properties['boolean'] is True
    assert record.connection.properties['integer'] == 77
    assert record.connection.properties['float'] == 12.34
    assert record.connection.properties['complex'] == -2-3j
    assert record.connection.properties['enum'] == StopBits.ONE_POINT_FIVE
    assert record.connection.serial == 'ABC123'
    assert record.description == 'Sométhing uséful'
    assert record.is_operable
    assert len(record.maintenances) == 1
    assert record.maintenances[0].date == datetime.date(2019, 1, 1)
    assert record.maintenances[0].comment == 'fixed it'
    assert record.manufacturer == 'uñicödé'
    assert record.model == 'XYZ'
    assert record.serial == 'ABC123'
    assert record.team == 'P&R'
    assert record.unique_key == 'keykeykey'
    assert record.user_defined['a'] == 'a'
    assert record.user_defined['b'] == 8
    assert record.user_defined['c'] == (1, 2, 3)
    assert record.latest_calibration is record.calibrations[0]

    a = record.to_dict()
    assert len(a) == len(record.__slots__)
    assert a['alias'] == 'my alias'
    assert len(a['calibrations']) == 1
    assert a['calibrations'][0]['calibration_cycle'] == 2
    assert a['calibrations'][0]['calibration_date'] == datetime.date(2018, 8, 20)
    assert a['calibrations'][0]['report_date'] == datetime.date(2018, 8, 20)
    assert a['calibrations'][0]['report_number'] == 'Report:12-3/4'
    assert len(a['calibrations'][0]['measurands']) == 2
    assert a['calibrations'][0]['measurands']['A'].calibration['min'] == 0
    assert a['calibrations'][0]['measurands']['A'].calibration['max'] == 10
    assert a['calibrations'][0]['measurands']['A'].calibration['coeff'] == (1, 2, 3)
    assert a['calibrations'][0]['measurands']['A'].type == 'A'
    assert a['calibrations'][0]['measurands']['A'].unit == 'B'
    assert a['calibrations'][0]['measurands']['X'].calibration['range'] == (0, 10)
    assert a['calibrations'][0]['measurands']['X'].calibration['coeff'] == (0.2, 11)
    assert a['calibrations'][0]['measurands']['X'].type == 'X'
    assert a['calibrations'][0]['measurands']['X'].unit == 'Y'
    assert a['category'] == 'DMM'
    assert a['connection']['address'] == 'GPIB::15'
    assert a['connection']['backend'] == Backend.PyVISA
    assert a['connection']['interface'] == Interface.NONE  # using PyVISA as the backend
    assert a['connection']['manufacturer'] == 'uñicödé'
    assert a['connection']['model'] == 'XYZ'
    assert a['connection']['properties']['none'] is None
    assert a['connection']['properties']['bytes'] == b'\x02\x19\x08'
    assert a['connection']['properties']['string'] == 'string'
    assert a['connection']['properties']['unicode'] == 'uñicödé'
    assert a['connection']['properties']['termination'] == b'\r\n'
    assert a['connection']['properties']['boolean'] is True
    assert a['connection']['properties']['integer'] == 77
    assert a['connection']['properties']['float'] == 12.34
    assert a['connection']['properties']['complex'] == -2-3j
    assert a['connection']['properties']['enum'] == StopBits.ONE_POINT_FIVE
    assert a['connection']['serial'] == 'ABC123'
    assert a['description'] == 'Sométhing uséful'
    assert a['is_operable']
    assert len(a['maintenances']) == 1
    assert a['maintenances'][0]['date'] == datetime.date(2019, 1, 1)
    assert a['maintenances'][0]['comment'] == 'fixed it'
    assert a['manufacturer'] == 'uñicödé'
    assert a['model'] == 'XYZ'
    assert a['serial'] == 'ABC123'
    assert a['team'] == 'P&R'
    assert a['unique_key'] == 'keykeykey'
    assert a['user_defined']['a'] == 'a'
    assert a['user_defined']['b'] == 8
    assert a['user_defined']['c'] == (1, 2, 3)

    a = record.to_json()
    assert len(a) == len(record.__slots__)
    assert a['alias'] == 'my alias'
    assert len(a['calibrations']) == 1
    assert a['calibrations'][0]['calibration_cycle'] == 2
    assert a['calibrations'][0]['calibration_date'] == '2018-08-20'
    assert a['calibrations'][0]['report_date'] == '2018-08-20'
    assert a['calibrations'][0]['report_number'] == 'Report:12-3/4'
    assert len(a['calibrations'][0]['measurands']) == 2
    assert a['calibrations'][0]['measurands'][0]['calibration']['min'] == 0
    assert a['calibrations'][0]['measurands'][0]['calibration']['max'] == 10
    assert a['calibrations'][0]['measurands'][0]['calibration']['coeff'] == (1, 2, 3)
    assert a['calibrations'][0]['measurands'][0]['type'] == 'A'
    assert a['calibrations'][0]['measurands'][0]['unit'] == 'B'
    assert a['calibrations'][0]['measurands'][1]['calibration']['range'] == (0, 10)
    assert a['calibrations'][0]['measurands'][1]['calibration']['coeff'] == (0.2, 11)
    assert a['calibrations'][0]['measurands'][1]['type'] == 'X'
    assert a['calibrations'][0]['measurands'][1]['unit'] == 'Y'
    assert a['category'] == 'DMM'
    assert a['connection']['address'] == 'GPIB::15'
    assert a['connection']['backend'] == 'PyVISA'
    assert a['connection']['interface'] == 'NONE'  # using PyVISA as the backend
    assert a['connection']['manufacturer'] == 'uñicödé'
    assert a['connection']['model'] == 'XYZ'
    assert a['connection']['properties']['none'] is None
    assert a['connection']['properties']['bytes'] == "b'\\x02\\x19\\x08'"
    assert a['connection']['properties']['string'] == 'string'
    assert a['connection']['properties']['unicode'] == 'uñicödé'
    assert a['connection']['properties']['termination'] == "b'\\r\\n'"
    assert a['connection']['properties']['boolean'] is True
    assert a['connection']['properties']['integer'] == 77
    assert a['connection']['properties']['float'] == 12.34
    assert a['connection']['properties']['complex'] == '(-2-3j)'
    assert a['connection']['properties']['enum'] == 'ONE_POINT_FIVE'
    assert a['connection']['serial'] == 'ABC123'
    assert a['description'] == 'Sométhing uséful'
    assert a['is_operable']
    assert len(a['maintenances']) == 1
    assert a['maintenances'][0]['date'] == '2019-01-01'
    assert a['maintenances'][0]['comment'] == 'fixed it'
    assert a['manufacturer'] == 'uñicödé'
    assert a['model'] == 'XYZ'
    assert a['serial'] == 'ABC123'
    assert a['team'] == 'P&R'
    assert a['unique_key'] == 'keykeykey'
    assert a['user_defined']['a'] == 'a'
    assert a['user_defined']['b'] == 8
    assert a['user_defined']['c'] == (1, 2, 3)
    json_record = EquipmentRecord(**json.loads(json.dumps(a)))

    with codecs.open(temp, mode='w', encoding='utf-8') as fp:  # has unicode, use codecs.open() function
        fp.write(convert_to_xml_string(record.to_xml()))
    a = ElementTree().parse(temp)
    assert len(a) == len(record.__slots__)
    assert a.find('alias').text == 'my alias'
    assert len(a.find('calibrations')) == 1
    assert a.find('calibrations/CalibrationRecord/calibration_cycle').text == '2.0'
    assert a.find('calibrations/CalibrationRecord/calibration_date').text == '2018-08-20'
    assert a.find('calibrations/CalibrationRecord/calibration_date').attrib['format'] == 'YYYY-MM-DD'
    assert a.find('calibrations/CalibrationRecord/report_date').text == '2018-08-20'
    assert a.find('calibrations/CalibrationRecord/report_date').attrib['format'] == 'YYYY-MM-DD'
    assert a.find('calibrations/CalibrationRecord/report_number').text == 'Report:12-3/4'
    measurands = a.find('calibrations/CalibrationRecord/measurands')
    assert len(measurands) == 2
    ta = measurands.find('./MeasurandRecord[type="A"]')
    assert ta.find('calibration/max').text == '10'
    assert ta.find('calibration/min').text == '0'
    assert ta.find('calibration/max').text == '10'
    assert ta.find('calibration/coeff').text == '(1, 2, 3)'
    assert ta.find('conditions').text is None
    assert ta.find('type').text == 'A'
    assert ta.find('unit').text == 'B'
    tx = measurands.find('./MeasurandRecord[type="X"]')
    assert tx.find('calibration/range').text == '(0, 10)'
    assert tx.find('calibration/coeff').text == '(0.2, 11)'
    assert tx.find('type').text == 'X'
    assert tx.find('unit').text == 'Y'
    assert a.find('category').text == 'DMM'
    assert a.find('connection/ConnectionRecord/address').text == 'GPIB::15'
    assert a.find('connection/ConnectionRecord/backend').text == 'PyVISA'
    assert a.find('connection/ConnectionRecord/interface').text == 'NONE'  # using PyVISA as the backend
    assert a.find('connection/ConnectionRecord/manufacturer').text == 'uñicödé'
    assert a.find('connection/ConnectionRecord/model').text == 'XYZ'
    assert len(a.find('connection/ConnectionRecord/properties').text.strip()) == 0
    assert a.find('connection/ConnectionRecord/properties/none').text == 'None'
    assert a.find('connection/ConnectionRecord/properties/bytes').text == "b'\\x02\\x19\\x08'"
    assert a.find('connection/ConnectionRecord/properties/string').text == 'string'
    assert a.find('connection/ConnectionRecord/properties/unicode').text == 'uñicödé'
    assert a.find('connection/ConnectionRecord/properties/termination').text == "b'\\r\\n'"
    assert a.find('connection/ConnectionRecord/properties/boolean').text == 'True'
    assert a.find('connection/ConnectionRecord/properties/integer').text == '77'
    assert a.find('connection/ConnectionRecord/properties/float').text == '12.34'
    assert a.find('connection/ConnectionRecord/properties/complex').text == '(-2-3j)'
    assert a.find('connection/ConnectionRecord/properties/enum').text == 'ONE_POINT_FIVE'
    assert a.find('connection/ConnectionRecord/serial').text == 'ABC123'
    assert a.find('description').text == 'Sométhing uséful'
    assert a.find('is_operable').text == 'True'
    assert len(a.find('maintenances')) == 1
    assert a.find('maintenances/MaintenanceRecord/date').text == '2019-01-01'
    assert a.find('maintenances/MaintenanceRecord/comment').text == 'fixed it'
    assert a.find('manufacturer').text == 'uñicödé'
    assert a.find('model').text == 'XYZ'
    assert a.find('serial').text == 'ABC123'
    assert a.find('team').text == 'P&R'
    assert a.find('unique_key').text == 'keykeykey'
    assert len(a.find('user_defined').text.strip()) == 0
    assert a.find('user_defined/a').text == 'a'
    assert a.find('user_defined/b').text == '8'
    assert a.find('user_defined/c').text == '(1, 2, 3)'

    # The JSON-dumps-loads process should return the same EquipmentRecord object
    for rec in [record, json_record]:
        print(str(rec))  # make sure it is printable
        print(str(repr(rec)))
        assert rec.alias == 'my alias'
        assert len(rec.calibrations) == 1
        assert rec.calibrations[0].calibration_cycle == 2
        assert rec.calibrations[0].calibration_date == datetime.date(2018, 8, 20)
        assert rec.calibrations[0].report_date == datetime.date(2018, 8, 20)
        assert rec.calibrations[0].report_number == 'Report:12-3/4'
        assert len(rec.calibrations[0].measurands) == 2
        assert rec.calibrations[0].measurands.A.calibration.min == 0
        assert rec.calibrations[0].measurands.A.calibration.max == 10
        assert rec.calibrations[0].measurands.A.calibration.coeff == (1, 2, 3)
        assert rec.calibrations[0].measurands.A.type == 'A'
        assert rec.calibrations[0].measurands.A.unit == 'B'
        assert rec.calibrations[0].measurands['X'].calibration.range == (0, 10)
        assert rec.calibrations[0].measurands['X'].calibration.coeff == (0.2, 11)
        assert rec.calibrations[0].measurands['X'].type == 'X'
        assert rec.calibrations[0].measurands['X'].unit == 'Y'
        assert rec.category == 'DMM'
        assert rec.connection.address == 'GPIB::15'
        assert rec.connection.backend == Backend.PyVISA
        assert rec.connection.interface == Interface.NONE  # using PyVISA as the backend
        assert rec.connection.manufacturer == 'uñicödé'
        assert rec.connection.model == 'XYZ'
        assert rec.connection.properties['none'] is None
        if rec is json_record:
            assert rec.connection.properties['bytes'] == "b'\\x02\\x19\\x08'"
        else:
            assert rec.connection.properties['bytes'] == b'\x02\x19\x08'
        assert rec.connection.properties['string'] == 'string'
        assert rec.connection.properties['termination'] == b'\r\n'
        assert rec.connection.properties['unicode'] == 'uñicödé'
        assert rec.connection.properties['boolean'] is True
        assert rec.connection.properties['integer'] == 77
        assert rec.connection.properties['float'] == 12.34
        if rec is json_record:
            assert rec.connection.properties['complex'] == '(-2-3j)'
            # the 'enum' value is a string because there is no reason for this value
            # to be associated with a StopBits enum. A ConnectionRecord looks for a key
            # that starts with 'stop' to convert the value to a StopBits enum
            assert rec.connection.properties['enum'] == 'ONE_POINT_FIVE'
        else:
            assert rec.connection.properties['complex'] == -2 - 3j
            assert rec.connection.properties['enum'] == StopBits.ONE_POINT_FIVE
        assert rec.connection.serial == 'ABC123'
        assert rec.description == 'Sométhing uséful'
        assert rec.is_operable
        assert len(rec.maintenances) == 1
        assert rec.maintenances[0].date == datetime.date(2019, 1, 1)
        assert rec.maintenances[0].comment == 'fixed it'
        assert rec.manufacturer == 'uñicödé'
        assert rec.model == 'XYZ'
        assert rec.serial == 'ABC123'
        assert rec.team == 'P&R'
        assert rec.unique_key == 'keykeykey'
        assert rec.user_defined['a'] == 'a'
        assert rec.user_defined['b'] == 8
        assert rec.user_defined['c'] == (1, 2, 3)
        assert rec.latest_calibration is rec.calibrations[0]

    a = repr(record).splitlines()
    assert len(a) == 59
    assert a[0] == 'EquipmentRecord'
    assert a[1] == "  alias: 'my alias'"
    assert a[2] == '  calibrations: '
    assert a[3] == '    CalibrationRecord'
    assert a[4] == '      calibration_cycle: 2.0'
    assert a[5] == '      calibration_date: 2018-08-20'
    assert a[6] == '      measurands: '
    assert a[7] == '        MeasurandRecord'
    assert a[8] == '          calibration: '
    assert a[9] == '            coeff: (1, 2, 3)'
    assert a[10] == '            max: 10'
    assert a[11] == '            min: 0'
    assert a[12] == '          conditions: None'
    assert a[13] == '          type: {}'.format("'A'")
    assert a[14] == '          unit: {}'.format("'B'")
    assert a[15] == '        MeasurandRecord'
    assert a[16] == '          calibration: '
    assert a[17] == '            coeff: (0.2, 11)'
    assert a[18] == '            range: (0, 10)'
    assert a[19] == '          conditions: None'
    assert a[20] == '          type: {}'.format("'X'")
    assert a[21] == '          unit: {}'.format("'Y'")
    assert a[22] == '      report_date: 2018-08-20'
    assert a[23] == '      report_number: {}'.format("'Report:12-3/4'")
    assert a[24] == '  category: {}'.format("'DMM'")
    assert a[25] == '  connection: '
    assert a[26] == '    ConnectionRecord'
    assert a[27] == '      address: {}'.format("'GPIB::15'")
    assert a[28] == '      backend: <Backend.PyVISA: 2>'
    assert a[29] == '      interface: <Interface.NONE: 0>'
    assert a[30] == '      manufacturer: {}'.format("'uñicödé'")
    assert a[31] == '      model: {}'.format("'XYZ'")
    assert a[32] == '      properties: '
    assert a[33] == '        boolean: True'
    assert a[34] == '        bytes: {}'.format("b'\\x02\\x19\\x08'")
    assert a[35] == '        complex: (-2-3j)'
    assert a[36] == '        enum: <StopBits.ONE_POINT_FIVE: 1.5>'
    assert a[37] == '        float: 12.34'
    assert a[38] == '        integer: 77'
    assert a[39] == '        none: None'
    assert a[40] == "        string: 'string'"
    assert a[41] == '        termination: {}'.format("b'\\r\\n'")
    assert a[42] == '        unicode: {}'.format("'uñicödé'")
    assert a[43] == '      serial: {}'.format("'ABC123'")
    assert a[44] == '  description: {}'.format("'Sométhing uséful'")
    assert a[45] == '  is_operable: True'
    assert a[46] == '  maintenances: '
    assert a[47] == '    MaintenanceRecord'
    assert a[48] == '      comment: {}'.format("'fixed it'")
    assert a[49] == '      date: 2019-01-01'
    assert a[50] == '  manufacturer: {}'.format("'uñicödé'")
    assert a[51] == '  model: {}'.format("'XYZ'")
    assert a[52] == '  serial: {}'.format("'ABC123'")
    assert a[53] == '  team: {}'.format("'P&R'")
    assert a[54] == '  unique_key: {}'.format("'keykeykey'")
    assert a[55] == '  user_defined: '
    assert a[56] == "    a: 'a'"
    assert a[57] == '    b: 8'
    assert a[58] == '    c: (1, 2, 3)'

    #
    # The `alias` can be redefined
    #
    assert record.alias != 'my new alias'
    record.alias = 'my new alias'
    assert record.alias == 'my new alias'

    #
    # Check that the `calibrations` attribute cannot be modified
    #
    with pytest.raises(TypeError):
        record.calibrations = None
    with pytest.raises(TypeError):
        setattr(record, 'calibrations', None)
    with pytest.raises(TypeError):
        record.calibrations[0] = None

    #
    # Check that the `category` attribute cannot be modified
    #
    with pytest.raises(TypeError):
        record.category = None
    with pytest.raises(TypeError):
        setattr(record, 'category', None)

    #
    # Check that the `connection` attribute cannot be modified
    #
    with pytest.raises(TypeError):
        record.connection = None
    with pytest.raises(TypeError):
        setattr(record, 'connection', None)

    #
    # Check that the `description` attribute cannot be modified
    #
    with pytest.raises(TypeError):
        record.description = None
    with pytest.raises(TypeError):
        setattr(record, 'description', None)

    #
    # Check that the `is_operable` attribute cannot be modified
    #
    with pytest.raises(TypeError):
        record.is_operable = None
    with pytest.raises(TypeError):
        setattr(record, 'is_operable', None)

    #
    # Check that the `maintenances` attribute cannot be modified
    #
    with pytest.raises(TypeError):
        record.maintenances = None
    with pytest.raises(TypeError):
        setattr(record, 'maintenances', None)
    with pytest.raises(TypeError):
        record.maintenances[0] = None

    #
    # Check that the `manufacturer` attribute cannot be modified
    #
    with pytest.raises(TypeError):
        record.manufacturer = None
    with pytest.raises(TypeError):
        setattr(record, 'manufacturer', None)

    #
    # Check that the `model` attribute cannot be modified
    #
    with pytest.raises(TypeError):
        record.model = None
    with pytest.raises(TypeError):
        setattr(record, 'model', None)

    #
    # Check that the `serial` attribute cannot be modified
    #
    with pytest.raises(TypeError):
        record.serial = None
    with pytest.raises(TypeError):
        setattr(record, 'serial', None)

    #
    # Check that the `team` attribute cannot be modified
    #
    with pytest.raises(TypeError):
        record.team = None
    with pytest.raises(TypeError):
        setattr(record, 'team', None)

    #
    # Check that the `unique_key` attribute cannot be modified
    #
    with pytest.raises(TypeError):
        record.unique_key = None
    with pytest.raises(TypeError):
        setattr(record, 'unique_key', None)

    #
    # Check that the `user_defined` attribute cannot be modified
    #
    with pytest.raises(TypeError):
        record.user_defined = None
    with pytest.raises(TypeError):
        setattr(record, 'user_defined', None)
    with pytest.raises(TypeError):
        record.user_defined['new key'] = 'new value'
    with pytest.raises(TypeError):
        record.user_defined['a'] = 88

    #
    # Check setting invalid `calibrations`
    #
    with pytest.raises(TypeError, match=r"'int' object is not iterable"):
        EquipmentRecord(calibrations=0)
    with pytest.raises(TypeError):  # not a iterable of CalibrationRecord
        EquipmentRecord(calibrations=[1])
    with pytest.raises(TypeError):  # not a iterable of CalibrationRecord
        EquipmentRecord(calibrations=(None,))
    with pytest.raises(KeyError):  # KeyError: 'measurands'
        EquipmentRecord(calibrations=[{'calibration_cycle': 7}])
    with pytest.raises(TypeError, match=r"unexpected keyword argument 'invalid_kwarg'"):
        EquipmentRecord(calibrations=[{'invalid_kwarg': 7, 'measurands': []}])

    #
    # Check setting invalid `maintenances`
    #
    with pytest.raises(TypeError, match=r"'int' object is not iterable"):
        EquipmentRecord(maintenances=0)
    with pytest.raises(TypeError):  # not an iterable of MaintenanceRecord
        EquipmentRecord(maintenances=[1])
    with pytest.raises(TypeError):  # not an iterable of MaintenanceRecord
        EquipmentRecord(maintenances=(None,))
    with pytest.raises(TypeError, match=r"unexpected keyword argument 'invalid_kwarg'"):
        EquipmentRecord(maintenances=[{'invalid_kwarg': 7}])

    #
    # Check setting the ConnectionRecord
    #

    for item in [1, 6j, 'hello', True, object, 7.7, b'\x00']:
        with pytest.raises(TypeError):
            EquipmentRecord(connection=item)

    # no exception is raised since the manufacturer, model and serial values all match
    cr = ConnectionRecord(manufacturer='ABC def', model='ZZZ', serial='DY135/055')
    EquipmentRecord(manufacturer='ABC def', model='ZZZ', serial='DY135/055', connection=cr)

    # one of the manufacturer, model or serial values do not match
    with pytest.raises(ValueError, match='.manufacturer'):
        cr = ConnectionRecord(manufacturer='XYZ')
        EquipmentRecord(manufacturer='ABC def', model='ZZZ', serial='DY135/055', connection=cr)
    with pytest.raises(ValueError, match='.model'):
        cr = ConnectionRecord(manufacturer='ABC def', model='AAA')
        EquipmentRecord(manufacturer='ABC def', model='ZZZ', serial='DY135/055', connection=cr)
    with pytest.raises(ValueError, match='.serial'):
        cr = ConnectionRecord(manufacturer='ABC def', model='ZZZ', serial='AAA')
        EquipmentRecord(manufacturer='ABC def', model='ZZZ', serial='DY135/055', connection=cr)

    # check that the manufacturer, model and serial values for the ConnectionRecord get updated
    record = EquipmentRecord(manufacturer='Company', model='ABC', serial='XYZ', connection=ConnectionRecord())
    assert record.connection.manufacturer == 'Company'
    assert record.connection.model == 'ABC'
    assert record.connection.serial == 'XYZ'

    #
    # Specifying a kwarg that is not expected goes into the user_defined dictionary
    #
    record = EquipmentRecord(unknown_attribute='AAA', dictionary={'a': 1, 'b': 2})
    assert record.user_defined['unknown_attribute'] == 'AAA'
    assert record.user_defined['dictionary'] == dict(a=1, b=2)

    record = EquipmentRecord(user_defined={'x': 1, 'y': 2, 'z': 3}, unknown_attribute='AAA', dictionary={'a': 1, 'b': 2})
    assert record.user_defined['x'] == 1
    assert record.user_defined['y'] == 2
    assert record.user_defined['z'] == 3
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
    assert record.backend == Backend.MSL
    assert record.interface == Interface.NONE
    assert record.manufacturer == ''
    assert record.model == ''
    assert record.properties == {}
    assert record.serial == ''

    a = record.to_dict()
    assert len(a) == 7
    assert a['address'] == ''
    assert a['backend'] == Backend.MSL
    assert a['interface'] == Interface.NONE
    assert a['manufacturer'] == ''
    assert a['model'] == ''
    assert a['properties'] == {}
    assert a['serial'] == ''

    a = record.to_json()
    assert len(a) == 7
    assert a['address'] == ''
    assert a['backend'] == 'MSL'
    assert a['interface'] == 'NONE'
    assert a['manufacturer'] == ''
    assert a['model'] == ''
    assert a['properties'] == {}
    assert a['serial'] == ''
    ConnectionRecord(**json.loads(json.dumps(a)))  # check that this does not raise an error

    with open(temp, mode='wt') as fp:  # no unicode, use builtin open() function
        fp.write(convert_to_xml_string(record.to_xml()))
    a = ElementTree().parse(temp)
    assert len(a) == 7
    assert a.find('address').text is None
    assert a.find('backend').text == 'MSL'
    assert a.find('interface').text == 'NONE'
    assert a.find('manufacturer').text is None
    assert a.find('model').text is None
    assert a.find('properties').text is None
    assert a.find('serial').text is None

    a = repr(ConnectionRecord()).splitlines()
    assert len(a) == 8
    assert a[0] == 'ConnectionRecord'
    assert a[1] == '  address: {!r}'.format('')
    assert a[2] == '  backend: <Backend.MSL: 1>'
    assert a[3] == '  interface: <Interface.NONE: 0>'
    assert a[4] == '  manufacturer: {!r}'.format('')
    assert a[5] == '  model: {!r}'.format('')
    assert a[6] == '  properties: None'
    assert a[7] == '  serial: {!r}'.format('')

    # create a new ConnectionRecord
    record = ConnectionRecord(
        address='GPIB::15',
        backend=Backend.PyVISA,
        manufacturer='uñicödé',
        model='XYZ',
        serial='ABC123',
        properties={
            'none': None,
            'bytes': b'\x02\x19\x08',
            'string': 'string',
            'unicode': 'uñicödé',
            'termination': '\r\n',
            'boolean': True,
            'integer': 77,
            'float': 12.34,
            'complex': -2-3j,
            'enum': StopBits.ONE_POINT_FIVE,
        },
    )
    print(str(record))  # make sure it is printable
    print(str(repr(record)))
    assert record.address == 'GPIB::15'
    assert record.backend == Backend.PyVISA
    assert record.interface == Interface.NONE  # using PyVISA as the backend
    assert record.manufacturer == 'uñicödé'
    assert record.model == 'XYZ'
    assert record.properties['none'] is None
    assert record.properties['bytes'] == b'\x02\x19\x08'
    assert record.properties['string'] == 'string'
    assert record.properties['unicode'] == 'uñicödé'
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
    assert a['interface'] == Interface.NONE  # using PyVISA as the backend
    assert a['manufacturer'] == 'uñicödé'
    assert a['model'] == 'XYZ'
    assert a['properties']['none'] is None
    assert a['properties']['bytes'] == b'\x02\x19\x08'
    assert a['properties']['string'] == 'string'
    assert a['properties']['unicode'] == 'uñicödé'
    assert a['properties']['termination'] == b'\r\n'
    assert a['properties']['boolean'] is True
    assert a['properties']['integer'] == 77
    assert a['properties']['float'] == 12.34
    assert a['properties']['complex'] == -2-3j
    assert a['properties']['enum'] == StopBits.ONE_POINT_FIVE
    assert a['serial'] == 'ABC123'

    a = record.to_json()
    assert len(a) == 7
    assert a['address'] == 'GPIB::15'
    assert a['backend'] == 'PyVISA'
    assert a['interface'] == 'NONE'  # using PyVISA as the backend
    assert a['manufacturer'] == 'uñicödé'
    assert a['model'] == 'XYZ'
    assert a['properties']['none'] is None
    assert a['properties']['bytes'] == "b'\\x02\\x19\\x08'"
    assert a['properties']['string'] == 'string'
    assert a['properties']['unicode'] == 'uñicödé'
    assert a['properties']['termination'] == "b'\\r\\n'"
    assert a['properties']['boolean'] is True
    assert a['properties']['integer'] == 77
    assert a['properties']['float'] == 12.34
    assert a['properties']['complex'] == '(-2-3j)'
    assert a['properties']['enum'] == 'ONE_POINT_FIVE'
    assert a['serial'] == 'ABC123'
    json_record = ConnectionRecord(**json.loads(json.dumps(a)))  # check that this does not raise an error

    with codecs.open(temp, mode='w', encoding='utf-8') as fp:  # has unicode, use codecs.open() function
        fp.write(convert_to_xml_string(record.to_xml()))
    a = ElementTree().parse(temp)
    assert len(a) == 7
    assert a.find('address').text == 'GPIB::15'
    assert a.find('backend').text == 'PyVISA'
    assert a.find('interface').text == 'NONE'
    assert a.find('manufacturer').text == 'uñicödé'
    assert a.find('model').text == 'XYZ'
    props = a.find('properties')
    assert props.find('none').text == 'None'
    assert props.find('bytes').text == "b'\\x02\\x19\\x08'"
    assert props.find('string').text == 'string'
    assert props.find('unicode').text == 'uñicödé'
    assert props.find('termination').text == "b'\\r\\n'"
    assert props.find('boolean').text == 'True'
    assert props.find('integer').text == '77'
    assert props.find('float').text == '12.34'
    assert props.find('complex').text == '(-2-3j)'
    assert props.find('enum').text == 'ONE_POINT_FIVE'
    assert a.find('serial').text == 'ABC123'

    for rec in [record, json_record]:
        print(str(rec))  # make sure it is printable
        print(str(repr(rec)))
        assert rec.address == 'GPIB::15'
        assert rec.backend == Backend.PyVISA
        assert rec.interface == Interface.NONE  # using PyVISA as the backend
        assert rec.manufacturer == 'uñicödé'
        assert rec.model == 'XYZ'
        assert rec.properties['none'] is None
        if rec is json_record:
            assert rec.properties['bytes'] == "b'\\x02\\x19\\x08'"
        else:
            assert rec.properties['bytes'] == b'\x02\x19\x08'
        if rec is json_record:
            assert rec.properties['enum'] == 'ONE_POINT_FIVE'
            assert rec.properties['complex'] == '(-2-3j)'
        else:
            assert rec.properties['enum'] == StopBits.ONE_POINT_FIVE
            assert rec.properties['complex'] == -2 - 3j
        assert rec.properties['string'] == 'string'
        assert rec.properties['unicode'] == 'uñicödé'
        assert rec.properties['termination'] == b'\r\n'
        assert rec.properties['boolean'] is True
        assert rec.properties['integer'] == 77
        assert rec.properties['float'] == 12.34
        assert rec.serial == 'ABC123'

    a = repr(record).splitlines()
    assert len(a) == 18
    assert a[0] == 'ConnectionRecord'
    assert a[1] == '  address: {}'.format("'GPIB::15'")
    assert a[2] == '  backend: <Backend.PyVISA: 2>'
    assert a[3] == '  interface: <Interface.NONE: 0>'
    assert a[4] == '  manufacturer: {}'.format("'uñicödé'")
    assert a[5] == '  model: {}'.format("'XYZ'")
    assert a[6] == '  properties: '
    assert a[7] == '    boolean: True'
    assert a[8] == '    bytes: {}'.format("b'\\x02\\x19\\x08'")
    assert a[9] == '    complex: (-2-3j)'
    assert a[10] == '    enum: <StopBits.ONE_POINT_FIVE: 1.5>'
    assert a[11] == '    float: 12.34'
    assert a[12] == '    integer: 77'
    assert a[13] == '    none: None'
    assert a[14] == "    string: 'string'"
    assert a[15] == '    termination: {}'.format("b'\\r\\n'")
    assert a[16] == '    unicode: {}'.format("'uñicödé'")
    assert a[17] == '  serial: {}'.format("'ABC123'")

    os.remove(temp)


def test_connection_record_interface():

    # an invalid `address` does not raise an exception because the backend is not MSL
    c = ConnectionRecord(address='XXXXXX', backend='UNKNOWN')
    assert c.interface == Interface.NONE

    # invalid `address` using the MSL Backend -> cannot determine the Interface
    with pytest.raises(ValueError, match='Cannot determine the Interface'):
        ConnectionRecord(address='XXXXXX')

    # if the user specifies the interface then this interface is used regardless of the value of address
    for interface in [Interface.SDK, 'SDK', 'SDK', 'sDk', 1]:
        c = ConnectionRecord(address='XXXXXX', interface=interface)
        assert c.interface == Interface.SDK
    for interface in [Interface.SOCKET, 'SOCKET', 'SOCKET', 'soCKet', 3]:
        c = ConnectionRecord(address='XXXXXX', interface=interface)
        assert c.interface == Interface.SOCKET

    # setting the interface to something that cannot be converted to an Interface
    for interface in [-1, -9.9, 'XXXXX']:
        with pytest.raises(ValueError, match='Cannot create'):
            ConnectionRecord(address='COM1', interface=interface)

    # Interface.SDK
    record = ConnectionRecord(address='SDK::file.dll')
    assert record.interface == Interface.SDK

    record = ConnectionRecord(address='SDK::/path/to/file.so')
    assert record.interface == Interface.SDK

    record = ConnectionRecord(address='SDK::C:\\path\\to\\file.dll')
    assert record.interface == Interface.SDK

    record = ConnectionRecord(address=r'SDK::C:\path\to\file.dll')
    assert record.interface == Interface.SDK

    # Interface.SERIAL
    record = ConnectionRecord(address='COM4')
    assert record.interface == Interface.SERIAL

    record = ConnectionRecord(address='ASRLCOM4')
    assert record.interface == Interface.SERIAL   # ASRLCOM is used by PyVISA

    record = ConnectionRecord(address='ASRL4')
    assert record.interface == Interface.SERIAL  # ASRL is an alias

    record = ConnectionRecord(address='ASRL4::INSTR')
    assert record.interface == Interface.SERIAL

    record = ConnectionRecord(address='ASRL/dev/ttyS1')
    assert record.interface == Interface.SERIAL

    record = ConnectionRecord(address='ASRL/dev/ttyUSB0::INSTR')
    assert record.interface == Interface.SERIAL

    # Interface.SOCKET
    record = ConnectionRecord(address='SOCKET::127.0.0.1::1234')
    assert record.interface == Interface.SOCKET

    record = ConnectionRecord(address='TCPIP::127.0.0.1::1234::SOCKET')
    assert record.interface == Interface.SOCKET  # PyVISA naming scheme

    record = ConnectionRecord(address='TCPIP0::127.0.0.1::1234::SOCKET')
    assert record.interface == Interface.SOCKET  # PyVISA naming scheme

    record = ConnectionRecord(address='TCP::127.0.0.1::1234')
    assert record.interface == Interface.SOCKET  # TCP is an alias for SOCKET

    record = ConnectionRecord(address='UDP::127.0.0.1::1234', properties=dict(x=1))
    assert record.interface == Interface.SOCKET  # UDP is an alias for SOCKET
    assert record.properties['socket_type'] == 'SOCK_DGRAM'  # gets set automatically
    assert record.properties['x'] == 1  # does not get overwritten

    # Interface.PROLOGIX
    record = ConnectionRecord(address='Prologix::192.168.1.110::1234::6')
    assert record.interface == Interface.PROLOGIX

    record = ConnectionRecord(address='Prologix::domain.name::1234::6')
    assert record.interface == Interface.PROLOGIX

    record = ConnectionRecord(address='PROLOGIX::/dev/ttyS0::16::100')
    assert record.interface == Interface.PROLOGIX

    record = ConnectionRecord(address='Prologix::COM4::1')
    assert record.interface == Interface.PROLOGIX

    record = ConnectionRecord(address='Prologix::ASRL4::1')
    assert record.interface == Interface.PROLOGIX

    record = ConnectionRecord(address='Prologix::ASRLCOM4::1')
    assert record.interface == Interface.PROLOGIX


def test_connection_record_backend():

    # equivalent ways to define a Backend
    for backend in [Backend.MSL, 'MSL', 1]:
        c = ConnectionRecord(backend=backend)
        assert c.backend == Backend.MSL

    # invalid Backends
    for backend in [None, -1, -9.9, 'XXXXX']:
        with pytest.raises(ValueError, match='Cannot create'):
            ConnectionRecord(backend=backend)


def test_connection_record_properties():

    # unexpected kwargs get inserted into the "properties" dict
    c = ConnectionRecord(model='ABC', unknown_attribute='AAA', xxxx=7.2)
    assert c.model == 'ABC'
    assert c.properties['unknown_attribute'] == 'AAA'
    assert c.properties['xxxx'] == 7.2

    # define the properties explicitly
    c = ConnectionRecord(properties=dict(a=1, b=True, c={'one': -1, 'two': 2.2}, d=4-9j, e='hey!', f=[0, -1]))
    assert c.properties['a'] == 1
    assert c.properties['b'] is True
    assert c.properties['c']['one'] == -1
    assert c.properties['c']['two'] == 2.2
    assert c.properties['d'] == 4-9j
    assert c.properties['e'] == 'hey!'
    assert c.properties['f'][0] == 0
    assert c.properties['f'][1] == -1

    # define the properties explicitly with additional kwargs
    c = ConnectionRecord(properties={'one': 1, 'two': 2}, three=3, four=4)
    assert c.properties['one'] == 1
    assert c.properties['two'] == 2
    assert c.properties['three'] == 3
    assert c.properties['four'] == 4

    with pytest.raises(TypeError, match='must be of type dict'):
        ConnectionRecord(properties=1, three=3, four=4)

    # bool(properties) evaluates to False so the 'properties' automatically get
    # converted to an empty dict and 'three' and 'four' are added to the dict
    for item in ['', None, False, []]:
        c = ConnectionRecord(properties=item, three=3, four=4)
        assert c.properties['three'] == 3
        assert c.properties['four'] == 4

    # setting the read/write termination value to None is okay
    c = ConnectionRecord(address='COM1', properties={'termination': None})
    assert c.properties['termination'] is None

    # different ways to define Serial key-values pairs
    c = ConnectionRecord(address='COM1', data_bits=6, parity='EvEn', stop_bits=1.5)
    assert c.properties['data_bits'].name == 'SIX'
    assert c.properties['data_bits'].value == DataBits.SIX.value
    assert c.properties['data_bits'] == DataBits.SIX
    assert c.properties['parity'].name == 'EVEN'
    assert c.properties['parity'].value == Parity.EVEN.value
    assert c.properties['parity'] == Parity.EVEN
    assert c.properties['stop_bits'].name == 'ONE_POINT_FIVE'
    assert c.properties['stop_bits'].value == StopBits.ONE_POINT_FIVE.value
    assert c.properties['stop_bits'] == StopBits.ONE_POINT_FIVE

    c = ConnectionRecord(address='COM1', data_bits=DataBits.SEVEN, parity=Parity.ODD, stop_bits=StopBits.ONE)
    assert c.properties['data_bits'].name == 'SEVEN'
    assert c.properties['data_bits'].value == DataBits.SEVEN.value
    assert c.properties['data_bits'] == DataBits.SEVEN
    assert c.properties['parity'].name == 'ODD'
    assert c.properties['parity'].value == Parity.ODD.value
    assert c.properties['parity'] == Parity.ODD
    assert c.properties['stop_bits'].name == 'ONE'
    assert c.properties['stop_bits'].value == StopBits.ONE.value
    assert c.properties['stop_bits'] == StopBits.ONE

    # use PySerial kwargs (bytesize, stopbits) and use :data:`None` for parity
    c = ConnectionRecord(address='COM1', bytesize=8, parity=None, stopbits=StopBits.TWO)
    assert c.properties['bytesize'].name == 'EIGHT'
    assert c.properties['bytesize'].value == DataBits.EIGHT.value
    assert c.properties['bytesize'] == DataBits.EIGHT
    assert c.properties['parity'].name == 'NONE'
    assert c.properties['parity'].value == Parity.NONE.value
    assert c.properties['parity'] == Parity.NONE
    assert c.properties['stopbits'].name == 'TWO'
    assert c.properties['stopbits'].value == StopBits.TWO.value
    assert c.properties['stopbits'] == StopBits.TWO


def test_dbase():

    path = os.path.join(ROOT_DIR, 'db.xml')
    c = Config(path)

    dbase = c.database()

    eq1 = dbase.equipment['712ae']
    assert eq1.manufacturer == 'F D080'
    assert eq1.model == '712ae'
    assert eq1.serial == '49e39f1'
    assert eq1.category == 'DMM'
    assert eq1.description == 'Digital Multimeter'
    assert eq1.connection is None

    eq2 = dbase.equipment['dvm']
    assert eq2.alias == 'dvm'
    assert eq2.category == 'DVM'
    assert eq2.description == 'Digital nanovoltmeter'
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
    assert c.interface == Interface.SERIAL
    assert c.properties['baud_rate'] == 9600
    assert c.properties['read_termination'] == CR + LF
    assert c.properties['write_termination'] == LF

    for r in dbase.records():
        for key, value in r.to_dict().items():
            if key == 'user_defined':
                assert isinstance(value, RecordDict)
            elif key == 'connection':
                if isinstance(value, dict):
                    for k, v in value.items():
                        if k == 'backend':
                            assert isinstance(v, Backend)
                        elif k == 'interface':
                            assert isinstance(v, Interface)
                        elif k == 'properties':
                            assert isinstance(v, dict)
                        else:
                            assert isinstance(v, str)
                else:
                    assert value is None
            elif key == 'calibrations' or key == 'maintenances':
                assert isinstance(value, tuple)
            elif key == 'is_operable':
                assert isinstance(value, bool)
            else:
                assert isinstance(value, str)


def test_asrl():
    c = Config(os.path.join(ROOT_DIR, 'db_asrl.xml'))

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


def test_is_calibration_due():
    today = datetime.date.today()

    record = EquipmentRecord(is_operable=True)
    assert not record.is_calibration_due()

    record = EquipmentRecord(is_operable=True, calibrations=[CalibrationRecord()])
    assert not record.is_calibration_due()  # the calibration_cycle value has not been set

    record = EquipmentRecord(
        is_operable=True,
        calibrations=[CalibrationRecord(calibration_date=today, calibration_cycle=5)]
    )
    assert not record.is_calibration_due()

    record = EquipmentRecord(
        is_operable=True,
        calibrations=[CalibrationRecord(calibration_date=datetime.date(2000, 1, 1), calibration_cycle=1)]
    )
    assert record.is_calibration_due()

    record = EquipmentRecord(
        is_operable=False,
        calibrations=[CalibrationRecord(calibration_date=datetime.date(2000, 1, 1), calibration_cycle=1)]
    )
    assert not record.is_calibration_due()

    record = EquipmentRecord(
        is_operable=True,
        calibrations=[CalibrationRecord(calibration_date=datetime.date(2000, 1, 1), calibration_cycle=999)]
    )
    assert not record.is_calibration_due()

    date = datetime.date(today.year-1, today.month, today.day)
    record = EquipmentRecord(
        is_operable=True,
        calibrations=[CalibrationRecord(calibration_date=date, calibration_cycle=1.5)]
    )
    assert not record.is_calibration_due()  # not due for another 6 months
    assert record.is_calibration_due(12)

    # the calibration date gets precedence over the report date
    cal_date = datetime.date(today.year-1, today.month, today.day)
    rep_date = datetime.date(today.year, today.month, today.day)
    record = EquipmentRecord(
        is_operable=True,
        calibrations=[CalibrationRecord(calibration_date=cal_date, calibration_cycle=1.5, report_date=rep_date)]
    )
    assert not record.is_calibration_due()  # not due for another 6 months
    assert record.is_calibration_due(12)

    # the report date is used if the calibration date is not specified
    record = EquipmentRecord(
        is_operable=True,
        calibrations=[CalibrationRecord(calibration_cycle=1.5, report_date=rep_date)]
    )
    assert not record.is_calibration_due()  # not due for another 18 months
    assert not record.is_calibration_due(12)
    assert record.is_calibration_due(19)


def test_next_calibration_date():

    # not operable and the calibration_cycle is not defined
    record = EquipmentRecord(
        is_operable=False,
        calibrations=[CalibrationRecord(calibration_date=datetime.date(2000, 1, 1))]
    )
    assert record.next_calibration_date() is None

    # operable but the calibration_cycle is not defined
    record = EquipmentRecord(
        is_operable=True,
        calibrations=[CalibrationRecord(calibration_date=datetime.date(2000, 1, 1))]
    )
    assert record.next_calibration_date() is None

    # not operable but the calibration_cycle is defined
    record = EquipmentRecord(
        is_operable=False,
        calibrations=[CalibrationRecord(calibration_date=datetime.date(2000, 1, 1), calibration_cycle=1)]
    )
    assert record.next_calibration_date() is None

    record = EquipmentRecord(
        is_operable=True,
        calibrations=[CalibrationRecord(calibration_date=datetime.date(2000, 8, 4), calibration_cycle=1)]
    )
    d = record.next_calibration_date()
    assert d.year == 2001
    assert d.month == 8
    assert d.day == 4

    record = EquipmentRecord(
        is_operable=True,
        calibrations=[CalibrationRecord(calibration_date=datetime.date(2000, 12, 30), calibration_cycle=5.0)]
    )
    d = record.next_calibration_date()
    assert d.year == 2005
    assert d.month == 12
    assert d.day == 30

    record = EquipmentRecord(
        is_operable=True,
        calibrations=[CalibrationRecord(calibration_date=datetime.date(2000, 8, 4), calibration_cycle=1.5)]
    )
    d = record.next_calibration_date()
    assert d.year == 2002
    assert d.month == 2
    assert d.day == 4

    record = EquipmentRecord(
        is_operable=True,
        calibrations=[CalibrationRecord(calibration_date=datetime.date(2000, 3, 14), calibration_cycle=0.7)]
    )
    d = record.next_calibration_date()
    assert d.year == 2000
    assert d.month == 11
    assert d.day == 14

    # the calibration date gets precedence over the report date
    record = EquipmentRecord(
        is_operable=True,
        calibrations=[CalibrationRecord(calibration_date=datetime.date(2000, 3, 14), calibration_cycle=0.7,
                                        report_date=datetime.date(2000, 7, 8))]
    )
    d = record.next_calibration_date()
    assert d.year == 2000
    assert d.month == 11
    assert d.day == 14

    # the report_date gets used if calibration_date is not defined
    record = EquipmentRecord(
        is_operable=True,
        calibrations=[CalibrationRecord(report_date=datetime.date(2000, 3, 14), calibration_cycle=0.7)]
    )
    d = record.next_calibration_date()
    assert d.year == 2000
    assert d.month == 11
    assert d.day == 14


def test_record_dict():

    for item in [None, 1, 3.56, [], (), 5j, set(), 'hello', True, b'world']:
        with pytest.raises(TypeError):
            RecordDict(item)

    rd = RecordDict({'one': 1, 'ints': [1, 2, [3, 4, 5, [6, 7, [8]]], 9],
                     'nested1': {'a': 'x', 'b': 'y', 'nested2': {'matrix': [[1, 2], [3, 4], [5, 6]]}}})

    assert len(rd) == 3
    assert sorted(list(rd.keys())) == ['ints', 'nested1', 'one']

    # key access
    assert rd['one'] == 1
    assert rd['ints'] == (1, 2, (3, 4, 5, (6, 7, (8,))), 9)  # nested lists become nested tuples
    assert isinstance(rd['nested1'], RecordDict)
    assert rd['nested1']['a'] == 'x'
    assert rd['nested1']['b'] == 'y'
    assert isinstance(rd['nested1']['nested2'], RecordDict)
    assert rd['nested1']['nested2']['matrix'] == ((1, 2), (3, 4), (5, 6))  # nested lists become nested tuples

    # attribute access
    assert rd.one == 1
    assert rd.ints == (1, 2, (3, 4, 5, (6, 7, (8,))), 9)  # nested lists become nested tuples
    assert isinstance(rd.nested1, RecordDict)
    assert rd.nested1.a == 'x'
    assert rd.nested1.b == 'y'
    assert isinstance(rd.nested1.nested2, RecordDict)
    assert rd.nested1.nested2.matrix == ((1, 2), (3, 4), (5, 6))  # nested lists become nested tuples

    # read only
    for key in ['one', 'ints', 'nested1']:
        with pytest.raises(TypeError):
            rd[key] = None
    for key in ['a', 'b', 'nested2']:
        with pytest.raises(TypeError):
            rd['nested1'][key] = None
    with pytest.raises(TypeError):
        rd['nested1']['nested2']['matrix'] = None
    with pytest.raises(TypeError):
        rd.clear()
    with pytest.raises(TypeError):
        rd.fromkeys()
    with pytest.raises(TypeError):
        rd.pop()
    with pytest.raises(TypeError):
        rd.popitem()
    with pytest.raises(TypeError):
        rd.setdefault()
    with pytest.raises(TypeError):
        rd.update(x=7)

    # convert to JSON
    a = rd.to_json()
    assert a['one'] == 1
    assert a['ints'] == (1, 2, (3, 4, 5, (6, 7, (8,))), 9)
    assert a['nested1']['a'] == 'x'
    assert a['nested1']['b'] == 'y'
    assert a['nested1']['nested2']['matrix'] == ((1, 2), (3, 4), (5, 6))
    RecordDict(json.loads(json.dumps(a)))  # check that this does not raise an error

    # convert to XML element
    element = rd.to_xml()
    assert element.tag == 'RecordDict'
    assert element.find('one').text == '1'
    assert element.find('ints').text == '(1, 2, (3, 4, 5, (6, 7, (8,))), 9)'
    assert element.find('nested1/a').text == "'x'"
    assert element.find('nested1/b').text == "'y'"
    assert element.find('nested1/nested2/matrix').text == '((1, 2), (3, 4), (5, 6))'

    element = rd.to_xml(tag='whatever')
    assert element.tag == 'whatever'


def test_maintenance_record():

    mr = MaintenanceRecord()
    assert mr.date == datetime.date(datetime.MINYEAR, 1, 1)
    assert mr.comment == ''

    mr = MaintenanceRecord(comment='my comment', date='2019-04-23')
    assert mr.date == datetime.date(2019, 4, 23)
    assert mr.comment == 'my comment'

    # read only
    with pytest.raises(TypeError):
        mr.date = datetime.date(2000, 1, 17)
    with pytest.raises(TypeError):
        mr.comment = 'update comment'

    # cannot create new attributes
    with pytest.raises(TypeError):
        mr.new_attrib = 1

    d = mr.to_dict()
    assert d['date'] == datetime.date(2019, 4, 23)
    assert d['comment'] == 'my comment'

    # convert to JSON
    a = mr.to_json()
    assert a['date'] == '2019-04-23'
    assert a['comment'] == 'my comment'
    json_record = MaintenanceRecord(**json.loads(json.dumps(a)))  # check that this does not raise an error

    x = mr.to_xml()
    assert x.tag == 'MaintenanceRecord'
    assert x.find('date').text == '2019-04-23'
    assert x.find('comment').text == 'my comment'

    for rec in [mr, json_record]:
        assert rec.date == datetime.date(2019, 4, 23)
        assert rec.comment == 'my comment'

    assert str(mr) == 'MaintenanceRecord<2019-04-23>'

    s = repr(mr).splitlines()
    assert s[0] == 'MaintenanceRecord'
    assert s[1] == '  comment: {}'.format("'my comment'")
    assert s[2] == '  date: 2019-04-23'


def test_measurand_record():

    mr = MeasurandRecord()
    assert isinstance(mr.calibration, RecordDict)
    assert len(mr.calibration) == 0
    assert isinstance(mr.conditions, RecordDict)
    assert len(mr.conditions) == 0
    assert mr.type == ''
    assert mr.unit == ''

    # type and unit are always converted to type str
    mr = MeasurandRecord(type=7, unit=-1.2)
    assert mr.type == '7'
    assert mr.unit == '-1.2'

    # calibration and conditions must always be of type dict
    for item in [1, 3.56, [], (), 5j, set(), 'hello', True, b'world']:
        with pytest.raises(TypeError):
            MeasurandRecord(calibration=item)
        with pytest.raises(TypeError):
            MeasurandRecord(conditions=item)

    mr = MeasurandRecord(calibration={'a': 0, 'b': 1}, conditions=dict(c=2, d=3), type='Humidity', unit='%rh')
    assert mr.calibration.a == 0
    assert mr.calibration.b == 1
    assert mr.conditions.c == 2
    assert mr.conditions.d == 3
    assert mr.type == 'Humidity'
    assert mr.unit == '%rh'

    # read only
    with pytest.raises(TypeError):
        mr.calibration = None
    with pytest.raises(TypeError):
        mr.conditions = None
    with pytest.raises(TypeError):
        mr.type = None
    with pytest.raises(TypeError):
        mr.unit = None

    # cannot create new attributes
    with pytest.raises(TypeError):
        mr.new_attrib = 1

    assert str(mr) == 'MeasurandRecord<Humidity>'

    s = repr(mr).splitlines()
    assert s[0] == 'MeasurandRecord'
    assert s[1] == '  calibration: '
    assert s[2] == '    a: 0'
    assert s[3] == '    b: 1'
    assert s[4] == '  conditions: '
    assert s[5] == '    c: 2'
    assert s[6] == '    d: 3'
    assert s[7] == '  type: {}'.format("'Humidity'")
    assert s[8] == '  unit: {}'.format("'%rh'")

    d = mr.to_dict()
    assert d['calibration']['a'] == 0
    assert d['calibration']['b'] == 1
    assert d['conditions']['c'] == 2
    assert d['conditions']['d'] == 3
    assert d['type'] == 'Humidity'
    assert d['unit'] == '%rh'

    d = mr.to_json()
    assert d['calibration']['a'] == 0
    assert d['calibration']['b'] == 1
    assert d['conditions']['c'] == 2
    assert d['conditions']['d'] == 3
    assert d['type'] == 'Humidity'
    assert d['unit'] == '%rh'
    json_record = MeasurandRecord(**json.loads(json.dumps(d)))  # check that this does not raise an error

    x = mr.to_xml()
    assert x.tag == 'MeasurandRecord'
    assert x.find('calibration/a').text == '0'
    assert x.find('calibration/b').text == '1'
    assert x.find('conditions/c').text == '2'
    assert x.find('conditions/d').text == '3'
    assert x.find('type').text == 'Humidity'
    assert x.find('unit').text == '%rh'

    for rec in [mr, json_record]:
        assert rec.calibration.a == 0
        assert rec.calibration.b == 1
        assert rec.conditions.c == 2
        assert rec.conditions.d == 3
        assert rec.type == 'Humidity'
        assert rec.unit == '%rh'


def test_calibration_record():

    cr = CalibrationRecord()
    assert cr.calibration_cycle == 0
    assert isinstance(cr.calibration_cycle, float)
    assert cr.calibration_date == datetime.date(datetime.MINYEAR, 1, 1)
    assert isinstance(cr.measurands, RecordDict)
    assert len(cr.measurands) == 0
    assert cr.report_date == datetime.date(datetime.MINYEAR, 1, 1)
    assert cr.report_number == ''

    # read only
    with pytest.raises(TypeError):
        cr.calibration_cycle = None
    with pytest.raises(TypeError):
        cr.calibration_date = None
    with pytest.raises(TypeError):
        cr.measurands = None
    with pytest.raises(TypeError):
        cr.report_date = None
    with pytest.raises(TypeError):
        cr.report_number = None

    # cannot create new attributes
    with pytest.raises(TypeError):
        cr.new_attrib = 1

    # the calibration_cycle is always of type float
    for val in [1, '1', 1.0]:
        c = CalibrationRecord(calibration_cycle=val)
        assert c.calibration_cycle == 1.0
        assert isinstance(c.calibration_cycle, float)

    # the calibration_date and report_date are always of type datetime.date
    for val in [None, '2019-02-13', datetime.date(2019, 2, 13), datetime.datetime(2018, 5, 2, 4, 5, 12)]:
        c = CalibrationRecord(calibration_date=val, report_date=val)
        assert isinstance(c.calibration_date, datetime.date)
        assert isinstance(c.report_date, datetime.date)

    # the report_number is always of type str
    for val in ['7', 7]:
        c = CalibrationRecord(report_number=val)
        assert c.report_number == '7'

    # the measurands must be an iterable of MeasurandRecord's
    cr = CalibrationRecord(measurands=(None, 1, 2))
    assert isinstance(cr.measurands, RecordDict)
    assert len(cr.measurands) == 0

    cr = CalibrationRecord(measurands={None, 1, 2})
    assert isinstance(cr.measurands, RecordDict)
    assert len(cr.measurands) == 0

    cr = CalibrationRecord(measurands=[None, 1, 2])
    assert isinstance(cr.measurands, RecordDict)
    assert len(cr.measurands) == 0

    with pytest.raises(TypeError):
        CalibrationRecord(measurands=MeasurandRecord())

    # items that are not of type MeasurandRecord are silently ignored
    measurands = [MeasurandRecord(type='a'), None, MeasurandRecord(type='b'), {}, MeasurandRecord(type='c'), 99]

    cr = CalibrationRecord(calibration_cycle=5, calibration_date='2018-02-24',
                           measurands=measurands, report_date='2010-12-13', report_number='ABC123')

    assert cr.calibration_cycle == 5.0
    assert cr.calibration_date == datetime.date(2018, 2, 24)
    assert isinstance(cr.measurands, RecordDict)
    assert len(cr.measurands) == 3
    assert 'a' in cr.measurands
    assert 'b' in cr.measurands
    assert 'c' in cr.measurands
    assert cr.report_date == datetime.date(2010, 12, 13)
    assert cr.report_number == 'ABC123'

    d = cr.to_dict()
    assert d['calibration_cycle'] == 5.0
    assert d['calibration_date'] == datetime.date(2018, 2, 24)
    assert isinstance(d['measurands'], RecordDict)
    assert len(d['measurands']) == 3
    assert 'a' in d['measurands']
    assert 'b' in d['measurands']
    assert 'c' in d['measurands']
    assert d['report_date'] == datetime.date(2010, 12, 13)
    assert d['report_number'] == 'ABC123'

    d = cr.to_json()
    assert d['calibration_cycle'] == 5.0
    assert d['calibration_date'] == '2018-02-24'
    assert isinstance(d['measurands'], tuple)
    assert len(d['measurands']) == 3
    assert d['measurands'][0]['calibration'] == {}
    assert d['measurands'][0]['conditions'] == {}
    assert d['measurands'][0]['type'] == 'a'
    assert d['measurands'][0]['unit'] == ''
    assert d['measurands'][1]['calibration'] == {}
    assert d['measurands'][1]['conditions'] == {}
    assert d['measurands'][1]['type'] == 'b'
    assert d['measurands'][1]['unit'] == ''
    assert d['measurands'][2]['calibration'] == {}
    assert d['measurands'][2]['conditions'] == {}
    assert d['measurands'][2]['type'] == 'c'
    assert d['measurands'][2]['unit'] == ''
    assert d['report_date'] == '2010-12-13'
    assert d['report_number'] == 'ABC123'
    json_record = CalibrationRecord(**json.loads(json.dumps(d)))  # check that this does not raise an error

    x = cr.to_xml()
    assert x.tag == 'CalibrationRecord'
    assert x.find('calibration_cycle').text == '5.0'
    assert x.find('calibration_date').text == '2018-02-24'
    ta = x.find('.//MeasurandRecord[type="a"]')
    assert ta.find('calibration').text is None
    assert ta.find('conditions').text is None
    assert ta.find('type').text == 'a'
    assert ta.find('unit').text == ''
    tb = x.find('.//MeasurandRecord[type="b"]')
    assert tb.find('calibration').text is None
    assert tb.find('conditions').text is None
    assert tb.find('type').text == 'b'
    assert tb.find('unit').text == ''
    tc = x.find('.//MeasurandRecord[type="c"]')
    assert tc.find('calibration').text is None
    assert tc.find('conditions').text is None
    assert tc.find('type').text == 'c'
    assert tc.find('unit').text == ''
    assert x.find('report_date').text == '2010-12-13'
    assert x.find('report_number').text == 'ABC123'

    assert str(cr) == 'CalibrationRecord<ABC123>'

    s = repr(cr).splitlines()
    assert s[0] == 'CalibrationRecord'
    assert s[1] == '  calibration_cycle: 5.0'
    assert s[2] == '  calibration_date: 2018-02-24'
    assert s[3] == '  measurands: '
    assert s[4] == '    MeasurandRecord'
    assert s[5] == '      calibration: None'
    assert s[6] == '      conditions: None'
    assert s[7] == '      type: {}'.format("'a'")
    assert s[8] == '      unit: {}'.format("''")
    assert s[9] == '    MeasurandRecord'
    assert s[10] == '      calibration: None'
    assert s[11] == '      conditions: None'
    assert s[12] == '      type: {}'.format("'b'")
    assert s[13] == '      unit: {}'.format("''")
    assert s[14] == '    MeasurandRecord'
    assert s[15] == '      calibration: None'
    assert s[16] == '      conditions: None'
    assert s[17] == '      type: {}'.format("'c'")
    assert s[18] == '      unit: {}'.format("''")
    assert s[19] == '  report_date: 2010-12-13'
    assert s[20] == '  report_number: {}'.format("'ABC123'")

    for rec in [cr, json_record]:
        assert rec.calibration_cycle == 5.0
        assert rec.calibration_date == datetime.date(2018, 2, 24)
        assert isinstance(rec.measurands, RecordDict)
        assert len(rec.measurands) == 3
        assert 'a' in rec.measurands
        assert 'b' in rec.measurands
        assert 'c' in rec.measurands
        assert rec.report_date == datetime.date(2010, 12, 13)
        assert rec.report_number == 'ABC123'
