"""Resources for equipment from [OptoSigma](https://jp.optosigma.com/en_jp/)."""

from __future__ import annotations

from .shot702 import SHOT702, Mode, Speed, State, Status

__all__: list[str] = [
    "SHOT702",
    "Mode",
    "Speed",
    "State",
    "Status",
]
