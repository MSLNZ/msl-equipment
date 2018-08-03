"""
MSL-Equipment constants.
"""
import enum

import serial


MSL_INTERFACE_ALIASES = {
    'SERIAL': ('ASRLCOM', 'ASRL', 'COM', 'LPT'),
    'SOCKET': ('ENET', 'ETHERNET', 'LAN', 'TCP', 'UDP'),
}


class Backend(enum.IntEnum):
    """
    The software backend to use for the communication system.
    """
    UNKNOWN = 0
    MSL = 1
    PyVISA = 2


class MSLInterface(enum.IntEnum):
    """
    The interface to use for the communication system that transfers data between
    a computer and the equipment. Only used if
    :data:`Backend.MSL <msl.equipment.constants.Backend.MSL>` is chosen
    as the communication system.
    """
    NONE = 0
    SDK = 1
    SERIAL = 2
    SOCKET = 3
    # USB = 4
    # GPIB = 5
    # PXI = 6
    # VXI = 7
    # TCPIP_ASRL = 8
    # TCPIP_GPIB = 9
    # USB_GPIB = 10
    # PROLOGIX_ENET = 11
    # PROLOGIX_USB = 12


class Parity(enum.Enum):
    """
    The parity type to use for Serial communication.
    """
    NONE = serial.PARITY_NONE
    ODD = serial.PARITY_ODD
    EVEN = serial.PARITY_EVEN
    MARK = serial.PARITY_MARK
    SPACE = serial.PARITY_SPACE


class StopBits(enum.Enum):
    """
    The number of stop bits to use for Serial communication.
    """
    ONE = serial.STOPBITS_ONE
    ONE_POINT_FIVE = serial.STOPBITS_ONE_POINT_FIVE
    TWO = serial.STOPBITS_TWO


class DataBits(enum.IntEnum):
    """
    The number of data bits to use for Serial communication.
    """
    FIVE = serial.FIVEBITS
    SIX = serial.SIXBITS
    SEVEN = serial.SEVENBITS
    EIGHT = serial.EIGHTBITS
