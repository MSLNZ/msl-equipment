"""Enumeration constants."""

from __future__ import annotations

import enum

import serial


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
        MARK (str): "M"
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
