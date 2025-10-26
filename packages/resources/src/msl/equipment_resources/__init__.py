"""Custom resources for communicating with equipment."""

from __future__ import annotations

from . import avantes, cmi, electron_dynamics, isotech
from .aim_tti import MXSeries
from .avantes import AvaSpec
from .cmi import SIA3
from .electron_dynamics import TCSeries
from .energetiq import EQ99
from .greisinger import GMH3000
from .isotech import MilliK

__all__: list[str] = [
    "EQ99",
    "GMH3000",
    "SIA3",
    "AvaSpec",
    "MXSeries",
    "MilliK",
    "TCSeries",
    "avantes",
    "cmi",
    "electron_dynamics",
    "isotech",
]
