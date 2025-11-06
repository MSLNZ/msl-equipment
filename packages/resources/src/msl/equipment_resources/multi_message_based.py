"""A resource that supports multiple interfaces for message-based communication."""

from __future__ import annotations

from typing import TYPE_CHECKING

from msl.equipment.interfaces import MessageBased, MSLConnectionError
from msl.equipment.schema import Connection

if TYPE_CHECKING:
    from msl.equipment.schema import Equipment


class MultiMessageBased(MessageBased, append=False):
    """A resource that supports multiple interfaces for message-based communication."""

    def __init__(self, equipment: Equipment) -> None:
        """A resource that supports multiple interfaces for message-based communication.

        A [Connection][msl.equipment.schema.Connection] instance supports the same _properties_ as
        [MessageBased][msl.equipment.interfaces.message_based.MessageBased].

        Args:
            equipment: An [Equipment][] instance.
        """
        self._connected: bool = False
        super().__init__(equipment)

        c = equipment.connection
        assert c is not None  # noqa: S101

        try:
            # Let the address (not the manufacturer/model) decide which interface to use
            self._interface: MessageBased = Connection(c.address, **c.properties).connect()
        except MSLConnectionError as e:
            lines = str(e).splitlines()
            raise MSLConnectionError(self, message="\n".join(lines[1:])) from None

        self._connected = True
        self._set_interface_max_read_size()
        self._set_interface_timeout()

    def _read(self, size: int | None) -> bytes:  # pyright: ignore[reportImplicitOverride]
        """Read from the interface."""
        return self._interface._read(size=size)  # noqa: SLF001

    def _set_interface_max_read_size(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Some connections need to be notified of the max_read_size change.

        The connection subclass must override this method to notify the backend.
        """
        if self._connected:
            self._interface.max_read_size = self.max_read_size
            self._interface._set_interface_max_read_size()  # noqa: SLF001

    def _set_interface_timeout(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Some connections (e.g. serial, socket) need to be notified of the timeout change.

        The connection subclass must override this method to notify the backend.
        """
        if self._connected:
            self._interface.timeout = self.timeout
            self._interface._set_interface_timeout()  # noqa: SLF001

    def _write(self, message: bytes) -> int:  # pyright: ignore[reportImplicitOverride]
        """Write the message."""
        return self._interface._write(message)  # noqa: SLF001

    def disconnect(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Disconnect from the equipment."""
        if self._connected:
            self._interface.disconnect()
            super().disconnect()
            self._connected = False
