"""Custom type annotations."""

from __future__ import annotations

from ctypes import _Pointer, c_int32  # pyright: ignore[reportPrivateUsage]
from typing import Callable

AvaSpecCallback = Callable[[_Pointer[c_int32], _Pointer[c_int32]], None]
"""Callback handler for the [AvaSpec][msl.equipment_resources.avantes.avaspec.AvaSpec] SDK."""

HighFinesseCallback = Callable[[int, int, int, float, int], None]
"""Callback handler for the [HighFinesse][msl.equipment_resources.high_finesse.HighFinesse] SDK.

Args:
    serial (int): The serial number of the device that called the callback.
    mode (int): Indicates the meaning of the `data1` and `data2` parameters. See the
        `CallbackProcEx` function in the HighFinesse manual for more information. For example,
        `mode=42` corresponds to `cmiWavelength1` and `mode=14` corresponds to `cmiTemperature`.
    data1 (int): Interpretation depends on `mode` (see manual).
    data2 (float): Interpretation depends on `mode` (see manual).
    switcher_timestamp (int): Only applicable if `mode=203` (`cmiSwitcherChannel`), in which
        case this value is the switching timestamp. For all other `mode` values this is `0`.
"""

NKTPortStatusCallback = Callable[[str, int, int, int, int], None]
"""Callback handler for the [NKTDLL][msl.equipment_resources.nkt.nktpdll.NKTDLL] SDK when a port changes."""

NKTDeviceStatusCallback = Callable[[str, int, int, int, int], None]
"""Callback handler for the [NKTDLL][msl.equipment_resources.nkt.nktpdll.NKTDLL] SDK when a device changes."""

NKTRegisterStatusCallback = Callable[[str, int, int, int, int, int, int], None]
"""Callback handler for the [NKTDLL][msl.equipment_resources.nkt.nktpdll.NKTDLL] SDK when a register changes."""

PicoTechBlockReadyCallback = Callable[[int, int, None], None]
"""Block-ready callback handler for the [PicoScope][msl.equipment_resources.picotech.picoscope.PicoScope] SDK."""

PicoTechDataReadyCallback = Callable[[int, int, int, int, None], None]
"""Data-ready callback handler for the [PicoScope][msl.equipment_resources.picotech.picoscope.PicoScope] SDK."""

PicoTechStreamingReadyCallback = Callable[[int, int, int, int, int, int, int, None], None]
"""Streaming-ready callback handler for the [PicoScope][msl.equipment_resources.picotech.picoscope.PicoScope] SDK."""
