"""Resources for equipment from [Thorlabs](https://www.thorlabs.com/){:target="_blank"}."""

from __future__ import annotations

from .bsc import BSC
from .fwxx2c import FWxx2C
from .k10cr import K10CR
from .kdc import KDC
from .ksc import KSC
from .kst import KST
from .lts import LTS
from .mff import MFF

__all__: list[str] = [
    "BSC",
    "K10CR",
    "KDC",
    "KSC",
    "KST",
    "LTS",
    "MFF",
    "FWxx2C",
]
