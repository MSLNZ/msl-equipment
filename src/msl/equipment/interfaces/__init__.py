"""Interfaces for computer control."""

from __future__ import annotations

from .gpib import GPIB
from .message_based import MessageBased, MSLTimeoutError
from .nidaq import NIDAQ
from .pyvisa import PyVISA
from .sdk import SDK
from .socket import Socket
from .zeromq import ZeroMQ

__all__: list[str] = [
    "GPIB",
    "NIDAQ",
    "SDK",
    "MSLTimeoutError",
    "MessageBased",
    "PyVISA",
    "Socket",
    "ZeroMQ",
]
