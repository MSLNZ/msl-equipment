"""Custom resources for communicating with equipment."""

from __future__ import annotations

from . import avantes, cmi
from .aim_tti import MXSeries
from .avantes import AvaSpec
from .cmi import SIA3

__all__: list[str] = [
    "SIA3",
    "AvaSpec",
    "MXSeries",
    "avantes",
    "cmi",

]
