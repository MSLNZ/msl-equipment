from __future__ import annotations

# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
import nidaqmx  # type: ignore[import-untyped]  # pyright: ignore[reportMissingTypeStubs]
import pytest

from msl.equipment import NIDAQ, Connection, Equipment


def test_equivalent_to_importing_nidaqmx() -> None:
    daq = NIDAQ(Equipment(connection=Connection(address="Dev1")))

    assert f"{daq.address}/ai0" == "Dev1/ai0"

    assert daq.CtrFreq is nidaqmx.CtrFreq
    assert daq.CtrTick is nidaqmx.CtrTick
    assert daq.CtrTime is nidaqmx.CtrTime
    assert daq.DaqError is nidaqmx.DaqError
    assert daq.DaqReadError is nidaqmx.DaqReadError
    assert daq.DaqResourceWarning is nidaqmx.DaqResourceWarning
    assert daq.DaqWarning is nidaqmx.DaqWarning
    assert daq.DaqWriteError is nidaqmx.DaqWriteError
    assert daq.GRPC_SERVICE_INTERFACE_NAME is nidaqmx.GRPC_SERVICE_INTERFACE_NAME
    assert daq.GrpcSessionOptions is nidaqmx.GrpcSessionOptions
    assert daq.Scale is nidaqmx.Scale
    assert daq.Task is nidaqmx.Task
    assert daq.constants is nidaqmx.constants
    assert daq.error_codes is nidaqmx.error_codes
    assert daq.errors is nidaqmx.errors
    assert daq.grpc_session_options is nidaqmx.grpc_session_options
    assert daq.scale is nidaqmx.scale
    assert daq.system is nidaqmx.system
    assert daq.task is nidaqmx.task
    assert daq.types is nidaqmx.types
    assert daq.utils is nidaqmx.utils
    assert daq.version is nidaqmx.version

    # these must not raise AttributeError
    assert daq.stream_readers
    assert daq.stream_writers

    with pytest.raises(AttributeError):
        _ = nidaqmx.doesnotexist

    with pytest.raises(AttributeError):
        _ = daq.doesnotexist


def test_no_connection_instance() -> None:
    with pytest.raises(TypeError, match=r"A Connection is not associated"):
        _ = NIDAQ(Equipment())
