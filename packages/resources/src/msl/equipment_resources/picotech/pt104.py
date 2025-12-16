"""PT-104 Platinum Resistance Data Logger from [Pico Technology](https://www.picotech.com/)."""

from __future__ import annotations

import sys
from ctypes import POINTER, byref, c_char_p, c_int8, c_int16, c_int32, c_uint16, c_uint32, create_string_buffer
from enum import IntEnum
from typing import TYPE_CHECKING

from msl.loadlib import LoadLibrary

from msl.equipment.interfaces import SDK, MSLConnectionError
from msl.equipment.utils import to_enum

from .status import PICO_INFO, PICO_OK, PICO_STATUS, Error, PicoInfo

if TYPE_CHECKING:
    from typing import Any, Literal

    from msl.loadlib.types import PathLike

    from msl.equipment.schema import Equipment


IS_WINDOWS = sys.platform == "win32"


class PT104(SDK, manufacturer=r"Pico\s*Tech", model=r"PT[-]?104"):
    """PT-104 Platinum Resistance Data Logger from [Pico Technology](https://www.picotech.com/)."""

    class Mode(IntEnum):
        """The measurement mode for a PT-104 Data Logger channel.

        Attributes:
            OFF (int): `0`
            PT100 (int): `1`
            PT1000 (int): `2`
            RESISTANCE_TO_375R (int): `3`
            RESISTANCE_TO_10K (int): `4`
            DIFFERENTIAL_TO_115MV (int): `5`
            DIFFERENTIAL_TO_2500MV (int): `6`
            SINGLE_ENDED_TO_115MV (int): `7`
            SINGLE_ENDED_TO_2500MV (int): `8`
        """

        OFF = 0
        PT100 = 1
        PT1000 = 2
        RESISTANCE_TO_375R = 3
        RESISTANCE_TO_10K = 4
        DIFFERENTIAL_TO_115MV = 5
        DIFFERENTIAL_TO_2500MV = 6
        SINGLE_ENDED_TO_115MV = 7
        SINGLE_ENDED_TO_2500MV = 8

    def __init__(self, equipment: Equipment) -> None:
        """PT-104 Platinum Resistance Data Logger from Pico Technology.

        Args:
            equipment: An [Equipment][] instance.

        A [Connection][msl.equipment.schema.Connection] instance supports the following _properties_
        for a PT104 Data Logger.

        Attributes: Connection Properties:
            ip_address (str): The IP address and port number, separated by a `:`, of the PT-104
                (e.g., `"192.168.1.201:1234"`).
            open_via_ip (bool): Whether to connect to the PT-104 by Ethernet. Default is to connect by USB.
                If `True`, then `ip_address` must be specified.
        """
        self._handle: int | None = None
        libtype = "windll" if IS_WINDOWS else "cdll"
        super().__init__(equipment, libtype=libtype)

        sdk = self.sdk
        sdk.UsbPt104OpenUnit.argtypes = [POINTER(c_int16), c_char_p]
        sdk.UsbPt104OpenUnit.restype = PICO_STATUS
        sdk.UsbPt104OpenUnit.errcheck = self._check
        sdk.UsbPt104OpenUnitViaIp.argtypes = [POINTER(c_int16), c_char_p, c_char_p]
        sdk.UsbPt104OpenUnitViaIp.restype = PICO_STATUS
        sdk.UsbPt104OpenUnitViaIp.errcheck = self._check
        sdk.UsbPt104CloseUnit.argtypes = [c_int16]
        sdk.UsbPt104CloseUnit.restype = PICO_STATUS
        sdk.UsbPt104CloseUnit.errcheck = self._check
        sdk.UsbPt104GetUnitInfo.argtypes = [c_int16, c_char_p, c_int16, POINTER(c_int16), PICO_INFO]
        sdk.UsbPt104GetUnitInfo.restype = PICO_STATUS
        sdk.UsbPt104GetUnitInfo.errcheck = self._check
        sdk.UsbPt104GetValue.argtypes = [c_int16, c_uint32, POINTER(c_int32), c_int16]
        sdk.UsbPt104GetValue.restype = PICO_STATUS
        sdk.UsbPt104GetValue.errcheck = self._check
        sdk.UsbPt104IpDetails.argtypes = [
            c_int16,
            POINTER(c_int16),
            c_char_p,
            POINTER(c_uint16),
            POINTER(c_uint16),
            c_uint32,
        ]
        sdk.UsbPt104IpDetails.restype = PICO_STATUS
        sdk.UsbPt104IpDetails.errcheck = self._check
        sdk.UsbPt104SetChannel.argtypes = [c_int16, c_uint32, c_uint32, c_int16]
        sdk.UsbPt104SetChannel.restype = PICO_STATUS
        sdk.UsbPt104SetChannel.errcheck = self._check
        sdk.UsbPt104SetMains.argtypes = [c_int16, c_uint16]
        sdk.UsbPt104SetMains.restype = PICO_STATUS
        sdk.UsbPt104SetMains.errcheck = self._check

        assert equipment.connection is not None  # noqa: S101
        p = equipment.connection.properties

        if p.get("open_via_ip", False):
            self._open_via_ip(p.get("ip_address", ""))
        else:
            self._open()

        self._scaling: dict[int, float] = {}

    def _check(self, result: Any, func: Any, arguments: tuple[Any, ...]) -> None:  # noqa: ANN401
        self._log_errcheck(result, func, arguments)
        if result != PICO_OK:
            msg = Error.get(result, f"UnknownPicoTechError: Error code 0x{result:08x}")
            raise MSLConnectionError(self, message=msg)

    def _open(self) -> None:
        """Open the connection to the PT-104 via USB."""
        handle = c_int16()
        self.sdk.UsbPt104OpenUnit(byref(handle), create_string_buffer(self.equipment.serial.encode()))
        self._handle = handle.value

    def _open_via_ip(self, address: str) -> None:
        """Open the connection to the PT-104 via ETHERNET.

        Args:
            address: The IP address and port number to use to connect to the PT-104.
                For example, `"192.168.1.201:1234"`.
        """
        if not address:
            msg = "You must specify the IP address in Connection.properties"
            raise MSLConnectionError(self, message=msg)

        handle = c_int16()
        serial = create_string_buffer(self.equipment.serial.encode())
        self.sdk.UsbPt104OpenUnitViaIp(byref(handle), serial, create_string_buffer(address.encode()))
        self._handle = handle.value

    def disconnect(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Disconnect from the PT-104 Data Logger."""
        if self._handle is not None:
            self.sdk.UsbPt104CloseUnit(self._handle)
            self._handle = None
            super().disconnect()

    @staticmethod
    def enumerate_units(
        path: PathLike = "usbpt104",
        communication: Literal["both", "ethernet", "usb"] = "both",
    ) -> list[str]:
        """Find PT-104 Platinum Resistance Data Logger's.

        This routine returns a list of all the attached PT-104 devices for the specified communication type.

        !!! warning
            You cannot call this function after you have opened a connection to a Data Logger.

        Args:
            path: The path to the Pico Technology SDK.
            communication: The communication type used by the PT-104.

        Returns:
            A list of serial numbers of the PT-104 Data Logger's that were found.
        """
        details = create_string_buffer(1024)

        t = communication.lower()
        if t == "usb":
            t_val = 0x00000001
        elif t == "ethernet":
            t_val = 0x00000002
        elif t == "both":
            t_val = 0xFFFFFFFF
        else:
            msg = f"Invalid communication type {communication}"
            raise ValueError(msg)

        libtype = "windll" if IS_WINDOWS else "cdll"
        sdk = LoadLibrary(path, libtype=libtype)
        result = sdk.lib.UsbPt104Enumerate(byref(details), byref(c_int16(len(details))), t_val)
        if result != PICO_OK:
            msg = Error.get(result, f"UnknownPicoTechError: Error code 0x{result:08x}")
            raise OSError(msg)

        return details.value.decode().split(",")

    def get_ip_details(self) -> tuple[bool, str, int]:
        """Reads the ethernet details of the PT-104 Data Logger.

        Returns:
            Whether connecting via ethernet is enabled, the IP address and the port number.
        """
        enabled = c_int16()
        address = create_string_buffer(128)
        port = c_uint16()
        self.sdk.UsbPt104IpDetails(self._handle, byref(enabled), address, byref(c_uint16(len(address))), byref(port), 0)
        return bool(enabled.value), address.value.decode(), port.value

    def get_unit_info(self, info: PicoInfo | str | int | None = None, *, prefix: bool = True) -> str:
        """Retrieves information about the PT-104 Data Logger.

        If the device fails to open, or no device is opened only the driver version is available.

        Args:
            info: An enum value or member name (case insensitive). If `None`, request all information from the PT-104.
            prefix: If `True`, includes the enum member name as a prefix.
                For example, returns `"CAL_DATE: 09Aug16"` if `prefix` is `True` else `"09Aug16"`.

        Returns:
            The requested information from the PT-104 Data Logger.
        """
        values = [PicoInfo(i) for i in range(7)] if info is None else [to_enum(info, PicoInfo, to_upper=True)]
        if info is None:
            values.append(PicoInfo.MAC_ADDRESS)

        string = create_string_buffer(32)
        required_size = c_int16()

        out: list[str] = []
        for value in values:
            name = f"{value.name}: " if prefix else ""
            self.sdk.UsbPt104GetUnitInfo(self._handle, string, len(string), byref(required_size), value)
            out.append(f"{name}{string.value.decode()}")
        return "\n".join(out)

    def get_value(self, channel: int, *, filtered: bool = False) -> float:
        r"""Get the most recent reading for the specified channel.

        Once you open the driver and define some channels, the driver begins to take
        continuous readings from the PT-104 Data Logger.

        Args:
            channel: The channel number to read, from 1 to 4 in differential mode or
                1 to 8 in single-ended mode.
            filtered: If `True`, the driver returns a low-pass filtered value of the temperature.
                The time constant of the filter depends on the channel parameters as set by
                [set_channel][msl.equipment_resources.picotech.pt104.PT104.set_channel]
                and on how many channels are active.

        Returns:
            The latest reading for the specified channel. A voltage reading is in $\text{V}$,
                a temperature reading is in $^{\circ}\text{C}$ and a resistance reading is in $\Omega$.
        """
        value = c_int32()
        self.sdk.UsbPt104GetValue(self._handle, channel, byref(value), int(filtered))
        return value.value * self._scaling.get(channel, 1.0)

    def set_channel(self, channel: int, mode: Mode | str | int, num_wires: Literal[2, 3, 4]) -> None:
        """Configure a single channel of the PT-104 Data Logger.

        The fewer channels configured, the more frequently they will be updated. A measurement
        takes about 1 second per active channel.

        If a call to the [set_channel][msl.equipment_resources.picotech.pt104.PT104.set_channel]
        method has a measurement mode of *single-ended*, then the specified channel's *sister* channel is
        also enabled (i.e., enabling 3 also enables 7).

        Args:
            channel: The channel number to configure. It should be between 1 and 4 if using
                single-ended inputs in voltage mode.
            mode: The measurement mode to configure the `channel` for. Can be an enum value or member name.
            num_wires: The number of wires that are used for the measurement.
        """
        _mode = to_enum(mode, PT104.Mode, to_upper=True)
        if num_wires not in {2, 3, 4}:
            msg = f"The num_wires value is {num_wires}. It must be 2, 3 or 4."
            raise ValueError(msg)
        self.sdk.UsbPt104SetChannel(self._handle, channel, _mode, num_wires)

        #    Measurement Type    |    Scaling factor
        #  Temperature           | value * 1/1000 deg C
        #  Resistance            | value * 1 mOhm
        #  Voltage (0 to 2.5 V)  | value * 10 nV
        #  Voltage (0 to 115 mV) | value * 1 nV
        if _mode in {PT104.Mode.PT100, PT104.Mode.PT1000, PT104.Mode.RESISTANCE_TO_375R, PT104.Mode.RESISTANCE_TO_10K}:
            self._scaling[channel] = 1e-3
        elif _mode in {PT104.Mode.DIFFERENTIAL_TO_115MV, PT104.Mode.SINGLE_ENDED_TO_115MV}:
            self._scaling[channel] = 1e-9
            if _mode == PT104.Mode.SINGLE_ENDED_TO_115MV:
                self._scaling[channel + 4] = 1e-9
        elif _mode in {PT104.Mode.DIFFERENTIAL_TO_2500MV, PT104.Mode.SINGLE_ENDED_TO_2500MV}:
            self._scaling[channel] = 10e-9
            if _mode == PT104.Mode.SINGLE_ENDED_TO_2500MV:
                self._scaling[channel + 4] = 10e-9
        else:
            self._scaling[channel] = 1.0

    def set_ip_details(self, *, enabled: bool, ip_address: str | None = None, port: int | None = None) -> None:
        """Set the IP details to the device.

        Args:
            enabled: Whether to enable or disable ethernet communication for this device.
            ip_address: The new IP address. If `None`, do not change the IP address.
            port: The new port number. If `None`, do not change the port number.
        """
        if ip_address is None or port is None:
            _, _ip_address, _port = self.get_ip_details()
            if ip_address is None:
                ip_address = _ip_address
            if port is None:
                port = _port

        c_address = (c_int8 * len(ip_address)).from_buffer_copy(ip_address.encode())
        self.sdk.UsbPt104IpDetails(
            self._handle, c_int16(enabled), c_address, c_uint16(len(ip_address)), c_uint16(port), 1
        )

    def set_mains(self, hertz: Literal[50, 60]) -> None:
        """Inform the driver of the local mains (line) frequency.

        This helps the driver to filter out electrical noise.

        Args:
            hertz: Power-line frequency, 50 or 60 Hz.
        """
        if hertz not in {50, 60}:
            msg = f"The mains frequency must be 50 or 60. Got {hertz}"
            raise ValueError(msg)
        self.sdk.UsbPt104SetMains(self._handle, 0 if hertz == 50 else 1)  # noqa: PLR2004
