"""Wrapper around the `NKTPDLL.dll` SDK from [NKT Photonics](https://www.nktphotonics.com/).

The wrapper was written using v2.1.2.766 of the SDK.
"""

# cSpell: ignore superk Acoustik portnames portname partnumber
from __future__ import annotations

import os
from ctypes import (
    CFUNCTYPE,
    POINTER,
    Structure,
    c_byte,
    c_char,
    c_char_p,
    c_double,
    c_float,
    c_long,
    c_longlong,
    c_short,
    c_ubyte,
    c_uint8,
    c_ulong,
    c_ulonglong,
    c_ushort,
    c_void_p,
    create_string_buffer,
)
from dataclasses import dataclass
from enum import IntEnum
from typing import TYPE_CHECKING, Any, final

from msl.loadlib import IS_PYTHON_64BIT, LoadLibrary

from msl.equipment.interfaces import MSLConnectionError
from msl.equipment.schema import Interface
from msl.equipment.utils import logger

if TYPE_CHECKING:
    from ctypes import CDLL, _CFunctionType  # pyright: ignore[reportPrivateUsage]
    from typing import Any

    from msl.equipment._types import NKTDeviceStatusCallback, NKTPortStatusCallback, NKTRegisterStatusCallback, PathLike
    from msl.equipment.schema import Equipment


# The example code that comes with the SDK uses NKTP_SDK_PATH
_path = os.environ.get("NKTP_SDK_PATH", "")
if _path:
    x = "x64" if IS_PYTHON_64BIT else "x86"
    _path += f"/NKTPDLL/{x}/NKTPDLL.dll"
else:
    _path = "NKTPDLL.dll"


PortStatusCallback = CFUNCTYPE(None, c_char_p, c_ubyte, c_ubyte, c_ubyte, c_ubyte)
"""A callback function when the status of a port changes."""


def port_status_callback(f: NKTPortStatusCallback) -> _CFunctionType:
    """Used as a decorator for a callback function when the status of a port changes.

    See [superk_callback.py](https://github.com/MSLNZ/msl-equipment/blob/main/packages/resources/examples/nkt/superk_callback.py)
    for an example usage.
    """
    return PortStatusCallback(f)


DeviceStatusCallback = CFUNCTYPE(None, c_char_p, c_ubyte, c_ubyte, c_ubyte, c_void_p)
"""A callback function when the status of a device changes."""


def device_status_callback(f: NKTDeviceStatusCallback) -> _CFunctionType:
    """Used as a decorator for a callback function when the status of a device changes.

    See [superk_callback.py](https://github.com/MSLNZ/msl-equipment/blob/main/packages/resources/examples/nkt/superk_callback.py)
    for an example usage.
    """
    return DeviceStatusCallback(f)


RegisterStatusCallback = CFUNCTYPE(None, c_char_p, c_ubyte, c_ubyte, c_ubyte, c_ubyte, c_ubyte, c_void_p)
"""A callback function when the status of a register changes."""


def register_status_callback(f: NKTRegisterStatusCallback) -> _CFunctionType:
    """Used as a decorator for a callback function when the status of a register changes.

    See [superk_callback.py](https://github.com/MSLNZ/msl-equipment/blob/main/packages/resources/examples/nkt/superk_callback.py)
    for an example usage.
    """
    return RegisterStatusCallback(f)


@dataclass
class PointToPoint:
    """A point-to-point port.

    Args:
        host_address: The local ip address, e.g., `"192.168.1.67"`.
        host_port: The local port number.
        client_address: The remote ip address, e.g., `"192.168.1.100"`.
        client_port: The remote port number.
        protocol: Either `0` (TCP) or `1` (UDP).
        ms_timeout: Telegram timeout value in milliseconds.
    """

    host_address: str
    host_port: int
    client_address: str
    client_port: int
    protocol: int
    ms_timeout: int


@final
class DateTime(Structure):
    """The DateTimeType struct (24 hour format).

    Attributes:
        Sec (c_uint8): Second.
        Min (c_uint8): Minute.
        Hour (c_uint8): Hour.
        Day (c_uint8): Day.
        Month (c_uint8): Month.
        Year (c_uint8): Year.
    """

    _pack_ = 1
    _fields_ = (
        ("Sec", c_uint8),
        ("Min", c_uint8),
        ("Hour", c_uint8),
        ("Day", c_uint8),
        ("Month", c_uint8),
        ("Year", c_uint8),
    )


@final
class ParameterSet(Structure):
    """The ParameterSet struct.

    This is how a calculation on parameter sets is done internally by modules:

    DAC_value = (value * (X/Y)) + Offset

    where, value is either `ParameterSet.StartVal` or `ParameterSet.FactoryVal`

    value = (ADC_value * (X/Y)) + Offset

    where, value often is available via another measurement register.

    Attributes:
        Unit (c_uint8): Unit type as defined in tParamSetUnitTypes.
        ErrorHandler (c_uint8): Warning/Error handler not used.
        StartVal (c_ushort): Setpoint for Settings parameter set, unused in Measurement parameter sets.
        FactoryVal (c_ushort): Factory Setpoint for Settings parameter set, unused in Measurement parameter sets.
        ULimit (c_ushort): Upper limit.
        LLimit (c_ushort): Lower limit.
        Numerator (c_short): Numerator(X) for calculation.
        Denominator (c_short): Denominator(Y) for calculation.
        Offset (c_short): Offset for calculation.
    """

    _pack_ = 1
    _fields_ = (
        ("Unit", c_uint8),
        ("ErrorHandler", c_uint8),
        ("StartVal", c_ushort),
        ("FactoryVal", c_ushort),
        ("ULimit", c_ushort),
        ("LLimit", c_ushort),
        ("Numerator", c_short),
        ("Denominator", c_short),
        ("Offset", c_short),
    )


class DeviceMode(IntEnum):
    """The DeviceModeTypes enum.

    Attributes:
        Disabled (int): The device is disabled. Not being polled and serviced, `0`.
        AnalyseInit (int): The analyse cycle has been started for the device, `1`.
        Analyse (int): The analyse cycle is in progress. All default registers being
            read to determine its state, `2`.
        Normal (int): The analyse cycle has completed and the device is ready, `3`.
        LogDownload (int): A log is being downloaded from the device, `4`.
        Error (int): The device is in an error state, `5`.
        Timeout (int): The connection to the device has been lost, `6`.
        Upload (int): The device is in upload mode and can not be used normally, `7`.
    """

    Disabled = 0
    AnalyseInit = 1
    Analyse = 2
    Normal = 3
    LogDownload = 4
    Error = 5
    Timeout = 6
    Upload = 7


class DeviceStatus(IntEnum):
    """The DeviceStatusTypes enum.

    Attributes:
        ModeChanged (int): Data contains 1 unsigned byte
            [DeviceMode][msl.equipment_resources.nkt.nktpdll.DeviceMode], `0`.
        LiveChanged (int): Data contains 1 unsigned byte, 0=live off, 1=live on, `1`.
        TypeChanged (int): Data contains 1 unsigned byte with DeviceType, `2`.
        PartNumberChanged (int): Data contains a zero terminated string with part number, `3`.
        PCBVersionChanged (int): Data contains 1 unsigned byte with PCB version number, `4`.
        StatusBitsChanged (int): Data contains 1 unsigned long with status bits, `5`.
        ErrorCodeChanged (int): Data contains 1 unsigned short with error code, `6`.
        BlVerChanged (int): Data contains a zero terminated string with Bootloader version, `7`.
        FwVerChanged (int): Data contains a zero terminated string with Firmware version, `8`.
        ModuleSerialChanged (int): Data contains a zero terminated string with Module serial number, `9`.
        PCBSerialChanged (int): Data contains a zero terminated string with PCB serial number, `10`.
        SysTypeChanged (int): Data contains 1 unsigned byte with SystemType, `11`.
    """

    ModeChanged = 0
    LiveChanged = 1
    TypeChanged = 2
    PartNumberChanged = 3
    PCBVersionChanged = 4
    StatusBitsChanged = 5
    ErrorCodeChanged = 6
    BlVerChanged = 7
    FwVerChanged = 8
    ModuleSerialChanged = 9
    PCBSerialChanged = 10
    SysTypeChanged = 11


class Unit(IntEnum):
    """The ParamSetUnitTypes enum.

    Attributes:
        NONE (int): None/Unknown, `0`.
        mV (int): mV, `1`.
        V (int): V, `2`.
        uA (int): uA, `3`.
        mA (int): mA, `4`.
        A (int): A, `5`.
        uW (int): uW, `6`.
        cmW (int): mW/100, `7`.
        dmW (int): mW/10, `8`.
        mW (int): mW, `9`.
        W (int): W, `10`.
        mC (int): degC/1000, `11`.
        cC (int): degC/100, `12`.
        dC (int): degC/10, `13`.
        pm (int): pm, `14`.
        dnm (int): nm/10, `15`.
        nm (int): nm, `16`.
        percent (int): %, `17`.
        perMile (int): per mile, `18`.
        cmA (int): mA/100, `19`.
        dmA (int): mA/10, `20`.
        RPM (int): RPM, `21`.
        dBm (int): dBm, `22`.
        cBm (int): dBm/10, `23`.
        mBm (int): dBm/100, `24`.
        dB (int): dB, `25`.
        cB (int): dB/10, `26`.
        mB (int): dB/100, `27`.
        dpm (int): pm/10, `28`.
        cV (int): V/100, `29`.
        dV (int): V/10, `30`.
        lm (int): lm (lumen), `31`.
        dlm (int): lm/10, `32`.
        clm (int): lm/100, `33`.
        mlm (int): lm/1000, `34`.
    """

    NONE = 0
    mV = 1  # noqa: N815
    V = 2
    uA = 3  # noqa: N815
    mA = 4  # noqa: N815
    A = 5
    uW = 6  # noqa: N815
    cmW = 7  # noqa: N815
    dmW = 8  # noqa: N815
    mW = 9  # noqa: N815
    W = 10
    mC = 11  # noqa: N815
    cC = 12  # noqa: N815
    dC = 13  # noqa: N815
    pm = 14
    dnm = 15
    nm = 16
    percent = 17
    perMile = 18  # noqa: N815
    cmA = 19  # noqa: N815
    dmA = 20  # noqa: N815
    RPM = 21
    dBm = 22  # noqa: N815
    cBm = 23  # noqa: N815
    mBm = 24  # noqa: N815
    dB = 25  # noqa: N815
    cB = 26  # noqa: N815
    mB = 27  # noqa: N815
    dpm = 28
    cV = 29  # noqa: N815
    dV = 30  # noqa: N815
    lm = 31
    dlm = 32
    clm = 33
    mlm = 34


class RegisterPriority(IntEnum):
    """The RegisterPriorityTypes enum.

    Attributes:
        Low (int): The register is polled with low priority, `0`.
        High (int): The register is polled with high priority, `1`.
    """

    Low = 0
    High = 1


class RegisterData(IntEnum):
    """The RegisterDataTypes enum.

    Attributes:
        UNKNOWN (int): Unknown/Undefined data type, `0`.
        MIXED (int): Mixed content data type, `1`.
        U8 (int): 8-bit unsigned data type (unsigned char), `2`.
        S8 (int): 8-bit signed data type (char), `3`.
        U16 (int): 16-bit unsigned data type (unsigned short), `4`.
        S16 (int): 16-bit signed data type (short), `5`.
        U32 (int): 32-bit unsigned data type (unsigned long), `6`.
        S32 (int): 32-bit signed data type (long), `7`.
        F32 (int): 32-bit floating point data type (float), `8`.
        U64 (int): 64-bit unsigned data type (unsigned long long), `9`.
        S64 (int): 64-bit signed data type (long long), `10`.
        F64 (int): 64-bit floating point data type (double), `11`.
        ASCII (int): Zero terminated ascii string data type, `12`.
        ParamSet (int): [ParameterSet][msl.equipment_resources.nkt.nktpdll.ParameterSet] data type, `13`.
        B8 (int): 8-bit binary data type (unsigned char), `14`.
        H8 (int): 8-bit hexadecimal data type (unsigned char), `15`.
        B16 (int): 16-bit binary data type (unsigned short), `16`.
        H16 (int): 16-bit hexadecimal data type (unsigned short), `17`.
        B32 (int): 32-bit binary data type (unsigned long), `18`.
        H32 (int): 32-bit hexadecimal data type (unsigned long), `19`.
        B64 (int): 64-bit binary data type (unsigned long long), `20`.
        H64 (int): 64-bit hexadecimal data type (unsigned long long), `21`.
        DATETIME (int): [DateTime][msl.equipment_resources.nkt.nktpdll.DateTime] data type, `22`.
    """

    UNKNOWN = 0
    MIXED = 1
    U8 = 2
    S8 = 3
    U16 = 4
    S16 = 5
    U32 = 6
    S32 = 7
    F32 = 8
    U64 = 9
    S64 = 10
    F64 = 11
    ASCII = 12
    ParamSet = 13
    B8 = 14
    H8 = 15
    B16 = 16
    H16 = 17
    B32 = 18
    H32 = 19
    B64 = 20
    H64 = 21
    DATETIME = 22


class RegisterStatus(IntEnum):
    """The RegisterStatusTypes enum.

    Attributes:
        Success (int): Register operation was successful `0`.
        Busy (int): Register operation resulted in a busy, `1`.
        Knackered (int): Register operation resulted in a knackered register (a non-existing register), `2`.
        CRCErr (int): Register operation resulted in a CRC error, `3`.
        Timeout (int): Register operation resulted in a timeout, `4`.
        ComError (int): Register operation resulted in a COM error. Out of sync. or garbage error, `5`.
    """

    Success = 0
    Busy = 1
    Knackered = 2
    CRCErr = 3
    Timeout = 4
    ComError = 5


class PortStatus(IntEnum):
    """The PortStatusTypes enum.

    Attributes:
        Unknown (int): Unknown status, `0`.
        Opening (int): The port is opening, `1`.
        Opened (int): The port is now open, `2`.
        OpenFail (int): The port open failed, `3`.
        ScanStarted (int): The port scanning is started, `4`.
        ScanProgress (int): The port scanning progress, `5`.
        ScanDeviceFound (int): The port scan found a device, `6`.
        ScanEnded (int): The port scanning ended, `7`.
        Closing (int): The port is closing, `8`.
        Closed (int): The port is now closed, `9`.
        Ready (int): The port is open and ready, `10`.
    """

    Unknown = 0
    Opening = 1
    Opened = 2
    OpenFail = 3
    ScanStarted = 4
    ScanProgress = 5
    ScanDeviceFound = 6
    ScanEnded = 7
    Closing = 8
    Closed = 9
    Ready = 10


class NKT(Interface, manufacturer=r"^NKT"):
    """Wrapper around the `NKTPDLL.dll` SDK from [NKT Photonics](https://www.nktphotonics.com/)."""

    _SDK: CDLL | None = None

    def __init__(self, equipment: Equipment) -> None:
        """Wrapper around the `NKTPDLL.dll` SDK from [NKT Photonics](https://www.nktphotonics.com/).

        Args:
            equipment: An [Equipment][] instance.

        A [Connection][msl.equipment.schema.Connection] instance supports the following _properties_
        for the NKT wrapper.

        Attributes: Connection Properties:
            sdk_path (str): The path to the SDK library. _Default: `"NKTPDLL.dll"`_
            open_port (bool): Whether to automatically open the port. _Default: `True`_
            auto (bool): Whether to open the port with bus scanning. _Default: `True`_
            live (bool): Whether to open the port in live mode. _Default: `True`_
        """
        super().__init__(equipment)

        assert equipment.connection is not None  # noqa: S101
        address = equipment.connection.address
        self._portname: bytes = address.encode()

        p = equipment.connection.properties
        _load_sdk(p.get("sdk_path", _path), self)
        assert NKT._SDK is not None  # noqa: S101

        self._sdk: CDLL = NKT._SDK
        if p.get("open_port", True):
            NKT.open_ports(address, auto=p.get("auto", True), live=p.get("live", True))

    def _check_port_result(self, result: Any, func: Any, arguments: tuple[Any, ...]) -> Any:  # noqa: ANN401
        _log_debug(result, func, arguments)
        if result != 0:
            err, msg = _port_errors.get(result, ("UnknownError", f"Unknown error [code={result}]"))
            raise MSLConnectionError(self, f"{err}: {msg}")
        return result

    def _check_p2p_result(self, result: Any, func: Any, arguments: tuple[Any, ...]) -> Any:  # noqa: ANN401
        _log_debug(result, func, arguments)
        if result != 0:
            err, msg = _p2p_errors.get(result, ("UnknownError", f"Unknown error [code={result}]"))
            raise MSLConnectionError(self, f"{err}: {msg}")
        return result

    def _check_device_result(self, result: Any, func: Any, arguments: tuple[Any, ...]) -> Any:  # noqa: ANN401
        _log_debug(result, func, arguments)
        if result != 0:
            err, msg = _device_errors.get(result, ("UnknownError", f"Unknown error [code={result}]"))
            raise MSLConnectionError(self, f"{err}: {msg}")
        return result

    def _check_register_result(self, result: Any, func: Any, arguments: tuple[Any, ...]) -> Any:  # noqa: ANN401
        _log_debug(result, func, arguments)
        if result != 0:
            err, msg = _register_errors.get(result, ("UnknownError", f"Unknown error [code={result}]"))
            raise MSLConnectionError(self, f"{err}: {msg}")
        return result

    @staticmethod
    def close_ports(*ports: str) -> None:
        """Close the specified port(s).

        Args:
            ports: The name(s) of the port(s) to close. If not specified, close all opened ports.
                Port names are case sensitive.
        """
        if NKT._SDK is None:
            return

        _names = b",".join(port.encode() for port in ports)
        NKT._SDK.closePorts(ports)

    @staticmethod
    def load_sdk(path: PathLike | None = None) -> None:
        """Load the SDK.

        Args:
            path: The path to `NKTPDLL.dll`. Reads from the `NKTP_SDK_PATH` environment
                variable if not specified.
        """
        _load_sdk(_path if not path else os.fsdecode(path))

    @staticmethod
    def device_get_all_types(*ports: str, size: int = 255) -> dict[str, dict[str, int]]:
        """Returns all device types (module types) from the internal device list.

        Args:
            ports: A port or multiple ports. If not specified then the
                [get_open_ports][msl.equipment_resources.nkt.nktpdll.NKT.get_open_ports]
                method is called.
            size: The maximum number of bytes that the device list can be.

        Returns:
            The port names are the keys and each value is [dict][] with the
                module type as the keys and its corresponding device ID as the value.
        """
        if NKT._SDK is None:
            msg = "NKTError: You must first call NKT.load_sdk()"
            raise RuntimeError(msg)

        if not ports:
            opened_ports = [port.encode() for port in NKT.get_open_ports()]
        else:
            opened_ports = [port.encode() for port in ports]

        out: dict[str, dict[str, int]] = {}
        length = c_ubyte(size)
        types = create_string_buffer(size)
        for port in opened_ports:
            NKT._SDK.deviceGetAllTypes(port, types, length)
            key = port.decode()
            out[key] = {}
            for dev_id, typ in enumerate(types.raw):
                if typ != 0:
                    out[key][f"0x{typ:02X}"] = dev_id
        return out

    def device_create(self, device_id: int, *, wait_ready: bool) -> None:
        """Creates a device in the internal device list.

        If the [open_ports][msl.equipment_resources.nkt.nktpdll.NKT.open_ports] function has
        been called with `live=True` then the kernel immediately starts to monitor the device.

        Args:
            device_id: The device id (module address).
            wait_ready: `False` means don't wait for the device to be ready. `True` means to
                wait up to 2 seconds for the device to complete its analyse cycle.
                (All standard registers being successfully read)
        """
        self._sdk.deviceCreate(self._portname, device_id, int(bool(wait_ready)))

    def device_exists(self, device_id: int) -> bool:
        """Checks if a specific device already exists in the internal device list.

        Args:
            device_id: The device id (module address).

        Returns:
            Whether the device exists.
        """
        exists = c_ubyte(0)
        self._sdk.deviceExists(self._portname, device_id, exists)
        return bool(exists.value)

    def device_get_boot_loader_version(self, device_id: int) -> int:
        """Returns the boot-loader version (int) for a given device id.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated read.

        Args:
            device_id: The device id (module address).

        Returns:
            The boot-loader version.
        """
        version = c_ushort(0)
        self._sdk.deviceGetBootloaderVersion(self._portname, device_id, version)
        return version.value

    def device_get_boot_loader_version_str(self, device_id: int) -> str:
        """Returns the boot-loader version (string) for a given device id.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated read.

        Args:
            device_id: The device id (module address).

        Returns:
            The boot-loader version.
        """
        size = c_ubyte(255)
        version = create_string_buffer(size.value)
        self._sdk.deviceGetBootloaderVersionStr(self._portname, device_id, version, size)
        return bytes(version.value).decode()

    def device_get_error_code(self, device_id: int) -> int:
        """Returns the error code for a given device id.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated read.

        Args:
            device_id: The device id (module address).

        Returns:
            The error code.
        """
        error_code = c_ushort(0)
        self._sdk.deviceGetErrorCode(self._portname, device_id, error_code)
        return error_code.value

    def device_get_firmware_version(self, device_id: int) -> int:
        """Returns the firmware version (int) for a given device id.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated read.

        Args:
            device_id: The device id (module address).

        Returns:
            The firmware version.
        """
        version = c_ushort(0)
        self._sdk.deviceGetFirmwareVersion(self._portname, device_id, version)
        return version.value

    def device_get_firmware_version_str(self, device_id: int) -> str:
        """Returns the firmware version (string) for a given device id.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated read.

        Args:
            device_id: The device id (module address).

        Returns:
            The firmware version.
        """
        size = c_ubyte(255)
        version = create_string_buffer(size.value)
        self._sdk.deviceGetFirmwareVersionStr(self._portname, device_id, version, size)
        return bytes(version.value).decode()

    def device_get_live(self, device_id: int) -> bool:
        """Returns the internal device live status for a specific device id.

        Requires the port being already opened with the [open_ports][msl.equipment_resources.nkt.nktpdll.NKT.open_ports]
        function and the device being already created, either automatically or with the
        [device_create][msl.equipment_resources.nkt.nktpdll.NKT.device_create] function.

        Args:
            device_id: The device id (module address).

        Returns:
            Whether live mode is enabled.
        """
        live_mode = c_ubyte(0)
        self._sdk.deviceGetLive(self._portname, device_id, live_mode)
        return bool(live_mode.value)

    def device_get_mode(self, device_id: int) -> DeviceMode:
        """Returns the internal device mode for a specific device id.

        Requires the port being already opened with the [open_ports][msl.equipment_resources.nkt.nktpdll.NKT.open_ports]
        function and the device being already created, either automatically or with the
        [device_create][msl.equipment_resources.nkt.nktpdll.NKT.device_create] function.

        Args:
            device_id: The device id (module address).

        Returns:
            The device mode type.
        """
        dev_mode = c_ubyte(0)
        self._sdk.deviceGetMode(self._portname, device_id, dev_mode)
        return DeviceMode(dev_mode.value)

    def device_get_module_serial_number_str(self, device_id: int) -> str:
        """Returns the module serial number (string) for a given device id.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated read.

        Args:
            device_id: The device id (module address).

        Returns:
            The serial number.
        """
        size = c_ubyte(255)
        serial = create_string_buffer(size.value)
        self._sdk.deviceGetModuleSerialNumberStr(self._portname, device_id, serial, size)
        return bytes(serial.value).decode()

    def device_get_part_number_str(self, device_id: int) -> str:
        """Returns the part number for a given device id.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated read.

        Args:
            device_id: The device id (module address).

        Returns:
            The part number.
        """
        size = c_ubyte(255)
        part = create_string_buffer(size.value)
        self._sdk.deviceGetPartNumberStr(self._portname, device_id, part, size)
        return bytes(part.value).decode()

    def device_get_pcb_serial_number_str(self, device_id: int) -> str:
        """Returns the PCB serial number (string) for a given device id.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated read.

        Args:
            device_id: The device id (module address).

        Returns:
            The part number.
        """
        size = c_ubyte(255)
        serial = create_string_buffer(size.value)
        self._sdk.deviceGetPCBSerialNumberStr(self._portname, device_id, serial, size)
        return bytes(serial.value).decode()

    def device_get_pcb_version(self, device_id: int) -> int:
        """Returns the PCB version for a given device id.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated read.

        Args:
            device_id: The device id (module address).

        Returns:
            The PCB version number.
        """
        version = c_ubyte(0)
        self._sdk.deviceGetPCBVersion(self._portname, device_id, version)
        return version.value

    def device_get_status_bits(self, device_id: int) -> int:
        """Returns the status bits for a given device id.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated read.

        Args:
            device_id: The device id (module address).

        Returns:
            The status bits.
        """
        status = c_ushort(0)
        self._sdk.deviceGetStatusBits(self._portname, device_id, status)
        return status.value

    def device_get_type(self, device_id: int) -> int:
        """Returns the module type for a specific device id.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated read.

        Args:
            device_id: The device id (module address).

        Returns:
            The module type.
        """
        dev_type = c_ubyte(0)
        self._sdk.deviceGetType(self._portname, device_id, dev_type)
        return dev_type.value

    def device_remove(self, device_id: int) -> None:
        """Remove a specific device from the internal device list.

        Args:
            device_id: The device id (module address).
        """
        self._sdk.deviceRemove(self._portname, device_id)

    def device_remove_all(self) -> None:
        """Remove all devices from the internal device list.

        No confirmation is given, the list is simply cleared.
        """
        self._sdk.deviceRemoveAll(self._portname)

    def device_set_live(self, device_id: int, *, enabled: bool) -> None:
        """Sets the internal device live status for a specific device id (module address).

        Args:
            device_id: The device id (module address).
            enabled: Whether to enable (`True`) or disable (`False`) live status.
        """
        self._sdk.deviceSetLive(self._portname, device_id, int(enabled))

    def disconnect(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Disconnect from the port."""
        if hasattr(self, "_address") and self._portname:
            self.close_ports(self._portname.decode())
            self._portname = b""

    @staticmethod
    def get_all_ports(size: int = 255) -> list[str]:
        """Returns a list of all ports.

        Args:
            size: The maximum size of the string buffer to fetch the results.

        Returns:
            A list of port names.
        """
        if NKT._SDK is None:
            msg = "NKTError: You must first call NKT.load_sdk()"
            raise RuntimeError(msg)

        length = c_ushort(size)
        names = create_string_buffer(size)
        NKT._SDK.getAllPorts(names, length)
        return [name for name in bytes(names.value).decode().split(",") if name]

    def get_modules(self, size: int = 255) -> dict[str, int]:
        """Returns all device types (module types) from the device.

        Args:
            size: The maximum number of bytes that the device list can be.

        Returns:
            The module type as the keys and its corresponding device ID as the value.
        """
        a = self._portname.decode()
        return NKT.device_get_all_types(a, size=size)[a]

    @staticmethod
    def get_legacy_bus_scanning() -> bool:
        """Get the bus-scanning mode.

        Returns:
            `True` if in legacy mode, `False` if in normal mode.
        """
        if NKT._SDK is None:
            msg = "NKTError: You must first call NKT.load_sdk()"
            raise RuntimeError(msg)

        return bool(NKT._SDK.getLegacyBusScanning())

    @staticmethod
    def get_open_ports(size: int = 255) -> list[str]:
        """Returns a list of already-opened ports.

        Args:
            size: The maximum size of the string buffer to fetch the results.

        Returns:
            A list of port names that are already open.
        """
        if NKT._SDK is None:
            msg = "NKTError: You must first call NKT.load_sdk()"
            raise RuntimeError(msg)

        length = c_ushort(size)
        names = create_string_buffer(size)
        NKT._SDK.getOpenPorts(names, length)
        return [name for name in bytes(names.value).decode().split(",") if name]

    def get_port_error_msg(self) -> str:
        """Retrieve error message for the port.

        Returns:
            The error message. An empty string indicates no error.
        """
        length = c_ushort(255)
        msg = create_string_buffer(length.value)
        self._sdk.getPortErrorMsg(self._portname, msg, length)
        return bytes(msg.value).decode()

    def get_port_status(self) -> PortStatus:
        """Get the status of the port.

        Returns:
            The port status.
        """
        status = c_ubyte(0)
        self._sdk.getPortStatus(self._portname, status)
        return PortStatus(status.value)

    @staticmethod
    def open_ports(*names: str, auto: bool = True, live: bool = True) -> None:
        """Open the specified port(s).

        Repeated calls to this function is allowed to reopen and/or rescan for devices.

        Args:
            names: If not specified then open all available ports are opened. Port
                names are case sensitive. Example port names are `"AcoustikPort1"`, `"COM6"`.
            auto: If `True` then automatically start bus scanning and add the
                found devices in the internal device list. If `False` then
                bus scanning and device creation is not automatically handled. The
                port is automatically closed if no devices are found.
            live: If `True` then keep all the found or created devices in live
                mode, which means the inter-bus kernel keeps monitoring all the found
                devices and their registers. Please note that this will keep the modules
                watchdog alive as long as the port is open. If `False` then disable
                continuous monitoring of the registers. No callback is possible on register
                changes, so you must call the [register_read][msl.equipment_resources.nkt.nktpdll.NKT.register_read],
                [register_write][msl.equipment_resources.nkt.nktpdll.NKT.register_write] and
                [register_write_read][msl.equipment_resources.nkt.nktpdll.NKT.register_write_read]
                methods.
        """
        if NKT._SDK is None:
            msg = "NKTError: You must first call NKT.load_sdk()"
            raise RuntimeError(msg)

        _names = b",".join(name.encode() for name in names)
        NKT._SDK.openPorts(names, int(bool(auto)), int(bool(live)))

    def point_to_point_port_add(self, port: PointToPoint) -> None:
        """Creates or modifies a point-to-point port.

        Args:
            port: A point-to-point port.
        """
        self._sdk.pointToPointPortAdd(
            self._portname,
            port.host_address.encode(),
            port.host_port,
            port.client_address.encode(),
            port.client_port,
            port.protocol,
            port.ms_timeout,
        )

    def point_to_point_port_del(self) -> None:
        """Delete the point-to-point port."""
        self._sdk.pointToPointPortDel(self._portname)

    def point_to_point_port_get(self) -> PointToPoint:
        """Retrieve the information about the point-to-point port setting.

        Returns:
            The information about the point-to-point port setting.
        """
        host_length = c_ubyte(255)
        host_address = create_string_buffer(host_length.value)
        host_port = c_ushort(0)
        client_length = c_ubyte(255)
        client_address = create_string_buffer(client_length.value)
        client_port = c_ushort(0)
        protocol = c_ubyte(0)
        ms_timeout = c_ubyte(0)
        self._sdk.pointToPointPortGet(
            self._portname,
            host_address,
            host_length,
            host_port,
            client_address,
            client_length,
            client_port,
            protocol,
            ms_timeout,
        )
        return PointToPoint(
            host_address=host_address.value.decode(),
            host_port=host_port.value,
            client_address=client_address.value.decode(),
            client_port=client_port.value,
            protocol=protocol.value,
            ms_timeout=ms_timeout.value,
        )

    def register_read(self, device_id: int, reg_id: int, index: int = -1) -> bytes:
        """Reads a register value and returns the result.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated read.

        Args:
            device_id: The device id (module address).
            reg_id: The register id (register address).
            index: Value index. Typically -1, but could be used to extract data from
                a specific position in the register. Index is byte counted.

        Returns:
            The register value.
        """
        size = c_ubyte(255)
        data = create_string_buffer(size.value)
        self._sdk.registerRead(self._portname, device_id, reg_id, data, size, index)
        return data.raw[: size.value]

    def register_create(
        self, device_id: int, reg_id: int, priority: int | RegisterPriority, data: int | RegisterData
    ) -> None:
        """Creates a register in the internal register list.

        If the [open_ports][msl.equipment_resources.nkt.nktpdll.NKT.open_ports] function has
        been called with `live=True` then the kernel immediately starts to monitor the register.

        Args:
            device_id: The device id (module address).
            reg_id: The register id (register address).
            priority: The monitoring priority.
            data: The register data type. Not used internally but could be used in a
                common callback function to determine the data type.
        """
        self._sdk.registerCreate(self._portname, device_id, reg_id, RegisterPriority(priority), RegisterData(data))

    def register_exists(self, device_id: int, reg_id: int) -> bool:
        """Checks if a specific register already exists in the internal register list.

        Args:
            device_id: The device id (module address).
            reg_id: The register id (register address).

        Returns:
            Whether the register exists.
        """
        exists = c_ubyte(0)
        self._sdk.registerExists(self._portname, device_id, reg_id, exists)
        return bool(exists.value)

    def register_get_all(self, device_id: int) -> list[int]:
        """Returns the register ids (register addresses) from the internal register list.

        Args:
            device_id: The device id (module address).

        Returns:
            The register ids.
        """
        size = c_ubyte(255)
        regs = create_string_buffer(size.value)
        self._sdk.registerGetAll(self._portname, device_id, regs, size)
        ids: list[int] = list(regs.value)
        return ids

    def register_read_ascii(self, device_id: int, reg_id: int, index: int = -1) -> str:
        """Reads an ascii string from the register.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated read.

        Args:
            device_id: The device id (module address).
            reg_id: The register id (register address).
            index: Value index. Typically -1, but could be used to extract data from
                a specific position in the register. Index is byte counted.

        Returns:
            The ascii value.
        """
        size = c_ubyte(255)
        data = create_string_buffer(size.value)
        self._sdk.registerReadAscii(self._portname, device_id, reg_id, data, size, index)
        return bytes(data.value).decode()

    def register_read_f32(self, device_id: int, reg_id: int, index: int = -1) -> float:
        """Reads 32-bit float value from the register.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated read.

        Args:
            device_id: The device id (module address).
            reg_id: The register id (register address).
            index: Value index. Typically -1, but could be used to extract data from
                a specific position in the register. Index is byte counted.

        Returns:
            The 32-bit float value.
        """
        data = c_float(0)
        self._sdk.registerReadF32(self._portname, device_id, reg_id, data, index)
        return data.value

    def register_read_f64(self, device_id: int, reg_id: int, index: int = -1) -> float:
        """Reads 64-bit double value from the register.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated read.

        Args:
            device_id: The device id (module address).
            reg_id: The register id (register address).
            index: Value index. Typically -1, but could be used to extract data from
                a specific position in the register. Index is byte counted.

        Returns:
            The 64-bit double value.
        """
        data = c_double(0)
        self._sdk.registerReadF64(self._portname, device_id, reg_id, data, index)
        return data.value

    def register_read_s16(self, device_id: int, reg_id: int, index: int = -1) -> int:
        """Reads 16-bit signed short value from the register.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated read.

        Args:
            device_id: The device id (module address).
            reg_id: The register id (register address).
            index: Value index. Typically -1, but could be used to extract data from
                a specific position in the register. Index is byte counted.

        Returns:
            The 16-bit signed short value.
        """
        data = c_short(0)
        self._sdk.registerReadS16(self._portname, device_id, reg_id, data, index)
        return data.value

    def register_read_s32(self, device_id: int, reg_id: int, index: int = -1) -> int:
        """Reads 32-bit signed long value from the register.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated read.

        Args:
            device_id: The device id (module address).
            reg_id: The register id (register address).
            index: Value index. Typically -1, but could be used to extract data from
                a specific position in the register. Index is byte counted.

        Returns:
            The 32-bit signed long value.
        """
        data = c_long(0)
        self._sdk.registerReadS32(self._portname, device_id, reg_id, data, index)
        return data.value

    def register_read_s64(self, device_id: int, reg_id: int, index: int = -1) -> int:
        """Reads 64-bit signed long long value from the register.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated read.

        Args:
            device_id: The device id (module address).
            reg_id: The register id (register address).
            index: Value index. Typically -1, but could be used to extract data from
                a specific position in the register. Index is byte counted.

        Returns:
            The 64-bit signed long long value.
        """
        data = c_longlong(0)
        self._sdk.registerReadS64(self._portname, device_id, reg_id, data, index)
        return data.value

    def register_read_s8(self, device_id: int, reg_id: int, index: int = -1) -> int:
        """Reads 8-bit signed char value from the register.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated read.

        Args:
            device_id: The device id (module address).
            reg_id: The register id (register address).
            index: Value index. Typically -1, but could be used to extract data from
                a specific position in the register. Index is byte counted.

        Returns:
            The 8-bit signed char value.
        """
        data = c_byte(0)
        self._sdk.registerReadS8(self._portname, device_id, reg_id, data, index)
        return data.value

    def register_read_u16(self, device_id: int, reg_id: int, index: int = -1) -> int:
        """Reads 16-bit unsigned short value from the register.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated read.

        Args:
            device_id: The device id (module address).
            reg_id: The register id (register address).
            index: Value index. Typically -1, but could be used to extract data from
                a specific position in the register. Index is byte counted.

        Returns:
            The 16-bit unsigned short value.
        """
        data = c_ushort(0)
        self._sdk.registerReadU16(self._portname, device_id, reg_id, data, index)
        return data.value

    def register_read_u32(self, device_id: int, reg_id: int, index: int = -1) -> int:
        """Reads 32-bit unsigned long value from the register.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated read.

        Args:
            device_id: The device id (module address).
            reg_id: The register id (register address).
            index: Value index. Typically -1, but could be used to extract data from
                a specific position in the register. Index is byte counted.

        Returns:
            The 32-bit unsigned long value.
        """
        data = c_ulong(0)
        self._sdk.registerReadU32(self._portname, device_id, reg_id, data, index)
        return data.value

    def register_read_u64(self, device_id: int, reg_id: int, index: int = -1) -> int:
        """Reads 64-bit unsigned long long value from the register.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated read.

        Args:
            device_id: The device id (module address).
            reg_id: The register id (register address).
            index: Value index. Typically -1, but could be used to extract data from
                a specific position in the register. Index is byte counted.

        Returns:
            The 64-bit unsigned long long value.
        """
        data = c_ulonglong(0)
        self._sdk.registerReadU64(self._portname, device_id, reg_id, data, index)
        return data.value

    def register_read_u8(self, device_id: int, reg_id: int, index: int = -1) -> int:
        """Reads 8-bit unsigned char value from the register.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated read.

        Args:
            device_id: The device id (module address).
            reg_id: The register id (register address).
            index: Value index. Typically -1, but could be used to extract data from
                a specific position in the register. Index is byte counted.

        Returns:
            The 8-bit unsigned char value.
        """
        data = c_ubyte(0)
        self._sdk.registerReadU8(self._portname, device_id, reg_id, data, index)
        return data.value

    def register_remove(self, device_id: int, reg_id: int) -> None:
        """Remove a specific register from the internal register list.

        Args:
            device_id: The device id (module address).
            reg_id: The register id (register address).
        """
        self._sdk.registerRemove(self._portname, device_id, reg_id)

    def register_remove_all(self, device_id: int) -> None:
        """Remove all registers from the internal register list.

        No confirmation given, the list is simply cleared.

        Args:
            device_id: The device id (module address).
        """
        self._sdk.registerRemoveAll(self._portname, device_id)

    def register_write(self, device_id: int, reg_id: int, data: bytes, index: int = -1) -> None:
        """Writes a register value.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated write.

        Args:
            device_id: The device id (module address).
            reg_id: The register id (register address).
            data: The data to write to the register.
            index: Value index. Typically -1, but could be used to write a value in a multi-value register.
        """
        self._sdk.registerWrite(self._portname, device_id, reg_id, data, len(data), index)

    def register_write_ascii(
        self, device_id: int, reg_id: int, string: str, *, write_eol: bool = False, index: int = -1
    ) -> None:
        """Writes a string to the register value.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated write.

        Args:
            device_id: The device id (module address).
            reg_id: The register id (register address).
            string: The string to write to the register.
            write_eol: Whether to append the End Of Line character (a null character) to the string.
            index: Value index. Typically -1, but could be used to write a value in a mixed-type register.
        """
        buffer = create_string_buffer(string.encode("ascii"))
        self._sdk.registerWriteAscii(self._portname, device_id, reg_id, buffer, int(write_eol), index)

    def register_write_f32(self, device_id: int, reg_id: int, value: float, index: int = -1) -> None:
        """Writes a 32-bit float register value.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated write.

        Args:
            device_id: The device id (module address).
            reg_id: The register id (register address).
            value: The 32-bit float to write to the register.
            index: Value index. Typically -1, but could be used to write a value in a multi-value register.
        """
        self._sdk.registerWriteF32(self._portname, device_id, reg_id, value, index)

    def register_write_f64(self, device_id: int, reg_id: int, value: float, index: int = -1) -> None:
        """Writes a 64-bit double register value.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated write.

        Args:
            device_id: The device id (module address).
            reg_id: The register id (register address).
            value: The 64-bit double to write to the register.
            index: Value index. Typically -1, but could be used to write a value in a multi-value register.
        """
        self._sdk.registerWriteF64(self._portname, device_id, reg_id, value, index)

    def register_write_read(self, device_id: int, reg_id: int, data: bytes, index: int = -1) -> bytes:
        """Writes then reads a register value.

        It is not necessary to open the port, create the device or register before using
        this function, since it will do a dedicated write followed by a dedicated read.

        Args:
            device_id: The device id (module address).
            reg_id: The register id (register address).
            data: The data to write to the register.
            index: Value index. Typically -1, but could be used to write a value in a multi-value register.

        Returns:
            The data that was written to the register.
        """
        size = c_ubyte(255)
        read = create_string_buffer(size.value)
        self._sdk.registerWriteRead(self._portname, device_id, reg_id, data, len(data), index, read, size, index)
        return read.raw[: size.value]

    def register_write_read_ascii(
        self, device_id: int, reg_id: int, string: str, *, write_eol: bool = False, index: int = -1
    ) -> str:
        """Writes then reads a string register value.

        It is not necessary to open the port, create the device or register before using
        this function, since it will do a dedicated write followed by a dedicated read.

        Args:
            device_id: The device id (module address).
            reg_id: The register id (register address).
            string: The string to write to the register.
            write_eol: Whether to append the End Of Line character (a null character) to the string.
            index: Value index. Typically -1, but could be used to write a value in a multi-value register.

        Returns:
            The string that was written to the register.
        """
        ascii_value = create_string_buffer(string.encode("ascii"))
        size = c_ubyte(255)
        read = create_string_buffer(size.value)
        self._sdk.registerWriteReadAscii(
            self._portname, device_id, reg_id, ascii_value, int(write_eol), read, size, index
        )
        return bytes(read.value).decode("ascii")

    def register_write_read_f32(self, device_id: int, reg_id: int, value: float, index: int = -1) -> float:
        """Writes then reads a 32-bit float register value.

        It is not necessary to open the port, create the device or register before using
        this function, since it will do a dedicated write followed by a dedicated read.

        Args:
            device_id: The device id (module address).
            reg_id: The register id (register address).
            value: The 32-bit float value to write to the register.
            index: Value index. Typically -1, but could be used to write a value in a multi-value register.

        Returns:
            The 32-bit float value that was written to the register.
        """
        read = c_float(0)
        self._sdk.registerWriteReadF32(self._portname, device_id, reg_id, value, read, index)
        return read.value

    def register_write_read_f64(self, device_id: int, reg_id: int, value: float, index: int = -1) -> float:
        """Writes then reads a 64-bit double register value.

        It is not necessary to open the port, create the device or register before using
        this function, since it will do a dedicated write followed by a dedicated read.

        Args:
            device_id: The device id (module address).
            reg_id: The register id (register address).
            value: The 64-bit double value to write to the register.
            index: Value index. Typically -1, but could be used to write a value in a multi-value register.

        Returns:
            The 64-bit double value that was written to the register.
        """
        read = c_double(0)
        self._sdk.registerWriteReadF64(self._portname, device_id, reg_id, value, read, index)
        return read.value

    def register_write_read_s16(self, device_id: int, reg_id: int, value: int, index: int = -1) -> int:
        """Writes then reads a 16-bit signed short register value.

        It is not necessary to open the port, create the device or register before using
        this function, since it will do a dedicated write followed by a dedicated read.

        Args:
            device_id: The device id (module address).
            reg_id: The register id (register address).
            value: The 16-bit signed short value to write to the register.
            index: Value index. Typically -1, but could be used to write a value in a multi-value register.

        Returns:
            The 16-bit signed short value that was written to the register.
        """
        read = c_short(0)
        self._sdk.registerWriteReadS16(self._portname, device_id, reg_id, value, read, index)
        return read.value

    def register_write_read_s32(self, device_id: int, reg_id: int, value: int, index: int = -1) -> int:
        """Writes then reads a 32-bit signed long register value.

        It is not necessary to open the port, create the device or register before using
        this function, since it will do a dedicated write followed by a dedicated read.

        Args:
            device_id: The device id (module address).
            reg_id: The register id (register address).
            value: The 32-bit signed long value to write to the register.
            index: Value index. Typically -1, but could be used to write a value in a multi-value register.

        Returns:
            The 32-bit signed long value that was written to the register.
        """
        read = c_long(0)
        self._sdk.registerWriteReadS32(self._portname, device_id, reg_id, value, read, index)
        return read.value

    def register_write_read_s64(self, device_id: int, reg_id: int, value: int, index: int = -1) -> int:
        """Writes then reads a 64-bit signed long long register value.

        It is not necessary to open the port, create the device or register before using
        this function, since it will do a dedicated write followed by a dedicated read.

        Args:
            device_id: The device id (module address).
            reg_id: The register id (register address).
            value: The 64-bit signed long long value to write to the register.
            index: Value index. Typically -1, but could be used to write a value in a multi-value register.

        Returns:
            The 64-bit signed long long value that was written to the register.
        """
        read = c_longlong(0)
        self._sdk.registerWriteReadS64(self._portname, device_id, reg_id, value, read, index)
        return read.value

    def register_write_read_s8(self, device_id: int, reg_id: int, value: int, index: int = -1) -> int:
        """Writes then reads a 8-bit signed char register value.

        It is not necessary to open the port, create the device or register before using
        this function, since it will do a dedicated write followed by a dedicated read.

        Args:
            device_id: The device id (module address).
            reg_id: The register id (register address).
            value: The 8-bit signed char value to write to the register.
            index: Value index. Typically -1, but could be used to write a value in a multi-value register.

        Returns:
            The 8-bit signed char value that was written to the register.
        """
        read = c_byte(0)
        self._sdk.registerWriteReadS8(self._portname, device_id, reg_id, value, read, index)
        return read.value

    def register_write_read_u16(self, device_id: int, reg_id: int, value: int, index: int = -1) -> int:
        """Writes then reads a 16-bit unsigned short register value.

        It is not necessary to open the port, create the device or register before using
        this function, since it will do a dedicated write followed by a dedicated read.

        Args:
            device_id: The device id (module address).
            reg_id: The register id (register address).
            value: The 16-bit unsigned short value to write to the register.
            index: Value index. Typically -1, but could be used to write a value in a multi-value register.

        Returns:
            The 16-bit unsigned short value that was written to the register.
        """
        read = c_ushort(0)
        self._sdk.registerWriteReadU16(self._portname, device_id, reg_id, value, read, index)
        return read.value

    def register_write_read_u32(self, device_id: int, reg_id: int, value: int, index: int = -1) -> int:
        """Writes then reads a 32-bit unsigned long register value.

        It is not necessary to open the port, create the device or register before using
        this function, since it will do a dedicated write followed by a dedicated read.

        Args:
            device_id: The device id (module address).
            reg_id: The register id (register address).
            value: The 32-bit unsigned long value to write to the register.
            index: Value index. Typically -1, but could be used to write a value in a multi-value register.

        Returns:
            The 32-bit unsigned long value that was written to the register.
        """
        read = c_ulong(0)
        self._sdk.registerWriteReadU32(self._portname, device_id, reg_id, value, read, index)
        return read.value

    def register_write_read_u64(self, device_id: int, reg_id: int, value: int, index: int = -1) -> int:
        """Writes then reads a 64-bit unsigned long long register value.

        It is not necessary to open the port, create the device or register before using
        this function, since it will do a dedicated write followed by a dedicated read.

        Args:
            device_id: The device id (module address).
            reg_id: The register id (register address).
            value: The 64-bit unsigned long long value to write to the register.
            index: Value index. Typically -1, but could be used to write a value in a multi-value register.

        Returns:
            The 64-bit unsigned long long value that was written to the register.
        """
        read = c_ulonglong(0)
        self._sdk.registerWriteReadU64(self._portname, device_id, reg_id, value, read, index)
        return read.value

    def register_write_read_u8(self, device_id: int, reg_id: int, value: int, index: int = -1) -> int:
        """Writes then reads a 8-bit unsigned char register value.

        It is not necessary to open the port, create the device or register before using
        this function, since it will do a dedicated write followed by a dedicated read.

        Args:
            device_id: The device id (module address).
            reg_id: The register id (register address).
            value: The 8-bit unsigned char value to write to the register.
            index: Value index. Typically -1, but could be used to write a value in a multi-value register.

        Returns:
            The 8-bit unsigned char value that was written to the register.
        """
        read = c_ubyte(0)
        self._sdk.registerWriteReadU8(self._portname, device_id, reg_id, value, read, index)
        return read.value

    def register_write_s16(self, device_id: int, reg_id: int, value: int, index: int = -1) -> None:
        """Writes a 16-bit signed short register value.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated write.

        Args:
            device_id: The device id (module address).
            reg_id: The register id (register address).
            value: The 16-bit signed short to write to the register.
            index: Value index. Typically -1, but could be used to write a value in a multi-value register.
        """
        self._sdk.registerWriteS16(self._portname, device_id, reg_id, value, index)

    def register_write_s32(self, device_id: int, reg_id: int, value: int, index: int = -1) -> None:
        """Writes a 32-bit signed long register value.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated write.

        Args:
            device_id: The device id (module address).
            reg_id: The register id (register address).
            value: The 32-bit signed long to write to the register.
            index: Value index. Typically -1, but could be used to write a value in a multi-value register.
        """
        self._sdk.registerWriteS32(self._portname, device_id, reg_id, value, index)

    def register_write_s64(self, device_id: int, reg_id: int, value: int, index: int = -1) -> None:
        """Writes a 64-bit signed long long register value.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated write.

        Args:
            device_id: The device id (module address).
            reg_id: The register id (register address).
            value: The 64-bit signed long long to write to the register.
            index: Value index. Typically -1, but could be used to write a value in a multi-value register.
        """
        self._sdk.registerWriteS64(self._portname, device_id, reg_id, value, index)

    def register_write_s8(self, device_id: int, reg_id: int, value: int, index: int = -1) -> None:
        """Writes a 8-bit signed char register value.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated write.

        Args:
            device_id: The device id (module address).
            reg_id: The register id (register address).
            value: The 8-bit signed char to write to the register.
            index: Value index. Typically -1, but could be used to write a value in a multi-value register.
        """
        self._sdk.registerWriteS8(self._portname, device_id, reg_id, value, index)

    def register_write_u16(self, device_id: int, reg_id: int, value: int, index: int = -1) -> None:
        """Writes a 16-bit unsigned short register value.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated write.

        Args:
            device_id: The device id (module address).
            reg_id: The register id (register address).
            value: The 16-bit unsigned short to write to the register.
            index: Value index. Typically -1, but could be used to write a value in a multi-value register.
        """
        self._sdk.registerWriteU16(self._portname, device_id, reg_id, value, index)

    def register_write_u32(self, device_id: int, reg_id: int, value: int, index: int = -1) -> None:
        """Writes a 32-bit unsigned long register value.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated write.

        Args:
            device_id: The device id (module address).
            reg_id: The register id (register address).
            value: The 32-bit unsigned long to write to the register.
            index: Value index. Typically -1, but could be used to write a value in a multi-value register.
        """
        self._sdk.registerWriteU32(self._portname, device_id, reg_id, value, index)

    def register_write_u64(self, device_id: int, reg_id: int, value: int, index: int = -1) -> None:
        """Writes a 64-bit unsigned long long register value.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated write.

        Args:
            device_id: The device id (module address).
            reg_id: The register id (register address).
            value: The 64-bit unsigned long long to write to the register.
            index: Value index. Typically -1, but could be used to write a value in a multi-value register.
        """
        self._sdk.registerWriteU64(self._portname, device_id, reg_id, value, index)

    def register_write_u8(self, device_id: int, reg_id: int, value: int, index: int = -1) -> None:
        """Writes a 8-bit unsigned char register value.

        It is not necessary to open the port, create the device or register before
        using this function, since it will do a dedicated write.

        Args:
            device_id: The device id (module address).
            reg_id: The register id (register address).
            value: The 8-bit unsigned char to write to the register.
            index: Value index. Typically -1, but could be used to write a value in a multi-value register.
        """
        self._sdk.registerWriteU8(self._portname, device_id, reg_id, value, index)

    @staticmethod
    def set_legacy_bus_scanning(*, mode: bool) -> None:
        """Set the bus-scanning mode to normal or legacy.

        Args:
            mode: If `False`, bus scanning is set to normal mode and allows for a
                rolling _masterId_. In this mode the _masterId_ is changed for each
                message to allow for out-of-sync detection. If `True`, bus scanning
                is set to legacy mode and fixes the _masterId_ at address 66 (0x42).
                Some older modules do not accept _masterIds_ other than 66 (0x42).
        """
        if NKT._SDK is None:
            msg = "NKTError: You must first call NKT.load_sdk()"
            raise RuntimeError(msg)

        NKT._SDK.setLegacyBusScanning(int(bool(mode)))

    @staticmethod
    def set_callback_device_status(callback: NKTDeviceStatusCallback | None) -> None:
        """Enables/Disables a callback for device status changes.

        See [superk_callback.py](https://github.com/MSLNZ/msl-equipment/blob/main/packages/resources/examples/nkt/superk_callback.py)
        for an example usage.

        !!! note
            Due to a risk of circular runaway leading to stack overflow, it is not allowed
            to call functions in the DLL from within the callback function. If a call is
            made to a function in the DLL the function will raise an exception.

        Args:
            callback: A callback function. Pass in `None` to disable the device-status callback.
        """
        if NKT._SDK is None:
            msg = "NKTError: You must first call NKT.load_sdk()"
            raise RuntimeError(msg)

        if callback is not None and not isinstance(callback, DeviceStatusCallback):
            msg = "NKTError: Must pass in a DeviceStatusCallback object"
            raise TypeError(msg)

        NKT._SDK.setCallbackPtrDeviceInfo(callback)

    @staticmethod
    def set_callback_port_status(callback: NKTPortStatusCallback | None) -> None:
        """Enables/Disables a callback for port status changes.

        Used by the [open_ports][msl.equipment_resources.nkt.nktpdll.NKT.open_ports] and
        [close_ports][msl.equipment_resources.nkt.nktpdll.NKT.close_ports] functions.

        See [superk_callback.py](https://github.com/MSLNZ/msl-equipment/blob/main/packages/resources/examples/nkt/superk_callback.py)
        for an example usage.

        !!! note
            Due to a risk of circular runaway leading to stack overflow, it is not allowed
            to call functions in the DLL from within the callback function. If a call is
            made to a function in the DLL the function will raise an exception.

        Args:
            callback: A callback function. Pass in `None` to disable the port-status callback.
        """
        if NKT._SDK is None:
            msg = "NKTError: You must first call NKT.load_sdk()"
            raise RuntimeError(msg)

        if callback is not None and not isinstance(callback, PortStatusCallback):
            msg = "NKTError: Must pass in a PortStatusCallback object"
            raise TypeError(msg)

        NKT._SDK.setCallbackPtrPortInfo(callback)

    @staticmethod
    def set_callback_register_status(callback: NKTRegisterStatusCallback | None) -> None:
        """Enables/Disables a callback for register status changes.

        See [superk_callback.py](https://github.com/MSLNZ/msl-equipment/blob/main/packages/resources/examples/nkt/superk_callback.py)
        for an example usage.

        !!! note
            Due to a risk of circular runaway leading to stack overflow, it is not allowed
            to call functions in the DLL from within the callback function. If a call is
            made to a function in the DLL the function will raise an exception.

        Args:
            callback: A callback function. Pass in `None` to disable the register-status callback.
        """
        if NKT._SDK is None:
            msg = "NKTError: You must first call NKT.load_sdk()"
            raise RuntimeError(msg)

        if callback is not None and not isinstance(callback, RegisterStatusCallback):
            msg = "NKTError: Must pass in a RegisterStatusCallback object"
            raise TypeError(msg)

        NKT._SDK.setCallbackPtrRegisterInfo(callback)


_port_errors = {
    0: ("OPSuccess", "Successful operation"),
    1: ("OPFailed", "The NKT.open_ports() function has failed"),
    2: ("OPPortNotFound", "The specified port name could not be found"),
    3: ("OPNoDevices", "No devices found on the specified port"),
    4: ("OPApplicationBusy", "The function is not allowed to be invoked from within a callback function"),
}

_p2p_errors = {
    0: ("P2PSuccess", "Successful operation"),
    1: ("P2PInvalidPortName", "Invalid port name provided"),
    2: ("P2PInvalidLocalIP", "Invalid local IP provided"),
    3: ("P2PInvalidRemoteIP", "Invalid remote IP provided"),
    4: ("P2PPortNameNotFound", "Port name not found"),
    5: ("P2PPortNameExists", "Port name already exists"),
    6: ("P2PApplicationBusy", "The function is not allowed to be invoked from within a callback function"),
}

_device_errors = {
    0: ("DevResultSuccess", "Successful operation"),
    1: ("DevResultWaitTimeout", "The function device_create() timed out waiting for the device being ready"),
    2: ("DevResultFailed", "The function device_create(), failed"),
    3: ("DevResultDeviceNotFound", "The specified device could not be found in the internal device list"),
    4: (
        "DevResultPortNotFound",
        "The function device_create() failed due to not being able to find the specified port",
    ),
    5: ("DevResultPortOpenError", "The function device_create() failed due to port not being open"),
    6: ("DevResultApplicationBusy", "The function is not allowed to be invoked from within a callback function"),
}

_register_errors = {
    0: ("RegResultSuccess", "Successful operation"),
    1: ("RegResultReadError", "Arises from a register write function with index > 0, if the pre-read fails"),
    2: ("RegResultFailed", "The function register_create() has failed"),
    3: (
        "RegResultBusy",
        "The module has reported a BUSY error, the kernel automatically retries on busy but have given up",
    ),
    4: ("RegResultKnackered", "The module has knackered the register, which typically means a non-existing register"),
    5: ("RegResultCRCErr", "The module has reported a CRC error, which means the received message has CRC errors"),
    6: ("RegResultTimeout", "The module has not responded in time. A module should respond in max. 75ms"),
    7: ("RegResultComError", "The module has reported a COM error, which typically means out of sync or garbage error"),
    8: ("RegResultTypeError", "The datatype does not seem to match the register datatype"),
    9: ("RegResultIndexError", "The index seem to be out of range of the register length"),
    10: (
        "RegResultPortClosed",
        "The specified port is closed error. Could happen if the USB is unplugged in the middle of a sequence",
    ),
    11: (
        "RegResultRegisterNotFound",
        "The specified register could not be found in the internal register list for the specified device",
    ),
    12: ("RegResultDeviceNotFound", "The specified device could not be found in the internal device list"),
    13: ("RegResultPortNotFound", "The specified port name could not be found"),
    14: (
        "RegResultPortOpenError",
        "The specified port name could not be opened. The port might be in use by another application",
    ),
    15: ("RegResultApplicationBusy", "The function is not allowed to be invoked from within a callback function"),
}


def _log_debug(result: Any, func: Any, arguments: tuple[Any, ...]) -> Any:  # noqa: ANN401
    logger.debug("NKT.%s%s -> %s", func.__name__, arguments, result)
    return result


def __check_port_result(result: Any, func: Any, arguments: tuple[Any, ...]) -> Any:  # noqa: ANN401
    _log_debug(result, func, arguments)
    if result != 0:
        err, msg = _port_errors.get(result, ("UnknownError", f"Unknown error [code={result}]"))
        message = f"NKTError: {err}: {msg}"
        raise RuntimeError(message)
    return result


def __check_p2p_result(result: Any, func: Any, arguments: tuple[Any, ...]) -> Any:  # noqa: ANN401
    _log_debug(result, func, arguments)
    if result != 0:
        err, msg = _p2p_errors.get(result, ("UnknownError", f"Unknown error [code={result}]"))
        message = f"NKTError: {err}: {msg}"
        raise RuntimeError(message)
    return result


def __check_device_result(result: Any, func: Any, arguments: tuple[Any, ...]) -> Any:  # noqa: ANN401
    _log_debug(result, func, arguments)
    if result != 0:
        err, msg = _device_errors.get(result, ("UnknownError", f"Unknown error [code={result}]"))
        message = f"NKTError: {err}: {msg}"
        raise RuntimeError(message)
    return result


def __check_register_result(result: Any, func: Any, arguments: tuple[Any, ...]) -> Any:  # noqa: ANN401
    _log_debug(result, func, arguments)
    if result != 0:
        err, msg = _register_errors.get(result, ("UnknownError", f"Unknown error [code={result}]"))
        message = f"NKTError: {err}: {msg}"
        raise RuntimeError(message)
    return result


def _load_sdk(path: str, nkt: NKT | None = None) -> None:
    """Load the SDK.

    Args:
        path: The path to `NKTPDLL.dll`.
        nkt: The NKT class instance that the SDK is associated with.
    """
    if NKT._SDK is not None:  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
        return

    if nkt is None:
        _check_p2p_result = __check_p2p_result
        _check_port_result = __check_port_result
        _check_device_result = __check_device_result
        _check_register_result = __check_register_result
    else:
        _check_p2p_result = nkt._check_p2p_result  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
        _check_port_result = nkt._check_port_result  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
        _check_device_result = nkt._check_device_result  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
        _check_register_result = nkt._check_register_result  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001

    functions = {  # pyright: ignore[reportUnknownVariableType]
        # Port functions
        "getAllPorts": (None, _log_debug, [("portnames", POINTER(c_char)), ("maxLen", POINTER(c_ushort))]),
        "getOpenPorts": (None, _log_debug, [("portnames", POINTER(c_char)), ("maxLen", POINTER(c_ushort))]),
        "pointToPointPortAdd": (
            c_ubyte,
            _check_p2p_result,
            [
                ("portname", c_char_p),
                ("hostAddress", c_char_p),
                ("hostPort", c_ushort),
                ("clientAddress", c_char_p),
                ("clientPort", c_ushort),
                ("protocol", c_ubyte),
                ("msTimeout", c_ubyte),
            ],
        ),
        "pointToPointPortGet": (
            c_ubyte,
            _check_p2p_result,
            [
                ("portname", c_char_p),
                ("hostAddress", POINTER(c_char)),
                ("hostMaxLen", POINTER(c_ubyte)),
                ("hostPort", POINTER(c_ushort)),
                ("clientAddress", POINTER(c_char)),
                ("clientMaxLen", POINTER(c_ubyte)),
                ("clientPort", POINTER(c_ushort)),
                ("protocol", POINTER(c_ubyte)),
                ("msTimeout", POINTER(c_ubyte)),
            ],
        ),
        "pointToPointPortDel": (c_ubyte, _check_p2p_result, [("portname", c_char_p)]),
        "openPorts": (
            c_ubyte,
            _check_port_result,
            [("portnames", c_char_p), ("autoMode", c_ubyte), ("liveMode", c_ubyte)],
        ),
        "closePorts": (c_ubyte, _check_port_result, [("portnames", c_char_p)]),
        "setLegacyBusScanning": (None, _log_debug, [("legacyScanning", c_ubyte)]),
        "getLegacyBusScanning": (c_ubyte, _log_debug, []),
        "getPortStatus": (c_ubyte, _check_port_result, [("portname", c_char_p), ("portStatus", POINTER(c_ubyte))]),
        "getPortErrorMsg": (
            c_ubyte,
            _check_port_result,
            [("portname", c_char_p), ("errorMessage", POINTER(c_char)), ("maxLen", POINTER(c_ushort))],
        ),
        # Dedicated - Register read functions
        "registerRead": (
            c_ubyte,
            _check_register_result,
            [
                ("portname", c_char_p),
                ("devId", c_ubyte),
                ("regId", c_ubyte),
                ("readData", POINTER(c_char)),
                ("readSize", POINTER(c_ubyte)),
                ("index", c_short),
            ],
        ),
        "registerReadU8": (
            c_ubyte,
            _check_register_result,
            [
                ("portname", c_char_p),
                ("devId", c_ubyte),
                ("regId", c_ubyte),
                ("value", POINTER(c_ubyte)),
                ("index", c_short),
            ],
        ),
        "registerReadS8": (
            c_ubyte,
            _check_register_result,
            [
                ("portname", c_char_p),
                ("devId", c_ubyte),
                ("regId", c_ubyte),
                ("value", POINTER(c_byte)),
                ("index", c_short),
            ],
        ),
        "registerReadU16": (
            c_ubyte,
            _check_register_result,
            [
                ("portname", c_char_p),
                ("devId", c_ubyte),
                ("regId", c_ubyte),
                ("value", POINTER(c_ushort)),
                ("index", c_short),
            ],
        ),
        "registerReadS16": (
            c_ubyte,
            _check_register_result,
            [
                ("portname", c_char_p),
                ("devId", c_ubyte),
                ("regId", c_ubyte),
                ("value", POINTER(c_short)),
                ("index", c_short),
            ],
        ),
        "registerReadU32": (
            c_ubyte,
            _check_register_result,
            [
                ("portname", c_char_p),
                ("devId", c_ubyte),
                ("regId", c_ubyte),
                ("value", POINTER(c_ulong)),
                ("index", c_short),
            ],
        ),
        "registerReadS32": (
            c_ubyte,
            _check_register_result,
            [
                ("portname", c_char_p),
                ("devId", c_ubyte),
                ("regId", c_ubyte),
                ("value", POINTER(c_long)),
                ("index", c_short),
            ],
        ),
        "registerReadU64": (
            c_ubyte,
            _check_register_result,
            [
                ("portname", c_char_p),
                ("devId", c_ubyte),
                ("regId", c_ubyte),
                ("value", POINTER(c_ulonglong)),
                ("index", c_short),
            ],
        ),
        "registerReadS64": (
            c_ubyte,
            _check_register_result,
            [
                ("portname", c_char_p),
                ("devId", c_ubyte),
                ("regId", c_ubyte),
                ("value", POINTER(c_longlong)),
                ("index", c_short),
            ],
        ),
        "registerReadF32": (
            c_ubyte,
            _check_register_result,
            [
                ("portname", c_char_p),
                ("devId", c_ubyte),
                ("regId", c_ubyte),
                ("value", POINTER(c_float)),
                ("index", c_short),
            ],
        ),
        "registerReadF64": (
            c_ubyte,
            _check_register_result,
            [
                ("portname", c_char_p),
                ("devId", c_ubyte),
                ("regId", c_ubyte),
                ("value", POINTER(c_double)),
                ("index", c_short),
            ],
        ),
        "registerReadAscii": (
            c_ubyte,
            _check_register_result,
            [
                ("portname", c_char_p),
                ("devId", c_ubyte),
                ("regId", c_ubyte),
                ("readStr", POINTER(c_char)),
                ("maxLen", POINTER(c_ubyte)),
                ("index", c_short),
            ],
        ),
        # Dedicated - Register write functions
        "registerWrite": (
            c_ubyte,
            _check_register_result,
            [
                ("portname", c_char_p),
                ("devId", c_ubyte),
                ("regId", c_ubyte),
                ("writeData", POINTER(c_char)),
                ("writeSize", c_ubyte),
                ("index", c_short),
            ],
        ),
        "registerWriteU8": (
            c_ubyte,
            _check_register_result,
            [
                ("portname", c_char_p),
                ("devId", c_ubyte),
                ("regId", c_ubyte),
                ("value", c_ubyte),
                ("index", c_short),
            ],
        ),
        "registerWriteS8": (
            c_ubyte,
            _check_register_result,
            [("portname", c_char_p), ("devId", c_ubyte), ("regId", c_ubyte), ("value", c_byte), ("index", c_short)],
        ),
        "registerWriteU16": (
            c_ubyte,
            _check_register_result,
            [
                ("portname", c_char_p),
                ("devId", c_ubyte),
                ("regId", c_ubyte),
                ("value", c_ushort),
                ("index", c_short),
            ],
        ),
        "registerWriteS16": (
            c_ubyte,
            _check_register_result,
            [
                ("portname", c_char_p),
                ("devId", c_ubyte),
                ("regId", c_ubyte),
                ("value", c_short),
                ("index", c_short),
            ],
        ),
        "registerWriteU32": (
            c_ubyte,
            _check_register_result,
            [
                ("portname", c_char_p),
                ("devId", c_ubyte),
                ("regId", c_ubyte),
                ("value", c_ulong),
                ("index", c_short),
            ],
        ),
        "registerWriteS32": (
            c_ubyte,
            _check_register_result,
            [("portname", c_char_p), ("devId", c_ubyte), ("regId", c_ubyte), ("value", c_long), ("index", c_short)],
        ),
        "registerWriteU64": (
            c_ubyte,
            _check_register_result,
            [
                ("portname", c_char_p),
                ("devId", c_ubyte),
                ("regId", c_ubyte),
                ("value", c_ulonglong),
                ("index", c_short),
            ],
        ),
        "registerWriteS64": (
            c_ubyte,
            _check_register_result,
            [
                ("portname", c_char_p),
                ("devId", c_ubyte),
                ("regId", c_ubyte),
                ("value", c_longlong),
                ("index", c_short),
            ],
        ),
        "registerWriteF32": (
            c_ubyte,
            _check_register_result,
            [
                ("portname", c_char_p),
                ("devId", c_ubyte),
                ("regId", c_ubyte),
                ("value", c_float),
                ("index", c_short),
            ],
        ),
        "registerWriteF64": (
            c_ubyte,
            _check_register_result,
            [
                ("portname", c_char_p),
                ("devId", c_ubyte),
                ("regId", c_ubyte),
                ("value", c_double),
                ("index", c_short),
            ],
        ),
        "registerWriteAscii": (
            c_ubyte,
            _check_register_result,
            [
                ("portname", c_char_p),
                ("devId", c_ubyte),
                ("regId", c_ubyte),
                ("writeStr", c_char_p),
                ("writeEOL", c_ubyte),
                ("index", c_short),
            ],
        ),
        # Dedicated - Register write/read functions (A write immediately followed by a read)
        "registerWriteRead": (
            c_ubyte,
            _check_register_result,
            [
                ("portname", c_char_p),
                ("devId", c_ubyte),
                ("regId", c_ubyte),
                ("writeData", POINTER(c_char)),
                ("writeSize", c_ubyte),
                ("readData", POINTER(c_char)),
                ("readSize", POINTER(c_ubyte)),
                ("index", c_short),
            ],
        ),
        "registerWriteReadU8": (
            c_ubyte,
            _check_register_result,
            [
                ("portname", c_char_p),
                ("devId", c_ubyte),
                ("regId", c_ubyte),
                ("writeValue", c_ubyte),
                ("readValue", POINTER(c_ubyte)),
                ("index", c_short),
            ],
        ),
        "registerWriteReadS8": (
            c_ubyte,
            _check_register_result,
            [
                ("portname", c_char_p),
                ("devId", c_ubyte),
                ("regId", c_ubyte),
                ("writeValue", c_byte),
                ("readValue", POINTER(c_byte)),
                ("index", c_short),
            ],
        ),
        "registerWriteReadU16": (
            c_ubyte,
            _check_register_result,
            [
                ("portname", c_char_p),
                ("devId", c_ubyte),
                ("regId", c_ubyte),
                ("writeValue", c_ushort),
                ("readValue", POINTER(c_ushort)),
                ("index", c_short),
            ],
        ),
        "registerWriteReadS16": (
            c_ubyte,
            _check_register_result,
            [
                ("portname", c_char_p),
                ("devId", c_ubyte),
                ("regId", c_ubyte),
                ("writeValue", c_short),
                ("readValue", POINTER(c_short)),
                ("index", c_short),
            ],
        ),
        "registerWriteReadU32": (
            c_ubyte,
            _check_register_result,
            [
                ("portname", c_char_p),
                ("devId", c_ubyte),
                ("regId", c_ubyte),
                ("writeValue", c_ulong),
                ("readValue", POINTER(c_ulong)),
                ("index", c_short),
            ],
        ),
        "registerWriteReadS32": (
            c_ubyte,
            _check_register_result,
            [
                ("portname", c_char_p),
                ("devId", c_ubyte),
                ("regId", c_ubyte),
                ("writeValue", c_long),
                ("readValue", POINTER(c_long)),
                ("index", c_short),
            ],
        ),
        "registerWriteReadU64": (
            c_ubyte,
            _check_register_result,
            [
                ("portname", c_char_p),
                ("devId", c_ubyte),
                ("regId", c_ubyte),
                ("writeValue", c_ulonglong),
                ("readValue", POINTER(c_ulonglong)),
                ("index", c_short),
            ],
        ),
        "registerWriteReadS64": (
            c_ubyte,
            _check_register_result,
            [
                ("portname", c_char_p),
                ("devId", c_ubyte),
                ("regId", c_ubyte),
                ("writeValue", c_longlong),
                ("readValue", POINTER(c_longlong)),
                ("index", c_short),
            ],
        ),
        "registerWriteReadF32": (
            c_ubyte,
            _check_register_result,
            [
                ("portname", c_char_p),
                ("devId", c_ubyte),
                ("regId", c_ubyte),
                ("writeValue", c_float),
                ("readValue", POINTER(c_float)),
                ("index", c_short),
            ],
        ),
        "registerWriteReadF64": (
            c_ubyte,
            _check_register_result,
            [
                ("portname", c_char_p),
                ("devId", c_ubyte),
                ("regId", c_ubyte),
                ("writeValue", c_double),
                ("readValue", POINTER(c_double)),
                ("index", c_short),
            ],
        ),
        "registerWriteReadAscii": (
            c_ubyte,
            _check_register_result,
            [
                ("portname", c_char_p),
                ("devId", c_ubyte),
                ("regId", c_ubyte),
                ("writeStr", c_char_p),
                ("writeEOL", c_ubyte),
                ("readStr", POINTER(c_char)),
                ("maxLen", POINTER(c_ubyte)),
                ("index", c_short),
            ],
        ),
        # Dedicated - Device functions
        "deviceGetType": (
            c_ubyte,
            _check_device_result,
            [("portname", c_char_p), ("devId", c_ubyte), ("devType", POINTER(c_ubyte))],
        ),
        "deviceGetPartNumberStr": (
            c_ubyte,
            _check_device_result,
            [
                ("portname", c_char_p),
                ("devId", c_ubyte),
                ("partnumber", POINTER(c_char)),
                ("maxLen", POINTER(c_ubyte)),
            ],
        ),
        "deviceGetPCBVersion": (
            c_ubyte,
            _check_device_result,
            [("portname", c_char_p), ("devId", c_ubyte), ("PCBVersion", POINTER(c_ubyte))],
        ),
        "deviceGetStatusBits": (
            c_ubyte,
            _check_device_result,
            [("portname", c_char_p), ("devId", c_ubyte), ("statusBits", POINTER(c_ushort))],
        ),
        "deviceGetErrorCode": (
            c_ubyte,
            _check_device_result,
            [("portname", c_char_p), ("devId", c_ubyte), ("errorCode", POINTER(c_ushort))],
        ),
        "deviceGetBootloaderVersion": (
            c_ubyte,
            _check_device_result,
            [("portname", c_char_p), ("devId", c_ubyte), ("version", POINTER(c_ushort))],
        ),
        "deviceGetBootloaderVersionStr": (
            c_ubyte,
            _check_device_result,
            [
                ("portname", c_char_p),
                ("devId", c_ubyte),
                ("versionStr", POINTER(c_char)),
                ("maxLen", POINTER(c_ubyte)),
            ],
        ),
        "deviceGetFirmwareVersion": (
            c_ubyte,
            _check_device_result,
            [("portname", c_char_p), ("devId", c_ubyte), ("version", POINTER(c_ushort))],
        ),
        "deviceGetFirmwareVersionStr": (
            c_ubyte,
            _check_device_result,
            [
                ("portname", c_char_p),
                ("devId", c_ubyte),
                ("versionStr", POINTER(c_char)),
                ("maxLen", POINTER(c_ubyte)),
            ],
        ),
        "deviceGetModuleSerialNumberStr": (
            c_ubyte,
            _check_device_result,
            [
                ("portname", c_char_p),
                ("devId", c_ubyte),
                ("serialNumber", POINTER(c_char)),
                ("maxLen", POINTER(c_ubyte)),
            ],
        ),
        "deviceGetPCBSerialNumberStr": (
            c_ubyte,
            _check_device_result,
            [
                ("portname", c_char_p),
                ("devId", c_ubyte),
                ("serialNumber", POINTER(c_char)),
                ("maxLen", POINTER(c_ubyte)),
            ],
        ),
        # Callback - Device functions
        "deviceCreate": (
            c_ubyte,
            _check_device_result,
            [("portname", c_char_p), ("devId", c_ubyte), ("waitReady", c_ubyte)],
        ),
        "deviceExists": (
            c_ubyte,
            _check_device_result,
            [("portname", c_char_p), ("devId", c_ubyte), ("exists", POINTER(c_ubyte))],
        ),
        "deviceRemove": (c_ubyte, _check_device_result, [("portname", c_char_p), ("devId", c_ubyte)]),
        "deviceRemoveAll": (c_ubyte, _check_device_result, [("portname", c_char_p)]),
        "deviceGetAllTypes": (
            c_ubyte,
            _check_device_result,
            [("portname", c_char_p), ("types", POINTER(c_char)), ("maxTypes", POINTER(c_ubyte))],
        ),
        "deviceGetMode": (
            c_ubyte,
            _check_device_result,
            [("portname", c_char_p), ("devId", c_ubyte), ("devMode", POINTER(c_ubyte))],
        ),
        "deviceGetLive": (
            c_ubyte,
            _check_device_result,
            [("portname", c_char_p), ("devId", c_ubyte), ("liveMode", POINTER(c_ubyte))],
        ),
        "deviceSetLive": (
            c_ubyte,
            _check_device_result,
            [("portname", c_char_p), ("devId", c_ubyte), ("liveMode", c_ubyte)],
        ),
        # Callback - Register functions
        "registerCreate": (
            c_ubyte,
            _check_register_result,
            [
                ("portname", c_char_p),
                ("devId", c_ubyte),
                ("regId", c_ubyte),
                ("priority", c_ubyte),
                ("dataType", c_ubyte),
            ],
        ),
        "registerExists": (
            c_ubyte,
            _check_register_result,
            [("portname", c_char_p), ("devId", c_ubyte), ("regId", c_ubyte), ("exists", POINTER(c_ubyte))],
        ),
        "registerRemove": (
            c_ubyte,
            _check_register_result,
            [("portname", c_char_p), ("devId", c_ubyte), ("regId", c_ubyte)],
        ),
        "registerRemoveAll": (c_ubyte, _check_register_result, [("portname", c_char_p), ("devId", c_ubyte)]),
        "registerGetAll": (
            c_ubyte,
            _check_register_result,
            [("portname", c_char_p), ("devId", c_ubyte), ("regs", POINTER(c_char)), ("maxRegs", POINTER(c_ubyte))],
        ),
        # Callback - Support functions
        "setCallbackPtrPortInfo": (None, _log_debug, [("callback", c_void_p)]),
        "setCallbackPtrDeviceInfo": (None, _log_debug, [("callback", c_void_p)]),
        "setCallbackPtrRegisterInfo": (None, _log_debug, [("callback", c_void_p)]),
    }

    NKT._SDK = LoadLibrary(path).lib  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    for key, value in functions.items():  # pyright: ignore[reportUnknownVariableType]
        attr = getattr(NKT._SDK, key)  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
        attr.restype, attr.errcheck = value[:2]
        attr.argtypes = [t for _, t in value[2]]
