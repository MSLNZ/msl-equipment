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

import contextlib
import re
import struct
from time import sleep
from typing import TYPE_CHECKING

from msl.equipment.enumerations import RENMode
from msl.equipment.utils import logger, to_enum

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
        self.tag = (self.tag % 255) + 1
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

        !!! warning
            Do not instantiate this class. The device capabilities are automatically determined
            when the connection is established. You can access these attributes via the
            [capabilities][msl.equipment.interfaces.usbtmc.USBTMC.capabilities] property.
            A manufacturer may not strictly follow the rules defined in the USBTMC standard.
            You may change the value of an attribute if you get an error when requesting
            a capability (such as [trigger][msl.equipment.interfaces.usbtmc.USBTMC.trigger])
            stating that the capability is not supported even though you know that it is.

        Attributes:
            data (array[int]): The `GET_CAPABILITIES` response from the device.
            accepts_indicator_pulse (bool): Whether the interface accepts the `INDICATOR_PULSE` request.
            accepts_remote_local (bool): Whether the interface accepts `REN_CONTROL`, `GO_TO_LOCAL`
                and `LOCAL_LOCKOUT` requests.
            accepts_service_request (bool): Whether the device accepts a service request.
            accepts_term_char (bool): Whether the device supports ending a Bulk-IN transfer when a byte matches the
                [read_termination][msl.equipment.interfaces.message_based.MessageBased.read_termination] character.
            accepts_trigger (bool): Whether the device accepts the `TRIGGER` request.
            is_488_interface (bool): Whether the device understands all mandatory SCPI commands, accepts a service
                request and is a 488.2 interface. See *Appendix 2: IEEE 488.2 compatibility* in
                [USBTMC_usb488_subclass_1_00.pdf](https://www.usb.org/document-library/test-measurement-class-specification){:target="_blank"}
                for more details.
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
        self.is_488_interface: bool = understands_scpi or (is_sr_capable and is_488_interface)  # rule 4

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
            f"  is_488_interface={self.is_488_interface},\n"
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
                request=7,  # GET_CAPABILITIES, Table 15
                value=0,
                index=self.bulk_in_endpoint.interface_number,
                data_or_length=0x0018,
            )
        )

    def _abort_transaction(self, direction: USB.CtrlDirection, tag: int | None = None) -> None:  # noqa: C901
        """Abort a pending Bulk-OUT/IN transaction."""
        logger.debug("%s aborting %r transaction ...", self, direction)

        # USBTMC_1_00.pdf, Section 4.2.1.2 (Abort Bulk-OUT), Section 4.2.1.4 (Abort Bulk-IN)
        if direction == USB.CtrlDirection.OUT:
            # Table 15: INITIATE_ABORT_BULK_OUT=1, CHECK_ABORT_BULK_OUT_STATUS=2
            initiate, check, index = 1, 2, self.bulk_out_endpoint.address
        else:
            # Table 15: INITIATE_ABORT_BULK_IN=3, CHECK_ABORT_BULK_IN_STATUS=4
            initiate, check, index = 3, 4, self.bulk_in_endpoint.address

        # Tables 18 (Bulk-OUT) and 24 (Bulk-IN)
        status, current_tag = self.ctrl_transfer(
            request_type=0xA2,  # Dir=IN, Type=Class, Recipient=Endpoint
            request=initiate,
            value=self._msg.tag if tag is None else tag,
            index=index,
            data_or_length=0x0002,
        )

        if status == 0x81:  # USBTMC_1_00.pdf, Table 16, STATUS_TRANSFER_NOT_IN_PROGRESS  # noqa: PLR2004
            if tag is None:  # Avoid RecursionError
                # For a STATUS_TRANSFER_NOT_IN_PROGRESS issue, Tables 20 (Bulk-OUT) and 26 (Bulk-IN) state:
                #   * There is a transfer in progress, but the specified bTag does not match
                #   * There is no transfer in progress, but the Bulk-OUT FIFO is not empty
                # Specified wrong tag? Try again with the tag that was returned from the device
                self._abort_transaction(direction, current_tag)
            return

        if status != 0x01:  # USBTMC_1_00.pdf: Table 16, STATUS_SUCCESS
            return

        def read_short_packet() -> None:
            self._byte_buffer.clear()
            with contextlib.suppress(OSError):
                self._device.read(self.bulk_in_endpoint.address, self.bulk_in_endpoint.max_packet_size, 1000)

        # Table 26 (Bulk-IN)
        # The Host should continue reading from the Bulk-IN endpoint until a short packet is received
        if direction == USB.CtrlDirection.IN:
            read_short_packet()

        # USBTMC_1_00.pdf: Tables 21 (Bulk-OUT) and 27 (Bulk-IN)
        for i in range(1, 100):
            status, fifo, *_ = self.ctrl_transfer(
                request_type=0xA2,  # Dir=IN, Type=Class, Recipient=Endpoint
                request=check,
                value=0x0000,
                index=index,
                data_or_length=0x0008,
            )

            # Tables 23 (Bulk-OUT) and 29 (Bulk-IN) describes Host behaviour
            if status == 0x02:  # USBTMC_1_00.pdf, Table 16, STATUS_PENDING  # noqa: PLR2004
                logger.debug("%s aborting %r transaction PENDING [iteration=%d]", self, direction, i)
                sleep(0.05)
                if fifo and direction == USB.CtrlDirection.IN:
                    read_short_packet()  # Table 29, bmAbortBulkIn.D0 = 1
                continue  # check again if STATUS_PENDING

            if direction == self.CtrlDirection.OUT:
                # USBTMC_1_00.pdf, Section 4.1.1 and Table 23 -- send CLEAR_FEATURE then done
                self.clear_halt(self.bulk_out_endpoint)

            logger.debug("%s aborting %r transaction done", self, direction)
            return

    def _check_ctrl_in_status(self, data: array[int]) -> array[int]:
        if data[0] != 1:  # USBTMC_1_00.pdf: Table 16, STATUS_SUCCESS
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

        message = bytearray()
        msg_in_size = size or self._buffer_size

        try:
            # USBTMC_1_00.pdf, Section 3.3
            # Rule 9:
            #   When the Bulk-IN transfer is completed, if more message data bytes are expected,
            #   the Host may send a new USBTMC command message to read the remainder of the message.
            # Rule 13:
            #   The device may send a Bulk-IN message using multiple transfers, as the data becomes available.
            # These two rules are the reason for the 'while' loop to handle multiple transfers
            while True:
                # USBTMC_1_00.pdf, Section 3.2.1.2
                # Send the REQUEST_DEV_DEP_MSG_IN USBTMC command message
                _ = write(self._msg.request_dev_dep_msg_in(msg_in_size))

                # USBTMC_1_00.pdf, Section 3.3.1.1, Table 9
                # Parse Bulk-IN header, ignore bTagInverse (only check bTag)
                msg_id, tag, transfer_size, attributes = struct.unpack("<BBxxLBxxx", read(12))

                if msg_id != 2 or tag != self._msg.tag:  # Table 2, DEV_DEP_MSG_IN=2  # noqa: PLR2004
                    msg = "Unexpected USBTMC response header"
                    if msg_id != 2:  # noqa: PLR2004
                        msg = f", wrong DEV_DEP_MSG_IN value {msg_id} (expect 2)"
                    if tag != self._msg.tag:
                        msg = f", received bTag [{tag}] != sent bTag [{self._msg.tag}]"
                    raise MSLConnectionError(self, msg)

                message.extend(read(transfer_size))
                if attributes & 1:  # EOM condition satisfied?
                    # USBTMC_1_00.pdf
                    # Section 3.3, Rule 10 states:
                    #   The device may send extra alignment bytes
                    # Section 3.3.1.1, Table 9, TransferSize field states:
                    #   This does not include the number of bytes in this header or alignment bytes.
                    # Therefore, the buffer "may" have alignment bytes to discard
                    self._byte_buffer.clear()
                    if size is not None:
                        # Must read the full Bulk-IN USBTMC response message (so the USB device is happy)
                        # but only return the requested size
                        return bytes(message[:size])
                    return bytes(message)
        except OSError:
            self._abort_transaction(USB.CtrlDirection.IN)
            raise

    def _write(self, message: bytes) -> int:  # pyright: ignore[reportImplicitOverride]
        """Overrides method in USB."""
        if self._capabilities.is_talk_only:
            msg = "The USBTMC device does not accept a write request"
            raise MSLConnectionError(self, msg)

        # USBTMC_1_00.pdf, Section 3.2
        # Rule 5 (below Table 2) states:
        #   The Host must send a complete USBTMC command message with a single transfer
        # Rule 1 (below Table 3) states:
        #   The Host may send this USBTMC command message with multiple transfers, as the data becomes available
        # Rule 5 uses the word "must", rule 1 uses "may". Follow Rule 5, write complete message in a single transfer.
        # Also, libusb manages packet transactions (fragmentation), so we should not do it in Python.
        try:
            return super()._write(self._msg.dev_dep_msg_out(message))
        except OSError:
            self._abort_transaction(USB.CtrlDirection.OUT)
            raise

    def clear_device_buffers(self) -> None:
        """Clear all input and output buffers associated with the USBTMC device."""
        logger.debug("%s clearing USBTMC buffers ...", self)
        self._byte_buffer.clear()

        # USBTMC_1_00.pdf, Section 4.2.1.6
        _ = self._check_ctrl_in_status(
            self.ctrl_transfer(
                request_type=0xA1,  # Dir=IN, Type=Class, Recipient=Interface
                request=5,  # INITIATE_CLEAR, Table 15
                value=0,
                index=self.bulk_in_endpoint.interface_number,  # Bulk-IN/OUT have the same interface number
                data_or_length=0x0001,
            )
        )

        # USBTMC_1_00.pdf, Section 4.2.1.7
        for i in range(1, 100):
            # Table 33 and 34
            status, clear = self.ctrl_transfer(
                request_type=0xA1,  # Dir=IN, Type=Class, Recipient=Interface
                request=6,  # CHECK_CLEAR_STATUS, Table 15
                value=0,
                index=self.bulk_in_endpoint.interface_number,  # Bulk-IN/OUT have the same interface number
                data_or_length=0x0002,
            )

            # Table 35 describes Host behaviour
            if status == 0x02:  # USBTMC_1_00.pdf, Table 16, STATUS_PENDING  # noqa: PLR2004
                logger.debug("%s clearing USBTMC buffers PENDING [iteration=%d]", self, i)
                sleep(0.05)
                if clear:  # Table 34, bmClear.D0 = 1
                    with contextlib.suppress(OSError):
                        self._device.read(self.bulk_in_endpoint.address, self.bulk_in_endpoint.max_packet_size, 1000)
                continue  # check again if STATUS_PENDING

            # Section 4.1.1 and Table 35, send CLEAR_FEATURE then done
            self.clear_halt(self.bulk_out_endpoint)
            logger.debug("%s clearing USBTMC buffers done", self)
            return

    def control_ren(self, mode: RENMode | str | int) -> None:
        """Controls the state of the GPIB Remote Enable (REN) line.

        Optionally the remote/local state of the device is also controlled.

        Args:
            mode: The mode of the REN line and optionally the device remote/local state.
                Can be an enum member name (case insensitive) or value.
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
                    request=160,  # REN_CONTROL, Table 9
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
                    request=162,  # LOCAL_LOCKOUT, Table 9
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
                    request=161,  # GO_TO_LOCAL, Table 9
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
                    request=160,  # REN_CONTROL, Table 9
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
                request=64,  # INDICATOR_PULSE, Table 15
                value=0,
                index=self.bulk_in_endpoint.interface_number,
                data_or_length=0x0001,
            )
        )

    def serial_poll(self) -> int:
        """Read status byte / serial poll (device).

        This method is equivalent to the [ibrsp](https://linux-gpib.sourceforge.io/doc_html/reference-function-ibrsp.html){:target="_blank"}
        function.

        Returns:
            The status byte.
        """
        if not self._capabilities.is_488_interface:
            msg = "The USBTMC device does not accept the serial-poll request"
            raise MSLConnectionError(self, msg)

        self._tag_status += 1
        if self._tag_status > 127:  # noqa: PLR2004
            self._tag_status = 2

        # USBTMC_usb488_subclass_1_00.pdf: Section 4.3.1, Table 11
        _, tag, data = self._check_ctrl_in_status(
            self.ctrl_transfer(
                request_type=0xA1,  # Dir=IN, Type=Class, Recipient=Interface
                request=128,  # READ_STATUS_BYTE, Table 9
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
