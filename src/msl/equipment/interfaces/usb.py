"""Base class for (raw) USB communication."""

# cSpell: ignore altsetting geteuid
# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportAttributeAccessIssue=false
from __future__ import annotations

import contextlib
import os
import re
import sys
import time
from dataclasses import dataclass
from enum import IntEnum
from itertools import combinations
from typing import TYPE_CHECKING

import usb  # type: ignore[import-untyped]  # pyright: ignore[reportMissingTypeStubs]

from msl.equipment.utils import logger

from .message_based import MessageBased, MSLConnectionError, MSLTimeoutError

if TYPE_CHECKING:
    from array import array
    from types import ModuleType
    from typing import Any, Literal

    from msl.equipment.schema import Equipment


REGEX = re.compile(
    r"^USB(?P<board>\d*)::(?P<vid>[^:]+)::(?P<pid>[^:]+)::(?P<serial>(?:[^:]*|:(?!:))*)(::(?P<interface>\d+))?::((?<!INSTR)|(RAW))$",
    flags=re.IGNORECASE,
)

IS_WINDOWS = sys.platform == "win32"
UNKNOWN_USB_DEVICE = "Unknown USB Device"


def _is_linux_and_not_sudo() -> bool:
    return sys.platform == "linux" and os.geteuid() != 0


def _usb_backend(name: str) -> Any:  # noqa: ANN401
    """Returns a usb.backend.IBackend subclass or raises ValueError."""
    from usb.backend import (  # type: ignore[import-untyped]  # pyright: ignore[reportMissingTypeStubs]  # noqa: PLC0415
        libusb0,
        libusb1,
        openusb,
    )

    backends: dict[str, ModuleType] = {
        "libusb0": libusb0,
        "libusb1": libusb1,
        "openusb": openusb,
    }

    backend_module = backends.get(name)
    if backend_module is None:
        options = ", ".join(backends)
        msg = f"The requested {name!r} PyUSB backend is invalid, must be one of: {options}"
        raise ValueError(msg)

    backend = backend_module.get_backend()
    if backend is None:
        msg = f"Cannot load the requested {name!r} PyUSB backend"
        raise ValueError(msg)

    return backend


def _find_device(parsed: ParsedUSBAddress, backend: Any) -> Any:  # noqa: ANN401
    """Returns the usb.core.Device object or None."""
    bus_address_regex = re.compile(r"bus=(?P<bus>\d+),address=(?P<address>\d+)")

    for dev in usb.core.find(find_all=True, backend=backend, idVendor=parsed.vendor_id, idProduct=parsed.product_id):
        # Check if only the VID and PID are required to find the USB device and return the first one found
        if parsed.serial_id == "IGNORE":
            return dev

        # Multiple USB devices exist with the same serial number or the serial number cannot be determined
        match = bus_address_regex.match(parsed.serial_id)
        if match is not None and (dev.bus == int(match["bus"])) and (dev.address == int(match["address"])):
            return dev

        with contextlib.suppress(NotImplementedError, ValueError):
            if dev.serial_number == parsed.serial_id:
                return dev

    return None


class _USBDevice:
    """A device that support the USB protocol."""

    def __init__(self, usb_core_device: Any) -> None:  # noqa: ANN401
        self.vid: int = usb_core_device.idVendor
        self.pid: int = usb_core_device.idProduct
        self.bus: int | None = usb_core_device.bus
        self.address: int | None = usb_core_device.address

        info: list[str] = []
        with contextlib.suppress(NotImplementedError, ValueError):
            info.append(usb_core_device.manufacturer.rstrip() or "")
        with contextlib.suppress(NotImplementedError, ValueError):
            info.append(usb_core_device.product.rstrip() or "")
        self.description: str = ", ".join(item for item in info if item) or UNKNOWN_USB_DEVICE

        serial = ""
        with contextlib.suppress(NotImplementedError, ValueError):
            serial = usb_core_device.serial_number or ""

        self.serial: str = serial

        self.is_serial_unique: bool = True
        self.type: Literal["FTDI", "USB"] = "USB"
        self.interface_number: int = 0
        self.suffix: Literal["RAW", "INSTR"] | None = None

    def check_vid_pid_serial_equal(self, other: _USBDevice) -> None:
        """Check if idVendor::idProduct::serial_number is unique.

        If not, then `self.is_serial_unique` and `other.is_serial_unique` are set to False.
        """
        if self.serial and self.serial == other.serial and self.vid == other.vid and self.pid == other.pid:
            self.is_serial_unique = False
            other.is_serial_unique = False

    @property
    def visa_address(self) -> str:
        """Returns the VISA-style address."""
        serial_id: str
        if self.serial and self.is_serial_unique:
            serial_id = self.serial
        elif self.bus is not None and self.address is not None:
            if self.serial and not self.is_serial_unique:
                self.description += f", serial number is {self.serial!r} but it is not unique"
            serial_id = f"bus={self.bus},address={self.address}"
        else:
            serial_id = "IGNORE"

        iface = "" if self.interface_number == 0 else f"::{self.interface_number}"
        suffix = f"::{self.suffix}" if self.suffix else ""
        return f"{self.type}::0x{self.vid:04x}::0x{self.pid:04x}::{serial_id}{iface}{suffix}"


def find_usb(usb_backend: Any = None) -> list[_USBDevice]:  # noqa: ANN401, C901, PLR0912
    """Find USB devices.

    These include: FTDI, USBTMC and RAW.
    """
    logger.debug("Searching for USB devices (backend=%r)", usb_backend)

    devices: list[_USBDevice] = []

    if isinstance(usb_backend, str):
        try:
            usb_backend = _usb_backend(usb_backend)
        except ValueError as e:
            logger.debug("ValueError: %s", e)
            return devices

    try:
        libusb_devices = usb.core.find(find_all=True, backend=usb_backend)
    except usb.core.NoBackendError:
        link = "https://mslnz.github.io/msl-equipment/dev/api/interfaces/usb/"
        logger.debug("NoBackendError: A PyUSB backend is not available. For tips on how to fix this issue see %s", link)
        return devices

    for usb_core_device in libusb_devices:
        for index, config in enumerate(usb_core_device):
            for interface in config:
                device: _USBDevice | None = None

                if usb_core_device.idVendor == 0x0403:  # noqa: PLR2004
                    device = _USBDevice(usb_core_device)
                    device.type = "FTDI"
                    if IS_WINDOWS and device.description == UNKNOWN_USB_DEVICE and not device.serial:
                        device.description += ", use FTDI2 address (if available) or use Zadig to replace driver"
                elif interface.bInterfaceClass == 0xFE and interface.bInterfaceSubClass == 3:  # noqa: PLR2004
                    device = _USBDevice(usb_core_device)
                    device.suffix = "INSTR"
                elif interface.bInterfaceClass == 0xFF and interface.bInterfaceSubClass == 0xFF:  # noqa: PLR2004
                    device = _USBDevice(usb_core_device)
                    device.suffix = "RAW"

                if device is not None:
                    if _is_linux_and_not_sudo() and device.description == UNKNOWN_USB_DEVICE:
                        device.description += ", try running as sudo or create a udev rule"
                    device.interface_number = interface.bInterfaceNumber
                    if usb_core_device.bNumConfigurations > 1 and index > 0:
                        device.description += f", define bConfigurationValue={config.bConfigurationValue}"
                    if interface.bAlternateSetting != 0:
                        device.description += f", define bAlternateSetting={interface.bAlternateSetting}"
                    devices.append(device)

    # Check for non-unique VID::PID::Serial
    for device1, device2 in combinations(devices, 2):
        device1.check_vid_pid_serial_equal(device2)

    return devices


@dataclass
class Endpoint:
    """Information about a USB Endpoint.

    Attributes:
        address (int): The `bEndpointAddress` value of the USB Endpoint.
        max_packet_size (int): The `wMaxPacketSize` value of the USB Endpoint.
        interface_number (int): The `bInterfaceNumber` value of the USB Interface
            that the USB Endpoint is associated with.
    """

    address: int
    interface_number: int
    max_packet_size: int


def _endpoint(cls: USB, interface: Any, direction: int, typ: int) -> Endpoint | None:  # noqa: ANN401
    """Get information about an Endpoint.

    Args:
        cls: A USB class instance.
        interface: A usb.core.Interface instance.
        direction: Either usb.util.ENDPOINT_IN or usb.util.ENDPOINT_OUT.
        typ: One of the usb.util.ENDPOINT_TYPE_* values.
    """

    def custom_match(ep: Any) -> bool:  # noqa: ANN401
        return bool(
            usb.util.endpoint_direction(ep.bEndpointAddress) == direction
            and usb.util.endpoint_type(ep.bmAttributes) == typ
        )

    ep = usb.util.find_descriptor(interface, custom_match=custom_match)
    if ep is None:
        if typ == usb.util.ENDPOINT_TYPE_BULK:
            d = "IN" if direction == usb.util.ENDPOINT_IN else "OUT"
            msg = f"Cannot find a bulk-{d} endpoint for {interface!r}"
            raise MSLConnectionError(cls, msg)
        return None

    return Endpoint(
        address=ep.bEndpointAddress,
        interface_number=interface.bInterfaceNumber,
        max_packet_size=ep.wMaxPacketSize,
    )


class USB(MessageBased, regex=REGEX):
    """Base class for (raw) USB communication."""

    class CtrlDirection(IntEnum):
        """The direction of a control transfer.

        Attributes:
            IN (int): Transfer direction is from device to computer.
            OUT (int): Transfer direction is from computer to device.
        """

        IN = usb.util.CTRL_IN
        OUT = usb.util.CTRL_OUT

    class CtrlRecipient(IntEnum):
        """The recipient of a control transfer.

        Attributes:
            DEVICE (int): Transfer is for a Device descriptor.
            INTERFACE (int): Transfer is for an Interface descriptor.
            ENDPOINT (int): Transfer is for an Endpoint descriptor.
        """

        DEVICE = usb.util.CTRL_RECIPIENT_DEVICE
        INTERFACE = usb.util.CTRL_RECIPIENT_INTERFACE
        ENDPOINT = usb.util.CTRL_RECIPIENT_ENDPOINT

    class CtrlType(IntEnum):
        """The type of a control transfer.

        Attributes:
            STANDARD (int): Standard type.
            CLASS (int): Class type.
            VENDOR (int): Vendor type.
        """

        STANDARD = usb.util.CTRL_TYPE_STANDARD
        CLASS = usb.util.CTRL_TYPE_CLASS
        VENDOR = usb.util.CTRL_TYPE_VENDOR

    def __init__(self, equipment: Equipment) -> None:  # noqa: C901, PLR0915
        """Base class for (raw) USB communication.

        Args:
            equipment: An [Equipment][] instance.

        A [Connection][msl.equipment.schema.Connection] instance supports the following _properties_
        for the USB communication protocol, as well as the _properties_ defined in
        [MessageBased][msl.equipment.interfaces.message_based.MessageBased].

        Attributes: Connection Properties:
            bAlternateSetting (int): The value of `bAlternateSetting` of the USB Interface Descriptor.
                _Default: `0`_
            bConfigurationValue (int | None): The value of `bConfigurationValue` of the USB Configuration
                Descriptor. If `None`, use the first Configuration found. _Default: `None`_
            usb_backend (Literal["libusb1", "libusb0", "openusb"] | None): The PyUSB backend library to use
                for the connection. If `None`, selects the first backend that is available. _Default: `None`_
        """
        self._detached: bool = False
        self._interface_number: int = 0
        self._timeout_ms: int = 0
        self._byte_buffer: bytearray = bytearray()
        super().__init__(equipment)

        assert equipment.connection is not None  # noqa: S101
        parsed = parse_usb_address(equipment.connection.address)
        if parsed is None:
            msg = f"Invalid USB address {equipment.connection.address!r}"
            raise ValueError(msg)

        p = equipment.connection.properties

        backend = p.get("usb_backend")
        if isinstance(backend, str):
            backend = _usb_backend(backend)

        try:
            device = _find_device(parsed, backend)
        except usb.core.NoBackendError:
            msg = (
                "A PyUSB backend is not available. For tips on how to fix this issue see "
                "https://mslnz.github.io/msl-equipment/dev/api/interfaces/usb/"
            )
            raise MSLConnectionError(self, msg) from None

        if device is None:
            msg = "The USB device was not found"
            if _is_linux_and_not_sudo():
                msg += " (try running as sudo or create a udev rule)"
            raise MSLConnectionError(self, msg)

        self._device: Any = device  # usb.core.Device instance

        self._interface_number = parsed.interface_number
        configuration_value: int | None = p.get("bConfigurationValue")
        alternate_setting: int = p.get("bAlternateSetting", 0)

        # If a kernel driver is active, the device will be unable to perform I/O
        # On Windows there is no kernel so NotImplementedError is raised
        with contextlib.suppress(usb.core.USBError, NotImplementedError):
            if device.is_kernel_driver_active(self._interface_number):
                device.detach_kernel_driver(self._interface_number)
                self._detached = True

        # Only set the USB Configuration if one is not already set
        # https://libusb.sourceforge.io/api-1.0/libusb_caveats.html#configsel
        cfg = None
        with contextlib.suppress(usb.core.USBError):
            cfg = device.get_active_configuration()

        if cfg is None or (configuration_value is not None and cfg.bConfigurationValue != configuration_value):
            try:
                device.set_configuration(configuration_value)
                cfg = device.get_active_configuration()
            except ValueError:
                msg = f"Invalid configuration value {configuration_value}"
                raise MSLConnectionError(self, msg) from None
            except usb.core.USBError as e:
                msg = f"Cannot set configuration to value {configuration_value}, {e}"
                raise MSLConnectionError(self, msg) from None

        # Get the USB Interface (and maybe set the Alternate Setting)
        interface = cfg[(self._interface_number, alternate_setting)]
        alternates = list(usb.util.find_descriptor(cfg, find_all=True, bInterfaceNumber=interface.bInterfaceNumber))
        if len(alternates) > 1:
            try:
                interface.set_altsetting()
            except usb.core.USBError as e:
                msg = f"Cannot set alternate setting for {interface!r}, {e}"
                raise MSLConnectionError(self, msg) from None

        # Get the info about some of the In/Out Endpoints for the selected USB Interface
        ep = _endpoint(self, interface, usb.util.ENDPOINT_IN, usb.util.ENDPOINT_TYPE_BULK)
        assert ep is not None  # noqa: S101
        self._bulk_in: Endpoint = ep

        ep = _endpoint(self, interface, usb.util.ENDPOINT_OUT, usb.util.ENDPOINT_TYPE_BULK)
        assert ep is not None  # noqa: S101
        self._bulk_out: Endpoint = ep

        self._intr_in: Endpoint | None = _endpoint(self, interface, usb.util.ENDPOINT_IN, usb.util.ENDPOINT_TYPE_INTR)
        self._intr_out: Endpoint | None = _endpoint(self, interface, usb.util.ENDPOINT_OUT, usb.util.ENDPOINT_TYPE_INTR)

    def _read(self, size: int | None) -> bytes:  # pyright: ignore[reportImplicitOverride]
        """Overrides method in MessageBased."""
        original_timeout = self._timeout_ms
        timeout = original_timeout
        address = self._bulk_in.address
        packet_size = self._bulk_in.max_packet_size
        termination = self._read_termination
        read = self._device.read
        t0 = time.time()
        while True:
            if size is not None:
                if len(self._byte_buffer) >= size:
                    msg = self._byte_buffer[:size]
                    self._byte_buffer = self._byte_buffer[size:]
                    break

            elif termination:
                index = self._byte_buffer.find(termination)
                if index != -1:
                    index += len(termination)
                    msg = self._byte_buffer[:index]
                    self._byte_buffer = self._byte_buffer[index:]
                    break

            data: array[int] = read(address, packet_size, timeout)
            self._byte_buffer.extend(data)

            if len(self._byte_buffer) > self._max_read_size:
                error = f"len(message) [{len(self._byte_buffer)}] > max_read_size [{self._max_read_size}]"
                raise RuntimeError(error)

            if original_timeout > 0:
                # decrease the timeout when reading each packet so that the total
                # time to receive all packets preserves what was specified
                elapsed_time = int((time.time() - t0) * 1000)
                if elapsed_time >= original_timeout:
                    raise MSLTimeoutError(self)
                timeout = max(1, original_timeout - elapsed_time)

        return bytes(msg)

    def _set_interface_timeout(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Overrides method in MessageBased."""
        # libusb docs: For an unlimited timeout, use value 0
        self._timeout_ms = 0 if self._timeout is None else round(self._timeout * 1000)

    def _write(self, message: bytes) -> int:  # pyright: ignore[reportImplicitOverride]
        """Overrides method in MessageBased."""
        address = self._bulk_out.address
        packet_size = self._bulk_out.max_packet_size
        timeout = self._timeout_ms
        write = self._device.write
        offset: int = 0
        size = len(message)
        while offset < size:
            write_size = packet_size
            if offset + write_size > size:
                write_size = size - offset
            length = write(address, message[offset : offset + write_size], timeout)
            if length <= 0:
                msg = "USB bulk OUT wrote <=0 bytes"
                raise MSLConnectionError(self, msg)
            offset += length
        return offset

    @staticmethod
    def build_request_type(direction: USB.CtrlDirection, type: USB.CtrlType, recipient: USB.CtrlRecipient) -> int:  # noqa: A002
        """Build a `bmRequestType` field for a control request.

        Args:
            direction: Transfer direction.
            type: Transfer type.
            recipient: Recipient of the transfer.

        Returns:
            The `request_type` argument for a [ctrl_transfer][msl.equipment.interfaces.usb.USB.ctrl_transfer].
        """
        request: int = usb.util.build_request_type(direction, type, recipient)
        return request

    @property
    def bulk_in_endpoint(self) -> Endpoint:
        """Information about the Bulk-IN endpoint."""
        return self._bulk_in

    @property
    def bulk_out_endpoint(self) -> Endpoint:
        """Information about the Bulk-OUT endpoint."""
        return self._bulk_out

    def clear_halt(self, endpoint: Endpoint) -> None:
        """Clear the halt/stall condition for an endpoint.

        Args:
            endpoint: The endpoint to clear.
        """
        logger.debug("%s.clear_halt(0x%02X)", self, endpoint.address)
        self._device.clear_halt(endpoint.address)

    def ctrl_transfer(
        self,
        request_type: int,
        request: int,
        value: int = 0,
        index: int = 0,
        data_or_length: int | bytes | bytearray | array[int] | str | None = None,
    ) -> int | array[int]:
        """Perform a control transfer on Endpoint 0.

        Args:
            request_type: The `bmRequestType` field for the setup packet. The bit-map value
                defines the direction (OUT or IN) of the request, the type of request
                and the designated recipient. See
                [build_request_type][msl.equipment.interfaces.usb.USB.build_request_type].
            request: Defines the request being made.
            value: The value field for the request.
            index: The index field for the request.
            data_or_length: Either the data payload for an OUT transfer or the number of
                bytes to read for an IN transfer. If there is no data payload, the parameter
                should be `None` for an OUT transfer or 0 for an IN transfer.

        Returns:
            For an OUT transfer, the returned value is the number of bytes sent to the equipment.
                For an IN transfer, the returned value is the data that was read.
        """
        # fmt: off
        logger.debug(
            "%s.ctrl_transfer(0x%02X, 0x%02X, 0x%04X, 0x%04X, %s, %d)",
            self, request_type, request, value, index, data_or_length, self._timeout_ms
        )
        # fmt: on

        try:
            out: int | array[int] = self._device.ctrl_transfer(
                bmRequestType=request_type,
                bRequest=request,
                wValue=value,
                wIndex=index,
                data_or_wLength=data_or_length,
                timeout=self._timeout_ms,
            )
        except usb.core.USBTimeoutError:
            raise MSLTimeoutError(self) from None
        except usb.core.USBError as e:
            raise MSLConnectionError(self, str(e)) from None
        else:
            return out

    @property
    def device_version(self) -> int:
        """Returns the device version (release) number.

        Corresponds to the `bcdDevice` field in the Device Descriptor.
        """
        dv: int = self._device.bcdDevice
        return dv

    def disconnect(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Disconnect from the USB device."""
        if not hasattr(self, "_device") or self._device is None:
            return None

        if self._detached:
            with contextlib.suppress(usb.core.USBError):
                self._device.attach_kernel_driver(self._interface_number)

        with contextlib.suppress(usb.core.USBError):
            usb.util.dispose_resources(self._device)

        self._device = None
        return super().disconnect()

    @property
    def intr_in_endpoint(self) -> Endpoint | None:
        """Information about the Interrupt-IN endpoint."""
        return self._intr_in

    @property
    def intr_out_endpoint(self) -> Endpoint | None:
        """Information about the Interrupt-OUT endpoint."""
        return self._intr_out

    def reset_device(self) -> None:
        """Perform a USB port reset for the device.

        If your program has to call this method, the reset will cause the
        device state to change (e.g., register values may be reset).
        """
        logger.debug("%s.reset_device()", self)
        self._device.reset()


@dataclass
class ParsedUSBAddress:
    """The parsed result of a VISA-style address for the USB interface.

    Args:
        vendor_id: The manufacturer of the USB device.
        product_id: The specific product identifier from the manufacturer.
        serial_id: An identifier of the serial number. Either the
            1. serial_number
            2. bus=#,address=#
            3. IGNORE
        interface_number: The USB Interface to use for communication.
    """

    vendor_id: int
    product_id: int
    serial_id: str
    interface_number: int


def parse_usb_address(address: str) -> ParsedUSBAddress | None:
    """Get the vendor/product/serial ID and the interface number.

    Args:
        address: The VISA-style address to use for the connection.

    Returns:
        The parsed address or `None` if `address` is not valid for the USB interface.
    """
    splitted = address.split("::")
    if len(splitted) < 4 or not address[:4].upper().startswith(("USB", "FTDI")):  # noqa: PLR2004
        return None

    _, vid, pid, sid, *remaining = splitted

    try:
        vendor_id = int(vid, 16) if vid.lower().startswith("0x") else int(vid)
    except ValueError:
        return None

    try:
        product_id = int(pid, 16) if pid.lower().startswith("0x") else int(pid)
    except ValueError:
        return None

    interface = 0
    with contextlib.suppress(ValueError, IndexError):
        interface = int(remaining[0])

    return ParsedUSBAddress(
        vendor_id=vendor_id,
        product_id=product_id,
        serial_id=sid,
        interface_number=interface,
    )
