"""Deprecated classes."""

from __future__ import annotations

import warnings
from typing import Any

from .schema import Connection, Equipment


class _Warn:
    show: bool = True

    @staticmethod
    def warn() -> None:
        msg = (
            "The EquipmentRecord and ConnectionRecord classes are deprecated and will be removed in a future release. "
            "Replace `EquipmentRecord` with `Equipment` and replace `ConnectionRecord` with `Connection`."
        )
        warnings.warn(msg, FutureWarning, stacklevel=3)
        _Warn.show = False


def EquipmentRecord(**kwargs: Any) -> Equipment:  # noqa: ANN401, N802
    """Deprecated. Replace `EquipmentRecord` with `Equipment`."""
    if _Warn.show:
        _Warn.warn()
    return Equipment(**kwargs)


def ConnectionRecord(**kwargs: Any) -> Connection:  # noqa: ANN401, N802
    """Deprecated. Replace `ConnectionRecord` with `Connection`."""
    if _Warn.show:
        _Warn.warn()
    return Connection(**kwargs)
