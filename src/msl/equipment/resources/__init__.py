"""Import the `msl-equipment-resources` package (if installed)."""

from __future__ import annotations

import contextlib

with contextlib.suppress(ImportError):
    from msl.equipment_resources import *  # pyright: ignore[reportWildcardImportFromLibrary]  # noqa: F403
