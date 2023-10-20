from __future__ import annotations

import os

import pytest

from msl.equipment.config import Config
from msl.equipment.connection_demo import ConnectionDemo
from msl.equipment.constants import Backend
from msl.equipment.factory import connect
from msl.equipment.record_types import ConnectionRecord
from msl.equipment.record_types import EquipmentRecord

ROOT_DIR = os.path.join(os.path.dirname(__file__), 'db_files')


def teardown_module():
    import cleanup_os_environ
    cleanup_os_environ.cleanup()
    Config.DEMO_MODE = False


def test_exceptions():
    Config.DEMO_MODE = False

    # not an EquipmentRecord
    for item in [None, ConnectionRecord()]:
        with pytest.raises(AttributeError, match=r"no attribute 'connection'"):
            connect(item)

    # only 1 EquipmentRecord is allowed
    with pytest.raises(AttributeError, match=r"no attribute 'connection'"):
        connect([
            EquipmentRecord(connection=ConnectionRecord(address='COM1', backend=Backend.MSL)),
            EquipmentRecord(connection=ConnectionRecord(address='COM2', backend=Backend.MSL))
        ])

    # only 1 EquipmentRecord is allowed
    with pytest.raises(AttributeError, match=r"no attribute 'connection'"):
        connect({
            'a': EquipmentRecord(connection=ConnectionRecord(address='COM1', backend=Backend.MSL)),
            'b': EquipmentRecord(connection=ConnectionRecord(address='COM2', backend=Backend.MSL))
        })

    # only 1 EquipmentRecord allowed
    c = Config(os.path.join(ROOT_DIR, 'db.xml'))
    with pytest.raises(AttributeError, match=r"no attribute 'connection'"):
        connect(c.database().equipment)

    # no ConnectionRecord defined for the EquipmentRecord
    with pytest.raises(ValueError, match='connection object'):
        connect(EquipmentRecord())

    # no address has been set
    with pytest.raises(ValueError, match='connection address'):
        connect(EquipmentRecord(connection=ConnectionRecord()))

    # no backend
    with pytest.raises(ValueError, match='connection backend'):
        connect(EquipmentRecord(connection=ConnectionRecord(address='COM1', backend=Backend.UNKNOWN)))

    # the SDK library does not exist
    with pytest.raises(OSError, match='Cannot find'):
        connect(EquipmentRecord(
            manufacturer='Thorlabs',
            model='FW212C',
            connection=ConnectionRecord(
                address='SDK::invalid.dll',
                backend=Backend.MSL
            )
        ))


def test_demo_mode():
    Config.DEMO_MODE = True

    c = connect(EquipmentRecord(connection=ConnectionRecord(address='COM1', backend=Backend.MSL)), demo=True)
    assert isinstance(c, ConnectionDemo)

    c = connect(EquipmentRecord(connection=ConnectionRecord(address='COM1', backend=Backend.MSL)))
    assert isinstance(c, ConnectionDemo)


def test_list_or_dict():
    record = EquipmentRecord(connection=ConnectionRecord(address='COM1', backend=Backend.MSL))
    c = connect([record], True)
    assert isinstance(c, ConnectionDemo)

    c = connect({'eq': record}, True)
    assert isinstance(c, ConnectionDemo)
