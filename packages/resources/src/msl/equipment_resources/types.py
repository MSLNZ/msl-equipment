"""Custom type annotations."""

from __future__ import annotations

from ctypes import _Pointer, c_int32  # pyright: ignore[reportPrivateUsage]
from typing import Callable

AvaSpecCallback = Callable[[_Pointer[c_int32], _Pointer[c_int32]], None]
"""Callback handler for the [AvaSpec][msl.equipment_resources.avantes.avaspec.AvaSpec] SDK."""

NKTPortStatusCallback = Callable[[str, int, int, int, int], None]
"""Callback handler for the [NKT][msl.equipment_resources.nkt.nktpdll.NKT] SDK when the status of a port changes."""

NKTDeviceStatusCallback = Callable[[str, int, int, int, int], None]
"""Callback handler for the [NKT][msl.equipment_resources.nkt.nktpdll.NKT] SDK when the status of a device changes."""

NKTRegisterStatusCallback = Callable[[str, int, int, int, int, int, int], None]
"""Callback handler for the [NKT][msl.equipment_resources.nkt.nktpdll.NKT] SDK when the status of a register changes."""
