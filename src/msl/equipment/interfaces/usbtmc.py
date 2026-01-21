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

from .usb import USB

if TYPE_CHECKING:
    from array import array

    from msl.equipment.schema import Equipment


REGEX = re.compile(
    r"^USB(?P<board>\d*)::(?P<vid>[^:]+)::(?P<pid>[^:]+)::(?P<serial>(?:[^:]*|:(?!:))*)(::(?P<interface>\d+))?(::INSTR)?$",
    flags=re.IGNORECASE,
)


class _Capabilities:
    def __init__(self, response: array[int]) -> None:
        # USBTMC_1_00.pdf: Section 4.2.1.8, Table 37
        # USBTMC_usb488_subclass_1_00.pdf: Section 4.2.2, Table 8
        status, iface, device, iface_488, device_488 = struct.unpack("B3x2B8x2B8x", response)
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
        self.is_full_488: bool = understands_scpi or (is_sr_capable and is_488_interface)  # rule 4

    def __repr__(self) -> str:  # pyright: ignore[reportImplicitOverride]
        return (
            "Capabilities(\n"
            f"  accepts_indicator_pulse={self.accepts_indicator_pulse},\n"
            f"  accepts_remote_local={self.accepts_remote_local},\n"
            f"  accepts_service_request={self.accepts_service_request},\n"
            f"  accepts_term_char={self.accepts_term_char},\n"
            f"  accepts_trigger={self.accepts_trigger},\n"
            f"  is_full_488={self.is_full_488},\n"
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

        # USBTMC_1_00.pdf: Section 4.2.1.8, Table 36
        response = self.ctrl_transfer(
            request_type=0xA1, request=7, value=0, index=self.bulk_in_endpoint.interface_number, data_or_length=0x0018
        )
        assert not isinstance(response, int)  # noqa: S101
        self._capabilities: _Capabilities = _Capabilities(response)
