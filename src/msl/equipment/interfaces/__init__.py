"""Interfaces for computer control."""

from __future__ import annotations

from .ftdi import FTDI
from .gpib import GPIB
from .hislip import HiSLIP
from .message import Message, MSLConnectionError, MSLTimeoutError, MultiInterface
from .modbus import Modbus
from .nidaq import NIDAQ
from .prologix import Prologix
from .pyvisa import PyVISA
from .sdk import SDK
from .serial import Serial
from .socket import Socket
from .usb import USB
from .usbtmc import USBTMC
from .vxi11 import VXI11
from .zeromq import ZeroMQ, ZeroMQServer

__all__: list[str] = [
    "FTDI",
    "GPIB",
    "NIDAQ",
    "SDK",
    "USB",
    "USBTMC",
    "VXI11",
    "HiSLIP",
    "MSLConnectionError",
    "MSLTimeoutError",
    "Message",
    "Modbus",
    "MultiInterface",
    "Prologix",
    "PyVISA",
    "Serial",
    "Socket",
    "ZeroMQ",
    "ZeroMQServer",
]
