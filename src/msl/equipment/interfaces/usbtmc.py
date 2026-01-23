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

from msl.equipment.enumerations import RENMode
from msl.equipment.utils import to_enum

from .message_based import MSLConnectionError
from .usb import USB

if TYPE_CHECKING:
    from array import array

    from msl.equipment.schema import Equipment


REGEX = re.compile(
    r"^USB(?P<board>\d*)::(?P<vid>[^:]+)::(?P<pid>[^:]+)::(?P<serial>(?:[^:]*|:(?!:))*)(::(?P<interface>\d+))?(::INSTR)?$",
    flags=re.IGNORECASE,
)


class _Message:
    """Prepare Bulk IN/OUT messages."""

    def __init__(self) -> None:
        self.tag: int = 0

    def dev_dep_msg_out(self, message: bytes, *, eom: bool = True) -> bytes:
        # USBTMC_1_00.pdf: Section 3.2.1.1, Table 3
        tag = self.next_tag()
        return (
            struct.pack(
                "<BBBxLBxxx",
                1,  # DEV_DEP_MSG_OUT, Table 2
                tag,
                tag ^ 0xFF,  # inverse
                len(message),
                eom,
            )
            + message
            + bytes((4 - len(message)) % 4)  # alignment bytes
        )

    def next_tag(self) -> int:
        # USBTMC_1_00.pdf: Section 3.2, Table 1
        self.tag += 1
        if self.tag > 255:  # noqa: PLR2004
            self.tag = 1
        return self.tag

    def request_dev_dep_msg_in(self, size: int) -> bytes:
        # USBTMC_1_00.pdf: Section 3.2.1.2, Table 4
        tag = self.next_tag()
        return struct.pack(
            "<BBBxLBBxx",
            2,  # REQUEST_DEV_DEP_MSG_IN, Table 2
            tag,
            tag ^ 0xFF,  # inverse
            size,
            0,  # do not use a termination character
            0,  # termination character
        )

    def trigger(self) -> bytes:
        # USBTMC_usb488_subclass_1_00.pdf, Section 3.2.1.1, Table 2
        tag = self.next_tag()
        return struct.pack(
            "BBB9x",
            128,  # TRIGGER, Table 1
            tag,
            tag ^ 0xFF,  # inverse
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
        # there are additional rules, however, not all manufacturer's obey these rules.
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
        self._tag_status: int = 1  # bTag for READ_STATUS_BYTE control transfer
        self._msg: _Message = _Message()

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

    def _read(self, size: int | None = None) -> bytes:  # pyright: ignore[reportImplicitOverride]
        """Overrides method in USB."""
        if self._capabilities.is_listen_only:
            msg = "The USBTMC device does not accept a read request"
            raise MSLConnectionError(self, msg)

        read = super()._read
        write = super()._write

        # Request for the device to send data
        # USBTMC_1_00.pdf, Section 3.2.1.2
        _ = write(self._msg.request_dev_dep_msg_in(size or self._max_read_size))

        # Parse Bulk-IN header
        # USBTMC_1_00.pdf, Section 3.3.1.1, Table 9
        # Ignore bTagInverse (only check bTag)
        msg_id, tag, transfer_size, eom = struct.unpack("<BBxxLBxxx", read(12))

        if msg_id != 2:  # DEV_DEP_MSG_IN, Table 2  # noqa: PLR2004
            # ABORT
            msg = f"Wrong DEV_DEP_MSG_IN value {msg_id} (expect 2), the device does not obey USBTMC standards."
            raise MSLConnectionError(self, msg)

        if tag != self._msg.tag:
            # ABORT
            msg = f"Received bTag [{tag}] != sent bTag [{self._msg.tag}], the device does not obey USBTMC standards."
            raise MSLConnectionError(self, msg)

        # Read all data plus the alignment bytes
        num_align_bytes = (4 - transfer_size) % 4
        data = read(transfer_size + num_align_bytes)
        if num_align_bytes == 0:
            return data
        return data[:transfer_size]

    def _write(self, message: bytes) -> int:  # pyright: ignore[reportImplicitOverride]
        """Overrides method in USB."""
        if self._capabilities.is_talk_only:
            msg = "The USBTMC device does not accept a write request"
            raise MSLConnectionError(self, msg)

        # USBTMC_1_00.pdf, Section 3.2
        # Rule 5 (below Table 2) states:
        #   "The Host must send a complete USBTMC command message with a single transfer"
        # Rule 1 (below Table 3) states:
        #  "The Host may send this USBTMC command message with multiple transfers, as the data becomes available"
        # Rule 5 uses the word "must", rule 1 uses "may". Follow Rule 5. Write complete message in a single transfer.
        # Also, libusb manages packet transactions (fragmentation), so we should not do it in Python.
        # Assume no Bulk-OUT transfer errors for now, if this becomes an issue see Section 3.2.2.3, Table 7.
        return super()._write(self._msg.dev_dep_msg_out(message))

    def control_ren(self, mode: RENMode | str | int) -> None:
        """Controls the state of the GPIB Remote Enable (REN) line.

        Optionally the remote/local state of the device is also controlled.

        Args:
            mode: The mode of the REN line and optionally the device remote/local state.
                Can be an enum member name (case insensitive) or value.
                Allowed values are:
        """
        if not self._capabilities.accepts_remote_local:
            msg = "The USBTMC device does not accept a remote-local request"
            raise MSLConnectionError(self, msg)

        mode = to_enum(mode, RENMode, to_upper=True)

        # mimic pyvisa-py
        if mode in {RENMode.ASSERT, RENMode.ASSERT_ADDRESS, RENMode.ASSERT_ADDRESS_LLO}:
            # USBTMC_usb488_subclass_1_00.pdf: Section 4.3.2, Table 15
            _ = self._check_ctrl_in_status(
                self.ctrl_transfer(
                    request_type=0xA1,  # Dir=IN, Type=Class, Recipient=Interface
                    request=160,  # REN_CONTROL, see Table 9
                    value=1,  # assert
                    index=self.bulk_in_endpoint.interface_number,
                    data_or_length=0x0001,
                )
            )

        if mode in {RENMode.ASSERT_LLO, RENMode.ASSERT_ADDRESS_LLO}:
            # USBTMC_usb488_subclass_1_00.pdf: Section 4.3.4, Table 19
            _ = self._check_ctrl_in_status(
                self.ctrl_transfer(
                    request_type=0xA1,  # Dir=IN, Type=Class, Recipient=Interface
                    request=162,  # LOCAL_LOCKOUT, see Table 9
                    value=0,  # always 0
                    index=self.bulk_in_endpoint.interface_number,
                    data_or_length=0x0001,
                )
            )

        if mode in {RENMode.DEASSERT_GTL, RENMode.ADDRESS_GTL}:
            # USBTMC_usb488_subclass_1_00.pdf: Section 4.3.3, Table 17
            _ = self._check_ctrl_in_status(
                self.ctrl_transfer(
                    request_type=0xA1,  # Dir=IN, Type=Class, Recipient=Interface
                    request=161,  # GO_TO_LOCAL, see Table 9
                    value=0,  # always 0
                    index=self.bulk_in_endpoint.interface_number,
                    data_or_length=0x0001,
                )
            )

        if mode in {RENMode.DEASSERT, RENMode.DEASSERT_GTL}:
            # USBTMC_usb488_subclass_1_00.pdf: Section 4.3.2, Table 15
            _ = self._check_ctrl_in_status(
                self.ctrl_transfer(
                    request_type=0xA1,  # Dir=IN, Type=Class, Recipient=Interface
                    request=160,  # REN_CONTROL, see Table 9
                    value=0,  # deassert
                    index=self.bulk_in_endpoint.interface_number,
                    data_or_length=0x0001,
                )
            )

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

        self._tag_status += 1
        if self._tag_status > 127:  # noqa: PLR2004
            self._tag_status = 2

        # USBTMC_usb488_subclass_1_00.pdf: Section 4.3.1, Table 11
        _, tag, data = self._check_ctrl_in_status(
            self.ctrl_transfer(
                request_type=0xA1,  # Dir=IN, Type=Class, Recipient=Interface
                request=128,  # READ_STATUS_BYTE, see Table 9
                value=self._tag_status,
                index=self.bulk_in_endpoint.interface_number,
                data_or_length=0x0003,
            )
        )

        if self._tag_status != tag:
            msg = f"sent bTag [{self._tag_status}] != received bTag [{tag}]"
            raise MSLConnectionError(self, msg)

        # USBTMC_usb488_subclass_1_00.pdf: Section 4.3.1.1, Table 12
        if self.intr_in_endpoint is None:
            return data

        # USBTMC_usb488_subclass_1_00.pdf: Section 3.4.2, Table 7
        status: int
        notify1, status = self._device.read(self.intr_in_endpoint.address, 2, self._timeout_ms)
        d7_not_1 = not (notify1 & 0x80)
        tag_mismatch = (notify1 & 0x7F) != self._tag_status
        if d7_not_1 or tag_mismatch:
            msg = "Invalid Interrupt-IN response packet"
            if d7_not_1:
                msg += ", bit 7 is not 1"
            if tag_mismatch:
                msg += f", sent bTag [{self._tag_status}] != received bTag [{notify1 & 0x7F}]"
            raise MSLConnectionError(self, msg)

        return status

    def trigger(self) -> None:
        """Trigger device."""
        if not self._capabilities.accepts_trigger:
            msg = "The USBTMC device does not accept the trigger request"
            raise MSLConnectionError(self, msg)

        _ = super()._write(self._msg.trigger())
