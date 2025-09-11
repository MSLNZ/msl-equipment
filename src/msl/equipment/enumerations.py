"""Enumeration constants."""

from __future__ import annotations

import enum
import re
import sys

import serial

IS_LINUX: bool = sys.platform == "linux"
IS_WINDOWS: bool = sys.platform == "win32"

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


class Backend(enum.Enum):
    """The backend library to use for communication with the equipment.

    Attributes:
        MSL (str): "MSL"
        PyVISA (str): "PyVISA"
        NIDAQ (str): "NIDAQ"
    """

    MSL = "MSL"
    PyVISA = "PyVISA"
    NIDAQ = "NIDAQ"


class Parity(enum.Enum):
    """The parity type to use for Serial communication.

    Attributes:
        NONE (str): "N"
        ODD (str): "O"
        EVEN (str): "E"
        MARK (str): "M""
        SPACE (str): "S"
    """

    NONE = serial.PARITY_NONE
    ODD = serial.PARITY_ODD
    EVEN = serial.PARITY_EVEN
    MARK = serial.PARITY_MARK
    SPACE = serial.PARITY_SPACE


class StopBits(enum.Enum):
    """The number of stop bits to use for Serial communication.

    Attributes:
        ONE (int): 1
        ONE_POINT_FIVE (float): 1.5
        TWO (int): 2
    """

    ONE = serial.STOPBITS_ONE
    ONE_POINT_FIVE = serial.STOPBITS_ONE_POINT_FIVE
    TWO = serial.STOPBITS_TWO


class DataBits(enum.IntEnum):
    """The number of data bits to use for Serial communication.

    Attributes:
        FIVE (int): 5
        SIX (int): 6
        SEVEN (int): 7
        EIGHT (int): 8
    """

    FIVE = serial.FIVEBITS
    SIX = serial.SIXBITS
    SEVEN = serial.SEVENBITS
    EIGHT = serial.EIGHTBITS
