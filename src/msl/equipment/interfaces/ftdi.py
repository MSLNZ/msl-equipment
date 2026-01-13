"""Base class for equipment that use a Future Technology Devices International (FTDI) chip for communication."""

# cSpell: ignore VIDPID CBUS MPSSE libftd
from __future__ import annotations

import os
import re
import sys
from ctypes import POINTER, byref, c_ubyte, c_uint16, c_ulong, c_ushort, c_void_p, create_string_buffer
from dataclasses import dataclass
from functools import partial
from itertools import combinations
from time import sleep
from typing import TYPE_CHECKING

from msl.equipment.enumerations import DataBits, Parity, StopBits
from msl.equipment.schema import Interface
from msl.equipment.utils import logger, to_enum
from msl.loadlib import LoadLibrary

from .message_based import MSLConnectionError
from .usb import USB

if TYPE_CHECKING:
    from typing import Any, Callable, Literal, Never

    from msl.equipment.schema import Equipment


IS_WINDOWS = sys.platform == "win32"

REGEX = re.compile(
    r"FTDI(?P<driver>\d+)?(::(?P<vid>[^\s:]+))(::(?P<pid>[^\s:]+))(::(?P<sid>[^\s:]+))(::(?P<interface>\d+))?",
    flags=re.IGNORECASE,
)

ftd2xx_error: dict[int, str] = {
    0: "FT_OK",
    1: "FT_INVALID_HANDLE",
    2: "FT_DEVICE_NOT_FOUND",
    3: "FT_DEVICE_NOT_OPENED",
    4: "FT_IO_ERROR",
    5: "FT_INSUFFICIENT_RESOURCES",
    6: "FT_INVALID_PARAMETER",
    7: "FT_INVALID_BAUD_RATE",
    8: "FT_DEVICE_NOT_OPENED_FOR_ERASE",
    9: "FT_DEVICE_NOT_OPENED_FOR_WRITE",
    10: "FT_FAILED_TO_WRITE_DEVICE",
    11: "FT_EEPROM_READ_FAILED",
    12: "FT_EEPROM_WRITE_FAILED",
    13: "FT_EEPROM_ERASE_FAILED",
    14: "FT_EEPROM_NOT_PRESENT",
    15: "FT_EEPROM_NOT_PROGRAMMED",
    16: "FT_INVALID_ARGS",
    17: "FT_NOT_SUPPORTED",
    18: "FT_OTHER_ERROR",
    19: "FT_DEVICE_LIST_NOT_READY",
}


@dataclass
class _FTDevice:
    """Info about a Future Technology Device.

    Attributes:
        index (int): The index value to use to open the connection.
        vid (int): The identity of the device manufacturer.
        pid (int): The identity of the device product.
        serial (str): The serial number of the device.
        description (str): A description about the device.
        driver (int): The FTDI driver to use to communicate with the device.

            0: libusb driver
            2: ftd2xx driver
            3: ftd3xx driver

    """

    index: int
    vid: int
    pid: int
    serial: str
    description: str
    driver: int
    is_serial_unique: bool = True

    def check_vid_pid_serial_equal(self, other: _FTDevice) -> None:
        """Check if idVendor::idProduct::serial_number is unique.

        If not, then `self.is_serial_unique` and `other.is_serial_unique` are set to False.
        """
        if self.serial and self.serial == other.serial and self.vid == other.vid and self.pid == other.pid:
            self.is_serial_unique = False
            other.is_serial_unique = False

    @property
    def visa_address(self) -> str:
        """Returns the VISA-style address."""
        sid = self.serial if self.serial and self.is_serial_unique else f"index={self.index}"
        return f"FTDI{self.driver}::0x{self.vid:04x}::0x{self.pid:04x}::{sid}"


def _maybe_load_ftd2xx(errcheck: Callable[..., Any] | None = None) -> LoadLibrary:
    """Maybe load the ftd2xx library, if it has not already been loaded."""
    if FTD2XX.ftd2xx is not None:
        return FTD2XX.ftd2xx

    path = os.getenv("D2XX_LIBRARY")
    if not path:
        path = "ftd2xx" if IS_WINDOWS else "libftd2xx"
        if IS_WINDOWS and sys.maxsize > (1 << 32):
            path += "64"

    libtype: Literal["windll", "cdll"] = "windll" if IS_WINDOWS else "cdll"
    library = LoadLibrary(path, libtype=libtype)

    definitions: list[tuple[str, tuple[Any, ...]]] = [
        ("FT_SetVIDPID", (c_ulong, c_ulong)),
        ("FT_Open", (c_ulong, c_void_p)),
        ("FT_OpenEx", (c_void_p, c_ulong, c_void_p)),
        ("FT_Close", (c_void_p,)),
        ("FT_Read", (c_void_p, c_void_p, c_ulong, POINTER(c_ulong))),
        ("FT_Write", (c_void_p, c_void_p, c_ulong, POINTER(c_ulong))),
        ("FT_SetBaudRate", (c_void_p, c_ulong)),
        ("FT_SetDivisor", (c_void_p, c_ushort)),
        ("FT_SetDataCharacteristics", (c_void_p, c_ubyte, c_ubyte, c_ubyte)),
        ("FT_SetTimeouts", (c_void_p, c_ulong, c_ulong)),
        ("FT_SetFlowControl", (c_void_p, c_uint16, c_ubyte, c_ubyte)),
        ("FT_SetDtr", (c_void_p,)),
        ("FT_ClrDtr", (c_void_p,)),
        ("FT_SetRts", (c_void_p,)),
        ("FT_ClrRts", (c_void_p,)),
        ("FT_GetModemStatus", (c_void_p, POINTER(c_ulong))),
        ("FT_GetQueueStatus", (c_void_p, POINTER(c_ulong))),
        ("FT_GetStatus", (c_void_p, POINTER(c_ulong), POINTER(c_ulong), POINTER(c_ulong))),
        ("FT_SetEventNotification", (c_void_p, c_ulong, c_void_p)),
        ("FT_SetChars", (c_void_p, c_ubyte, c_ubyte, c_ubyte, c_ubyte)),
        ("FT_SetBreakOn", (c_void_p,)),
        ("FT_SetBreakOff", (c_void_p,)),
        ("FT_Purge", (c_void_p, c_ulong)),
        ("FT_ResetDevice", (c_void_p,)),
        ("FT_ResetPort", (c_void_p,)),
        ("FT_CyclePort", (c_void_p,)),
        ("FT_StopInTask", (c_void_p,)),
        ("FT_RestartInTask", (c_void_p,)),
        ("FT_SetWaitMask", (c_void_p, c_ulong)),
        ("FT_WaitOnMask", (c_void_p, POINTER(c_ulong))),
        ("FT_SetLatencyTimer", (c_void_p, c_ubyte)),
        ("FT_GetLatencyTimer", (c_void_p, POINTER(c_ubyte))),
        ("FT_SetBitMode", (c_void_p, c_ubyte, c_ubyte)),
        ("FT_GetBitMode", (c_void_p, POINTER(c_ubyte))),
        ("FT_SetUSBParameters", (c_void_p, c_ulong, c_ulong)),
    ]

    lib = library.lib
    for fcn, argtypes in definitions:
        try:
            function = getattr(lib, fcn)
        except AttributeError:

            def not_implemented(*_: int, f: str = fcn) -> Never:
                msg = f"{f!r} is not implemented on {sys.platform!r}"
                raise NotImplementedError(msg)

            setattr(lib, fcn, partial(not_implemented, f=fcn))
            continue

        function.argtypes = argtypes
        function.restype = c_ulong
        if errcheck is not None:
            function.errcheck = errcheck

    FTD2XX.ftd2xx = library
    return library


def find_ftd2xx_devices(d2xx_library: str = "") -> list[_FTDevice]:
    """Calls `FT_CreateDeviceInfoList` then `FT_GetDeviceInfoDetail`."""
    logger.debug("Searching for FTDI devices that use the D2XX driver (d2xx_library=%r)", d2xx_library)

    if d2xx_library:
        os.environ["D2XX_LIBRARY"] = d2xx_library

    devices: list[_FTDevice] = []

    try:
        lib = _maybe_load_ftd2xx().lib
    except OSError as e:
        logger.debug("%s: %s", e.__class__.__name__, e)
        return devices

    num_devices = c_ulong()
    result = lib.FT_CreateDeviceInfoList(byref(num_devices))
    if result != 0:
        logger.debug("OSError: %s", ftd2xx_error[result])
        return devices

    flags = c_ulong()
    typ = c_ulong()
    _id = c_ulong()
    loc_id = c_ulong()
    serial = create_string_buffer(16)
    desc = create_string_buffer(64)
    tmp = c_void_p()
    for i in range(num_devices.value):
        result = lib.FT_GetDeviceInfoDetail(i, byref(flags), byref(typ), byref(_id), byref(loc_id), serial, desc, tmp)
        if result != 0:
            continue

        vid = (_id.value >> 16) & 0xFFFF
        pid = _id.value & 0xFFFF
        devices.append(
            _FTDevice(
                index=i,
                vid=vid,
                pid=pid,
                serial=serial.value.decode(),
                description=desc.value.decode(),
                driver=2,
            )
        )

    # Check for non-unique VID::PID::Serial
    for device1, device2 in combinations(devices, 2):
        device1.check_vid_pid_serial_equal(device2)

    return devices


class FTD2XX:
    """Wrapper around the FTD2XX driver."""

    ftd2xx: LoadLibrary | None = None

    def __init__(self) -> None:
        """Wrapper around the FTD2XX driver."""
        self._handle: int | None = None
        self._timeout: float | None = None
        self._lib: Any = _maybe_load_ftd2xx().lib

    def clr_dtr(self) -> None:
        """Clears the Data Terminal Ready (DTR) control signal."""
        self._lib.FT_ClrDtr(self._handle)

    def clr_rts(self) -> None:
        """Clears the Request To Send (RTS) control signal."""
        self._lib.FT_ClrRts(self._handle)

    def cycle_port(self) -> None:
        """Send a cycle command to the USB port.

        The effect of this function is the same as disconnecting then reconnecting the device from USB.

        !!! warning
            Only valid on Windows.
        """
        self._lib.FT_CyclePort(self._handle)

    def close(self) -> None:
        """Close the connection to the device."""
        if self._handle is not None:
            self._lib.FT_Close(self._handle)
            self._handle = None

    @property
    def handle(self) -> int | None:
        """Returns the handle to the opened device or `None` if the connection has been closed."""
        return self._handle

    def get_bit_mode(self) -> int:
        """Get the bit mode.

        Returns:
            The instantaneous value of the data bus.
        """
        mode = c_ubyte()
        self._lib.FT_GetBitMode(self._handle, byref(mode))
        return mode.value

    def get_latency_timer(self) -> int:
        """Get the value of the latency timer.

        Returns:
            The latency timer value, in milliseconds.
        """
        timer = c_ubyte()
        self._lib.FT_GetLatencyTimer(self._handle, byref(timer))
        return timer.value

    def get_line_modem_status(self) -> tuple[int, int]:
        """Gets the line status and the modem status from the device.

        Returns:
            The `(line, modem)` status values.
        """
        status = c_ulong()
        self._lib.FT_GetModemStatus(self._handle, byref(status))
        line = (status.value >> 8) & 0x000000FF
        modem = status.value & 0x000000FF
        return line, modem

    def get_queue_status(self) -> int:
        """Gets the number of bytes in the receive (Rx) queue.

        Returns:
            The number of bytes that are available to be read.
        """
        status = c_ulong()
        self._lib.FT_GetQueueStatus(self._handle, byref(status))
        return status.value

    def get_status(self) -> tuple[int, int, int]:
        """Gets the device status.

        Returns:
            The number of characters in the receive queue, the number of characters in the
                transmit queue and the state of the event status, e.g., `(rx, tx, status)`.
        """
        rx = c_ulong()
        tx = c_ulong()
        event = c_ulong()
        self._lib.FT_GetStatus(self._handle, byref(rx), byref(tx), byref(event))
        return rx.value, tx.value, event.value

    def open(self, index: int) -> None:
        """Open the device.

        Args:
            index: The index of the device (the first device is 0).
        """
        handle = c_void_p()
        self._lib.FT_Open(index, byref(handle))
        self._handle = handle.value

    def open_ex(self, serial: bytes | str) -> None:
        """Open the device.

        Args:
            serial: The serial number of the device.
        """
        arg1 = serial.encode() if isinstance(serial, str) else serial
        handle = c_void_p()
        self._lib.FT_OpenEx(arg1, 1, byref(handle))  # FT_OPEN_BY_SERIAL_NUMBER = 1
        self._handle = handle.value

    def purge_buffers(self) -> None:
        """Purge the receive (Rx) and transmit (Tx) buffers for the device."""
        self._lib.FT_Purge(self._handle, 3)

    def purge_rx_buffer(self) -> None:
        """Purge the receive (Rx) buffer for the device."""
        self._lib.FT_Purge(self._handle, 1)

    def purge_tx_buffer(self) -> None:
        """Purge the transmit (Tx) buffer for the device."""
        self._lib.FT_Purge(self._handle, 2)

    def read(self, size: int | None = None) -> bytes:
        """Read data from the device.

        Args:
            size: The number of bytes to read. If `None`, calls [get_queue_status][] to determine the size.

        Returns:
            The data from the device. The actual number of bytes read could be &lt; `size` if a timeout occurred.
        """
        if size is None:
            size = self.get_queue_status()

        buffer = create_string_buffer(size)
        num_read = c_ulong()
        self._lib.FT_Read(self._handle, buffer, size, byref(num_read))
        return buffer.raw

    def reset_device(self) -> None:
        """Sends a reset command to the device."""
        self._lib.FT_ResetDevice(self._handle)

    def reset_port(self) -> None:
        """Send a reset command to the port.

        This function is used to attempt to recover the port after a failure.
        It is not equivalent to an unplug/re-plug event. For the equivalent
        of an unplug/re-plug event, use [cycle_port][].

        !!! warning
            Only valid on Windows.
        """
        self._lib.FT_ResetPort(self._handle)

    def restart_in_task(self) -> None:
        """Restart the driver's IN task."""
        self._lib.FT_RestartInTask(self._handle)

    def set_baud_rate(self, rate: int) -> None:
        """Sets the baud rate for the device.

        Args:
            rate: The baud rate, e.g., 9600.
        """
        self._lib.FT_SetBaudRate(self._handle, rate)

    def set_bit_mode(self, mask: int, mode: int) -> None:
        """Enable different chip modes.

        Args:
            mask: Required value for bit mode mask. This sets up which bits are inputs and outputs.
                A bit value of 0 sets the corresponding pin to an input, a bit value of 1 sets the
                corresponding pin to an output. In the case of CBUS Bit Bang, the upper nibble of
                this value controls which pins are inputs and outputs, while the lower nibble
                controls which of the outputs are high and low.
            mode: Mode value. Can be one of the following:

                * `0x0`: Reset
                * `0x1`: Asynchronous Bit Bang
                * `0x2`: MPSSE (FT2232, FT2232H, FT4232H and FT232H devices only)
                * `0x4`: Synchronous Bit Bang (FT232R, FT245R, FT2232, FT2232H, FT4232H and FT232H devices only)
                * `0x8`: MCU Host Bus Emulation Mode (FT2232, FT2232H, FT4232H and FT232H devices only)
                * `0x10`: Fast Opto-Isolated Serial Mode (FT2232, FT2232H, FT4232H and FT232H devices only)
                * `0x20`: CBUS Bit Bang Mode (FT232R and FT232H devices only)
                * `0x40`: Single Channel Synchronous 245 FIFO Mode (FT2232H and FT232H devices only)

        """
        self._lib.FT_SetBitMode(self._handle, mask, mode)

    def set_break_on(self) -> None:
        """Sets the BREAK condition for the device."""
        self._lib.FT_SetBreakOn(self._handle)

    def set_break_off(self) -> None:
        """Resets the BREAK condition for the device."""
        self._lib.FT_SetBreakOff(self._handle)

    def set_chars(self, *, event: int, event_enable: bool, error: int, error_enable: bool) -> None:
        """Sets the special characters for the device.

        Args:
            event: Event character.
            event_enable: Whether to enable or disable the `char` character.
            error: Error character.
            error_enable: Whether to enable or disable `error` character.
        """
        self._lib.FT_SetChars(self._handle, event, int(event_enable), error, int(error_enable))

    def set_data_characteristics(self, *, data_bits: DataBits, stop_bits: StopBits, parity: Parity) -> None:
        """Sets the data characteristics for the device.

        Args:
            data_bits: Number of bits per word.
            stop_bits: Number of stop bits.
            parity: Device parity.
        """
        sb = {StopBits.ONE: 0, StopBits.ONE_POINT_FIVE: 1, StopBits.TWO: 2}[stop_bits]
        p = {Parity.NONE: 0, Parity.ODD: 1, Parity.EVEN: 2, Parity.MARK: 3, Parity.SPACE: 4}[parity]
        self._lib.FT_SetDataCharacteristics(self._handle, data_bits, sb, p)

    def set_divisor(self, divisor: int) -> None:
        """Set a non-standard baud rate.

        This function may no longer be required as [set_baud_rate][] will automatically
        calculate the required divisor for a requested baud rate.

        Args:
            divisor: The divisor for a non-standard baud rate.
        """
        self._lib.FT_SetDivisor(self._handle, divisor)

    def set_dtr(self) -> None:
        """Sets the Data Terminal Ready (DTR) control signal."""
        self._lib.FT_SetDtr(self._handle)

    def set_event_notification(self, mask: int, handle: int) -> None:
        """Sets conditions for event notification.

        Args:
            mask: Conditions that cause the event to be set.
            handle: The handle to the object that handles the event.
        """
        self._lib.FT_SetEventNotification(self._handle, mask, handle)

    def set_flow_control(
        self, flow: Literal["RTS_CTS", "DTR_DSR", "XON_XOFF"] | None = None, *, xon: int = 0, xoff: int = 0
    ) -> None:
        """Sets the flow control for the device.

        Args:
            flow: The type of flow control to use.
            xon: The character (between 0 and 255) used to signal Xon. Only used if flow control is `XON_XOFF`.
            xoff: The character (between 0 and 255) used to signal Xoff. Only used if flow control is `XON_XOFF`.
        """
        fc = 0 if flow is None else {"RTS_CTS": 0x0100, "DTR_DSR": 0x0200, "XON_XOFF": 0x0400}[flow]
        self._lib.FT_SetFlowControl(self._handle, fc, xon, xoff)

    def set_latency_timer(self, value: int) -> None:
        """Set the latency timer value.

        Args:
            value: Required value, in milliseconds, of the latency timer. Valid range is [2, 255].
        """
        self._lib.FT_SetLatencyTimer(self._handle, value)

    def set_rts(self) -> None:
        """Sets the Request To Send (RTS) control signal."""
        self._lib.FT_SetRts(self._handle)

    def set_usb_parameters(self, in_size: int, *, out_size: int = 0) -> None:
        """Set the USB request transfer size.

        This function can be used to change the transfer sizes from the default
        transfer size of 4096 bytes to better suit the application requirements.
        Transfer sizes must be set to a multiple of 64 bytes between 64 bytes
        and 64 kbytes.

        Args:
            in_size: Transfer size for USB IN request (e.g., 16384 for 16 kB).
            out_size: Transfer size for USB OUT request. This parameter may not be
                supported by the FTDI driver.
        """
        self._lib.FT_SetUSBParameters(self._handle, in_size, out_size)

    def set_vid_pid(self, vid: int, pid: int) -> None:
        """Set a custom VID and PID combination within the internal device list table.

        !!! warning
            Only available on Linux and macOS.

        Args:
            vid: Vendor ID.
            pid: Product ID.
        """
        self._lib.FT_SetVIDPID(vid, pid)

    def set_wait_mask(self, mask: int) -> None:
        """Set the wait mask.

        Args:
            mask: Mask value.
        """
        self._lib.FT_SetWaitMask(self._handle, mask)

    def stop_in_task(self) -> None:
        """Stops the driver's IN task."""
        self._lib.FT_StopInTask(self._handle)

    @property
    def timeout(self) -> float | None:
        """The timeout, in seconds, for read and write operations.

        A value &lt;0 will set the timeout to be `None` (blocking mode).
        """
        return self._timeout

    @timeout.setter
    def timeout(self, value: float | None) -> None:
        if value is None or value < 0:
            self._timeout = None
            t = (1 << 32) - 1  # ULONG_MAX
        else:
            self._timeout = float(value)
            t = round(self._timeout * 1e3)
        self._lib.FT_SetTimeouts(self._handle, t, t)

    def wait_on_mask(self) -> int:
        """Wait on mask.

        Returns:
            The mask value.
        """
        mask = c_ulong()
        self._lib.FT_WaitOnMask(self._handle, byref(mask))
        return mask.value

    def write(self, data: bytes) -> int:
        """Write data to the device.

        Args:
            data: The data to write to the device.

        Returns:
            The number of bytes written.
        """
        wrote = c_ulong()
        self._lib.FT_Write(self._handle, data, len(data), byref(wrote))
        return wrote.value


class FTDI(Interface, regex=REGEX):
    """Base class for equipment that use a Future Technology Devices International (FTDI) chip for communication."""

    def __init__(self, equipment: Equipment) -> None:
        """Base class for equipment that use a Future Technology Devices International (FTDI) chip for communication.

        Args:
            equipment: An [Equipment][] instance.

        A [Connection][msl.equipment.schema.Connection] instance supports the following _properties_
        for the FTDI communication protocol. The [DataBits][msl.equipment.enumerations.DataBits],
        [Parity][msl.equipment.enumerations.Parity] and [StopBits][msl.equipment.enumerations.StopBits]
        enumeration names and values may also be used. For properties that specify an _alias_, you
        may also use the alternative name as the property name.

        Attributes: Connection Properties:
            baud_rate (int): The baud rate (_alias:_ baudrate). _Default: `9600`_
            data_bits (int): The number of data bits, e.g. 5, 6, 7, 8 (_alias:_ bytesize). _Default: `8`_
            dsr_dtr (bool): Whether to enable hardware (DSR/DTR) flow control (_alias:_ dsrdtr). _Default: `False`_
            parity (str): Parity checking, e.g. 'even', 'odd'. _Default: `none`_
            rts_cts (bool): Whether to enable hardware (RTS/CTS) flow control (_alias:_ rtscts). _Default: `False`_
            stop_bits (int | float): The number of stop bits, e.g. 1, 1.5, 2 (_alias:_ stopbits). _Default: `1`_
            timeout (float | None): The timeout to use for _read_ and _write_ operations. _Default: `None`_
            xon_xoff (bool): Whether to enable software flow control (_alias:_ xonxoff). _Default: `False`_
        """
        super().__init__(equipment)

        assert equipment.connection is not None  # noqa: S101
        parsed = parse_ftdi_address(equipment.connection.address)
        if parsed is None:
            msg = f"Invalid FTDI address {equipment.connection.address!r}"
            raise ValueError(msg)

        if parsed.driver not in {0, 2}:
            msg = f"Invalid FTDI driver number {parsed.driver}"
            raise ValueError(msg)

        self._libusb: USB | None = None
        if parsed.driver == 0:
            self._libusb = USB(equipment)

        _ = _maybe_load_ftd2xx(self._error_check)
        ftd2xx = FTD2XX()
        if not IS_WINDOWS:
            ftd2xx.set_vid_pid(parsed.vid, parsed.pid)

        if parsed.index is None:
            ftd2xx.open_ex(parsed.serial)
        else:
            ftd2xx.open(parsed.index)

        p = equipment.connection.properties

        ftd2xx.set_baud_rate(p.get("baud_rate", p.get("baudrate", 9600)))

        db = p.get("data_bits", p.get("bytesize", DataBits.EIGHT))
        sb = p.get("stop_bits", p.get("stopbits", StopBits.ONE))
        ftd2xx.set_data_characteristics(
            data_bits=to_enum(db, DataBits, to_upper=True),
            stop_bits=to_enum(sb, StopBits, to_upper=True),
            parity=to_enum(p.get("parity", Parity.NONE), Parity, to_upper=True),
        )

        if p.get("xon_xoff", p.get("xonxoff", False)):
            ftd2xx.set_flow_control("XON_XOFF", xon=17, xoff=19)  # pySerial uses 17 and 19

        if p.get("dsr_dtr", p.get("dsrdtr", False)):
            ftd2xx.set_flow_control("DTR_DSR")

        if p.get("rts_cts", p.get("rtscts", False)):
            ftd2xx.set_flow_control("RTS_CTS")

        ftd2xx.timeout = p.get("timeout")

        self._ftd2xx: FTD2XX = ftd2xx

    def _error_check(self, result: int, func: Any, arguments: tuple[int, ...]) -> int:  # noqa: ANN401
        logger.debug("FTD2xx.%s%s -> %d", func.__name__, arguments, result)
        if result != 0:
            msg = ftd2xx_error.get(result, f"FTD2xxUnknownError: Error code {result}")
            raise MSLConnectionError(self, msg)
        return result

    def disconnect(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Disconnect from the equipment."""
        if hasattr(self, "_ftd2xx"):
            self._ftd2xx.close()
            super().disconnect()

    @property
    def ftd2xx(self) -> FTD2XX:
        """Returns the reference to the ftd2xx driver instance."""
        return self._ftd2xx

    def purge_buffers(self) -> None:
        """Purge the receive (Rx) and transmit (Tx) buffers for the device."""
        self._ftd2xx.purge_buffers()

    def query(self, data: bytes, *, delay: float = 0.1, size: int | None = None) -> bytes:
        """Convenience method for performing a write followed by a read.

        Args:
            data: The data to write to the equipment.
            delay: Time delay, in seconds, to wait between the _write_ and _read_ operations.
            size: The number of bytes to read. If `None`, determine the size from the receive (Rx) queue.

        Returns:
            The response from the equipment.
        """
        _ = self.write(data)
        if delay > 0:
            sleep(delay)
        return self.read(size)

    def read(self, size: int | None = None) -> bytes:
        """Read data from the equipment.

        Args:
            size: The number of bytes to read. If `None`, determine the size from the receive (Rx) queue.

        Returns:
            The data from the equipment.
        """
        if size is None:
            size = self._ftd2xx.get_queue_status()

        data = self._ftd2xx.read(size)
        if len(data) < size:
            msg = f"Timeout occurred after {self.timeout} second(s) [got {len(data)} bytes, requested {size}]"
            raise TimeoutError(msg)
        return data

    def reset_device(self) -> None:
        """Sends a reset command to the device."""
        self._ftd2xx.reset_device()

    def set_rts(self, *, state: bool) -> None:
        """Sets the Request To Send (RTS) control signal.

        Args:
            state: New RTS logical level: HIGH (`True`) or LOW (`False`).
        """
        if state:
            self._ftd2xx.set_rts()
        else:
            self._ftd2xx.clr_rts()

    @property
    def timeout(self) -> float | None:
        """The timeout, in seconds, for read and write operations.

        A value &lt;0 will set the timeout to be `None` (blocking mode).
        """
        return self._ftd2xx.timeout

    @timeout.setter
    def timeout(self, value: float | None) -> None:
        self._ftd2xx.timeout = value

    def write(self, data: bytes) -> int:
        """Write data to the equipment.

        Args:
            data: The data to write to the equipment.

        Returns:
            The number of bytes written.
        """
        return self._ftd2xx.write(data)


@dataclass
class ParsedFTDIAddress:
    """The parsed result of a VISA-style address for the FTDI interface.

    Args:
        driver: The version of the FTDI driver library, e.g., 0 (libusb), 2 (ftd2xx) or 3 (ftd3xx).
        vid: The identifier of the manufacturer.
        pid: The identifier of the product.
        serial: The serial number.
        index: The index number to use (for the ftd2xx or ftd3xx driver).
    """

    driver: int
    vid: int
    pid: int
    serial: str
    index: int | None


def parse_ftdi_address(address: str) -> ParsedFTDIAddress | None:
    """Get the driver number and the vendor/product/serial ID.

    Args:
        address: The VISA-style address to use for the connection.

    Returns:
        The parsed address or `None` if `address` is not valid for the FTDI interface.
    """
    match = REGEX.match(address)
    if not match:
        return None

    vid = match["vid"].lower()
    try:
        vendor_id = int(vid, 16) if vid.startswith("0x") else int(vid)
    except ValueError:
        return None

    pid = match["pid"].lower()
    try:
        product_id = int(pid, 16) if pid.startswith("0x") else int(pid)
    except ValueError:
        return None

    index: int | None = None
    serial: str = match["sid"]
    if serial.startswith("index="):
        serial = ""
        try:
            index = int(serial[6:])
        except ValueError:
            return None

    return ParsedFTDIAddress(
        driver=int(match["driver"]) if match["driver"] else 0,
        vid=vendor_id,
        pid=product_id,
        serial=serial,
        index=index,
    )
