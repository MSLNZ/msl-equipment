import os
import datetime

import pytest

from msl.equipment.config import Config
from msl.equipment import EquipmentRecord, ConnectionRecord
from msl.equipment import constants
from msl.equipment.connection_msl import ConnectionMessageBased


def test_equip_record():

    a = EquipmentRecord().to_dict()
    assert len(a) == 14
    assert 'alias' in a
    assert 'asset_number' in a
    assert 'calibration_cycle' in a
    assert 'category' in a
    assert 'connection' in a
    assert 'date_calibrated' in a
    assert 'description' in a
    assert 'latest_report_number' in a
    assert 'location' in a
    assert 'manufacturer' in a
    assert 'model' in a
    assert 'register' in a
    assert 'serial' in a
    assert 'team' in a

    # the default values
    record = EquipmentRecord()
    assert record.alias == ''
    assert record.asset_number == ''
    assert record.calibration_cycle == 0.0
    assert record.category == ''
    assert record.connection is None
    assert record.date_calibrated == datetime.date(datetime.MINYEAR, 1, 1)
    assert record.description == ''
    assert record.latest_report_number == ''
    assert record.location == ''
    assert record.manufacturer == ''
    assert record.model == ''
    assert record.register == ''
    assert record.serial == ''
    assert record.team == ''

    record = EquipmentRecord(manufacturer='ABC def', model='ZZZ', serial='DY135/055')
    assert record.manufacturer == 'ABC def'
    assert record.model == 'ZZZ'
    assert record.serial == 'DY135/055'

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

    with pytest.raises(ValueError) as err:
        EquipmentRecord(calibration_cycle='is not an number')
    assert 'calibration_cycle' in str(err.value)

    with pytest.raises(TypeError) as err:
        EquipmentRecord(date_calibrated='2017-08-15')
    assert 'date_calibrated' in str(err.value)

    with pytest.raises(TypeError) as err:
        EquipmentRecord(connection='should be a ConnectionRecord object')
    assert 'ConnectionRecord' in str(err.value)

    with pytest.raises(AttributeError):
        EquipmentRecord(unknown_attribute='AAA')

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


def test_conn_record():

    a = ConnectionRecord().to_dict()
    assert len(a) == 7
    assert 'address' in a
    assert 'backend' in a
    assert 'interface' in a
    assert 'manufacturer' in a
    assert 'model' in a
    assert 'properties' in a
    assert 'serial' in a

    # the default values
    record = ConnectionRecord()
    assert record.address == ''
    assert record.backend == constants.Backend.UNKNOWN
    assert record.interface == constants.MSLInterface.NONE
    assert record.manufacturer == ''
    assert record.model == ''
    assert record.properties == {}
    assert record.serial == ''

    # create a new ConnectionRecord
    record = ConnectionRecord(
        address='GPIB::15',
        backend=constants.Backend.MSL,
        manufacturer='ABC def',
        model='ZZZ',
        serial='DY135/055',
        properties={
            'resolution': '14bit',
            'data': 77,
        },
    )
    assert record.address == 'GPIB::15'
    assert record.backend == constants.Backend.MSL
    assert record.interface == constants.MSLInterface.GPIB
    assert record.manufacturer == 'ABC def'
    assert record.model == 'ZZZ'
    assert record.serial == 'DY135/055'
    assert record.properties['resolution'] == '14bit'
    assert record.properties['data'] == 77

    record = ConnectionRecord(address='COM4', backend=constants.Backend.MSL)
    assert record.address == 'COM4'
    assert record.backend == constants.Backend.MSL
    assert record.interface == constants.MSLInterface.ASRL  # COM is an alias for ASRL

    record = ConnectionRecord(address='LPT5', backend=constants.Backend.MSL)
    assert record.interface == constants.MSLInterface.ASRL   # LPT is an alias for ASRL

    record = ConnectionRecord(address='ASRL4', backend=constants.Backend.MSL)
    assert record.interface == constants.MSLInterface.ASRL

    record = ConnectionRecord(address='SDK', backend=constants.Backend.MSL)
    assert record.address == 'SDK'
    assert record.backend == constants.Backend.MSL
    assert record.interface == constants.MSLInterface.SDK

    record = ConnectionRecord(address='ENET::192.168.1.21', backend=constants.Backend.MSL)
    assert record.address == 'ENET::192.168.1.21'
    assert record.backend == constants.Backend.MSL
    assert record.interface == constants.MSLInterface.TCPIP  # ENET is an alias for TCPIP

    record = ConnectionRecord(address='ETHERNET::192.168.1.21', backend=constants.Backend.MSL)
    assert record.interface == constants.MSLInterface.TCPIP  # ETHERNET is an alias for TCPIP

    record = ConnectionRecord(address='LAN::192.168.1.21', backend=constants.Backend.MSL)
    assert record.interface == constants.MSLInterface.TCPIP  # LAN is an alias for TCPIP

    record = ConnectionRecord(address='TCPIP::192.168.1.21', backend=constants.Backend.MSL)
    assert record.interface == constants.MSLInterface.TCPIP

    record = ConnectionRecord(address='ENET+COM::192.168.1.21+3', backend=constants.Backend.MSL)
    assert record.address == 'ENET+COM::192.168.1.21+3'
    assert record.backend == constants.Backend.MSL
    assert record.interface == constants.MSLInterface.TCPIP_ASRL

    record = ConnectionRecord(address='LAN+GPIB::192.168.1.21+7', backend=constants.Backend.MSL)
    assert record.address == 'LAN+GPIB::192.168.1.21+7'
    assert record.backend == constants.Backend.MSL
    assert record.interface == constants.MSLInterface.TCPIP_GPIB

    # unknown address value
    c = ConnectionRecord(address='XXXXXX')
    assert c.interface == constants.MSLInterface.NONE

    # setting the interface, bad
    with pytest.raises(ValueError) as err:
        ConnectionRecord(address='COM1', backend=constants.Backend.MSL, interface=constants.MSLInterface.GPIB)
    assert 'interface' in str(err.value) and 'address' in str(err.value)

    # setting the interface, bad
    with pytest.raises(TypeError) as err:
        ConnectionRecord(address='COM1', backend=constants.Backend.MSL, interface=None)
    assert 'interface' in str(err.value) and 'enum' in str(err.value)

    # setting the interface, good
    ConnectionRecord(address='COM1', backend=constants.Backend.MSL, interface=constants.MSLInterface.ASRL)

    # the backend must be a Backend enum
    with pytest.raises(ValueError) as err:
        ConnectionRecord(backend='MSL')
    assert 'Backend' in str(err.value)

    # the properties attribute must be a dictionary
    with pytest.raises(TypeError) as err:
        ConnectionRecord(properties=[])
    assert 'dictionary' in str(err.value)

    with pytest.raises(AttributeError):
        ConnectionRecord(unknown_attribute='AAA')


def test_dbase():

    path = os.path.join(os.path.dirname(__file__), 'db.xml')
    c = Config(path)

    dbase = c.database()

    eq1 = dbase.equipment['712ae']
    assert eq1.manufacturer == 'F D080'
    assert eq1.model == '712ae'
    assert eq1.asset_number == 'f39a4f'
    assert eq1.serial == '49e39f1'
    assert eq1.date_calibrated.year == 2010
    assert eq1.date_calibrated.month == 11
    assert eq1.date_calibrated.day == 1
    assert eq1.register == 'MSLA.X.Y.Z'
    assert eq1.category == 'DMM'
    assert eq1.location == 'General'
    assert eq1.description == 'Digital Multimeter'
    assert eq1.connection is None

    eq2 = dbase.equipment['dvm']
    assert eq2.alias == 'dvm'
    assert eq2.asset_number == '00011'
    assert eq2.calibration_cycle == 5
    assert eq2.category == 'DVM'
    assert eq2.date_calibrated.year == 2009
    assert eq2.date_calibrated.month == 11
    assert eq2.date_calibrated.day == 12
    assert eq2.description == 'Digital nanovoltmeter'
    assert eq2.location == 'Watt Lab'
    assert eq2.manufacturer == 'Agilent'
    assert eq2.model == '34420A'
    assert eq2.register == 'MSLE.X.YYY'
    assert eq2.team == 'Any'
    assert eq2.serial == 'A00024'

    assert eq2.connection.manufacturer == 'Agilent'
    assert eq2.connection.model == '34420A'
    assert eq2.connection.serial == 'A00024'
    assert eq2.connection.address == 'ASRL1::INSTR'
    assert eq2.connection.backend == constants.Backend.MSL
    assert eq2.connection.interface == constants.MSLInterface.ASRL
    assert eq2.connection.properties['baud_rate'] == 9600
    assert eq2.connection.properties['read_termination'] == ConnectionMessageBased.CR + ConnectionMessageBased.LF
    assert eq2.connection.properties['write_termination'] == ConnectionMessageBased.LF


def test_asrl():
    c = Config(os.path.join(os.path.dirname(__file__), 'db_asrl.xml'))

    dbase = c.database()

    pyvisa = dbase.equipment['pyvisa'].connection
    msl = dbase.equipment['msl'].connection

    assert pyvisa.address == 'COM1'
    assert msl.address == 'COM1'

    assert pyvisa.properties['baud_rate'] == 119200
    assert msl.properties['baud_rate'] == 119200

    assert pyvisa.properties['data_bits'] == constants.DataBits.SEVEN
    assert msl.properties['data_bits'] == constants.DataBits.SEVEN

    assert pyvisa.properties['parity'] == constants.Parity.ODD
    assert msl.properties['parity'] == constants.Parity.ODD

    assert pyvisa.properties['stop_bits'] == constants.StopBits.ONE_POINT_FIVE
    assert msl.properties['stop_bits'] == constants.StopBits.ONE_POINT_FIVE


def test_calibration():
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
