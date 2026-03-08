"""Mock a serial.Serial instance by using the 'mock://' URL handler for the tests.

https://pyserial.readthedocs.io/en/stable/url_handlers.html
"""

from __future__ import annotations

from queue import Queue
from typing import TYPE_CHECKING

import serial

if TYPE_CHECKING:
    from typing import Any


class SerialServer(serial.SerialBase):
    """A Mocked Serial port."""

    def __init__(self, port: str | None = None, **kwargs: Any) -> None:  # noqa: ANN401
        """A Mocked Serial port."""
        super().__init__(port, **kwargs)
        self._previous_write: bytes = b""
        self._queue: Queue[bytes] = Queue()
        self._requests_responses: dict[bytes, bytes] = {}

    def _reconfigure_port(self) -> None:
        """Does nothing."""

    @property
    def in_waiting(self) -> int:
        """Always returns 1."""
        return 1

    def add_response(self, content: bytes) -> None:
        """Add a response to the server's queue.

        Args:
            content: The content of the response message.
        """
        self._queue.put(content)

    def add_requests_responses(self, mapping: dict[bytes, bytes]) -> None:
        """Add requests and the corresponding response.

        Args:
            mapping: A request -> response mapping.
        """
        self._requests_responses.update(mapping)

    def clear_response_queue(self) -> None:
        """Clear the server's response queue."""
        with self._queue.mutex:
            self._queue.queue.clear()

    def clear_requests_responses(self) -> None:
        """Clear the request -> response mapping."""
        self._requests_responses.clear()

    def open(self) -> None:
        """Sets the `is_open` attribute to `True`."""
        self.is_open: bool = True

    def read(self, size: int = 1) -> bytes:  # pyright: ignore[reportImplicitOverride]  # noqa: ARG002
        """Mock a read."""
        response = self._requests_responses.get(self._previous_write)
        if response is None:
            response = self._previous_write if self._queue.empty() else self._queue.get()

        self._previous_write = b""
        if response.startswith(b"1/0"):
            _ = 1 / 0
        return response

    def write(self, b: bytes) -> int:  # type: ignore[override]  # pyright: ignore[reportImplicitOverride, reportIncompatibleMethodOverride]
        """Mock a write."""
        self._previous_write = b
        return len(b)


def serial_class_for_url(url: str) -> tuple[str, type[SerialServer]]:
    return url, SerialServer
