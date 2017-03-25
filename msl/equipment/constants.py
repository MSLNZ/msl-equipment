"""
MSL-Equipment package constants.
"""
from enum import IntEnum

MSL_INTERFACE_ALIASES = {
    'ASRL': ('COM', 'RS', 'LPT', ),
    'TCPIP': ('ENET', 'ETHERNET', 'LAN', ),
}


class Backend(IntEnum):
    """
    The software backend to use for the communication system.
    """
    UNKNOWN = 0
    MSL = 1
    PyVISA = 2


class MSLInterface(IntEnum):
    """
    The interface to use for the communication system that transfers data between
    a computer and the equipment. Only used if
    :data:`Backend.MSL <msl.equipment.constants.Backend.MSL>` is chosen
    as the communication system.
    """
    NONE = 0
    ASRL = 1
    GPIB = 2
    USB = 3
    PXI = 4
    VXI = 5
    TCPIP = 6
    LIB = 7
    TCPIP_ASRL = 8
    TCPIP_GPIB = 9
    USB_ASRL = 10
    USB_GPIB = 11
    PROLOGIX_ENET = 12
    PROLOGIX_USB = 13


class Parity(IntEnum):
    """
    The parity type to use for Serial communication.
    """
    NONE = 0
    ODD = 1
    EVEN = 2
    MARK = 3
    SPACE = 4


class FlowControl(IntEnum):
    """
    The type of flow control (handshaking) to use for Serial communication.
    """
    NONE = 0
    XON_XOFF = 1
    RTS_CTS = 2
    DTR_DSR = 3


class StopBits(IntEnum):
    """
    The number of stop bits to use for Serial communication.
    """
    ONE = 10
    ONE_POINT_FIVE = 15
    TWO = 20


class DataBits(IntEnum):
    """
    The number of data bits to use for Serial communication.
    """
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
