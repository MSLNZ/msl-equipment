"""Interfaces for computer control."""
# pyright: reportImportCycles=false

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from msl.equipment.constants import Backend
from msl.equipment.utils import logger

if TYPE_CHECKING:
    from typing import TypeVar

    from msl.equipment.schema import Equipment

    Self = TypeVar("Self", bound="Interface")


__all__: list[str] = [
    "NIDAQ",
    "SDK",
    "Interface",
    "PyVISA",
]


def connect(equipment: Equipment) -> type[Interface]:
    """Factory function to establish a connection to equipment.

    Returns:
        The interface that handles communication.
    """
    connection = equipment.connection
    assert connection is not None  # noqa: S101

    if connection.backend == Backend.PyVISA:
        return PyVISA

    if connection.backend == Backend.NIDAQ:
        return NIDAQ

    for resource in resources:
        if resource.is_match(equipment):
            return resource.cls

    address = connection.address
    if parse_sdk_address(address):
        return SDK

    msg = f"Cannot determine the interface from address {address!r}"
    raise ValueError(msg)


# def find_interface(connection: Connection) -> Connection:
#     """Returns the interface for `address`.

#     Args:
#         address: address: The VISA-type address to use for a connection.
#     """

#     # this check must come before the SERIAL and SOCKET checks
#     if ConnectionPrologix.parse_address(address):
#         return Interface.PROLOGIX

#     if ConnectionSerial.parse_address(address):
#         return Interface.SERIAL

#     if ConnectionSocket.parse_address(address):
#         return Interface.SOCKET

#     if ConnectionTCPIPVXI11.parse_address(address):
#         return Interface.TCPIP_VXI11

#     if ConnectionTCPIPHiSLIP.parse_address(address):
#         return Interface.TCPIP_HISLIP

#     if ConnectionGPIB.parse_address(address):
#         return Interface.GPIB

#     if ConnectionZeroMQ.parse_address(address):
#         return Interface.ZMQ


class Interface:
    """Base class for all interfaces."""

    def __init__(self, equipment: Equipment) -> None:
        """Base class for all interfaces.

        Args:
            equipment: An [Equipment][] instance to use for communication.
        """
        assert equipment.connection is not None  # noqa: S101
        self._equipment: Equipment = equipment

        # __str__ and __repr__ can be called often for logging message, cache values
        self.__str: str = f"{self.__class__.__name__}<{equipment.manufacturer}|{equipment.model}|{equipment.serial}>"
        self.__repr: str = (
            f"{self.__class__.__name__}"
            f"<{equipment.manufacturer}|{equipment.model}|{equipment.serial} at {equipment.connection.address}>"
        )

        logger.debug("Connecting as %s", self)

    def __del__(self) -> None:
        """Calls disconnect()."""
        self.disconnect()

    def __enter__(self: Self) -> Self:  # noqa: PYI019
        """Enter a context manager."""
        return self

    def __exit__(self, *ignore: object) -> None:
        """Exit the context manager."""
        self.disconnect()

    def __init_subclass__(cls, manufacturer: str = "", model: str = "", flags: int = 0) -> None:
        """This method is called whenever the Interface is sub-classed.

        Args:
            manufacturer: The name of the manufacturer. Can be a regular-expression pattern.
            model: The model number of the equipment. Can be a regular-expression pattern.
            flags: The flags to use for the regular-expression patterns.
        """
        if manufacturer or model:
            resources.append(_Resource(cls, manufacturer, model, flags))
            logger.debug("added resource: %s", cls)

    def __repr__(self) -> str:  # pyright: ignore[reportImplicitOverride]
        """Returns the representation."""
        return self.__repr

    def __str__(self) -> str:  # pyright: ignore[reportImplicitOverride]
        """Returns the string representation."""
        return self.__str

    @property
    def equipment(self) -> Equipment:
        """The [Equipment][] associated with the interface."""
        return self._equipment

    def disconnect(self) -> None:
        """Disconnect from the equipment.

        This method should be overridden in the subclass if the subclass must implement
        tasks that need to be performed in order to safely disconnect from the equipment.

        For example

        * to clean up system resources from memory (e.g., if using a manufacturer's SDK)
        * to configure the equipment to be in a state that is safe for people
            working in the lab when the equipment is not in use

        !!! tip
            This method gets called automatically when the [Interface][msl.equipment.interfaces.Interface]
            instance gets garbage collected, which happens when the reference count is 0.
        """


class _Resource:
    def __init__(self, cls: type[Interface], manufacturer: str, model: str, flags: int) -> None:
        """Keep track of custom classes from msl-equipment-resources."""
        self.manufacturer: re.Pattern[str] | None = re.compile(manufacturer, flags=flags) if manufacturer else None
        self.model: re.Pattern[str] | None = re.compile(model, flags=flags) if model else None
        self.cls: type[Interface] = cls

    def is_match(self, equipment: Equipment) -> bool:
        """Checks if the resource is capable of communicating with the equipment."""
        if self.manufacturer and not self.manufacturer.search(equipment.manufacturer):
            return False
        return not (self.model and not self.model.search(equipment.model))


resources: list[_Resource] = []

from .nidaq import NIDAQ  # noqa: E402
from .pyvisa import PyVISA  # noqa: E402
from .sdk import SDK, parse_sdk_address  # noqa: E402
