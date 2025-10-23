"""Custom resources for communicating with equipment."""

from __future__ import annotations

from . import avantes, cmi, electron_dynamics
from .aim_tti import MXSeries
from .avantes import AvaSpec
from .cmi import SIA3
from .electron_dynamics import TCSeries
from .energetiq import EQ99

__all__: list[str] = [
    "EQ99",
    "SIA3",
    "AvaSpec",
    "MXSeries",
    "TCSeries",
    "avantes",
    "cmi",
    "electron_dynamics",
]
