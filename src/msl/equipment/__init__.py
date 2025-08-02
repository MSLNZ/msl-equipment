"""Manage and interface with equipment in the laboratory."""

from __future__ import annotations

from .__about__ import __version__, version_tuple
from .schema import Accessories, Alteration, Financial, Firmware, QualityManual, Status

__all__: list[str] = [
    "Accessories",
    "Alteration",
    "Financial",
    "Firmware",
    "QualityManual",
    "Status",
    "__version__",
    "version_tuple",
]
