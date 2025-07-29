"""Manage and interface with equipment in the laboratory."""

from __future__ import annotations

from .__about__ import __version__, version_tuple
from .schema import Alteration

__all__: list[str] = [
    "Alteration",
    "__version__",
    "version_tuple",
]
