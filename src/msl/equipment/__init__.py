"""Manage and interface with equipment in the laboratory."""

from __future__ import annotations

from .__about__ import __version__, version_tuple
from .schema import (
    AcceptanceCriteria,
    Accessories,
    Alteration,
    CompletedTask,
    Conditions,
    Equipment,
    Financial,
    Firmware,
    Maintenance,
    Measurand,
    PlannedTask,
    QualityManual,
    ReferenceMaterials,
    Specifications,
    SpecifiedRequirements,
    Status,
)

__all__: list[str] = [
    "AcceptanceCriteria",
    "Accessories",
    "Alteration",
    "CompletedTask",
    "Conditions",
    "Equipment",
    "Financial",
    "Firmware",
    "Maintenance",
    "Measurand",
    "PlannedTask",
    "QualityManual",
    "ReferenceMaterials",
    "Specifications",
    "SpecifiedRequirements",
    "Status",
    "__version__",
    "version_tuple",
]
