"""Base class for the USBTMC communication protocol.

The following documents were used as references:

https://www.usb.org/document-library/test-measurement-class-specification

* Universal Serial Bus Test and Measurement Class Specification (USBTMC)
    Revision 1.0
    April 14, 2003

* Universal Serial Bus Test and Measurement Class, Subclass USB488 Specification (USBTMC-USB488)
    Revision 1.0
    April 14, 2003
"""

from __future__ import annotations

import re
import struct
from typing import TYPE_CHECKING

from .message_based import MSLConnectionError
from .usb import USB

if TYPE_CHECKING:
    from array import array

    from msl.equipment.schema import Equipment


REGEX = re.compile(
    r"^USB(?P<board>\d*)::(?P<vid>[^:]+)::(?P<pid>[^:]+)::(?P<serial>(?:[^:]*|:(?!:))*)(::(?P<interface>\d+))?(::INSTR)?$",
    flags=re.IGNORECASE,
)


class Capabilities:
    """USBTMC device capabilities."""

    def __init__(self, data: array[int]) -> None:
        """USBTMC device capabilities.

        Attributes:
            data (array[int]): The `GET_CAPABILITIES` response from the device.
            accepts_indicator_pulse (bool): Whether the interface accepts the `INDICATOR_PULSE` request.
            accepts_remote_local (bool): Whether the interface accepts `REN_CONTROL`, `GO_TO_LOCAL`
                and `LOCAL_LOCKOUT` requests.
            accepts_service_request (bool): Whether the device accepts a service request.
            accepts_term_char (bool): Whether the device supports ending a Bulk-IN transfer when a byte matches the
                [read_termination][msl.equipment.interface.message_based.MessageBased.read_termination] character.
            accepts_trigger (bool): Whether the device accepts the `TRIGGER` request.
            is_488 (bool): Whether the device understands all mandatory SCPI commands, accepts a service
                request and is a 488.2 interface.
            is_listen_only (bool): Whether the interface is listen-only.
            is_talk_only (bool): Whether the interface is talk-only.
        """
        # USBTMC_1_00.pdf: Section 4.2.1.8, Table 37
        # USBTMC_usb488_subclass_1_00.pdf: Section 4.2.2, Table 8
        self.data: array[int] = data
        status, iface, device, iface_488, device_488 = struct.unpack("B3x2B8x2B8x", data)
        if status != 1:  # unsuccessful response, silently ignore the data that came back
            iface = device = iface_488 = device_488 = 0

        # USBTMC Interface Capabilities
        self.accepts_indicator_pulse: bool = bool(iface & (1 << 2))
        self.is_talk_only: bool = bool(iface & (1 << 1))
        self.is_listen_only: bool = bool(iface & (1 << 0))

        # USBTMC Device Capabilities
        self.accepts_term_char: bool = bool(device & (1 << 0))

        # USB488 Interface Capabilities
        is_488_interface = bool(iface_488 & (1 << 2))
        accepts_remote_local = bool(iface_488 & (1 << 1))
        accepts_interface_trigger = bool(iface_488 & (1 << 0))

        # USB488 Device Capabilities
        understands_scpi = bool(device_488 & (1 << 3))
        is_sr_capable = bool(device_488 & (1 << 2))
        is_rl_capable = bool(device_488 & (1 << 1))
        is_dt_capable = bool(device_488 & (1 << 0))

        # Underneath Table 8 (USBTMC_usb488_subclass_1_00.pdf: Section 4.2.2)
        # there are additional rules, however, not all manufacturer's follow these rules.
        # If either of the bitmap values is True then the instance attribute is considered True.
        self.accepts_trigger: bool = is_dt_capable or accepts_interface_trigger  # rule 1
        self.accepts_remote_local: bool = is_rl_capable or accepts_remote_local  # rule 2
        self.accepts_service_request: bool = is_488_interface or is_sr_capable  # rule 3
        self.is_488: bool = understands_scpi or (is_sr_capable and is_488_interface)  # rule 4

    def __repr__(self) -> str:  # pyright: ignore[reportImplicitOverride]
        """Returns the string representation."""
        return (
            "Capabilities(\n"
            f"  data={self.data},\n"
            f"  accepts_indicator_pulse={self.accepts_indicator_pulse},\n"
            f"  accepts_remote_local={self.accepts_remote_local},\n"
            f"  accepts_service_request={self.accepts_service_request},\n"
            f"  accepts_term_char={self.accepts_term_char},\n"
            f"  accepts_trigger={self.accepts_trigger},\n"
            f"  is_488={self.is_488},\n"
            f"  is_listen_only={self.is_listen_only},\n"
            f"  is_talk_only={self.is_talk_only}\n"
            ")"
        )


class USBTMC(USB, regex=REGEX):
    """Base class for the USBTMC communication protocol."""

    def __init__(self, equipment: Equipment) -> None:
        """Base class for the USBTMC communication protocol.

        Args:
            equipment: An [Equipment][] instance.

        A [Connection][msl.equipment.schema.Connection] instance supports the same _properties_
        as those specified in [USB][msl.equipment.interfaces.usb.USB].
        """
        super().__init__(equipment)
        self._status_tag: int = 1  # bTag for READ_STATUS_BYTE control transfer

        # USBTMC_1_00.pdf: Section 4.2.1.8, Table 36
        self._capabilities: Capabilities = Capabilities(
            self.ctrl_transfer(
                request_type=0xA1,  # Dir=IN, Type=Class, Recipient=Interface
                request=7,  # GET_CAPABILITIES, see Table 15
                value=0,
                index=self.bulk_in_endpoint.interface_number,
                data_or_length=0x0018,
            )
        )

    def _check_ctrl_in_status(self, data: array[int]) -> array[int]:
        # USBTMC_1_00.pdf: Table 16
        if data[0] != 1:  # STATUS_SUCCESS
            msg = f"The request was not successful [status_code=0x{data[0]:02X}]"
            raise MSLConnectionError(self, msg)
        return data

    @property
    def capabilities(self) -> Capabilities:
        """Returns the capabilities of the USBTMC device."""
        return self._capabilities

    def indicator_pulse(self) -> None:
        """Request to turn on an activity indicator for identification purposes.

        If the device supports the request, the device turns on an implementation-dependent
        activity indicator for a duration between 0.5 and 1 second. The activity indicator
        then automatically turns off.
        """
        if not self._capabilities.accepts_indicator_pulse:
            msg = "The USBTMC device does not accept the indicator-pulse request"
            raise MSLConnectionError(self, msg)

        # USBTMC_1_00.pdf: Section 4.2.1.9, Table 38
        _ = self._check_ctrl_in_status(
            self.ctrl_transfer(
                request_type=0xA1,  # Dir=IN, Type=Class, Recipient=Interface
                request=64,  # INDICATOR_PULSE, see Table 15
                value=0,
                index=self.bulk_in_endpoint.interface_number,
                data_or_length=0x0001,
            )
        )

    def serial_poll(self) -> int:
        """Read status byte / serial poll (device).

        This method is equivalent to the [ibrsp](https://linux-gpib.sourceforge.io/doc_html/reference-function-ibrsp.html)
        function.

        Returns:
            The status byte.
        """
        if not self._capabilities.is_488:
            msg = "The USBTMC device does not accept the serial-poll request"
            raise MSLConnectionError(self, msg)

        self._status_tag += 1
        if self._status_tag > 127:  # noqa: PLR2004
            self._status_tag = 2

        # USBTMC_usb488_subclass_1_00.pdf: Section 4.3.1, Table 11
        data = self._check_ctrl_in_status(
            self.ctrl_transfer(
                request_type=0xA1,  # Dir=IN, Type=Class, Recipient=Interface
                request=128,  # READ_STATUS_BYTE, see Table 9
                value=self._status_tag,
                index=self.bulk_in_endpoint.interface_number,
                data_or_length=0x0003,
            )
        )

        if self._status_tag != data[1]:
            msg = f"sent bTag [{self._status_tag}] != received bTag [{data[1]}]"
            raise MSLConnectionError(self, msg)

        # USBTMC_usb488_subclass_1_00.pdf: Section 4.3.1.1, Table 12
        if self.intr_in_endpoint is None:
            return data[2]

        # USBTMC_usb488_subclass_1_00.pdf: Section 3.4.2, Table 7
        byte: int
        notify1, byte = self._device.read(self.intr_in_endpoint.address, 2, self._timeout_ms)
        d7_not_1 = not (notify1 & 0x80)
        bad_tag = (notify1 & 0x7F) != self._status_tag
        if d7_not_1 or bad_tag:
            msg = "Invalid Interrupt-IN response packet"
            if d7_not_1:
                msg += ", bit 8 is not 1"
            if bad_tag:
                msg += f", sent bTag [{self._status_tag}] != received bTag [{notify1 & 0x7F}]"
            raise MSLConnectionError(self, msg)

        return byte
