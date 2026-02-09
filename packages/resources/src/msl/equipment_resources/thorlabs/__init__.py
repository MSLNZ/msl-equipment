"""Resources for equipment from [Thorlabs](https://www.thorlabs.com/)."""

from __future__ import annotations

from .fwxx2c import FWxx2C
from .k10cr import K10CR

__all__: list[str] = [
    "K10CR",
    "FWxx2C",
]
