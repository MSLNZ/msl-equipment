"""Resources for equipment from [NKT Photonics](https://www.nktphotonics.com/)."""

from __future__ import annotations

from .nkt import NKT
from .nktpdll import (
    NKTDLL,
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
from .superk import SuperK

__all__: list[str] = [
    "NKT",
    "NKTDLL",
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
    "SuperK",
    "Unit",
    "device_status_callback",
    "port_status_callback",
    "register_status_callback",
]
