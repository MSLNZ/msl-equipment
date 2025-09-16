from __future__ import annotations

from typing import TYPE_CHECKING

from msl.equipment import Backend, ConnectionRecord, EquipmentRecord
from msl.equipment.record_types import _Warn  # pyright: ignore[reportPrivateUsage]

if TYPE_CHECKING:
    import pytest


def test_warning_connection_record(recwarn: pytest.WarningsRecorder) -> None:
    _Warn.show = True

    equipment = EquipmentRecord(
        manufacturer="A",
        model="B",
        serial="C",
        connection=ConnectionRecord(
            address="COM1",
            backend=Backend.MSL,
            manufacturer="A",
            model="B",
            serial="C",
            timeout=10,
        ),
    )

    assert equipment.manufacturer == "A"
    assert equipment.model == "B"
    assert equipment.serial == "C"
    assert equipment.connection is not None
    assert equipment.connection.address == "COM1"
    assert equipment.connection.backend == Backend.MSL
    assert equipment.connection.manufacturer == "A"
    assert equipment.connection.model == "B"
    assert equipment.connection.serial == "C"
    assert equipment.connection.properties == {"timeout": 10}

    # Warnings issued once
    _ = EquipmentRecord(connection=ConnectionRecord(address="A", backend="MSL"))
    _ = EquipmentRecord(connection=ConnectionRecord(address="A", backend="PyVISA"))
    _ = EquipmentRecord(connection=ConnectionRecord(address="A", backend="NIDAQ"))

    assert len(recwarn) == 1
    w = recwarn.pop(FutureWarning)
    assert issubclass(w.category, FutureWarning)
    assert w.lineno == 19
    assert w.filename == __file__
    assert str(w.message).endswith(
        "Replace `EquipmentRecord` with `Equipment` and replace `ConnectionRecord` with `Connection`."
    )


def test_warning_equipment_record(recwarn: pytest.WarningsRecorder) -> None:
    _Warn.show = True

    equipment = EquipmentRecord(manufacturer="A", model="B", serial="C")

    assert equipment.manufacturer == "A"
    assert equipment.model == "B"
    assert equipment.serial == "C"
    assert equipment.connection is None

    # Warnings issued once
    _ = EquipmentRecord(manufacturer="D", model="E", serial="F")
    _ = EquipmentRecord(manufacturer="G", model="H", serial="I")
    _ = EquipmentRecord(manufacturer="J", model="K", serial="L")

    assert len(recwarn) == 1
    w = recwarn.pop(FutureWarning)
    assert issubclass(w.category, FutureWarning)
    assert w.lineno == 58
    assert w.filename == __file__
    assert str(w.message).endswith(
        "Replace `EquipmentRecord` with `Equipment` and replace `ConnectionRecord` with `Connection`."
    )
