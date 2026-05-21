"""Custom type annotations."""

from __future__ import annotations

from ctypes import _Pointer, c_int32  # pyright: ignore[reportPrivateUsage]
from typing import Callable

AvaSpecCallback = Callable[[_Pointer[c_int32], _Pointer[c_int32]], None]
"""Callback handler for the [AvaSpec][msl.equipment_resources.avantes.avaspec.AvaSpec] SDK."""

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
