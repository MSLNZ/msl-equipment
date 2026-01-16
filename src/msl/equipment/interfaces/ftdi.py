"""Base class for equipment that use a Future Technology Devices International (FTDI) chip for communication."""

# cSpell: ignore VIDPID CBUS MPSSE TCIFLUSH TCOFLUSH THRE TEMT RCVE libftd
from __future__ import annotations

import os
import re
import sys
import time
from ctypes import POINTER, byref, c_ubyte, c_uint16, c_ulong, c_ushort, c_void_p, create_string_buffer
from dataclasses import dataclass
from functools import partial
from itertools import combinations
from struct import unpack
from typing import TYPE_CHECKING

from msl.equipment.enumerations import DataBits, Parity, StopBits
from msl.equipment.utils import logger, to_enum
from msl.loadlib import LoadLibrary

from .message_based import MessageBased, MSLConnectionError, MSLTimeoutError
from .usb import USB

if TYPE_CHECKING:
    from array import array
    from ctypes import CDLL
    from typing import Any, Callable, Literal, Never

    from msl.equipment.schema import Equipment


IS_WINDOWS = sys.platform == "win32"

REGEX = re.compile(
    r"FTDI(?P<driver>\d+)?(::(?P<vid>[^\s:]+))(::(?P<pid>[^\s:]+))(::(?P<sid>[^\s:]+))(::(?P<interface>\d+))?",
    flags=re.IGNORECASE,
)

# some of the bcdDevice values for FTDI chips
# https://github.com/torvalds/linux/blob/5572ad8fddecd4a0db19801262072ff5916b7589/drivers/usb/serial/ftdi_sio.c#L1490
FT232A = 0x0200
FT2232C = 0x0500
FT2232H = 0x0700
FT4232H = 0x0800
FT232H = 0x0900
FT4232HA = 0x3600

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
    if _D2XX.ftd2xx is not None:
        return _D2XX.ftd2xx

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

    _D2XX.ftd2xx = library
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
        if result == 0:
            devices.append(
                _FTDevice(
                    index=i,
                    vid=(_id.value >> 16) & 0xFFFF,
                    pid=_id.value & 0xFFFF,
                    serial=serial.value.decode(),
                    description=desc.value.decode(),
                    driver=2,
                )
            )

    # Check for non-unique VID::PID::Serial
    for device1, device2 in combinations(devices, 2):
        device1.check_vid_pid_serial_equal(device2)

    return devices


def _ftdi_sio_index(baudrate: int) -> int:
    # https://github.com/torvalds/linux/blob/5572ad8fddecd4a0db19801262072ff5916b7589/drivers/usb/serial/ftdi_sio.c#L1273
    speeds = [300, 600, 1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]
    try:
        return speeds.index(baudrate)
    except ValueError:
        options = ", ".join(str(s) for s in speeds)
        msg = f"Invalid baudrate {baudrate}, must be one of: {options}"
        raise ValueError(msg) from None


def _ftdi_232am_baud_to_divisor(baudrate: int) -> tuple[int, int]:
    # Section 4.2: https://www.ftdichip.com/Documents/AppNotes/AN_120_Aliasing_VCP_Baud_Rates.pdf
    # https://github.com/torvalds/linux/blob/5572ad8fddecd4a0db19801262072ff5916b7589/drivers/usb/serial/ftdi_sio.c#L1120
    clock = 3e6

    if baudrate > clock:
        msg = f"Invalid baudrate {baudrate}, must be < {clock / 1e6:.1f} MBd"
        raise ValueError(msg)

    min_clock = clock / 16384.0
    if baudrate < min_clock:
        msg = f"Invalid baudrate {baudrate}, must be > {min_clock:.1f} Bd"
        raise ValueError(msg)

    divisor3 = round((8 * clock) / baudrate)
    if (divisor3 & 0x7) == 7:  # noqa: PLR2004
        divisor3 += 1  # round x.7/8 up to x+1

    divisor = divisor3 >> 3
    divisor3 &= 0x7

    if divisor == 1:  # deviates from ftdi_sio.c to properly handle 2MBd
        divisor = 1 if divisor3 else 0  # 2MBd -> 1, 3MBd -> 0
        actual = 2_000_000 if divisor else 3_000_000
        return actual, divisor

    if divisor3 == 1:
        actual = round(clock / (divisor + 0.125))
        divisor |= 0xC000  # +0.125 => 0b1100_0000_0000_0000
    elif divisor3 >= 4:  # noqa: PLR2004
        actual = round(clock / (divisor + 0.5))
        divisor |= 0x4000  # +0.5   => 0b0100_0000_0000_0000
    elif divisor3 != 0:
        actual = round(clock / (divisor + 0.25))
        divisor |= 0x8000  # +0.25  => 0b1000_0000_0000_0000
    else:
        actual = round(clock / divisor)

    return actual, divisor


def _ftdi_232bm_2232h_baud_to_divisor(baudrate: int, device_version: int) -> tuple[int, int]:
    # https://github.com/torvalds/linux/blob/5572ad8fddecd4a0db19801262072ff5916b7589/drivers/usb/serial/ftdi_sio.c#L1145
    # https://github.com/torvalds/linux/blob/5572ad8fddecd4a0db19801262072ff5916b7589/drivers/usb/serial/ftdi_sio.c#L1166
    div_frac = [0, 3, 2, 4, 1, 5, 6, 7]
    hi_speed = baudrate >= 1200 and device_version in {FT2232H, FT4232H, FT232H, FT4232HA}  # noqa: PLR2004
    clock = 12e6 if hi_speed else 3e6

    if baudrate > clock:
        msg = f"Invalid baudrate {baudrate}, must be < {clock / 1e6:.1f} MBd"
        raise ValueError(msg)

    min_clock = clock / 16384.0
    if baudrate < min_clock:
        msg = f"Invalid baudrate {baudrate}, must be > {min_clock:.1f} Bd"
        raise ValueError(msg)

    # Currently we don't allow bit-bang mode, but if we did we would need
    # to divide the baudrate here, e.g., baudrate //= 5 if hi_speed else 16

    divisor3 = round((8 * clock) / baudrate)
    actual = int(((8 * clock) + (divisor3 // 2)) // divisor3)

    # and then multiply the actual baudrate here, e.g., actual *= 5 if hi_speed else 16

    divisor = divisor3 >> 3
    divisor |= div_frac[divisor3 & 0x7] << 14
    if divisor == 1:
        divisor = 0
    elif divisor == 0x4001:  # noqa: PLR2004
        divisor = 1

    if hi_speed:
        divisor |= 0x00020000  # 1 << 17, most significant bit (MSB) of the divisor must be a 1

    return actual, divisor


def _get_ftdi_divisor(baudrate: int, device_version: int) -> int:
    # https://www.ftdichip.com/Documents/AppNotes/AN_120_Aliasing_VCP_Baud_Rates.pdf
    if device_version < FT232A:
        actual, divisor = baudrate, _ftdi_sio_index(baudrate)
    elif device_version == FT232A:
        actual, divisor = _ftdi_232am_baud_to_divisor(baudrate)
    else:
        actual, divisor = _ftdi_232bm_2232h_baud_to_divisor(baudrate, device_version)

    tolerance = abs(actual - baudrate) / baudrate
    if tolerance > 0.03:  # noqa: PLR2004
        # The exact baudrate may not be achievable, however, as long as the actual baudrate used
        # is within +/-3% of the required baudrate then the link should function without errors
        # https://www.ftdichip.com/Support/Knowledgebase/index.html?an232b_05calc.htm
        msg = f"The actual baudrate ({actual}) is not within 3% of the requested baudrate ({baudrate})"
        raise ValueError(msg)

    return divisor


class _D2XX:
    """Wrapper around the D2XX driver.

    https://ftdichip.com/wp-content/uploads/2025/06/D2XX_Programmers_Guide.pdf
    """

    ftd2xx: LoadLibrary | None = None

    def __init__(self, errcheck: Callable[..., Any]) -> None:
        """Wrapper around the D2XX driver."""
        self._handle: int | None = None
        self._timeout: float | None = None
        self._lib: CDLL = _maybe_load_ftd2xx(errcheck).lib

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

    def get_line_modem_status(self) -> int:
        """Gets the line status and the modem status from the device.

        Returns:
            The status value.
        """
        status = c_ulong()
        self._lib.FT_GetModemStatus(self._handle, byref(status))
        return status.value

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
        self._lib.FT_Purge(self._handle, 3)  # FT_PURGE_RX | FT_PURGE_TX

    def purge_rx_buffer(self) -> None:
        """Purge the receive (Rx) buffer for the device (host-to-ftdi)."""
        self._lib.FT_Purge(self._handle, 1)  # FT_PURGE_RX

    def purge_tx_buffer(self) -> None:
        """Purge the transmit (Tx) buffer for the device (ftdi-to-host)."""
        self._lib.FT_Purge(self._handle, 2)  # FT_PURGE_TX

    def read(self, size: int | None = None) -> bytes:
        """Read data from the device.

        Args:
            size: The number of bytes to read. If `None`, calls `get_queue_status()` to determine the size.

        Returns:
            The data from the device. The actual number of bytes read could be &lt; `size` if a timeout occurred.
        """
        if size is None:
            size = self.get_queue_status()
            if size == 0:
                timer = max(0.016, self.get_latency_timer() * 1e-3)
                previous = size
                for _ in range(10):  # typically takes < 3 iterations
                    time.sleep(timer)
                    size = self.get_queue_status()
                    if size > 0 and size == previous:
                        break
                    previous = size

            if size == 0:
                msg = "Cannot automatically determine the number of bytes to read, specify the `size` argument"
                raise RuntimeError(msg)

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
        of an unplug/re-plug event, use `cycle_port()`.

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

    def set_data_characteristics(self, *, data_bits: DataBits, parity: Parity, stop_bits: StopBits) -> None:
        """Sets the data characteristics for the device.

        Args:
            data_bits: Number of bits per word.
            stop_bits: Number of stop bits.
            parity: Device parity.
        """
        # Section 3.14: https://ftdichip.com/wp-content/uploads/2025/06/D2XX_Programmers_Guide.pdf
        sb = {StopBits.ONE: 0, StopBits.ONE_POINT_FIVE: 1, StopBits.TWO: 2}[stop_bits]
        p = {Parity.NONE: 0, Parity.ODD: 1, Parity.EVEN: 2, Parity.MARK: 3, Parity.SPACE: 4}[parity]
        self._lib.FT_SetDataCharacteristics(self._handle, data_bits, sb, p)

    def set_divisor(self, divisor: int) -> None:
        """Set a non-standard baud rate.

        This function may no longer be required as `set_baud_rate()` will automatically
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
        # Section 3.16: https://ftdichip.com/wp-content/uploads/2025/06/D2XX_Programmers_Guide.pdf
        fc = 0 if flow is None else {"RTS_CTS": 0x0100, "DTR_DSR": 0x0200, "XON_XOFF": 0x0400}[flow]
        self._lib.FT_SetFlowControl(self._handle, fc, xon, xoff)

    def set_latency_timer(self, value: int) -> None:
        """Set the latency timer value.

        Args:
            value: Required value, in milliseconds, of the latency timer. Valid range is [1, 255].
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
            in_size: Transfer size for USB IN request (e.g., 16384 for 16 kiB).
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


class FTDI(MessageBased, regex=REGEX):
    """Base class for equipment that use a Future Technology Devices International (FTDI) chip for communication."""

    def __init__(self, equipment: Equipment) -> None:
        """Base class for equipment that use a Future Technology Devices International (FTDI) chip for communication.

        Args:
            equipment: An [Equipment][] instance.

        A [Connection][msl.equipment.schema.Connection] instance supports the following _properties_
        for the FTDI communication protocol, as well as the _properties_ defined in
        [MessageBased][msl.equipment.interfaces.message_based.MessageBased]. The
        [DataBits][msl.equipment.enumerations.DataBits],
        [Parity][msl.equipment.enumerations.Parity] and [StopBits][msl.equipment.enumerations.StopBits]
        enumeration names or values may also be used. For properties that specify an _alias_, you
        may also use the alternative name as the property name. The
        [read_termination][msl.equipment.interfaces.message_based.MessageBased.read_termination] and
        [write_termination][msl.equipment.interfaces.message_based.MessageBased.write_termination] values
        are automatically set to `None` (termination characters are not used in the FTDI protocol).

        Attributes: Connection Properties:
            baud_rate (int): The baud rate (_alias:_ baudrate). _Default: `9600`_
            data_bits (int): The number of data bits: 7 or 8 (_alias:_ bytesize). _Default: `8`_
            dsr_dtr (bool): Whether to enable hardware (DSR/DTR) flow control (_alias:_ dsrdtr). _Default: `False`_
            parity (str): Parity checking: none, odd, even, mark or space. _Default: `none`_
            rts_cts (bool): Whether to enable hardware (RTS/CTS) flow control (_alias:_ rtscts). _Default: `False`_
            stop_bits (int | float): The number of stop bits: 1, 1.5 or 2 (_alias:_ stopbits). _Default: `1`_
            timeout (float | None): The timeout to use for _read_ and _write_ operations. _Default: `None`_
            xon_xoff (bool): Whether to enable software flow control (_alias:_ xonxoff). _Default: `False`_
        """
        self._d2xx: _D2XX | None = None
        self._libusb: USB | None = None
        super().__init__(equipment)

        self._read_termination: bytes | None = None
        self._write_termination: bytes | None = None

        assert equipment.connection is not None  # noqa: S101
        parsed = parse_ftdi_address(equipment.connection.address)
        if parsed is None:
            msg = f"Invalid FTDI address {equipment.connection.address!r}"
            raise ValueError(msg)

        self._out_req_type: int = -1
        self._in_req_type: int = -1
        self._index: int = -1

        if parsed.driver == 0:
            # http://developer.intra2net.com/git/?p=libftdi;a=tree;f=src;hb=HEAD
            self._libusb = USB(equipment)
            self._libusb._str = self._str  # noqa: SLF001
            self._index = self._libusb.bulk_in_endpoint.interface_number + 1
            self._out_req_type = self._libusb.build_request_type(
                direction=self._libusb.CtrlDirection.OUT,
                type=self._libusb.CtrlType.VENDOR,
                recipient=self._libusb.CtrlRecipient.DEVICE,
            )
            self._in_req_type = self._libusb.build_request_type(
                direction=self._libusb.CtrlDirection.IN,
                type=self._libusb.CtrlType.VENDOR,
                recipient=self._libusb.CtrlRecipient.DEVICE,
            )
        elif parsed.driver == 2:  # noqa: PLR2004
            self._d2xx = _D2XX(errcheck=self._error_check)
            if not IS_WINDOWS:
                self._d2xx.set_vid_pid(parsed.vid, parsed.pid)

            if parsed.index is None:
                self._d2xx.open_ex(parsed.serial)
            else:
                self._d2xx.open(parsed.index)
        else:
            msg = f"Invalid FTDI driver number {parsed.driver}, must be either 0 or 2"
            raise ValueError(msg)

        self._set_interface_timeout()

        p = equipment.connection.properties

        self.set_baud_rate(p.get("baud_rate", p.get("baudrate", 9600)))

        self.set_data_characteristics(
            data_bits=p.get("data_bits", p.get("bytesize", DataBits.EIGHT)),
            parity=p.get("parity", Parity.NONE),
            stop_bits=p.get("stop_bits", p.get("stopbits", StopBits.ONE)),
        )

        self.set_flow_control()  # set to None as default, the following may overwrite

        if p.get("xon_xoff", p.get("xonxoff", False)):
            self.set_flow_control("XON_XOFF", xon=17, xoff=19)  # pySerial uses 17 and 19

        if p.get("dsr_dtr", p.get("dsrdtr", False)):
            self.set_flow_control("DTR_DSR")

        if p.get("rts_cts", p.get("rtscts", False)):
            self.set_flow_control("RTS_CTS")

    def _error_check(self, result: int, func: Any, arguments: tuple[int, ...]) -> int:  # noqa: ANN401
        logger.debug("%s.%s%s -> %d", self, func.__name__, arguments, result)
        if result != 0:
            msg = ftd2xx_error.get(result, f"D2xxUnknownError: Error code {result}")
            raise MSLConnectionError(self, msg)
        return result

    def _read(self, size: int | None = None) -> bytes:  # pyright: ignore[reportImplicitOverride]  # noqa: C901
        if self._d2xx is not None:
            return self._d2xx.read(size)

        assert self._libusb is not None  # noqa: S101
        address = self._libusb.bulk_in_endpoint.address
        packet_size = self._libusb.bulk_in_endpoint.max_packet_size
        read = self._libusb._device.read  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
        original_timeout = self._libusb._timeout_ms  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
        timeout = original_timeout

        # First 2 bytes in each packet represent the current [modem, line] status
        n_skip = 2

        remaining = sys.maxsize if size is None else size
        buffer = bytearray()
        t0 = time.time()
        while True:
            data: array[int] = read(address, min(remaining + n_skip, packet_size), timeout)
            if len(data) > n_skip:
                if data[1] & 0x8E:  # check for Overrun, Parity, Framing or FIFO error -- see self.poll_status()
                    msg = f"FTDI read error, bit mask of the line-status byte is 0b{data[1]:08b}"
                    raise MSLConnectionError(self, msg)
                remaining -= len(data) - n_skip
                buffer.extend(data[n_skip:])

            if size is not None:
                if len(buffer) == size:
                    break
            elif buffer and len(data) == 2:  # noqa: PLR2004
                # If `size` is not specified then assume that once data is in the buffer and only
                # the 2 status bytes are returned that reading packets from the device is done.
                # Increasing the value of the latency timer could strengthen this ad hoc decision.
                # Do this because the D2XX library has the get_queue_status() function that can
                # determine the number of bytes in the Rx queue if size=None, so want to support
                # size=None here as well in some capacity.
                break

            if len(buffer) > self._max_read_size:
                error = f"len(message) [{len(buffer)}] > max_read_size [{self._max_read_size}]"
                raise RuntimeError(error)

            if original_timeout > 0:
                # decrease the timeout when reading each packet so that the total
                # time to receive all packets preserves what was specified
                elapsed_time = int((time.time() - t0) * 1000)
                if elapsed_time >= original_timeout:
                    raise MSLTimeoutError(self)
                timeout = max(1, original_timeout - elapsed_time)

        return bytes(buffer)

    def _set_interface_timeout(self) -> None:  # pyright: ignore[reportImplicitOverride]
        if self._d2xx is not None:
            self._d2xx.timeout = self.timeout
        elif self._libusb is not None:
            self._libusb.timeout = self.timeout

    def _write(self, message: bytes) -> int:  # pyright: ignore[reportImplicitOverride]
        if self._d2xx is not None:
            return self._d2xx.write(message)

        assert self._libusb is not None  # noqa: S101
        if self._libusb.device_version < FT232A:
            # https://github.com/torvalds/linux/blob/5572ad8fddecd4a0db19801262072ff5916b7589/drivers/usb/serial/ftdi_sio.c#L2366
            # https://github.com/torvalds/linux/blob/5572ad8fddecd4a0db19801262072ff5916b7589/drivers/usb/serial/ftdi_sio.h#L565
            msg = "The FTDI chip requires a header byte when writing data, which has not been implemented yet"
            raise MSLConnectionError(self, msg)
        return self._libusb._write(message)  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001

    def disconnect(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Disconnect from the equipment."""
        if self._d2xx is not None:
            self._d2xx.close()
            self._d2xx = None
            super().disconnect()
        elif self._libusb is not None:
            self._libusb.disconnect()
            self._libusb = None
            super().disconnect()

    def get_latency_timer(self) -> int:
        """Get the latency timer value.

        Returns:
            The latency timer value, in milliseconds.
        """
        if self._d2xx is not None:
            return self._d2xx.get_latency_timer()

        assert self._libusb is not None  # noqa: S101

        # https://github.com/torvalds/linux/blob/5572ad8fddecd4a0db19801262072ff5916b7589/drivers/usb/serial/ftdi_sio.c#L1408
        if self._libusb.device_version <= FT232A:
            # The linux code returns an error, but FT_GetLatencyTimer in the D2xx programming manual states:
            #  "In the FT8U232AM and FT8U245AM devices, the receive buffer timeout that is used
            #   to flush remaining data from the receive buffer was fixed at 16 ms."
            return 16

        data = self._libusb.ctrl_transfer(
            request_type=self._in_req_type,
            request=0x0A,  # FTDI_SIO_GET_LATENCY_TIMER
            value=0,
            index=self._index,
            data_or_length=1,
        )
        assert not isinstance(data, int)  # noqa: S101
        return data[0]

    def poll_status(self) -> tuple[int, int]:
        """Polls the modem and line status from the device.

        Returns:
            The `(modem, line)` status values.
                Bit mask of the `modem` byte:
                - B0..3: Should be 0 (reserved)
                - B4: Clear To Send (CTS) = 0x10 &mdash; 0 = inactive, 1 = active
                - B5: Data Set Ready (DSR) = 0x20 &mdash; 0 = inactive, 1 = active
                - B6: Ring Indicator (RI) = 0x40 &mdash; 0 = inactive, 1 = active
                - B7: Data Carrier Detect (DCD) = 0x80 &mdash; 0 = inactive, 1 = active

                Bit mask of the `line` byte:
                - B0: Data Ready (DR) = 0x01
                - B1: Overrun Error (OE) = 0x02
                - B2: Parity Error (PE) = 0x04
                - B3: Framing Error (FE) = 0x08
                - B4: Break Interrupt (BI) = 0x10
                - B5: Transmitter Holding Register Empty (THRE) = 0x20
                - B6: Transmitter Empty (TEMT) = 0x40
                - B7: Receiver FIFO Error (RCVE) = 0x80

        """
        status: int
        if self._d2xx is not None:
            status = self._d2xx.get_line_modem_status()
        else:
            assert self._libusb is not None  # noqa: S101

            # https://github.com/torvalds/linux/blob/5572ad8fddecd4a0db19801262072ff5916b7589/drivers/usb/serial/ftdi_sio.c#L2744
            length, fmt = (1, "B") if self._libusb.device_version < FT232A else (2, "<H")
            data = self._libusb.ctrl_transfer(
                request_type=self._in_req_type,
                request=5,  # FTDI_SIO_GET_MODEM_STATUS
                value=0,
                index=self._index,
                data_or_length=length,
            )
            assert not isinstance(data, int)  # noqa: S101
            (status,) = unpack(fmt, data)

        line = (status >> 8) & 0xFF
        modem = status & 0xFF
        return modem, line

    def purge_buffers(self) -> None:
        """Purge the receive (Rx) and transmit (Tx) buffers for the FTDI device."""
        if self._d2xx is not None:
            return self._d2xx.purge_buffers()

        assert self._libusb is not None  # noqa: S101
        # http://developer.intra2net.com/git/?p=libftdi;a=blob;f=src/ftdi.c;h=811f801feab8a04a62526c68ff2a93aae11feb2b;hb=HEAD#l1032
        # 0=SIO_RESET_REQUEST, 1=SIO_TCOFLUSH (host-to-ftdi), 2=SIO_TCIFLUSH (ftdi-to-host)
        _ = self._libusb.ctrl_transfer(request_type=self._out_req_type, request=0, value=1, index=self._index)
        _ = self._libusb.ctrl_transfer(request_type=self._out_req_type, request=0, value=2, index=self._index)
        return None

    def reset_device(self) -> None:
        """Sends a reset command to the device."""
        if self._d2xx is not None:
            return self._d2xx.reset_device()

        # http://developer.intra2net.com/git/?p=libftdi;a=blob;f=src/ftdi.c;h=811f801feab8a04a62526c68ff2a93aae11feb2b;hb=HEAD#l1006
        assert self._libusb is not None  # noqa: S101
        # SIO_RESET=0, SIO_RESET_SIO=0
        _ = self._libusb.ctrl_transfer(request_type=self._out_req_type, request=0, value=0, index=self._index)
        return None

    def set_baud_rate(self, rate: int) -> None:
        """Set the baud rate.

        Args:
            rate: The baud rate.
        """
        if self._d2xx is not None:
            return self._d2xx.set_baud_rate(rate)

        # https://github.com/torvalds/linux/blob/5572ad8fddecd4a0db19801262072ff5916b7589/drivers/usb/serial/ftdi_sio.c#L1342
        assert self._libusb is not None  # noqa: S101
        dv = self._libusb.device_version
        divisor = _get_ftdi_divisor(baudrate=rate, device_version=dv)
        value = divisor & 0xFFFF
        index = (divisor >> 16) & 0xFFFF
        if dv >= FT2232H or dv == FT2232C:
            index <<= 8
            index |= self._index

        _ = self._libusb.ctrl_transfer(
            request_type=self._out_req_type,
            request=3,  # FTDI_SIO_SET_BAUDRATE_REQUEST
            value=value,
            index=index,
        )
        return None

    def set_data_characteristics(
        self,
        *,
        data_bits: DataBits | str | int = DataBits.EIGHT,
        parity: Parity | str | int = Parity.NONE,
        stop_bits: StopBits | str | int = StopBits.ONE,
    ) -> None:
        """Set the RS-232 data characteristics.

        Args:
            data_bits: The number of data bits (7 or 8). Can be an enum member name (case insensitive) or value.
            parity: The parity. Can be an enum member name (case insensitive) or value.
            stop_bits: The number of stop bits. Can be an enum member name (case insensitive) or value.
        """
        data_bits = to_enum(data_bits, DataBits, to_upper=True)
        parity = to_enum(parity, Parity, to_upper=True)
        stop_bits = to_enum(stop_bits, StopBits, to_upper=True)

        if data_bits not in {7, 8}:
            msg = f"Unsupported data_bits value {data_bits!r}, must be either 7 or 8"
            raise ValueError(msg)

        if self._d2xx is not None:
            return self._d2xx.set_data_characteristics(data_bits=data_bits, parity=parity, stop_bits=stop_bits)

        # http://developer.intra2net.com/git/?p=libftdi;a=blob;f=src/ftdi.c;h=811f801feab8a04a62526c68ff2a93aae11feb2b;hb=HEAD#l1512
        assert self._libusb is not None  # noqa: S101
        value = data_bits.value
        value |= {Parity.NONE: 0, Parity.ODD: 256, Parity.EVEN: 512, Parity.MARK: 768, Parity.SPACE: 1024}[parity]
        value |= {StopBits.ONE: 0, StopBits.ONE_POINT_FIVE: 2048, StopBits.TWO: 4096}[stop_bits]

        _ = self._libusb.ctrl_transfer(
            request_type=self._out_req_type,
            request=4,  # SIO_SET_DATA
            value=value,
            index=self._index,
        )
        return None

    def set_dtr(self, *, active: bool) -> None:
        """Set the Data Terminal Ready (DTR) control signal.

        Args:
            active: New DTR logical level: HIGH (`True`) or LOW (`False`).
        """
        if self._d2xx is not None:
            return self._d2xx.set_dtr() if active else self._d2xx.clr_dtr()

        # https://github.com/torvalds/linux/blob/5572ad8fddecd4a0db19801262072ff5916b7589/drivers/usb/serial/ftdi_sio.c#L1199
        assert self._libusb is not None  # noqa: S101
        # FTDI_SIO_SET_DTR_HIGH=((0x01 << 8) | 1), FTDI_SIO_SET_DTR_LOW=((0x01 << 8) | 0)
        _ = self._libusb.ctrl_transfer(
            request_type=self._out_req_type,
            request=1,  # FTDI_SIO_MODEM_CTRL
            value=257 if active else 256,
            index=self._index,
        )
        return None

    def set_flow_control(
        self, flow: Literal["RTS_CTS", "DTR_DSR", "XON_XOFF"] | None = None, *, xon: int = 0, xoff: int = 0
    ) -> None:
        """Sets the flow control for the device.

        Args:
            flow: The type of flow control to use, `None` disables flow control.
            xon: The character (between 0 and 255) used to signal Xon. Only used if `flow` is `XON_XOFF`.
            xoff: The character (between 0 and 255) used to signal Xoff. Only used if `flow` is `XON_XOFF`.
        """
        if self._d2xx is not None:
            return self._d2xx.set_flow_control(flow, xon=xon, xoff=xoff)

        # https://github.com/torvalds/linux/blob/5572ad8fddecd4a0db19801262072ff5916b7589/drivers/usb/serial/ftdi_sio.c#L2716
        assert self._libusb is not None  # noqa: S101
        value, index = 0, 0
        if flow == "RTS_CTS":
            index = 0x1 << 8  # FTDI_SIO_RTS_CTS_HS
        elif flow == "DTR_DSR":
            index = 0x2 << 8  # FTDI_SIO_DTR_DSR_HS
        elif flow == "XON_XOFF":
            value = (xoff << 8) | xon
            index = 0x4 << 8  # FTDI_SIO_XON_XOFF_HS

        _ = self._libusb.ctrl_transfer(
            request_type=self._out_req_type,
            request=2,  # FTDI_SIO_SET_FLOW_CTRL
            value=value,
            index=index | self._index,
        )
        return None

    def set_latency_timer(self, value: int) -> None:
        """Set the latency timer value.

        Args:
            value: Required value, in milliseconds, of the latency timer. Valid range is [1, 255].
        """
        v = int(value)
        if v < 1 or v > 255:  # noqa: PLR2004
            msg = f"Invalid latency timer value {value}, must be an integer in the range [1, 255]"
            raise ValueError(msg)

        if self._d2xx is not None:
            return self._d2xx.set_latency_timer(v)

        # https://github.com/torvalds/linux/blob/5572ad8fddecd4a0db19801262072ff5916b7589/drivers/usb/serial/ftdi_sio.c#L1365
        assert self._libusb is not None  # noqa: S101
        if self._libusb.device_version <= FT232A:
            # The linux code returns an error, but FT_SetLatencyTimer in the D2xx programming manual states:
            #  "In the FT8U232AM and FT8U245AM devices, the receive buffer timeout that is used
            #   to flush remaining data from the receive buffer was fixed at 16 ms."
            if v == 16:  # noqa: PLR2004
                return None
            msg = "Cannot set latency timer for this (old) FTDI chip. The value is fixed at 16 ms."
            raise MSLConnectionError(self, msg)

        _ = self._libusb.ctrl_transfer(
            request_type=self._out_req_type,
            request=9,  # FTDI_SIO_SET_LATENCY_TIMER
            value=v,
            index=self._index,
        )
        return None

    def set_rts(self, *, active: bool) -> None:
        """Set the Request To Send (RTS) control signal.

        Args:
            active: New RTS logical level: HIGH (`True`) or LOW (`False`).
        """
        if self._d2xx is not None:
            return self._d2xx.set_rts() if active else self._d2xx.clr_rts()

        # https://github.com/torvalds/linux/blob/5572ad8fddecd4a0db19801262072ff5916b7589/drivers/usb/serial/ftdi_sio.c#L1199
        assert self._libusb is not None  # noqa: S101
        # FTDI_SIO_SET_RTS_HIGH=((0x2 << 8) | 2), FTDI_SIO_SET_RTS_LOW=((0x2 << 8) | 0)
        _ = self._libusb.ctrl_transfer(
            request_type=self._out_req_type,
            request=1,  # FTDI_SIO_MODEM_CTRL
            value=514 if active else 512,
            index=self._index,
        )
        return None


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
        try:
            index = int(serial[6:])
        except ValueError:
            return None
        serial = ""

    return ParsedFTDIAddress(
        driver=int(match["driver"]) if match["driver"] else 0,
        vid=vendor_id,
        pid=product_id,
        serial=serial,
        index=index,
    )
