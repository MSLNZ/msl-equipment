"""Custom resources for communicating with equipment."""

from __future__ import annotations

from . import avantes
from .aim_tti import MXSeries
from .avantes import AvaSpec

__all__: list[str] = [
    "AvaSpec",
    "MXSeries",
    "avantes",
]
