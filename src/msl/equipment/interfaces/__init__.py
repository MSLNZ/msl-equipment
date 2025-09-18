"""Interfaces for computer control."""

from __future__ import annotations

from .gpib import GPIB
from .message_based import MessageBased, MSLTimeoutError
from .nidaq import NIDAQ
from .pyvisa import PyVISA
from .sdk import SDK
from .serial import Serial
from .socket import Socket
from .vxi11 import VXI11
from .zeromq import ZeroMQ

__all__: list[str] = [
    "GPIB",
    "NIDAQ",
    "SDK",
    "VXI11",
    "MSLTimeoutError",
    "MessageBased",
    "PyVISA",
    "Serial",
    "Socket",
    "ZeroMQ",
]
