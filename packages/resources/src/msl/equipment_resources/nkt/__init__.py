"""Resources for equipment from [NKT Photonics](https://www.nktphotonics.com/)."""

from __future__ import annotations

from .nktpdll import (
    NKT,
    DateTime,
    DeviceMode,
    DeviceStatus,
    DeviceStatusCallback,
    ParameterSet,
    PointToPoint,
    PortStatus,
    PortStatusCallback,
    RegisterData,
    RegisterPriority,
    RegisterStatus,
    RegisterStatusCallback,
    Unit,
    device_status_callback,
    port_status_callback,
    register_status_callback,
)

__all__: list[str] = [
    "NKT",
    "DateTime",
    "DeviceMode",
    "DeviceStatus",
    "DeviceStatusCallback",
    "ParameterSet",
    "PointToPoint",
    "PortStatus",
    "PortStatusCallback",
    "RegisterData",
    "RegisterPriority",
    "RegisterStatus",
    "RegisterStatusCallback",
    "Unit",
    "device_status_callback",
    "port_status_callback",
    "register_status_callback",
]
