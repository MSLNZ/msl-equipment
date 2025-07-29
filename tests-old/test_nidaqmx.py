from __future__ import annotations

import nidaqmx
import pytest
from nidaqmx import stream_readers
from nidaqmx import stream_writers

from msl.equipment import Backend
from msl.equipment import ConnectionRecord
from msl.equipment import EquipmentRecord

try:
    with nidaqmx.Task() as task:
        pass
except:
    HAS_NIDAQ_INSTALLED = False
else:
    HAS_NIDAQ_INSTALLED = True


@pytest.mark.skipif(not HAS_NIDAQ_INSTALLED, reason="NI-DAQmx is not installed")
def test_equivalent_to_importing_nidaqmx():
    record = EquipmentRecord(connection=ConnectionRecord(backend=Backend.NIDAQ))

    daq = record.connect(demo=False)

    assert daq.CtrFreq == nidaqmx.CtrFreq
    assert daq.CtrTick == nidaqmx.CtrTick
    assert daq.CtrTime == nidaqmx.CtrTime
    assert daq.DaqError == nidaqmx.DaqError
    assert daq.DaqResourceWarning == nidaqmx.DaqResourceWarning
    assert daq.DaqWarning == nidaqmx.DaqWarning
    assert daq.Scale == nidaqmx.Scale
    assert daq.Task == nidaqmx.Task
    assert daq.constants == nidaqmx.constants
    assert daq.errors == nidaqmx.errors
    assert daq.stream_readers == stream_readers
    assert daq.stream_writers == stream_writers
    assert daq.system == nidaqmx.system
    assert daq.types == nidaqmx.types
    assert daq.utils == nidaqmx.utils

    for item in dir(nidaqmx.constants):
        if item.startswith("_"):
            continue
        assert getattr(daq.constants, item) == getattr(nidaqmx.constants, item)

    for item in dir(nidaqmx.errors):
        if item.startswith("_"):
            continue
        assert getattr(daq.errors, item) == getattr(nidaqmx.errors, item)

    for item in dir(stream_readers):
        if item.startswith("_"):
            continue
        assert getattr(daq.stream_readers, item) == getattr(stream_readers, item)

    for item in dir(stream_writers):
        if item.startswith("_"):
            continue
        assert getattr(daq.stream_writers, item) == getattr(stream_writers, item)

    for item in dir(nidaqmx.system):
        if item.startswith("_"):
            continue
        assert getattr(daq.system, item) == getattr(nidaqmx.system, item)

    for item in dir(nidaqmx.system.system):
        if item.startswith("_"):
            continue
        assert getattr(daq.system.system, item) == getattr(nidaqmx.system.system, item)

    for item in dir(nidaqmx.types):
        if item.startswith("_"):
            continue
        assert getattr(daq.types, item) == getattr(nidaqmx.types, item)

    for item in dir(nidaqmx.utils):
        if item.startswith("_"):
            continue
        assert getattr(daq.utils, item) == getattr(nidaqmx.utils, item)
