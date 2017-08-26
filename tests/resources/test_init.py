import os
import re
import fnmatch
import importlib

import pytest

from msl.equipment import resources
from msl.equipment.connection import Connection
from msl.equipment.record_types import ConnectionRecord
from msl.equipment.constants import Backend
from msl.equipment import connection_msl


def test_recursive_find_resource_class():
    r = resources.recursive_find_resource_class

    assert r('Bentham') == resources.bentham.benhw64.Bentham
    assert r('PicoScope2000') == resources.picotech.picoscope.ps2000.PicoScope2000
    assert r('PicoScope5000A') == resources.picotech.picoscope.ps5000a.PicoScope5000A
    assert r('FilterWheelXX2C') == resources.thorlabs.fwxx2c.FilterWheelXX2C
    assert r('FilterFlipper') == resources.thorlabs.kinesis.filter_flipper.FilterFlipper


def test_unique_resource_class_name():
    names = {}
    class_regex = re.compile(r'^class\s+(\w+)\(', re.MULTILINE)

    path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'msl', 'equipment', 'resources'))
    for root, dirs, files in os.walk(path):
        if root.endswith('__pycache__'):
            continue

        root_pkg = 'msl.equipment.resources' + root.replace(os.path.sep, '.').split('msl.equipment.resources')[1]

        for filename in fnmatch.filter(files, '*.py'):

            if filename.startswith('__init__'):
                continue

            with open(os.path.join(root, filename), 'r') as fp:
                lines = fp.read()

            candidates = [item for item in re.findall(class_regex, lines)]

            mod = importlib.import_module('{}.{}'.format(root_pkg, filename[:-3]))
            for item in candidates:
                obj = getattr(mod, item)
                if issubclass(obj, Connection):
                    if obj.__name__ in names:
                        name = obj.__name__
                        raise NameError('Class name is not unique: {}\n{}\n{}'.format(name, obj, names[name]))
                    names[obj.__name__] = obj


def test_check_manufacture_model_resource_name():

    record = ConnectionRecord(manufacturer='unknown', model='unknown')
    cls = resources.check_manufacture_model_resource_name(record)
    assert cls is None

    record = ConnectionRecord(manufacturer='CMI', model='SIA3')
    cls = resources.check_manufacture_model_resource_name(record)
    assert cls == resources.cmi.sia3.SIA3


def test_find_sdk_class():

    record = ConnectionRecord()
    with pytest.raises(ValueError) as err:
        resources.find_sdk_class(record)  # the interface is not MSLInterface.SDK
    assert 'interface' in str(err.value)

    record = ConnectionRecord(backend=Backend.PyVISA)
    with pytest.raises(ValueError) as err:
        resources.find_sdk_class(record)  # the interface is not MSLInterface.SDK
    assert 'interface' in str(err.value)

    record = ConnectionRecord(backend=Backend.MSL, address='COM3')
    with pytest.raises(ValueError) as err:
        resources.find_sdk_class(record)  # the interface is not MSLInterface.SDK
    assert 'interface' in str(err.value)

    record = ConnectionRecord(backend=Backend.MSL, address='SDK')
    with pytest.raises(ValueError) as err:
        resources.find_sdk_class(record)  # the address is not SDK::PythonClassName::PathToLibrary
    assert str(err.value).startswith('For a SDK interface')

    record = ConnectionRecord(backend=Backend.MSL, address='SDK::ClassName')
    with pytest.raises(ValueError) as err:
        resources.find_sdk_class(record)  # the address does not include PathToLibrary
    assert 'address' in str(err.value)

    record = ConnectionRecord(backend=Backend.MSL, address='SDK::PythonClassName::PathToLibrary')
    with pytest.raises(IOError):
        resources.find_sdk_class(record)  # invalid class name

    record = ConnectionRecord(backend=Backend.MSL, address='SDK::PicoScope5000A::PathToLibrary')
    cls = resources.find_sdk_class(record)  # valid class name
    assert cls == resources.picotech.picoscope.ps5000a.PicoScope5000A

    # do not include the PythonClassName (only the PathToLibrary) but use an invalid model number
    record = ConnectionRecord(backend=Backend.MSL, manufacturer='Thorlabs', model='FW102', address='SDK::FilterWheel102.dll')
    with pytest.raises(ValueError) as err:
        resources.find_sdk_class(record)
    assert 'automatically' in str(err.value)

    # do not include the PythonClassName (only the PathToLibrary) but use a record that does not use an SDK
    record = ConnectionRecord(backend=Backend.MSL, manufacturer='CMI', model='SIA3', address='SDK::FilterWheel102.dll')
    with pytest.raises(ValueError) as err:
        resources.find_sdk_class(record)
    assert 'subclass' in str(err.value)

    # include the PythonClassName
    record = ConnectionRecord(backend=Backend.MSL, manufacturer='Thorlabs', model='FW102C', address='SDK::FilterWheelXX2C::FilterWheel102.dll')
    cls = resources.find_sdk_class(record)
    assert cls == resources.thorlabs.fwxx2c.FilterWheelXX2C


def test_find_serial_class():

    record = ConnectionRecord()
    with pytest.raises(ValueError) as err:
        resources.find_serial_class(record)  # the interface is not an ASRL-type interface
    assert 'interface' in str(err.value)

    record = ConnectionRecord(backend=Backend.PyVISA)
    with pytest.raises(ValueError) as err:
        resources.find_serial_class(record)  # the interface is not an ASRL-type interface
    assert 'interface' in str(err.value)

    record = ConnectionRecord(backend=Backend.MSL)
    with pytest.raises(ValueError) as err:
        resources.find_serial_class(record)  # the interface is not an ASRL-type interface
    assert 'interface' in str(err.value)

    record = ConnectionRecord(backend=Backend.MSL, address='GPIB::02')
    with pytest.raises(ValueError) as err:
        resources.find_serial_class(record)  # the interface is not an ASRL-type interface
    assert 'interface' in str(err.value)

    record = ConnectionRecord(backend=Backend.MSL, address='COM1')
    assert resources.find_serial_class(record) == connection_msl.ConnectionSerial

    record = ConnectionRecord(backend=Backend.MSL, address='COM1::instr')
    assert resources.find_serial_class(record) == connection_msl.ConnectionSerial

    record = ConnectionRecord(backend=Backend.MSL, address='COM1', manufacturer='CMI', model='SIA3')
    assert resources.find_serial_class(record) == resources.cmi.sia3.SIA3

    record = ConnectionRecord(backend=Backend.MSL, address='COM1::INSTR', manufacturer='CMI', model='SIA3')
    assert resources.find_serial_class(record) == resources.cmi.sia3.SIA3
