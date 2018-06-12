import os

import pytest

from msl.equipment.factory import connect
from msl.equipment.config import Config
from msl.equipment.constants import Backend
from msl.equipment.record_types import EquipmentRecord, ConnectionRecord
from msl.equipment.connection_demo import ConnectionDemo


def test_exceptions():
    Config.DEMO_MODE = False

    with pytest.raises(TypeError) as err:
        connect(None)  # not an EquipmentRecord
    assert 'EquipmentRecord' in str(err.value)

    with pytest.raises(TypeError) as err:
        connect(ConnectionRecord())  # not an EquipmentRecord
    assert 'EquipmentRecord' in str(err.value)

    with pytest.raises(TypeError) as err:
        connect([None])  # not an EquipmentRecord
    assert 'EquipmentRecord' in str(err.value)

    with pytest.raises(TypeError) as err:
        connect({None})  # not an EquipmentRecord
    assert 'EquipmentRecord' in str(err.value)

    with pytest.raises(TypeError) as err:
        connect([
            EquipmentRecord(connection=ConnectionRecord(address='COM1', backend=Backend.MSL)),
            EquipmentRecord(connection=ConnectionRecord(address='COM2', backend=Backend.MSL))
        ])  # only 1 EquipmentRecord allowed
    assert 'list' in str(err.value)

    with pytest.raises(TypeError) as err:
        connect({
            'a': EquipmentRecord(connection=ConnectionRecord(address='COM1', backend=Backend.MSL)),
            'b': EquipmentRecord(connection=ConnectionRecord(address='COM2', backend=Backend.MSL))
        })  # only 1 EquipmentRecord allowed
    assert 'dict' in str(err.value)

    c = Config(os.path.join(os.path.dirname(__file__), 'db.xml'))
    with pytest.raises(TypeError) as err:
        connect(c.database().equipment)  # only 1 EquipmentRecord allowed
    assert 'dict' in str(err.value)

    with pytest.raises(ValueError) as err:
        connect(EquipmentRecord())  # no ConnectionRecord defined for the EquipmentRecord
    assert 'connection object' in str(err.value)

    with pytest.raises(ValueError) as err:
        connect(EquipmentRecord(connection=ConnectionRecord()))  # no address has been set
    assert 'connection address' in str(err.value)

    with pytest.raises(ValueError) as err:
        connect(EquipmentRecord(connection=ConnectionRecord(address='COM1', backend=Backend.UNKNOWN)))  # no backend
    assert 'connection backend' in str(err.value)

    # the SDK library does not exist
    with pytest.raises(IOError) as err:
        connect(EquipmentRecord(
            manufacturer='thorlabs',
            model='fw212c',
            connection=ConnectionRecord(
                manufacturer='thorlabs',
                model='fw212c',
                address='SDK::invalid.dll', backend=Backend.MSL
            )
        ))
    assert 'loadlib' in str(err)


def test_demo_mode():
    Config.DEMO_MODE = True

    c = connect(EquipmentRecord(connection=ConnectionRecord(address='COM1', backend=Backend.MSL)), True)
    assert isinstance(c, ConnectionDemo)

    c = connect(EquipmentRecord(connection=ConnectionRecord(address='COM1', backend=Backend.MSL)))
    assert isinstance(c, ConnectionDemo)


def test_list_or_dict():
    record = EquipmentRecord(connection=ConnectionRecord(address='COM1', backend=Backend.MSL))
    c = connect([record], True)
    assert isinstance(c, ConnectionDemo)

    c = connect({'eq': record}, True)
    assert isinstance(c, ConnectionDemo)
