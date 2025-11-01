"""Wrapper around the `ARC_Instrument.dll` SDK from Princeton Instruments."""

from __future__ import annotations

from .arc_instrument import PrincetonInstruments

__all__: list[str] = [
    "PrincetonInstruments",
]
