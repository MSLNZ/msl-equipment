"""Enumeration constants."""

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
    """The software backend to use for communication.

    Attributes:
        MSL (int): 0
        PyVISA (int): 1
        NIDAQ (int): 2
    """

    MSL = 0
    PyVISA = 1
    NIDAQ = 2


class Interface(enum.IntEnum):
    """The interface to use for the communication system.

    Only used if `MSL` is chosen as the [Backend][msl.equipment.constants.Backend].

    Attributes:
        UNKNOWN (int): 0
        SDK (int): 1
        SERIAL (int): 2
        SOCKET (int): 3
        PROLOGIX (int): 4
        TCPIP_VXI11 (int): 5
        TCPIP_HISLIP (int): 6
        ZMQ (int): 7
        GPIB (int): 8
    """

    UNKNOWN = 0
    SDK = 1
    SERIAL = 2
    SOCKET = 3
    PROLOGIX = 4
    TCPIP_VXI11 = 5
    TCPIP_HISLIP = 6
    ZMQ = 7
    GPIB = 8


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
