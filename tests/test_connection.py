import enum

import pytest

from msl.equipment import exceptions
from msl.equipment.connection import Connection
from msl.equipment.record_types import EquipmentRecord


class EnumTest1(enum.IntEnum):
    A = 1
    B = 2
    C = 3


class EnumTest2(enum.IntEnum):
    data_A = 11
    DATA_B = 12
    RES_C = 13


class EnumTest3(enum.Enum):
    first = 1.1
    second = 2.2
    third = 3.3


class EnumTest4(enum.Enum):
    START = 'the beginning'
    STOP = 'the end'


def test_convert_to_enum():
    assert Connection.convert_to_enum('a', EnumTest1, to_upper=True) == EnumTest1.A
    assert Connection.convert_to_enum(2, EnumTest1) == EnumTest1.B
    assert Connection.convert_to_enum('C', EnumTest1) == EnumTest1.C
    with pytest.raises(ValueError):
        Connection.convert_to_enum(4, EnumTest1)
    with pytest.raises(ValueError):
        Connection.convert_to_enum(None, EnumTest1)

    assert Connection.convert_to_enum('A', EnumTest2, prefix='data_') == EnumTest2.data_A
    assert Connection.convert_to_enum(EnumTest2.DATA_B, EnumTest2) == EnumTest2.DATA_B
    assert Connection.convert_to_enum('res_c', EnumTest2, to_upper=True) == EnumTest2.RES_C

    assert Connection.convert_to_enum('first', EnumTest3) == EnumTest3.first
    assert Connection.convert_to_enum(2.2, EnumTest3) == EnumTest3.second
    assert Connection.convert_to_enum(EnumTest3.third, EnumTest3) == EnumTest3.third
    with pytest.raises(ValueError):
        Connection.convert_to_enum(1.17, EnumTest3)

    assert Connection.convert_to_enum('stop', EnumTest4, to_upper=True) == EnumTest4.STOP
    assert Connection.convert_to_enum('STarT', EnumTest4, to_upper=True) == EnumTest4.START
    assert Connection.convert_to_enum('the end', EnumTest4) == EnumTest4.STOP


def test_exception_handler():
    c = Connection(EquipmentRecord())
    assert c._exception_handler == exceptions.MSLConnectionError

    # not a class error
    with pytest.raises(TypeError) as err:
        c.set_exception_class(None)
    assert 'issubclass()' in str(err.value)

    # not a subclass of MSLConnectionError
    with pytest.raises(TypeError) as err:
        c.set_exception_class(IOError)
    assert 'MSLConnectionError' in str(err.value)

    c.set_exception_class(exceptions.ThorlabsError)
    assert c._exception_handler == exceptions.ThorlabsError
