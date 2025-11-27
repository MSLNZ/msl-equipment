"""Custom resources for communicating with equipment."""

from __future__ import annotations

from . import avantes, cmi, electron_dynamics, isotech, mks, nkt, optosigma
from .aim_tti import MXSeries
from .avantes import AvaSpec
from .cmi import SIA3
from .dataray import WinCamD
from .electron_dynamics import TCSeries
from .energetiq import EQ99
from .greisinger import GMH3000
from .isotech import MilliK
from .mks import PR4000B
from .nkt import NKT
from .omega import ITHX
from .optosigma import SHOT702
from .optronic_labs import OL756, OLxxA
from .princeton_instruments import PrincetonInstruments
from .raicol import RaicolTEC
from .thorlabs import FWxx2C
from .vaisala import PTB330, PTU300

__all__: list[str] = [
    "EQ99",
    "GMH3000",
    "ITHX",
    "NKT",
    "OL756",
    "PR4000B",
    "PTB330",
    "PTU300",
    "SHOT702",
    "SIA3",
    "AvaSpec",
    "FWxx2C",
    "MXSeries",
    "MilliK",
    "OLxxA",
    "PrincetonInstruments",
    "RaicolTEC",
    "TCSeries",
    "WinCamD",
    "avantes",
    "cmi",
    "electron_dynamics",
    "isotech",
    "mks",
    "nkt",
    "optosigma",
]
