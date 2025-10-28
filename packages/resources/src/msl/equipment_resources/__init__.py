"""Custom resources for communicating with equipment."""

from __future__ import annotations

from . import avantes, cmi, electron_dynamics, isotech, mks, nkt
from .aim_tti import MXSeries
from .avantes import AvaSpec
from .cmi import SIA3
from .electron_dynamics import TCSeries
from .energetiq import EQ99
from .greisinger import GMH3000
from .isotech import MilliK
from .mks import PR4000B
from .nkt import NKT

__all__: list[str] = [
    "EQ99",
    "GMH3000",
    "NKT",
    "PR4000B",
    "SIA3",
    "AvaSpec",
    "MXSeries",
    "MilliK",
    "TCSeries",
    "avantes",
    "cmi",
    "electron_dynamics",
    "isotech",
    "mks",
    "nkt",
]
