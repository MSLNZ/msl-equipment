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


class RENMode(enum.IntEnum):
    """The mode of the GPIB Remote Enable (REN) line and optionally the remote/local state.

    Attributes:
        DEASSERT (int): Deassert REN line, `0`
        ASSERT (int): Assert REN line, `1`
        DEASSERT_GTL (int): Deassert REN line and send the Go To Local (GTL) command, `2`
        ASSERT_ADDRESS (int): Assert REN line and address device, `3`
        ASSERT_LLO (int): Send local lockout (LLO) to any device that is addressed to listen, `4`
        ASSERT_ADDRESS_LLO (int): Address this device and send the LLO command, putting it in the
            Remote with Lockout State (RWLS), `5`
        ADDRESS_GTL (int): Send the GTL command to this device, `6`
    """

    # https://www.ni.com/docs/en-US/bundle/labview-api-ref/page/functions/visa-gpib-control-ren.html

    DEASSERT = 0
    ASSERT = 1
    DEASSERT_GTL = 2
    ASSERT_ADDRESS = 3
    ASSERT_LLO = 4
    ASSERT_ADDRESS_LLO = 5
    ADDRESS_GTL = 6


class ATNState(enum.IntEnum):
    """The state of the GPIB Attention (ATN) line.

    Attributes:
        DEASSERT (int): Deassert ATN line, `0`
        ASSERT (int): Assert ATN line and take control synchronously without corrupting transferred data, `1`
        DEASSERT_HANDSHAKE (int): Deassert ATN line and enter shadow handshake mode, `2`
        ASSERT_IMMEDIATE (int): Assert ATN line and take control asynchronously and immediately,
            without regard for any data transfer currently in progress, `3`
    """

    # https://www.ni.com/docs/en-US/bundle/labview-api-ref/page/functions/visa-gpib-control-atn.html

    DEASSERT = 0
    ASSERT = 1
    DEASSERT_HANDSHAKE = 2
    ASSERT_IMMEDIATE = 3
