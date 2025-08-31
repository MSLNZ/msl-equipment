"""Constants used by `msl-equipment`."""

from __future__ import annotations

import enum
import re
import sys

import serial

CR = b"\r"
LF = b"\n"

IS_LINUX: bool = sys.platform == "linux"
IS_WINDOWS: bool = sys.platform == "win32"

REGEX_SDK = re.compile(r"SDK::(?P<path>.+)", flags=re.IGNORECASE)

REGEX_SERIAL = re.compile(r"(COM|ASRL|ASRLCOM)((?P<dev>/dev/[^\s:]+)|(?P<number>\d+))", flags=re.IGNORECASE)

REGEX_SOCKET = re.compile(
    r"(?P<prefix>SOCKET|TCP|UDP|TCPIP\d*)::(?P<host>[^\s:]+)::(?P<port>\d+)(?P<suffix>::SOCKET)?", flags=re.IGNORECASE
)

# TCPIP[board]::host address[::LAN device name][::INSTR]
REGEX_TCPIP = re.compile(
    r"TCPIP(?P<board>\d*)::(?P<host>[^\s:]+)(::(?P<name>([^\s:]+\d+(\[.+])?)))?(::INSTR)?$", flags=re.IGNORECASE
)

REGEX_PROLOGIX = re.compile(
    r"Prologix::(?P<name>[^\s:]+)(?P<port>::1234)?(::GPIB\d*)?::(?P<pad>\d+)(::(?P<sad>\d+))?", flags=re.IGNORECASE
)

REGEX_ZMQ = re.compile(r"ZMQ::(?P<host>[^\s:]+)::(?P<port>\d+)", flags=re.IGNORECASE)

REGEX_GPIB = re.compile(
    r"(?P<board>\d{0,2})(::((?P<pad>\d+)|(?P<name>[^\s:]+)))?(::(?P<sad>\d+))?", flags=re.IGNORECASE
)


class Backend(enum.IntEnum):
    """The software backend to use for the communication system."""

    UNKNOWN = 0
    MSL = 1
    PyVISA = 2
    NIDAQ = 3


class Interface(enum.IntEnum):
    """The interface to use for the communication system.

    Only used if [Backend.MSL][msl.equipment.constants.Backend.MSL] is chosen as the backend.
    """

    NONE = 0
    SDK = 1
    SERIAL = 2
    SOCKET = 3
    PROLOGIX = 4
    TCPIP_VXI11 = 5
    TCPIP_HISLIP = 6
    ZMQ = 7
    GPIB = 8


class Parity(enum.Enum):
    """The parity type to use for Serial communication."""

    NONE = serial.PARITY_NONE
    ODD = serial.PARITY_ODD
    EVEN = serial.PARITY_EVEN
    MARK = serial.PARITY_MARK
    SPACE = serial.PARITY_SPACE


class StopBits(enum.Enum):
    """The number of stop bits to use for Serial communication."""

    ONE = serial.STOPBITS_ONE
    ONE_POINT_FIVE = serial.STOPBITS_ONE_POINT_FIVE
    TWO = serial.STOPBITS_TWO


class DataBits(enum.IntEnum):
    """The number of data bits to use for Serial communication."""

    FIVE = serial.FIVEBITS
    SIX = serial.SIXBITS
    SEVEN = serial.SEVENBITS
    EIGHT = serial.EIGHTBITS
