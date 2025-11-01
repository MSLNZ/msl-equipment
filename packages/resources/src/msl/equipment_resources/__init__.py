"""Custom resources for communicating with equipment."""

from __future__ import annotations

from . import avantes, cmi, electron_dynamics, isotech, mks, nkt, optosigma
from .aim_tti import MXSeries
from .avantes import AvaSpec
from .cmi import SIA3
from .electron_dynamics import TCSeries
from .energetiq import EQ99
from .greisinger import GMH3000
from .isotech import MilliK
from .mks import PR4000B
from .nkt import NKT
from .omega import ITHX
from .optosigma import SHOT702
from .princeton_instruments import PrincetonInstruments
from .raicol import RaicolTEC

__all__: list[str] = [
    "EQ99",
    "GMH3000",
    "ITHX",
    "NKT",
    "PR4000B",
    "SHOT702",
    "SIA3",
    "AvaSpec",
    "MXSeries",
    "MilliK",
    "PrincetonInstruments",
    "RaicolTEC",
    "TCSeries",
    "avantes",
    "cmi",
    "electron_dynamics",
    "isotech",
    "mks",
    "nkt",
    "optosigma",
]
