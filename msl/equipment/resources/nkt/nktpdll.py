"""
Wrapper around the ``NKTPDLL.dll`` SDK from NKT Photonics.

The wrapper was written using v2.1.2.766 of the SDK.
"""
import os
from ctypes import *
from enum import IntEnum

from msl.loadlib import LoadLibrary

from msl.equipment.connection import Connection
from msl.equipment.resources import register
from msl.equipment.exceptions import NKTError

_PATH = os.environ.get('NKTP_SDK_PATH')
if _PATH is not None:
    if sizeof(c_void_p) == 4:
        _PATH += '/NKTPDLL/x86/NKTPDLL.dll'
    else:
        _PATH += '/NKTPDLL/x64/NKTPDLL.dll'
else:
    _PATH = 'NKTPDLL.dll'


PortStatusCallback = CFUNCTYPE(None, c_char_p, c_ubyte, c_ubyte, c_ubyte, c_ubyte)
"""Use as a decorator for a callback function when a port status changes."""

DeviceStatusCallback = CFUNCTYPE(None, c_char_p, c_ubyte, c_ubyte, c_ubyte, c_void_p)
"""Use as a decorator for a callback function when a device status changes."""

RegisterStatusCallback = CFUNCTYPE(None, c_char_p, c_ubyte, c_ubyte, c_ubyte, c_ubyte, c_ubyte, c_void_p)
"""Use as a decorator for a callback function when a register status changes."""


class DateTimeType(Structure):
    """The DateTimeType struct (24 hour format)."""
    _pack_ = 1
    _fields_ = [
        ('Sec', c_uint8),    # Seconds
        ('Min', c_uint8),    # Minutes
        ('Hour', c_uint8),   # Hours
        ('Day', c_uint8),    # Days
        ('Month', c_uint8),  # Months
        ('Year', c_uint8),   # Years
    ]


class ParameterSetType(Structure):
    """The ParameterSet struct.

    This is how calculation on parameter sets is done internally by modules:

    DAC_value = (value * (X/Y)) + Offset

    where, value is either ParameterSetType::StartVal or ParameterSetType::FactoryVal

    value = (ADC_value * (X/Y)) + Offset

    where, value often is available via another measurement register.
    """
    _pack_ = 1
    _fields_ = [
        ('Unit', c_uint8),          # Unit type as defined in tParamSetUnitTypes
        ('ErrorHandler', c_uint8),  # Warning/Error handler not used
        ('StartVal', c_ushort),     # Setpoint for Settings parameter set, unused in Measurement parameter sets
        ('FactoryVal', c_ushort),   # Factory Setpoint for Settings parameter set, unused in Measurement parameter sets
        ('ULimit', c_ushort),       # Upper limit
        ('LLimit', c_ushort),       # Lower limit
        ('Numerator', c_short),     # Numerator(X) for calculation
        ('Denominator', c_short),   # Denominator(Y) for calculation
        ('Offset', c_short)         # Offset for calculation
    ]


class DeviceModeTypes(IntEnum):
    """The DeviceModeTypes enum."""
    DevModeDisabled = 0     # The device is disabled. Not being polled and serviced.
    DevModeAnalyzeInit = 1  # The analyze cycle has been started for the device.
    DevModeAnalyze = 2      # The analyze cycle is in progress. All default registers being read to determine its state.
    DevModeNormal = 3       # The analyze cycle has completed and the device is ready.
    DevModeLogDownload = 4  # A log is being downloaded from the device.
    DevModeError = 5        # The device is in an error state.
    DevModeTimeout = 6      # The connection to the device has been lost.
    DevModeUpload = 7       # The device is in upload mode and can not be used normally.


class DeviceStatusTypes(IntEnum):
    """The DeviceStatusTypes enum."""
    DeviceModeChanged = 0          # devData contains 1 unsigned byte DeviceModeTypes
    DeviceLiveChanged = 1          # devData contains 1 unsigned byte, 0=live off, 1=live on.
    DeviceTypeChanged = 2          # devData contains 1 unsigned byte with DeviceType (module type).
    DevicePartNumberChanged = 3    # devData contains a zero terminated string with part number.
    DevicePCBVersionChanged = 4    # devData contains 1 unsigned byte with PCB version number.
    DeviceStatusBitsChanged = 5    # devData contains 1 unsigned long with status bits.
    DeviceErrorCodeChanged = 6     # devData contains 1 unsigned short with error code.
    DeviceBlVerChanged = 7         # devData contains a zero terminated string with Bootloader version.
    DeviceFwVerChanged = 8         # devData contains a zero terminated string with Firmware version.
    DeviceModuleSerialChanged = 9  # devData contains a zero terminated string with Module serial number.
    DevicePCBSerialChanged = 10    # devData contains a zero terminated string with PCB serial number.
    DeviceSysTypeChanged = 11      # devData contains 1 unsigned byte with SystemType (system type).


class ParamSetUnitTypes(IntEnum):
    """The ParamSetUnitTypes enum"""
    UnitNone = 0       # none/unknown
    UnitmV = 1         # mV
    UnitV = 2          # V
    UnituA = 3         # uA
    UnitmA = 4         # mA
    UnitA = 5          # A
    UnituW = 6         # uW
    UnitcmW = 7        # mW/100
    UnitdmW = 8        # mW/10
    UnitmW = 9         # mW
    UnitW = 10         # W
    UnitmC = 11        # degC/1000
    UnitcC = 12        # degC/100
    UnitdC = 13        # degC/10
    Unitpm = 14        # pm
    Unitdnm = 15       # nm/10
    Unitnm = 16        # nm
    UnitPerCent = 17   # Percent
    UnitPerMille = 18  # Per mile
    UnitcmA = 19       # mA/100
    UnitdmA = 20       # mA/10
    UnitRPM = 21       # RPM
    UnitdBm = 22       # dBm
    UnitcBm = 23       # dBm/10
    UnitmBm = 24       # dBm/100
    UnitdB = 25        # dB
    UnitcB = 26        # dB/10
    UnitmB = 27        # dB/100
    Unitdpm = 28       # pm/10
    UnitcV = 29        # V/100
    UnitdV = 30        # V/10
    Unitlm = 31        # lm (lumen)
    Unitdlm = 32       # lm/10
    Unitclm = 33       # lm/100
    Unitmlm = 34       # lm/1000


class RegisterPriorityTypes(IntEnum):
    """The RegisterPriorityTypes enum."""
    RegPriority_Low = 0    # The register is polled with low priority.
    RegPriority_High = 1   # The register is polled with high priority.


class RegisterDataTypes(IntEnum):
    """The RegisterDataTypes enum."""
    RegData_Unknown = 0    # Unknown/Undefined data type.
    RegData_Mixed = 1      # Mixed content data type.
    RegData_U8 = 2         # 8 bit unsigned data type (unsigned char).
    RegData_S8 = 3         # 8 bit signed data type (char).
    RegData_U16 = 4        # 16 bit unsigned data type (unsigned short).
    RegData_S16 = 5        # 16 bit signed data type (short).
    RegData_U32 = 6        # 32 bit unsigned data type (unsigned long).
    RegData_S32 = 7        # 32 bit signed data type (long).
    RegData_F32 = 8        # 32 bit floating point data type (float).
    RegData_U64 = 9        # 64 bit unsigned data type (unsigned long long).
    RegData_S64 = 10       # 64 bit signed data type (long long).
    RegData_F64 = 11       # 64 bit floating point data type (double).
    RegData_Ascii = 12     # Zero terminated ascii string data type.
    RegData_Paramset = 13  # Parameterset data type. ::ParameterSetType
    RegData_B8 = 14        # 8 bit binary data type (unsigned char).
    RegData_H8 = 15        # 8 bit hexadecimal data type (unsigned char).
    RegData_B16 = 16       # 16 bit binary data type (unsigned short).
    RegData_H16 = 17       # 16 bit hexadecimal data type (unsigned short).
    RegData_B32 = 18       # 32 bit binary data type (unsigned long).
    RegData_H32 = 19       # 32 bit hexadecimal data type (unsigned long).
    RegData_B64 = 20       # 64 bit binary data type (unsigned long long).
    RegData_H64 = 21       # 64 bit hexadecimal data type (unsigned long long).
    RegData_DateTime = 22  # Datetime data type. ::DateTimeType


class RegisterStatusTypes(IntEnum):
    """The RegisterStatusTypes enum."""
    RegSuccess = 0     # Register operation was successful.
    RegBusy = 1        # Register operation resulted in a busy.
    RegNacked = 2      # Register operation resulted in a nack, seems to be non existing register.
    RegCRCErr = 3      # Register operation resulted in a CRC error.
    RegTimeout = 4     # Register operation resulted in a timeout.
    RegComError = 5    # Register operation resulted in a COM error. Out of sync. or garbage error.


class PortStatusTypes(IntEnum):
    """The PortStatusTypes enum"""
    PortStatusUnknown = 0     # Unknown status.
    PortOpening = 1           # The port is opening.
    PortOpened = 2            # The port is now open.
    PortOpenFail = 3          # The port open failed.
    PortScanStarted = 4       # The port scanning is started.
    PortScanProgress = 5      # The port scanning progress.
    PortScanDeviceFound = 6   # The port scan found a device.
    PortScanEnded = 7         # The port scanning ended.
    PortClosing = 8           # The port is closing.
    PortClosed = 9            # The port is now closed.
    PortReady = 10            # The port is open and ready.


@register(manufacturer=r'^NKT')
class NKT(Connection):

    _SDK = None

    RegisterStatusCallback = RegisterStatusCallback
    PortStatusCallback = PortStatusCallback
    DeviceStatusCallback = DeviceStatusCallback
    DeviceModeTypes = DeviceModeTypes
    DeviceStatusTypes = DeviceStatusTypes
    ParamSetUnitTypes = ParamSetUnitTypes
    RegisterPriorityTypes = RegisterPriorityTypes
    RegisterDataTypes = RegisterDataTypes
    RegisterStatusTypes = RegisterStatusTypes
    PortStatusTypes = PortStatusTypes

    def __init__(self, record):
        """Wrapper around the ``NKTPDLL.dll`` SDK from NKT Photonics.

        The :attr:`~msl.equipment.record_types.ConnectionRecord.properties`
        for a NKT connection supports the following key-value pairs in the
        :ref:`connections-database`::

            'sdk_path': str, The path to the SDK [default: 'NKTPDLL.dll']
            'open_port': bool, Whether to automatically open the port [default: True]
            'auto': bool, Whether to open the port with bus scanning [default: True]
            'live': bool, Whether to open the port in live mode [default: True]

        Do not instantiate this class directly. Use the :meth:`~.EquipmentRecord.connect`
        method to connect to the equipment.

        Parameters
        ----------
        record : :class:`~.EquipmentRecord`
            A record from an :ref:`equipment-database`.
        """
        self._PORTNAME = record.connection.address.encode()
        super(NKT, self).__init__(record)
        self.set_exception_class(NKTError)
        props = record.connection.properties
        self.load_sdk(props.get('sdk_path', _PATH))
        if props.get('open_port', True):
            NKT.open_ports(self._PORTNAME, auto=props.get('auto', True), live=props.get('live', True))
        self.log_debug('Connected to %s', record.connection)

    @staticmethod
    def close_ports(names=None):
        """Close the specified port name(s).

        Parameters
        ----------
        names : :class:`str`, :class:`list` of :class:`str`, optional
            If :data:`None` then close all opened ports. If a :class:`str`
            then the name of a port. Otherwise a :class:`list` of names. Port
            names are case sensitive.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        if names is None:
            names = b''
        elif isinstance(names, (list, tuple)):
            names = b','.join(name.encode() for name in names)
        elif isinstance(names, str):
            names = names.encode()
        NKT._SDK.closePorts(names)

    @staticmethod
    def load_sdk(path=None):
        """Load the SDK.

        Parameters
        ----------
        path : :class:`str`, optional
            The path to ``NKTPDLL.dll``. If not specified then searches for the library.
        """
        if NKT._SDK is not None:
            return

        functions = {
            # Port functions
            'getAllPorts': (
                None, _log_debug,
                [('portnames', POINTER(c_char)),
                 ('maxLen', POINTER(c_ushort))]),
            'getOpenPorts': (
                None, _log_debug,
                [('portnames', POINTER(c_char)),
                 ('maxLen', POINTER(c_ushort))]),
            'pointToPointPortAdd': (
                c_ubyte, _check_p2p_result,
                [('portname', c_char_p),
                 ('hostAddress', c_char_p),
                 ('hostPort', c_ushort),
                 ('clientAddress', c_char_p),
                 ('clientPort', c_ushort),
                 ('protocol', c_ubyte),
                 ('msTimeout', c_ubyte)]),
            'pointToPointPortGet': (
                c_ubyte, _check_p2p_result,
                [('portname', c_char_p),
                 ('hostAddress', POINTER(c_char)),
                 ('hostMaxLen', POINTER(c_ubyte)),
                 ('hostPort', POINTER(c_ushort)),
                 ('clientAddress', POINTER(c_char)),
                 ('clientMaxLen', POINTER(c_ubyte)),
                 ('clientPort', POINTER(c_ushort)),
                 ('protocol', POINTER(c_ubyte)),
                 ('msTimeout', POINTER(c_ubyte))]),
            'pointToPointPortDel': (
                c_ubyte, _check_p2p_result,
                [('portname', c_char_p)]),
            'openPorts': (
                c_ubyte, _check_port_result,
                [('portnames', c_char_p),
                 ('autoMode', c_ubyte),
                 ('liveMode', c_ubyte)]),
            'closePorts': (
                c_ubyte, _check_port_result,
                [('portnames', c_char_p)]),
            'setLegacyBusScanning': (
                None, _log_debug,
                [('legacyScanning', c_ubyte)]),
            'getLegacyBusScanning': (c_ubyte, _log_debug, []),
            'getPortStatus': (
                c_ubyte, _check_port_result,
                [('portname', c_char_p),
                 ('portStatus', POINTER(c_ubyte))]),
            'getPortErrorMsg': (
                c_ubyte, _check_port_result,
                [('portname', c_char_p),
                 ('errorMessage', POINTER(c_char)),
                 ('maxLen', POINTER(c_ushort))]),
            # Dedicated - Register read functions
            'registerRead': (
                c_ubyte, _check_register_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('regId', c_ubyte),
                 ('readData', POINTER(c_char)),
                 ('readSize', POINTER(c_ubyte)),
                 ('index', c_short)]),
            'registerReadU8': (
                c_ubyte, _check_register_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('regId', c_ubyte),
                 ('value', POINTER(c_ubyte)),
                 ('index', c_short)]),
            'registerReadS8': (
                c_ubyte, _check_register_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('regId', c_ubyte),
                 ('value', POINTER(c_byte)),
                 ('index', c_short)]),
            'registerReadU16': (
                c_ubyte, _check_register_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('regId', c_ubyte),
                 ('value', POINTER(c_ushort)),
                 ('index', c_short)]),
            'registerReadS16': (
                c_ubyte, _check_register_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('regId', c_ubyte),
                 ('value', POINTER(c_short)),
                 ('index', c_short)]),
            'registerReadU32': (
                c_ubyte, _check_register_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('regId', c_ubyte),
                 ('value', POINTER(c_ulong)),
                 ('index', c_short)]),
            'registerReadS32': (
                c_ubyte, _check_register_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('regId', c_ubyte),
                 ('value', POINTER(c_long)),
                 ('index', c_short)]),
            'registerReadU64': (
                c_ubyte, _check_register_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('regId', c_ubyte),
                 ('value', POINTER(c_ulonglong)),
                 ('index', c_short)]),
            'registerReadS64': (
                c_ubyte, _check_register_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('regId', c_ubyte),
                 ('value', POINTER(c_longlong)),
                 ('index', c_short)]),
            'registerReadF32': (
                c_ubyte, _check_register_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('regId', c_ubyte),
                 ('value', POINTER(c_float)),
                 ('index', c_short)]),
            'registerReadF64': (
                c_ubyte, _check_register_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('regId', c_ubyte),
                 ('value', POINTER(c_double)),
                 ('index', c_short)]),
            'registerReadAscii': (
                c_ubyte, _check_register_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('regId', c_ubyte),
                 ('readStr', POINTER(c_char)),
                 ('maxLen', POINTER(c_ubyte)),
                 ('index', c_short)]),
            # Dedicated - Register write functions
            'registerWrite': (
                c_ubyte, _check_register_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('regId', c_ubyte),
                 ('writeData', POINTER(c_char)),
                 ('writeSize', c_ubyte),
                 ('index', c_short)]),
            'registerWriteU8': (
                c_ubyte, _check_register_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('regId', c_ubyte),
                 ('value', c_ubyte),
                 ('index', c_short)]),
            'registerWriteS8': (
                c_ubyte, _check_register_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('regId', c_ubyte),
                 ('value', c_byte),
                 ('index', c_short)]),
            'registerWriteU16': (
                c_ubyte, _check_register_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('regId', c_ubyte),
                 ('value', c_ushort),
                 ('index', c_short)]),
            'registerWriteS16': (
                c_ubyte, _check_register_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('regId', c_ubyte),
                 ('value', c_short),
                 ('index', c_short)]),
            'registerWriteU32': (
                c_ubyte, _check_register_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('regId', c_ubyte),
                 ('value', c_ulong),
                 ('index', c_short)]),
            'registerWriteS32': (
                c_ubyte, _check_register_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('regId', c_ubyte),
                 ('value', c_long),
                 ('index', c_short)]),
            'registerWriteU64': (
                c_ubyte, _check_register_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('regId', c_ubyte),
                 ('value', c_ulonglong),
                 ('index', c_short)]),
            'registerWriteS64': (
                c_ubyte, _check_register_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('regId', c_ubyte),
                 ('value', c_longlong),
                 ('index', c_short)]),
            'registerWriteF32': (
                c_ubyte, _check_register_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('regId', c_ubyte),
                 ('value', c_float),
                 ('index', c_short)]),
            'registerWriteF64': (
                c_ubyte, _check_register_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('regId', c_ubyte),
                 ('value', c_double),
                 ('index', c_short)]),
            'registerWriteAscii': (
                c_ubyte, _check_register_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('regId', c_ubyte),
                 ('writeStr', c_char_p),
                 ('writeEOL', c_ubyte),
                 ('index', c_short)]),
            # Dedicated - Register write/read functions (A write immediately followed by a read)
            'registerWriteRead': (
                c_ubyte, _check_register_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('regId', c_ubyte),
                 ('writeData', POINTER(c_char)),
                 ('writeSize', c_ubyte),
                 ('readData', POINTER(c_char)),
                 ('readSize', POINTER(c_ubyte)),
                 ('index', c_short)]),
            'registerWriteReadU8': (
                c_ubyte, _check_register_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('regId', c_ubyte),
                 ('writeValue', c_ubyte),
                 ('readValue', POINTER(c_ubyte)),
                 ('index', c_short)]),
            'registerWriteReadS8': (
                c_ubyte, _check_register_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('regId', c_ubyte),
                 ('writeValue', c_byte),
                 ('readValue', POINTER(c_byte)),
                 ('index', c_short)]),
            'registerWriteReadU16': (
                c_ubyte, _check_register_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('regId', c_ubyte),
                 ('writeValue', c_ushort),
                 ('readValue', POINTER(c_ushort)),
                 ('index', c_short)]),
            'registerWriteReadS16': (
                c_ubyte, _check_register_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('regId', c_ubyte),
                 ('writeValue', c_short),
                 ('readValue', POINTER(c_short)),
                 ('index', c_short)]),
            'registerWriteReadU32': (
                c_ubyte, _check_register_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('regId', c_ubyte),
                 ('writeValue', c_ulong),
                 ('readValue', POINTER(c_ulong)),
                 ('index', c_short)]),
            'registerWriteReadS32': (
                c_ubyte, _check_register_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('regId', c_ubyte),
                 ('writeValue', c_long),
                 ('readValue', POINTER(c_long)),
                 ('index', c_short)]),
            'registerWriteReadU64': (
                c_ubyte, _check_register_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('regId', c_ubyte),
                 ('writeValue', c_ulonglong),
                 ('readValue', POINTER(c_ulonglong)),
                 ('index', c_short)]),
            'registerWriteReadS64': (
                c_ubyte, _check_register_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('regId', c_ubyte),
                 ('writeValue', c_longlong),
                 ('readValue', POINTER(c_longlong)),
                 ('index', c_short)]),
            'registerWriteReadF32': (
                c_ubyte, _check_register_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('regId', c_ubyte),
                 ('writeValue', c_float),
                 ('readValue', POINTER(c_float)),
                 ('index', c_short)]),
            'registerWriteReadF64': (
                c_ubyte, _check_register_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('regId', c_ubyte),
                 ('writeValue', c_double),
                 ('readValue', POINTER(c_double)),
                 ('index', c_short)]),
            'registerWriteReadAscii': (
                c_ubyte, _check_register_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('regId', c_ubyte),
                 ('writeStr', c_char_p),
                 ('writeEOL', c_ubyte),
                 ('readStr', POINTER(c_char)),
                 ('maxLen', POINTER(c_ubyte)),
                 ('index', c_short)]),
            # Dedicated - Device functions
            'deviceGetType': (
                c_ubyte, _check_device_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('devType', POINTER(c_ubyte))]),
            'deviceGetPartNumberStr': (
                c_ubyte, _check_device_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('partnumber', POINTER(c_char)),
                 ('maxLen', POINTER(c_ubyte))]),
            'deviceGetPCBVersion': (
                c_ubyte, _check_device_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('PCBVersion', POINTER(c_ubyte))]),
            'deviceGetStatusBits': (
                c_ubyte, _check_device_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('statusBits', POINTER(c_ushort))]),
            'deviceGetErrorCode': (
                c_ubyte, _check_device_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('errorCode', POINTER(c_ushort))]),
            'deviceGetBootloaderVersion': (
                c_ubyte, _check_device_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('version', POINTER(c_ushort))]),
            'deviceGetBootloaderVersionStr': (
                c_ubyte, _check_device_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('versionStr', POINTER(c_char)),
                 ('maxLen', POINTER(c_ubyte))]),
            'deviceGetFirmwareVersion': (
                c_ubyte, _check_device_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('version', POINTER(c_ushort))]),
            'deviceGetFirmwareVersionStr': (
                c_ubyte, _check_device_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('versionStr', POINTER(c_char)),
                 ('maxLen', POINTER(c_ubyte))]),
            'deviceGetModuleSerialNumberStr': (
                c_ubyte, _check_device_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('serialNumber', POINTER(c_char)),
                 ('maxLen', POINTER(c_ubyte))]),
            'deviceGetPCBSerialNumberStr': (
                c_ubyte, _check_device_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('serialNumber', POINTER(c_char)),
                 ('maxLen', POINTER(c_ubyte))]),
            # Callback - Device functions
            'deviceCreate': (
                c_ubyte, _check_device_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('waitReady', c_ubyte)]),
            'deviceExists': (
                c_ubyte, _check_device_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('exists', POINTER(c_ubyte))]),
            'deviceRemove': (
                c_ubyte, _check_device_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte)]),
            'deviceRemoveAll': (
                c_ubyte, _check_device_result,
                [('portname', c_char_p)]),
            'deviceGetAllTypes': (
                c_ubyte, _check_device_result,
                [('portname', c_char_p),
                 ('types', POINTER(c_char)),
                 ('maxTypes', POINTER(c_ubyte))]),
            'deviceGetMode': (
                c_ubyte, _check_device_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('devMode', POINTER(c_ubyte))]),
            'deviceGetLive': (
                c_ubyte, _check_device_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('liveMode', POINTER(c_ubyte))]),
            'deviceSetLive': (
                c_ubyte, _check_device_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('liveMode', c_ubyte)]),
            # Callback - Register functions
            'registerCreate': (
                c_ubyte, _check_register_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('regId', c_ubyte),
                 ('priority', c_ubyte),
                 ('dataType', c_ubyte)]),
            'registerExists': (
                c_ubyte, _check_register_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('regId', c_ubyte),
                 ('exists', POINTER(c_ubyte))]),
            'registerRemove': (
                c_ubyte, _check_register_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('regId', c_ubyte)]),
            'registerRemoveAll': (
                c_ubyte, _check_register_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte)]),
            'registerGetAll': (
                c_ubyte, _check_register_result,
                [('portname', c_char_p),
                 ('devId', c_ubyte),
                 ('regs', POINTER(c_char)),
                 ('maxRegs', POINTER(c_ubyte))]),
            # Callback - Support functions
            'setCallbackPtrPortInfo': (
                None, _log_debug,
                [('callback', c_void_p)]),
            'setCallbackPtrDeviceInfo': (
                None, _log_debug,
                [('callback', c_void_p)]),
            'setCallbackPtrRegisterInfo': (
                None, _log_debug,
                [('callback', c_void_p)]),
        }

        NKT._SDK = LoadLibrary(_PATH if path is None else path).lib
        for key, value in functions.items():
            attr = getattr(NKT._SDK, key)
            attr.restype, attr.errcheck = value[:2]
            attr.argtypes = [typ for _, typ in value[2]]

    @staticmethod
    def device_get_all_types(opened_ports=None, size=255):
        """Returns all device types (module types) from the internal device list.

        Parameters
        ----------
        opened_ports : :class:`str` or :class:`list` of :class:`str`, optional
            A port or a list of opened ports. If not specified then the
            :meth:`get_open_ports` method will be called and the types for each
            port will be returned.
        size : :class:`int`, optional
            The maximum number of bytes that the device list can be.

        Returns
        -------
        :class:`dict`
            The port names are the keys and each value is :class:`dict` with the
            module type as the keys and its corresponding device ID as the value.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        if opened_ports is None:
            opened_ports = [port.encode() for port in NKT.get_open_ports()]
        elif isinstance(opened_ports, (list, tuple)):
            opened_ports = [port.encode() for port in opened_ports]
        elif isinstance(opened_ports, str):
            opened_ports = [opened_ports.encode()]
        elif isinstance(opened_ports, bytes):
            opened_ports = [opened_ports]

        out = {}
        length = c_ubyte(size)
        types = create_string_buffer(size)
        for port in opened_ports:
            NKT._SDK.deviceGetAllTypes(port, types, length)
            key = port.decode()
            out[key] = {}
            for dev_id, typ in enumerate(types.raw):
                if not isinstance(typ, int):  # Python 2
                    typ = ord(typ)
                if typ != 0:
                    out[key]['0x%0.2X' % typ] = dev_id
        return out

    def device_create(self, device_id, wait_ready):
        """Creates a device in the internal device list.

        If the :meth:`open_ports` function has been called with `live` = 1 then the
        kernel immediately starts to monitor the device.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).
        wait_ready : :class:`bool`
            :data:`False` - Don't wait for the device to be ready.
            :data:`True` - Wait up to 2 seconds for the device to complete its analyze cycle.
            (All standard registers being successfully read)

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        NKT._SDK.deviceCreate(self._PORTNAME, device_id, int(bool(wait_ready)))

    def device_exists(self, device_id):
        """Checks if a specific device already exists in the internal device list.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).

        Returns
        -------
        :class:`bool`
            Whether the device exists.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        exists = c_ubyte(0)
        NKT._SDK.deviceExists(self._PORTNAME, device_id, exists)
        return bool(exists.value)

    def device_get_boot_loader_version(self, device_id):
        """Returns the boot-loader version (int) for a given device id.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated read.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).

        Returns
        -------
        :class:`int`
            The boot-loader version.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        version = c_ushort(0)
        NKT._SDK.deviceGetBootloaderVersion(self._PORTNAME, device_id, version)
        return version.value

    def device_get_boot_loader_version_str(self, device_id):
        """Returns the boot-loader version (string) for a given device id.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated read.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).

        Returns
        -------
        :class:`str`
            The boot-loader version.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        size = c_ubyte(255)
        version = create_string_buffer(size.value)
        NKT._SDK.deviceGetBootloaderVersionStr(self._PORTNAME, device_id, version, size)
        return version.value.decode()

    def device_get_error_code(self, device_id):
        """Returns the error code for a given device id.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated read.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).

        Returns
        -------
        :class:`int`
            The error code.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        error_code = c_ushort(0)
        NKT._SDK.deviceGetErrorCode(self._PORTNAME, device_id, error_code)
        return error_code.value

    def device_get_firmware_version(self, device_id):
        """Returns the firmware version (int) for a given device id.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated read.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).

        Returns
        -------
        :class:`int`
            The firmware version.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        version = c_ushort(0)
        NKT._SDK.deviceGetFirmwareVersion(self._PORTNAME, device_id, version)
        return version.value

    def device_get_firmware_version_str(self, device_id):
        """Returns the firmware version (string) for a given device id.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated read.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).

        Returns
        -------
        :class:`str`
            The firmware version.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        size = c_ubyte(255)
        version = create_string_buffer(size.value)
        NKT._SDK.deviceGetFirmwareVersionStr(self._PORTNAME, device_id, version, size)
        return version.value.decode()

    def device_get_live(self, device_id):
        """Returns the internal device live status for a specific device id.

        Requires the port being already opened with the :meth:`.open_ports` function
        and the device being already created, either automatically or with the
        :meth:`device_create` function.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).

        Returns
        -------
        :class:`bool`
            Whether live mode is enabled.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        live_mode = c_ubyte(0)
        NKT._SDK.deviceGetLive(self._PORTNAME, device_id, live_mode)
        return bool(live_mode.value)

    def device_get_mode(self, device_id):
        """Returns the internal device mode for a specific device id.

        Requires the port being already opened with the :meth:`.open_ports` function
        and the device being already created, either automatically or with the
        :meth:`device_create` function.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).

        Returns
        -------
        :class:`DeviceModeTypes`
            The device mode type.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        dev_mode = c_ubyte(0)
        NKT._SDK.deviceGetMode(self._PORTNAME, device_id, dev_mode)
        return DeviceModeTypes(dev_mode.value)

    def device_get_module_serial_number_str(self, device_id):
        """Returns the module serial number (string) for a given device id.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated read.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).

        Returns
        -------
        :class:`str`
            The serial number.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        size = c_ubyte(255)
        serial = create_string_buffer(size.value)
        NKT._SDK.deviceGetModuleSerialNumberStr(self._PORTNAME, device_id, serial, size)
        return serial.value.decode()

    def device_get_part_number_str(self, device_id):
        """Returns the part number for a given device id.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated read.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).

        Returns
        -------
        :class:`str`
            The part number.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        size = c_ubyte(255)
        part = create_string_buffer(size.value)
        NKT._SDK.deviceGetPartNumberStr(self._PORTNAME, device_id, part, size)
        return part.value.decode()

    def device_get_pcb_serial_number_str(self, device_id):
        """Returns the PCB serial number (string) for a given device id.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated read.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).

        Returns
        -------
        :class:`str`
            The part number.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        size = c_ubyte(255)
        serial = create_string_buffer(size.value)
        NKT._SDK.deviceGetPCBSerialNumberStr(self._PORTNAME, device_id, serial, size)
        return serial.value.decode()

    def device_get_pcb_version(self, device_id):
        """Returns the PCB version for a given device id.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated read.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).

        Returns
        -------
        :class:`int`
            The PCB version number.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        version = c_ubyte(0)
        NKT._SDK.deviceGetPCBVersion(self._PORTNAME, device_id, version)
        return version.value

    def device_get_status_bits(self, device_id):
        """Returns the status bits for a given device id.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated read.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).

        Returns
        -------
        :class:`int`
            The status bits.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        status = c_ushort(0)
        NKT._SDK.deviceGetStatusBits(self._PORTNAME, device_id, status)
        return status.value

    def device_get_type(self, device_id):
        """Returns the module type for a specific device id.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated read.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).

        Returns
        -------
        :class:`int`
            The module type.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        dev_type = c_ubyte(0)
        NKT._SDK.deviceGetType(self._PORTNAME, device_id, dev_type)
        return dev_type.value

    def device_remove(self, device_id):
        """Remove a specific device from the internal device list.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        NKT._SDK.deviceRemove(self._PORTNAME, device_id)

    def device_remove_all(self):
        """Remove all devices from the internal device list.

        No confirmation is given, the list is simply cleared.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        NKT._SDK.deviceRemoveAll(self._PORTNAME)

    def device_set_live(self, device_id, live_mode):
        """Sets the internal device live status for a specific device id (module address).

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).
        live_mode : :class:`bool`
            Set to :data:`True` to enable.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        NKT._SDK.deviceSetLive(self._PORTNAME, device_id, int(bool(live_mode)))

    def disconnect(self):
        """Disconnect from the port.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        if NKT._SDK is not None and self._PORTNAME is not None:
            self.close_ports(self._PORTNAME)
            self._PORTNAME = None

    @staticmethod
    def get_all_ports(size=255):
        """Returns a list of all ports.

        Parameters
        ----------
        size : :class:`int`, optional
            The maximum size of the string buffer to fetch the results.

        Returns
        -------
        :class:`list` of :class:`str`
            A list of port names.
        """
        length = c_ushort(size)
        names = create_string_buffer(size)
        NKT._SDK.getAllPorts(names, length)
        return [name for name in names.value.decode().split(',') if name]

    def get_modules(self, size=255):
        """Returns all device types (module types) from the device.

        Parameters
        ----------
        size : :class:`int`, optional
            The maximum number of bytes that the device list can be.

        Returns
        -------
        :class:`dict`
            The module type as the keys and its corresponding device ID as the value.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        return NKT.device_get_all_types(opened_ports=self._PORTNAME, size=size)[self._PORTNAME.decode()]

    @staticmethod
    def get_legacy_bus_scanning():
        """Get the bus-scanning mode.

        Returns
        -------
        :class:`bool`
            :data:`True` if in legacy mode otherwise in normal mode.
        """
        return bool(NKT._SDK.getLegacyBusScanning())

    @staticmethod
    def get_open_ports(size=255):
        """Returns a list of already-opened ports.

        Parameters
        ----------
        size : :class:`int`, optional
            The maximum size of the string buffer to fetch the results.

        Returns
        -------
        :class:`list` of :class:`str`
            A list of port names that are already open.
        """
        length = c_ushort(size)
        names = create_string_buffer(size)
        NKT._SDK.getOpenPorts(names, length)
        return [name for name in names.value.decode().split(',') if name]

    def get_port_error_msg(self):
        """Retrieve error message for the port.

        Returns
        -------
        :class:`str`
            The error message. An empty string indicates no error.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        length = c_ushort(255)
        msg = create_string_buffer(length.value)
        NKT._SDK.getPortErrorMsg(self._PORTNAME, msg, length)
        return msg.value.decode()

    def get_port_status(self):
        """Get the status of the port.

        Returns
        -------
        :class:`PortStatusTypes`
            The port status.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        status = c_ubyte(0)
        NKT._SDK.getPortStatus(self._PORTNAME, status)
        return PortStatusTypes(status.value)

    @staticmethod
    def open_ports(names=None, auto=True, live=True):
        """Open the specified port(s).

        Repeated calls to this function is allowed to reopen and/or rescan for devices.

        Parameters
        ----------
        names : :class:`str`, :class:`list` of :class:`str`, optional
            If :data:`None` then open all available ports. If a :class:`str`
            then the name of a port. Otherwise a :class:`list` of names. Port
            names are case sensitive. Example port names are ``'AcoustikPort1'``,
            ``'COM6'``.
        auto : :class:`bool`, optional
            If :data:`True` then automatically start bus scanning and add the
            found devices in the internal device list. If :data:`False` then
            bus scanning and device creation is not automatically handled. The
            port is automatically closed if no devices are found.
        live : :class:`bool`, optional
            If :data:`True` then keep all the found or created devices in live
            mode, which means the Interbus kernel keeps monitoring all the found
            devices and their registers. Please note that this will keep the modules
            watchdog alive as long as the port is open. If :data:`False` then disable
            continuous monitoring of the registers. No callback is possible on register
            changes. Use the :meth:`.register_read`, :meth:`.register_write` and
            :meth:`.register_write_read` methods.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        if names is None:
            names = b''
        elif isinstance(names, (list, tuple)):
            names = b','.join(name.encode() for name in names)
        elif not isinstance(names, bytes):
            names = names.encode()
        NKT._SDK.openPorts(names, int(bool(auto)), int(bool(live)))

    def point_to_point_port_add(self, host_address, host_port, client_address, client_port, protocol, ms_timeout=100):
        """Creates or modifies a point to point port.

        Parameters
        ----------
        host_address : :class:`str`
            The local ip address, e.g., ``'192.168.1.67'``.
        host_port : :class:`int`
            The local port number.
        client_address : :class:`str`
            The remote ip address, e.g., ``'192.168.1.100'``.
        client_port : :class:`int`
            The remote port number.
        protocol : :class:`int`
            Either 0 (TCP) or 1 (UDP).
        ms_timeout : :class:`int`, optional
            Telegram timeout value in milliseconds.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        NKT._SDK.pointToPointPortAdd(
            self._PORTNAME, host_address.encode(), host_port,
            client_address.encode(), client_port, protocol, ms_timeout
        )

    def point_to_point_port_del(self):
        """Delete the point-to-point port.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        NKT._SDK.pointToPointPortDel(self._PORTNAME)

    def point_to_point_port_get(self):
        """Retrieve the information about the point-to-point port setting.

        Returns
        -------
        :class:`dict`
            The information about the point-to-point port setting.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        host_length = c_ubyte(255)
        host_address = create_string_buffer(host_length.value)
        host_port = c_ushort(0)
        client_length = c_ubyte(255)
        client_address = create_string_buffer(client_length.value)
        client_port = c_ushort(0)
        protocol = c_ubyte(0)
        ms_timeout = c_ubyte(0)
        NKT._SDK.pointToPointPortGet(
            self._PORTNAME, host_address, host_length, host_port,
            client_address, client_length, client_port, protocol, ms_timeout
        )
        return {'host_address': host_address.value.decode(),
                'host_port': host_port.value,
                'client_address': client_address.value.decode(),
                'client_port': client_port.value,
                'protocol': protocol.value,
                'ms_timeout': ms_timeout.value}

    def register_read(self, device_id, reg_id, index=-1):
        """Reads a register value and returns the result.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated read.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).
        reg_id : :class:`int`
            The register id (register address).
        index : :class:`int`, optional
            Value index. Typically -1, but could be used to extract data from
            a specific position in the register. Index is byte counted.

        Returns
        -------
        :class:`bytes`
            The register value.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        size = c_ubyte(255)
        data = create_string_buffer(size.value)
        NKT._SDK.registerRead(self._PORTNAME, device_id, reg_id, data, size, index)
        return data.raw[:size.value]

    def register_create(self, device_id, reg_id, priority, data_type):
        """Creates a register in the internal register list.

        If the :meth:`open_ports` function has been called with the `live` = 1 then
        the kernel immediately starts to monitor the register.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).
        reg_id : :class:`int`
            The register id (register address).
        priority : :class:`int`
            The :class:`RegisterPriorityTypes` (monitoring priority).
        data_type : :class:`int`
            The :class:`RegisterDataTypes`, not used internally but could be used in a
            common callback function to determine data type.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        NKT._SDK.registerCreate(self._PORTNAME, device_id, reg_id,
                                RegisterPriorityTypes(priority), RegisterDataTypes(data_type))

    def register_exists(self, device_id, reg_id):
        """Checks if a specific register already exists in the internal register list.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).
        reg_id : :class:`int`
            The register id (register address).

        Returns
        -------
        :class:`bool`
            Whether the register exists.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        exists = c_ubyte(0)
        NKT._SDK.registerExists(self._PORTNAME, device_id, reg_id, exists)
        return bool(exists.value)

    def register_get_all(self, device_id):
        """Returns the register ids (register addresses) from the internal register list.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).

        Returns
        -------
        :class:`list` of :class:`int`
            The register ids.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        size = c_ubyte(255)
        regs = create_string_buffer(size.value)
        NKT._SDK.registerGetAll(self._PORTNAME, device_id, regs, size)
        return list(regs.value)

    def register_read_ascii(self, device_id, reg_id, index=-1):
        """Reads an ascii string from the register.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated read.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).
        reg_id : :class:`int`
            The register id (register address).
        index : :class:`int`, optional
            Value index. Typically -1, but could be used to extract data from
            a specific position in the register. Index is byte counted.

        Returns
        -------
        :class:`str`
            The ascii value.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        size = c_ubyte(255)
        data = create_string_buffer(size.value)
        NKT._SDK.registerReadAscii(self._PORTNAME, device_id, reg_id, data, size, index)
        return data.value.decode()

    def register_read_f32(self, device_id, reg_id, index=-1):
        """Reads 32-bit float value from the register.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated read.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).
        reg_id : :class:`int`
            The register id (register address).
        index : :class:`int`, optional
            Value index. Typically -1, but could be used to extract data from
            a specific position in the register. Index is byte counted.

        Returns
        -------
        :class:`float`
            The 32-bit float value.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        data = c_float(0)
        NKT._SDK.registerReadF32(self._PORTNAME, device_id, reg_id, data, index)
        return data.value

    def register_read_f64(self, device_id, reg_id, index=-1):
        """Reads 64-bit double value from the register.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated read.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).
        reg_id : :class:`int`
            The register id (register address).
        index : :class:`int`, optional
            Value index. Typically -1, but could be used to extract data from
            a specific position in the register. Index is byte counted.

        Returns
        -------
        :class:`float`
            The 64-bit double value.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        data = c_double(0)
        NKT._SDK.registerReadF64(self._PORTNAME, device_id, reg_id, data, index)
        return data.value

    def register_read_s16(self, device_id, reg_id, index=-1):
        """Reads 16-bit signed short value from the register.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated read.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).
        reg_id : :class:`int`
            The register id (register address).
        index : :class:`int`, optional
            Value index. Typically -1, but could be used to extract data from
            a specific position in the register. Index is byte counted.

        Returns
        -------
        :class:`int`
            The 16-bit signed short value.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        data = c_short(0)
        NKT._SDK.registerReadS16(self._PORTNAME, device_id, reg_id, data, index)
        return data.value

    def register_read_s32(self, device_id, reg_id, index=-1):
        """Reads 32-bit signed long value from the register.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated read.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).
        reg_id : :class:`int`
            The register id (register address).
        index : :class:`int`, optional
            Value index. Typically -1, but could be used to extract data from
            a specific position in the register. Index is byte counted.

        Returns
        -------
        :class:`int`
            The 32-bit signed long value.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        data = c_long(0)
        NKT._SDK.registerReadS32(self._PORTNAME, device_id, reg_id, data, index)
        return data.value

    def register_read_s64(self, device_id, reg_id, index=-1):
        """Reads 64-bit signed long long value from the register.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated read.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).
        reg_id : :class:`int`
            The register id (register address).
        index : :class:`int`, optional
            Value index. Typically -1, but could be used to extract data from
            a specific position in the register. Index is byte counted.

        Returns
        -------
        :class:`int`
            The 64-bit signed long long value.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        data = c_longlong(0)
        NKT._SDK.registerReadS64(self._PORTNAME, device_id, reg_id, data, index)
        return data.value

    def register_read_s8(self, device_id, reg_id, index=-1):
        """Reads 8-bit signed char value from the register.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated read.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).
        reg_id : :class:`int`
            The register id (register address).
        index : :class:`int`, optional
            Value index. Typically -1, but could be used to extract data from
            a specific position in the register. Index is byte counted.

        Returns
        -------
        :class:`int`
            The 8-bit signed char value.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        data = c_byte(0)
        NKT._SDK.registerReadS8(self._PORTNAME, device_id, reg_id, data, index)
        return data.value

    def register_read_u16(self, device_id, reg_id, index=-1):
        """Reads 16-bit unsigned short value from the register.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated read.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).
        reg_id : :class:`int`
            The register id (register address).
        index : :class:`int`, optional
            Value index. Typically -1, but could be used to extract data from
            a specific position in the register. Index is byte counted.

        Returns
        -------
        :class:`int`
            The 16-bit unsigned short value.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        data = c_ushort(0)
        NKT._SDK.registerReadU16(self._PORTNAME, device_id, reg_id, data, index)
        return data.value

    def register_read_u32(self, device_id, reg_id, index=-1):
        """Reads 32-bit unsigned long value from the register.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated read.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).
        reg_id : :class:`int`
            The register id (register address).
        index : :class:`int`, optional
            Value index. Typically -1, but could be used to extract data from
            a specific position in the register. Index is byte counted.

        Returns
        -------
        :class:`int`
            The 32-bit unsigned long value.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        data = c_ulong(0)
        NKT._SDK.registerReadU32(self._PORTNAME, device_id, reg_id, data, index)
        return data.value

    def register_read_u64(self, device_id, reg_id, index=-1):
        """Reads 64-bit unsigned long long value from the register.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated read.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).
        reg_id : :class:`int`
            The register id (register address).
        index : :class:`int`, optional
            Value index. Typically -1, but could be used to extract data from
            a specific position in the register. Index is byte counted.

        Returns
        -------
        :class:`int`
            The 64-bit unsigned long long value.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        data = c_ulonglong(0)
        NKT._SDK.registerReadU64(self._PORTNAME, device_id, reg_id, data, index)
        return data.value

    def register_read_u8(self, device_id, reg_id, index=-1):
        """Reads 8-bit unsigned char value from the register.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated read.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).
        reg_id : :class:`int`
            The register id (register address).
        index : :class:`int`, optional
            Value index. Typically -1, but could be used to extract data from
            a specific position in the register. Index is byte counted.

        Returns
        -------
        :class:`int`
            The 8-bit unsigned char value.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        data = c_ubyte(0)
        NKT._SDK.registerReadU8(self._PORTNAME, device_id, reg_id, data, index)
        return data.value

    def register_remove(self, device_id, reg_id):
        """Remove a specific register from the internal register list.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).
        reg_id : :class:`int`
            The register id (register address).

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        NKT._SDK.registerRemove(self._PORTNAME, device_id, reg_id)

    def register_remove_all(self, device_id):
        """Remove all registers from the internal register list.

        No confirmation given, the list is simply cleared.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        NKT._SDK.registerRemoveAll(self._PORTNAME, device_id)

    def register_write(self, device_id, reg_id, data, index=-1):
        """Writes a register value.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated write.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).
        reg_id : :class:`int`
            The register id (register address).
        data : :class:`bytes`
            The data to write to the register.
        index : :class:`int`, optional
            Value index. Typically -1, but could be used to write a value in a multi-value register.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        NKT._SDK.registerWrite(self._PORTNAME, device_id, reg_id, data, len(data), index)

    def register_write_ascii(self, device_id, reg_id, string, write_eol, index=-1):
        """Writes a string to the register value.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated write.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).
        reg_id : :class:`int`
            The register id (register address).
        string : :class:`str`
            The string to write to the register.
        write_eol : :class:`bool`
            Whether to append the End Of Line character (a null character) to the string.
        index : :class:`int`, optional
            Value index. Typically -1, but could be used to write a value in a mixed-type register.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        buffer = create_string_buffer(string.encode('ascii'))
        NKT._SDK.registerWriteAscii(self._PORTNAME, device_id, reg_id, buffer, int(bool(write_eol)), index)

    def register_write_f32(self, device_id, reg_id, value, index=-1):
        """Writes a 32-bit float register value.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated write.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).
        reg_id : :class:`int`
            The register id (register address).
        value : :class:`float`
            The 32-bit float to write to the register.
        index : :class:`int`, optional
            Value index. Typically -1, but could be used to write a value in a multi-value register.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        NKT._SDK.registerWriteF32(self._PORTNAME, device_id, reg_id, value, index)

    def register_write_f64(self, device_id, reg_id, value, index=-1):
        """Writes a 64-bit double register value.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated write.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).
        reg_id : :class:`int`
            The register id (register address).
        value : :class:`float`
            The 64-bit double to write to the register.
        index : :class:`int`, optional
            Value index. Typically -1, but could be used to write a value in a multi-value register.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        NKT._SDK.registerWriteF64(self._PORTNAME, device_id, reg_id, value, index)

    def register_write_read(self, device_id, reg_id, data, index=-1):
        """Writes then reads a register value.

        It is not necessary to open the port, create the device or register before using
        this function, since it will do a dedicated write followed by a dedicated read.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).
        reg_id : :class:`int`
            The register id (register address).
        data : :class:`bytes`
            The data to write to the register.
        index : :class:`int`, optional
            Value index. Typically -1, but could be used to write a value in a multi-value register.

        Returns
        -------
        :class:`bytes`
            The data that was written to the register.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        size = c_ubyte(255)
        read = create_string_buffer(size.value)
        NKT._SDK.registerWriteRead(self._PORTNAME, device_id, reg_id, data, len(data), index, read, size, index)
        return read.raw[:size.value]

    def register_write_read_ascii(self, device_id, reg_id, string, write_eol, index=-1):
        """Writes then reads a string register value.

        It is not necessary to open the port, create the device or register before using
        this function, since it will do a dedicated write followed by a dedicated read.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).
        reg_id : :class:`int`
            The register id (register address).
        string : :class:`str`
            The string to write to the register.
        write_eol : :class:`bool`
            Whether to append the End Of Line character (a null character) to the string.
        index : :class:`int`, optional
            Value index. Typically -1, but could be used to write a value in a multi-value register.

        Returns
        -------
        :class:`str`
            The string that was written to the register.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        ascii_value = create_string_buffer(string.encode('ascii'))
        size = c_ubyte(255)
        read = create_string_buffer(size.value)
        NKT._SDK.registerWriteReadAscii(self._PORTNAME, device_id, reg_id, ascii_value,
                                        int(bool(write_eol)), read, size, index)
        return read.value.decode('ascii')

    def register_write_read_f32(self, device_id, reg_id, value, index=-1):
        """Writes then reads a 32-bit float register value.

        It is not necessary to open the port, create the device or register before using
        this function, since it will do a dedicated write followed by a dedicated read.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).
        reg_id : :class:`int`
            The register id (register address).
        value : :class:`float`
            The 32-bit float value to write to the register.
        index : :class:`int`, optional
            Value index. Typically -1, but could be used to write a value in a multi-value register.

        Returns
        -------
        :class:`float`
            The 32-bit float value that was written to the register.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        read = c_float(0)
        NKT._SDK.registerWriteReadF32(self._PORTNAME, device_id, reg_id, value, read, index)
        return read.value

    def register_write_read_f64(self, device_id, reg_id, value, index=-1):
        """Writes then reads a 64-bit double register value.

        It is not necessary to open the port, create the device or register before using
        this function, since it will do a dedicated write followed by a dedicated read.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).
        reg_id : :class:`int`
            The register id (register address).
        value : :class:`float`
            The 64-bit double value to write to the register.
        index : :class:`int`, optional
            Value index. Typically -1, but could be used to write a value in a multi-value register.

        Returns
        -------
        :class:`float`
            The 64-bit double value that was written to the register.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        read = c_double(0)
        NKT._SDK.registerWriteReadF64(self._PORTNAME, device_id, reg_id, value, read, index)
        return read.value

    def register_write_read_s16(self, device_id, reg_id, value, index=-1):
        """Writes then reads a 16-bit signed short register value.

        It is not necessary to open the port, create the device or register before using
        this function, since it will do a dedicated write followed by a dedicated read.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).
        reg_id : :class:`int`
            The register id (register address).
        value : :class:`int`
            The 16-bit signed short value to write to the register.
        index : :class:`int`, optional
            Value index. Typically -1, but could be used to write a value in a multi-value register.

        Returns
        -------
        :class:`int`
            The 16-bit signed short value that was written to the register.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        read = c_short(0)
        NKT._SDK.registerWriteReadS16(self._PORTNAME, device_id, reg_id, value, read, index)
        return read.value

    def register_write_read_s32(self, device_id, reg_id, value, index=-1):
        """Writes then reads a 32-bit signed long register value.

        It is not necessary to open the port, create the device or register before using
        this function, since it will do a dedicated write followed by a dedicated read.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).
        reg_id : :class:`int`
            The register id (register address).
        value : :class:`int`
            The 32-bit signed long value to write to the register.
        index : :class:`int`, optional
            Value index. Typically -1, but could be used to write a value in a multi-value register.

        Returns
        -------
        :class:`int`
            The 32-bit signed long value that was written to the register.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        read = c_long(0)
        NKT._SDK.registerWriteReadS32(self._PORTNAME, device_id, reg_id, value, read, index)
        return read.value

    def register_write_read_s64(self, device_id, reg_id, value, index=-1):
        """Writes then reads a 64-bit signed long long register value.

        It is not necessary to open the port, create the device or register before using
        this function, since it will do a dedicated write followed by a dedicated read.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).
        reg_id : :class:`int`
            The register id (register address).
        value : :class:`int`
            The 64-bit signed long long value to write to the register.
        index : :class:`int`, optional
            Value index. Typically -1, but could be used to write a value in a multi-value register.

        Returns
        -------
        :class:`int`
            The 64-bit signed long long value that was written to the register.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        read = c_longlong(0)
        NKT._SDK.registerWriteReadS64(self._PORTNAME, device_id, reg_id, value, read, index)
        return read.value

    def register_write_read_s8(self, device_id, reg_id, value, index=-1):
        """Writes then reads a 8-bit signed char register value.

        It is not necessary to open the port, create the device or register before using
        this function, since it will do a dedicated write followed by a dedicated read.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).
        reg_id : :class:`int`
            The register id (register address).
        value : :class:`int`
            The 8-bit signed char value to write to the register.
        index : :class:`int`, optional
            Value index. Typically -1, but could be used to write a value in a multi-value register.

        Returns
        -------
        :class:`int`
            The 8-bit signed char value that was written to the register.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        read = c_byte(0)
        NKT._SDK.registerWriteReadS8(self._PORTNAME, device_id, reg_id, value, read, index)
        return read.value

    def register_write_read_u16(self, device_id, reg_id, value, index=-1):
        """Writes then reads a 16-bit unsigned short register value.

        It is not necessary to open the port, create the device or register before using
        this function, since it will do a dedicated write followed by a dedicated read.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).
        reg_id : :class:`int`
            The register id (register address).
        value : :class:`int`
            The 16-bit unsigned short value to write to the register.
        index : :class:`int`, optional
            Value index. Typically -1, but could be used to write a value in a multi-value register.

        Returns
        -------
        :class:`int`
            The 16-bit unsigned short value that was written to the register.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        read = c_ushort(0)
        NKT._SDK.registerWriteReadU16(self._PORTNAME, device_id, reg_id, value, read, index)
        return read.value

    def register_write_read_u32(self, device_id, reg_id, value, index=-1):
        """Writes then reads a 32-bit unsigned long register value.

        It is not necessary to open the port, create the device or register before using
        this function, since it will do a dedicated write followed by a dedicated read.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).
        reg_id : :class:`int`
            The register id (register address).
        value : :class:`int`
            The 32-bit unsigned long value to write to the register.
        index : :class:`int`, optional
            Value index. Typically -1, but could be used to write a value in a multi-value register.

        Returns
        -------
        :class:`int`
            The 32-bit unsigned long value that was written to the register.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        read = c_ulong(0)
        NKT._SDK.registerWriteReadU32(self._PORTNAME, device_id, reg_id, value, read, index)
        return read.value

    def register_write_read_u64(self, device_id, reg_id, value, index=-1):
        """Writes then reads a 64-bit unsigned long long register value.

        It is not necessary to open the port, create the device or register before using
        this function, since it will do a dedicated write followed by a dedicated read.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).
        reg_id : :class:`int`
            The register id (register address).
        value : :class:`int`
            The 64-bit unsigned long long value to write to the register.
        index : :class:`int`, optional
            Value index. Typically -1, but could be used to write a value in a multi-value register.

        Returns
        -------
        :class:`int`
            The 64-bit unsigned long long value that was written to the register.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        read = c_ulonglong(0)
        NKT._SDK.registerWriteReadU64(self._PORTNAME, device_id, reg_id, value, read, index)
        return read.value

    def register_write_read_u8(self, device_id, reg_id, value, index=-1):
        """Writes then reads a 8-bit unsigned char register value.

        It is not necessary to open the port, create the device or register before using
        this function, since it will do a dedicated write followed by a dedicated read.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).
        reg_id : :class:`int`
            The register id (register address).
        value : :class:`int`
            The 8-bit unsigned char value to write to the register.
        index : :class:`int`, optional
            Value index. Typically -1, but could be used to write a value in a multi-value register.

        Returns
        -------
        :class:`int`
            The 8-bit unsigned char value that was written to the register.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        read = c_ubyte(0)
        NKT._SDK.registerWriteReadU8(self._PORTNAME, device_id, reg_id, value, read, index)
        return read.value

    def register_write_s16(self, device_id, reg_id, value, index=-1):
        """Writes a 16-bit signed short register value.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated write.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).
        reg_id : :class:`int`
            The register id (register address).
        value : :class:`int`
            The 16-bit signed short to write to the register.
        index : :class:`int`, optional
            Value index. Typically -1, but could be used to write a value in a multi-value register.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        NKT._SDK.registerWriteS16(self._PORTNAME, device_id, reg_id, value, index)

    def register_write_s32(self, device_id, reg_id, value, index=-1):
        """Writes a 32-bit signed long register value.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated write.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).
        reg_id : :class:`int`
            The register id (register address).
        value : :class:`int`
            The 32-bit signed long to write to the register.
        index : :class:`int`, optional
            Value index. Typically -1, but could be used to write a value in a multi-value register.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        NKT._SDK.registerWriteS32(self._PORTNAME, device_id, reg_id, value, index)

    def register_write_s64(self, device_id, reg_id, value, index=-1):
        """Writes a 64-bit signed long long register value.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated write.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).
        reg_id : :class:`int`
            The register id (register address).
        value : :class:`int`
            The 64-bit signed long long to write to the register.
        index : :class:`int`, optional
            Value index. Typically -1, but could be used to write a value in a multi-value register.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        NKT._SDK.registerWriteS64(self._PORTNAME, device_id, reg_id, value, index)

    def register_write_s8(self, device_id, reg_id, value, index=-1):
        """Writes a 8-bit signed char register value.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated write.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).
        reg_id : :class:`int`
            The register id (register address).
        value : :class:`int`
            The 8-bit signed char to write to the register.
        index : :class:`int`, optional
            Value index. Typically -1, but could be used to write a value in a multi-value register.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        NKT._SDK.registerWriteS8(self._PORTNAME, device_id, reg_id, value, index)

    def register_write_u16(self, device_id, reg_id, value, index=-1):
        """Writes a 16-bit unsigned short register value.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated write.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).
        reg_id : :class:`int`
            The register id (register address).
        value : :class:`int`
            The 16-bit unsigned short to write to the register.
        index : :class:`int`, optional
            Value index. Typically -1, but could be used to write a value in a multi-value register.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        NKT._SDK.registerWriteU16(self._PORTNAME, device_id, reg_id, value, index)

    def register_write_u32(self, device_id, reg_id, value, index=-1):
        """Writes a 32-bit unsigned long register value.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated write.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).
        reg_id : :class:`int`
            The register id (register address).
        value : :class:`int`
            The 32-bit unsigned long to write to the register.
        index : :class:`int`, optional
            Value index. Typically -1, but could be used to write a value in a multi-value register.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        NKT._SDK.registerWriteU32(self._PORTNAME, device_id, reg_id, value, index)

    def register_write_u64(self, device_id, reg_id, value, index=-1):
        """Writes a 64-bit unsigned long long register value.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated write.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).
        reg_id : :class:`int`
            The register id (register address).
        value : :class:`int`
            The 64-bit unsigned long long to write to the register.
        index : :class:`int`, optional
            Value index. Typically -1, but could be used to write a value in a multi-value register.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        NKT._SDK.registerWriteU64(self._PORTNAME, device_id, reg_id, value, index)

    def register_write_u8(self, device_id, reg_id, value, index=-1):
        """Writes a 8-bit unsigned char register value.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated write.

        Parameters
        ----------
        device_id : :class:`int`
            The device id (module address).
        reg_id : :class:`int`
            The register id (register address).
        value : :class:`int`
            The 8-bit unsigned char to write to the register.
        index : :class:`int`, optional
            Value index. Typically -1, but could be used to write a value in a multi-value register.

        Raises
        ------
        ~msl.equipment.exceptions.NKTError
            If there was an error calling this method.
        """
        NKT._SDK.registerWriteU8(self._PORTNAME, device_id, reg_id, value, index)

    @staticmethod
    def set_legacy_bus_scanning(mode):
        """Set the bus-scanning mode to normal or legacy.

        Parameters
        ----------
        mode : :class:`bool`
            If :data:`False` then bus scanning is set to normal mode and
            allows for a rolling masterId. In this mode the masterId is changed
            for each message to allow for out-of-sync detection. If :data:`True`
            then bus scanning is set to legacy mode and fixes the masterId at
            address 66(0x42). Some older modules do not accept masterIds other
            than 66(0x42).
        """
        NKT._SDK.setLegacyBusScanning(int(bool(mode)))

    @staticmethod
    def set_callback_device_status(callback):
        """Enables/Disables a callback for device status changes.

        Parameters
        ----------
        callback : :class:`DeviceStatusCallback`
            A :class:`DeviceStatusCallback` object. Pass in :data:`None` to
            disable callbacks.

        Note
        ----
        Due to a risk of circular runaway leading to stack overflow, it is not allowed
        to call functions in the DLL from within the callback function. If a call is
        made to a function in the DLL the function will raise an exception.

        Examples
        --------
        .. code-block:: python

            from ctypes import c_ubyte
            from msl.equipment.resources import NKT

            @NKT.DeviceStatusCallback
            def device_callback(port, dev_id, status, length, address):
                # 'address' is an integer and represents the address of c_void_p from the callback
                data = bytearray((c_ubyte * length).from_address(address)[:])
                print('The port is {!r}'.format(port))
                print('The device ID is {}'.format(dev_id))
                print('The device status is {!r}'.format(NKT.DeviceStatusTypes(status)))
                print('The device data is {!r}'.format(data))

            NKT.set_callback_device_status(device_callback)
        """
        if callback is not None and not isinstance(callback, DeviceStatusCallback):
            raise TypeError('Must pass in a DeviceStatusCallback object')
        NKT._SDK.setCallbackPtrDeviceInfo(callback)

    @staticmethod
    def set_callback_port_status(callback):
        """Enables/Disables a callback for port status changes.

        Used by the :meth:`open_ports` and :meth:`close_ports` functions.

        Parameters
        ----------
        callback : :class:`PortStatusCallback`
            A :class:`PortStatusCallback` object. Pass in :data:`None` to
            disable callbacks.

        Note
        ----
        Due to a risk of circular runaway leading to stack overflow, it is not allowed
        to call functions in the DLL from within the callback function. If a call is
        made to a function in the DLL the function will raise an exception.

        Examples
        --------
        .. code-block:: python

            from msl.equipment.resources import NKT

            @NKT.PortStatusCallback
            def port_callback(port, status, cur_scan, max_scan, device):
                print('The port is {!r}'.format(port))
                print('The port status is {!r}'.format(NKT.PortStatusTypes(status)))
                print('Current scanned address or device found address is {}'.format(cur_scan))
                print('There are {} addresses to scan in total'.format(max_scan))
                print('Found device with type {}'.format(device))

            NKT.set_callback_port_status(port_callback)
        """
        if callback is not None and not isinstance(callback, PortStatusCallback):
            raise TypeError('Must pass in a PortStatusCallback object')
        NKT._SDK.setCallbackPtrPortInfo(callback)

    @staticmethod
    def set_callback_register_status(callback):
        """Enables/Disables a callback for register status changes.

        Parameters
        ----------
        callback : :class:`RegisterStatusCallback`
            A :class:`RegisterStatusCallback` object. Pass in :data:`None` to
            disable callbacks.

        Note
        ----
        Due to a risk of circular runaway leading to stack overflow, it is not allowed
        to call functions in the DLL from within the callback function. If a call is
        made to a function in the DLL the function will raise an exception.

        Examples
        --------
        .. code-block:: python

            from ctypes import c_ubyte
            from msl.equipment.resources import NKT

            @NKT.RegisterStatusCallback
            def register_callback(port, dev_id, reg_id, reg_status, reg_type, length, address):
                # 'address' is an integer and represents the address of c_void_p from the callback
                data = bytearray((c_ubyte * length).from_address(address)[:])
                print('The port is {!r}'.format(port))
                print('The device ID is {}'.format(dev_id))
                print('The register ID is {}'.format(reg_id))
                print('The register status is {!r}'.format(NKT.RegisterStatusTypes(reg_status)))
                print('The register type is {!r}'.format(NKT.RegisterDataTypes(reg_type)))
                print('The register data is {!r}'.format(data))

            NKT.set_callback_register_status(register_callback)
        """
        if callback is not None and not isinstance(callback, RegisterStatusCallback):
            raise TypeError('Must pass in a RegisterStatusCallback object')
        NKT._SDK.setCallbackPtrRegisterInfo(callback)


_port_errors = {
    0: ('OPSuccess', 'Successful operation'),
    1: ('OPFailed', 'The NKT.open_ports() function has failed'),
    2: ('OPPortNotFound', 'The specified port name could not be found'),
    3: ('OPNoDevices', 'No devices found on the specified port'),
    4: ('OPApplicationBusy', 'The function is not allowed to be invoked from within a callback function')
}

_p2p_errors = {
    0: ('P2PSuccess', 'Successful operation'),
    1: ('P2PInvalidPortname', 'Invalid port name provided'),
    2: ('P2PInvalidLocalIP', 'Invalid local IP provided'),
    3: ('P2PInvalidRemoteIP', 'Invalid remote IP provided'),
    4: ('P2PPortnameNotFound', 'Port name not found'),
    5: ('P2PPortnameExists', 'Port name already exists'),
    6: ('P2PApplicationBusy', 'The function is not allowed to be invoked from within a callback function')
}

_device_errors = {
    0: ('DevResultSuccess', 'Successful operation'),
    1: ('DevResultWaitTimeout', 'The function device_create() timed out waiting for the device being ready'),
    2: ('DevResultFailed', 'The function device_create(), failed'),
    3: ('DevResultDeviceNotFound', 'The specified device could not be found in the internal device list'),
    4: ('DevResultPortNotFound', 'The function device_create() failed due to not '
                                 'being able to find the specified port'),
    5: ('DevResultPortOpenError', 'The function device_create() failed due to port not being open'),
    6: ('DevResultApplicationBusy', 'The function is not allowed to be invoked from within a callback function')
}

_register_errors = {
    0: ('RegResultSuccess', 'Successful operation'),
    1: ('RegResultReadError', 'Arises from a register write function with index > 0, if the pre-read fails'),
    2: ('RegResultFailed', 'The function register_create() has failed'),
    3: ('RegResultBusy', 'The module has reported a BUSY error, '
                         'the kernel automatically retries on busy but have given up'),
    4: ('RegResultNacked', 'The module has Nacked the register, which typically means non existing register'),
    5: ('RegResultCRCErr', 'The module has reported a CRC error, which means the received message has CRC errors'),
    6: ('RegResultTimeout', 'The module has not responded in time. A module should respond in max. 75ms'),
    7: ('RegResultComError', 'The module has reported a COM error, which typically means out of sync or garbage error'),
    8: ('RegResultTypeError', 'The datatype does not seem to match the register datatype'),
    9: ('RegResultIndexError', 'The index seem to be out of range of the register length'),
    10: ('RegResultPortClosed', 'The specified port is closed error. Could happen if the '
                                'USB is unplugged in the middel of a sequence'),
    11: ('RegResultRegisterNotFound', 'The specified register could not be found in the '
                                      'internal register list for the specified device'),
    12: ('RegResultDeviceNotFound', 'The specified device could not be found in the internal device list'),
    13: ('RegResultPortNotFound', 'The specified port name could not be found'),
    14: ('RegResultPortOpenError', 'The specified port name could not be opened. The port '
                                   'might be in use by another application'),
    15: ('RegResultApplicationBusy', 'The function is not allowed to be invoked from within a callback function')
}


def unknown_error(result):
    return 'UnknownError', 'Error number {}'.format(result)


def _log_debug(result, func, arguments):
    Connection.log_debug('NKT.%s%s -> %s', func.__name__, arguments, result)
    return result


def _check_port_result(result, func, arguments):
    _log_debug(result, func, arguments)
    if result != 0:
        err, msg = _port_errors.get(result, unknown_error(result))
        raise NKTError('{}: {}'.format(err, msg))
    return result


def _check_p2p_result(result, func, arguments):
    _log_debug(result, func, arguments)
    if result != 0:
        err, msg = _p2p_errors.get(result, unknown_error(result))
        raise NKTError('{}: {}'.format(err, msg))
    return result


def _check_device_result(result, func, arguments):
    _log_debug(result, func, arguments)
    if result != 0:
        err, msg = _device_errors.get(result, unknown_error(result))
        raise NKTError('{}: {}'.format(err, msg))
    return result


def _check_register_result(result, func, arguments):
    _log_debug(result, func, arguments)
    if result != 0:
        err, msg = _register_errors.get(result, unknown_error(result))
        raise NKTError('{}: {}'.format(err, msg))
    return result
