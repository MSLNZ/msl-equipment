"""Communicate with equipment from NKT Photonics."""

# cSpell: ignore Koheras ADJUSTIK ACOUSTIK BOOSTIK BASIK MIKRO HARMONIK VARIA CHROMATUNE Aeropulse
from __future__ import annotations

import binascii
import contextlib
import struct
from enum import IntEnum
from threading import Lock
from typing import TYPE_CHECKING, NamedTuple, overload

from msl.equipment.interfaces.message_based import MSLConnectionError, MSLTimeoutError
from msl.equipment.interfaces.serial import Serial, parse_serial_address
from msl.equipment.interfaces.socket import Socket
from msl.equipment.schema import Interface

if TYPE_CHECKING:
    from typing import Literal

    from msl.equipment.schema import Equipment


# NKT's "SDK Instruction manual v2.1.15.pdf", Section 2.3
SOT = 0x0D  # Start of Telegram
EOT = 0x0A  # End of Telegram
SOE = 0x5E  # Start of substitution word
ECC = 0x40  # Second byte offset

HOST = 0xA2  # Address of host (computer)


def _crc(data: bytes) -> bytes:
    """Returns the Cyclic Redundancy Check (CRC) value of `data`."""
    return struct.pack(">H", binascii.crc_hqx(data, 0))


def _frame(message: bytes) -> bytes:
    """Frame a message using [SOT][MESSAGE][EOT], escaping special characters in the message."""
    # make local references for the loop
    ecc, soe, special = ECC, SOE, {SOT, EOT, SOE}

    telegram = [SOT]
    for char in message:
        if char in special:  # Section 2.3: Special character conversion
            telegram.extend([soe, char + ecc])
        else:
            telegram.append(char)
    telegram.append(EOT)
    return bytes(telegram)


def _build_telegram(dest: int, typ: int, reg: int, data: bytes = b"") -> bytes:
    """Build a telegram that may be sent to the device."""
    data = struct.pack("BBBB", dest, HOST, typ, reg) + data
    return _frame(data + _crc(data))


def _build_read_telegram(dest: int, reg: int) -> bytes:
    """Build a telegram to read a register value."""
    return _build_telegram(dest, 4, reg)  # READ=4


# Defined in "SDK\Register Files\Module types.txt", plus some extras
_module_types = {
    0x20: "Koheras ADJUSTIK/BOOSTIK (K81-1 to K83-1)",
    0x21: "Koheras BASIK Module (K80-1)",
    0x33: "Koheras BASIK Module (K1x2)",
    0x34: "Koheras ADJUSTIK/ACOUSTIK (K822 / K852)",
    0x36: "Koheras BASIK MIKRO Module (K0x2)",
    0x3A: "Koheras BOOSTIK HP (K533x / K833x)",
    0x3B: "Koheras HARMONIK (K592x)",
    0x60: "SuperK Extreme (S4x2), Fianium",
    0x61: "SuperK Extreme Front panel",
    0x62: "Seed",
    0x63: "Preamp",
    0x66: "RF Driver (A901) & SuperK Select (A203)",
    0x67: "SuperK SELECT (A203)",
    0x68: "SuperK VARIA (A301)",
    0x6A: "NKTP Booster 2013",
    0x6B: "Extend UV (A351)",
    0x70: "BoostiK OEM Amplifier (N83)",
    0x74: "SuperK COMPACT (S024)",
    0x7D: "SuperK EVO (S2x1)",
    0x81: "Ethernet Module",
    0x88: "SuperK FIANIUM (S4x3)",
    0x8A: "FS-60 Environment and Shutter Module",
    0x8F: "SuperK EVO v2",
    0x99: "SuperK CHROMATUNE",
    0x9D: "Aeropulse mainboard",
}


_data_types = {
    "u8": "B",
    "i8": "b",
    "h8": "B",
    "u16": "<H",
    "i16": "<h",
    "h16": "<H",
    "u32": "<I",
    "i32": "<i",
    "h32": "<I",
    "f32": "<f",
    "f64": "<d",
    "bytes": "bytes",
    "string": "string",
}


class _MessageType(IntEnum):
    """Message response type (Section 2.2)."""

    NACK = 0
    BUSY = 2
    ACK = 3
    READ = 4
    WRITE = 5
    DATAGRAM = 8


class _Response(NamedTuple):
    """Response from an NKT device.

    Attributes:
        address (int): Module address (device ID).
        type (MessageType): The message type of the response.
        register (int): Register address.
        data (bytes): Response data.
    """

    address: int
    type: _MessageType
    register: int
    data: bytes


class Module(NamedTuple):
    """Information about a module.

    Attributes:
        address (int): Module address.
        type (int): Module type.
        description (str): A description about the module.
        firmware (str): Firmware version number.
        serial (str): Serial number.
    """

    address: int
    type: int
    description: str
    firmware: str
    serial: str

    def __repr__(self) -> str:  # pyright: ignore[reportImplicitOverride]
        """Returns the string representation."""
        return (
            f"Module(address={self.address}, type=0x{self.type:04X}, description={self.description!r}, "
            f"firmware={self.firmware!r}, serial={self.serial!r})"
        )


class NKT(Interface):
    """Communicate with equipment from NKT Photonics."""

    def __init__(self, equipment: Equipment) -> None:
        """Communicate with equipment from NKT Photonics.

        Both ethernet and serial interfaces are supported.

        Args:
            equipment: An [Equipment][] instance.

        A [Connection][msl.equipment.schema.Connection] instance supports the following _properties_
        for the `NKT` class.

        Attributes: Connection Properties:
            timeout (float | None): The timeout, in seconds, for
                [read_register][msl.equipment_resources.nkt.nkt.NKT.read_register] and
                [write_register][msl.equipment_resources.nkt.nkt.NKT.write_register] operations.
                _Default: `None`_
        """
        self._connected: bool = False
        assert equipment.connection is not None  # noqa: S101
        super().__init__(equipment)

        props = equipment.connection.properties

        self._interface: Serial | Socket
        if parse_serial_address(equipment.connection.address) is not None:
            props.setdefault("baud_rate", 115200)
            props.setdefault("rts_cts", True)
            self._interface = Serial(equipment)
        else:
            self._interface = Socket(equipment)

        self._connected = True
        self._interface.read_termination = bytes([EOT])
        self._interface.write_termination = None

        self._lock: Lock = Lock()

        self.timeout = props.get("timeout")

    def _send_telegram(self, telegram: bytes, *, check_nack: bool = True, check_busy: bool = True) -> _Response:
        # Use a lock to avoid dealing with "Address cycling" (Section 2.2: Telegram)
        with self._lock:
            sot, *message, _ = self._interface.query(telegram, decode=False)

            if sot != SOT:
                msg = "NKT device sent an invalid Start of Telegram (SOT) value"
                raise MSLConnectionError(self, msg)

            # no need to check for EOT since read_termination handles it

            soe, ecc = SOE, ECC  # make local references for the loop
            iterable = iter(message)
            unescaped = bytes(next(iterable) - ecc if c == soe else c for c in iterable)

            payload = unescaped[:-2]
            if bytes(unescaped[-2:]) != _crc(payload):
                msg = "NKT device sent an invalid Cyclic Redundancy Check (CRC) value"
                raise MSLConnectionError(self, msg)

            dest, source, typ, reg = payload[:4]
            if check_nack and typ == _MessageType.NACK:
                msg = "The message sent to the NKT device is not understood, not applicable or not allowed"
                raise MSLConnectionError(self, msg)

            if check_busy and typ == _MessageType.BUSY:
                msg = "NKT device cannot respond at the moment, module too busy"
                raise MSLConnectionError(self, msg)

            if dest != HOST:
                msg = "NKT device sent a response that is not intended for the host (computer)"
                raise MSLConnectionError(self, msg)

            return _Response(address=source, type=_MessageType(typ), register=reg, data=payload[4:])

    def disconnect(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Disconnect from the NKT equipment."""
        if self._connected:
            self._interface.disconnect()
            super().disconnect()
            self._connected = False

    @overload
    def read_register(self, module: int, register: int, dtype: None = None) -> bytes: ...

    @overload
    def read_register(self, module: int, register: int, dtype: Literal["string"]) -> str: ...

    @overload
    def read_register(
        self, module: int, register: int, dtype: Literal["i8", "u8", "h8", "i16", "u16", "h16", "i32", "u32", "h32"]
    ) -> int: ...

    @overload
    def read_register(self, module: int, register: int, dtype: Literal["f32", "f64"]) -> float: ...

    def read_register(
        self,
        module: int,
        register: int,
        dtype: Literal["i8", "u8", "h8", "i16", "u16", "h16", "i32", "u32", "h32", "f32", "f64", "string"]
        | None = None,
    ) -> bytes | str | int | float:
        """Read the register value of the device.

        Args:
            module: Module address (device ID).
            register: Register address.
            dtype: The data type to return the value in. If not specified, returns the value as bytes.

        Returns:
            The register value.
        """
        r = self._send_telegram(_build_read_telegram(module, register))
        if r.type != _MessageType.DATAGRAM:
            msg = f"NKT device did not respond with a DATAGRAM message type, got {r.type!r}"
            raise MSLConnectionError(self, msg)

        if dtype is None:
            return r.data

        fmt = _data_types.get(dtype.lower())
        if fmt is None:
            dt = ", ".join(_data_types)
            msg = f"Invalid register data type {dtype!r}, must be one of: {dt}"
            raise ValueError(msg)

        if fmt == "string":
            return r.data.decode()

        value: int | float = struct.unpack(fmt, r.data)[0]
        return value

    def scan_modules(self, *, start: int = 1, stop: int = 160, timeout: float = 0.05) -> list[Module]:
        """Scan for available modules that can be communicated with.

        Args:
            start: The address to start the scan at.
            stop: The address to stop the scan at.
            timeout: The maximum number of seconds to wait for a reply from a potential module.

        Returns:
            The modules that are available.
        """
        original_timeout = self._interface.timeout
        self._interface.timeout = timeout

        modules: list[Module] = []
        for addr in range(start, stop + 1):
            with contextlib.suppress(MSLTimeoutError):
                r = self._send_telegram(_build_read_telegram(addr, 0x61), check_nack=False, check_busy=False)
                if r.type == _MessageType.DATAGRAM:
                    # Section 6.2: Module type could either be 1 or 2 bytes
                    if len(r.data) == 1:
                        mod_type, description = r.data[0], ""
                    else:
                        # Don't use second byte for K81-1, K82-1 and K83-1 (module type 20h) or K80-1 (module type 21h)
                        mod_type = r.data[0] if r.data[0] in {0x20, 0x21} else int(struct.unpack("<H", r.data[:2])[0])
                        description = r.data[2:].rstrip(b"\x00").decode()

                    # Serial number (65h)
                    sn = self._send_telegram(_build_read_telegram(addr, 0x65))

                    # Firmware version number (64h)
                    # The firmware version register returns two parameters:
                    #  1) 16-bit firmware version (major and minor version)
                    #  2) Version ASCII text string, of up to 64 bytes length, zero terminated.
                    fw = self._send_telegram(_build_read_telegram(addr, 0x64), check_nack=False)
                    # only use ASCII text
                    firmware = fw.data[2:].rstrip(b"\x00").decode() if fw.type == _MessageType.DATAGRAM else ""

                    modules.append(
                        Module(
                            address=r.address,
                            type=mod_type,
                            description=description or _module_types.get(mod_type, ""),
                            firmware=firmware,
                            serial=sn.data.decode(),
                        )
                    )

        self._interface.timeout = original_timeout
        return modules

    @property
    def timeout(self) -> float | None:
        """The timeout, in seconds, for [read_register][msl.equipment_resources.nkt.nkt.NKT.read_register]
        and [write_register][msl.equipment_resources.nkt.nkt.NKT.write_register] operations.

        A value &lt;0 will set the timeout to be `None` (blocking mode).
        """  # noqa: D205
        return self._interface.timeout

    @timeout.setter
    def timeout(self, value: float | None) -> None:
        self._interface.timeout = value

    def write_register(
        self,
        module: int,
        register: int,
        value: bytes | str | float,
        dtype: Literal["i8", "u8", "h8", "i16", "u16", "h16", "i32", "u32", "h32", "f32", "f64"] | None = None,
    ) -> None:
        """Write a value to a register of the device.

        Args:
            module: Module address (device ID).
            register: Register address.
            value: The value to write.
            dtype: The data type to convert `value` to. Only required if `value` is not already in bytes or a string.
        """
        if isinstance(value, bytes):
            data = value
        elif isinstance(value, str):
            data = value.encode()
        else:
            if dtype is None:
                msg = "Must specify the data type of the register value since the value is not already in bytes"
                raise ValueError(msg)

            fmt = _data_types.get(dtype.lower())
            if fmt is None:
                dt = ", ".join(_data_types)
                msg = f"Invalid register data type {dtype!r}, must be one of: {dt}"
                raise ValueError(msg)

            data = struct.pack(fmt, value)

        _ = self._send_telegram(_build_telegram(module, 5, register, data))  # WRITE=5
