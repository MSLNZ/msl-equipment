"""Base class for equipment that use message-based communication."""

from __future__ import annotations

import socket
import time
from typing import TYPE_CHECKING, overload

import serial

from msl.equipment.exceptions import MSLConnectionError
from msl.equipment.schema import Interface
from msl.equipment.utils import from_bytes, logger, to_bytes

if TYPE_CHECKING:
    from typing import Literal

    from msl.equipment._types import MessageDataType, MessageFormat, NumpyArray1D, Sequence1D
    from msl.equipment.schema import Equipment


class MessageBased(Interface):
    """Base class for equipment that use message-based communication."""

    def __init__(self, equipment: Equipment) -> None:
        r"""Base class for equipment that use message-based communication.

        Args:
            equipment: An [Equipment][] instance.

        A [Connection][msl.equipment.schema.Connection] instance supports the following
        _properties_ for message-based communication.

        Attributes: Connection Properties:
            encoding (str): Encoding to used for
                [read][msl.equipment.interfaces.message_based.MessageBased.read] and
                [write][msl.equipment.interfaces.message_based.MessageBased.write] operations.
                _Default: `utf-8`_
            max_read_size (int): Maximum number of bytes that can be
                [read][msl.equipment.interfaces.message_based.MessageBased.read].
                _Default: `1048576` (1 MB)_
            read_termination (bytes | str): Termination character(s) to use for
                [read][msl.equipment.interfaces.message_based.MessageBased.read] messages.
                _Default: `\n`_
            rstrip (bool): Whether to remove trailing whitespace from
                [read][msl.equipment.interfaces.message_based.MessageBased.read] messages.
                _Default: `False`_
            termination (bytes | str): Sets both `read_termination` and `write_termination`
                to the same termination character(s).
            timeout (float | None): Timeout, in seconds, for
                [read][msl.equipment.interfaces.message_based.MessageBased.read] and
                [write][msl.equipment.interfaces.message_based.MessageBased.write] operations.
                _Default: `None`_
            write_termination (bytes | str): Termination character(s) to use for
                [write][msl.equipment.interfaces.message_based.MessageBased.write] messages.
                _Default: `\r\n`_
        """
        super().__init__(equipment)
        assert equipment.connection is not None  # noqa: S101

        self._encoding: str = "utf-8"
        self._read_termination: bytes | None = None
        self._write_termination: bytes | None = None
        self._max_read_size: int = 1048576  # 1 << 20 (1 MB)
        self._timeout: float | None = None
        self._rstrip: bool = False

        p = equipment.connection.properties

        self.max_read_size = p.get("max_read_size", self._max_read_size)
        self.timeout = p.get("timeout", self._timeout)
        self.encoding = p.get("encoding", self._encoding)
        self.rstrip = p.get("rstrip", self._rstrip)

        if "termination" in p:
            self.read_termination = p["termination"]
            self.write_termination = p["termination"]
        else:
            self.read_termination = p.get("read_termination", b"\n")
            self.write_termination = p.get("write_termination", b"\r\n")

    def _read(self, size: int | None) -> bytes:  # pyright: ignore[reportUnusedParameter]
        """The subclass must override this method."""
        raise NotImplementedError

    def _set_interface_max_read_size(self) -> None:
        """Some connections need to be notified of the max_read_size change.

        The connection subclass must override this method to notify the backend.
        """

    def _set_interface_timeout(self) -> None:
        """Some connections (e.g. serial, socket) need to be notified of the timeout change.

        The connection subclass must override this method to notify the backend.
        """

    def _write(self, message: bytes) -> int:  # pyright: ignore[reportUnusedParameter]
        """The subclass must override this method."""
        raise NotImplementedError

    @property
    def encoding(self) -> str:
        """The encoding that is used for [read][msl.equipment.interfaces.message_based.MessageBased.read]
        and [write][msl.equipment.interfaces.message_based.MessageBased.write] operations.
        """  # noqa: D205
        return self._encoding

    @encoding.setter
    def encoding(self, encoding: str) -> None:
        """Set the encoding to use for `read` and `write` operations."""
        if self._read_termination is None and self._write_termination is None:
            _ = "test encoding".encode(encoding).decode(encoding)
        self._encoding = encoding
        if self._read_termination is not None:
            self.read_termination = self._read_termination.decode(encoding)
        if self._write_termination is not None:
            self.write_termination = self._write_termination.decode(encoding)

    @property
    def max_read_size(self) -> int:
        """The maximum number of bytes that can be [read][msl.equipment.interfaces.message_based.MessageBased.read]."""
        return self._max_read_size

    @max_read_size.setter
    def max_read_size(self, size: int) -> None:
        """The maximum number of bytes that can be `read`."""
        max_size = int(size)
        if max_size < 1:
            msg = f"The maximum number of bytes to read must be >= 1, got {size}"
            raise ValueError(msg)
        self._max_read_size = max_size
        self._set_interface_max_read_size()

    @overload
    def query(  # pyright: ignore[reportOverlappingOverload]  # pragma: no cover
        self,
        message: bytes | str,
        *,
        delay: float = 0.0,
        decode: Literal[True] = True,
        dtype: None = None,
        fmt: MessageFormat | None = ...,
        size: int | None = ...,
    ) -> str: ...

    @overload
    def query(  # pragma: no cover
        self,
        message: bytes | str,
        *,
        delay: float = 0.0,
        decode: Literal[False] = False,
        dtype: None = None,
        fmt: MessageFormat | None = ...,
        size: int | None = ...,
    ) -> bytes: ...

    @overload
    def query(  # pragma: no cover
        self,
        message: bytes | str,
        *,
        delay: float = 0.0,
        decode: bool = ...,
        dtype: MessageDataType = ...,
        fmt: MessageFormat | None = ...,
        size: int | None = ...,
    ) -> NumpyArray1D: ...

    def query(  # noqa: PLR0913
        self,
        message: bytes | str,
        *,
        delay: float = 0.0,
        decode: bool = True,
        dtype: MessageDataType | None = None,
        fmt: MessageFormat | None = None,
        size: int | None = None,
    ) -> bytes | str | NumpyArray1D:
        """Convenience method for performing a [write][msl.equipment.interfaces.message_based.MessageBased.write]
        followed by a [read][msl.equipment.interfaces.message_based.MessageBased.read].

        Args:
            message: The message to write to the equipment.
            delay: Time delay, in seconds, to wait between the _write_ and _read_ operations.
            decode: Whether to decode the returned message (i.e., convert the message to a [str][])
                or keep the message as [bytes][]. Ignored if `dtype` is not `None`.
            dtype: The data type of the elements in the returned message. Can be any object
                that numpy [dtype][numpy.dtype] supports. See [from_bytes][msl.equipment.utils.from_bytes]
                for more details. For messages that are of scalar type (i.e., a single number)
                it is more efficient to not specify `dtype` but to pass the returned message to the
                [int][] or [float][] class to convert the message to the appropriate numeric type.
            fmt: The format that the returned message data is in. Ignored if `dtype` is `None`.
                 See [from_bytes][msl.equipment.utils.from_bytes] for more details.
            size: The number of bytes to read. Ignored if the value is `None`.

        Returns:
            The message from the equipment. If `dtype` is specified, then the message is
                returned as a numpy [ndarray][numpy.ndarray], if `decode` is `True` then the message
                is returned as a [str][], otherwise the message is returned as [bytes][].
        """  # noqa: D205
        _ = self.write(message)
        if delay > 0:
            time.sleep(delay)
        if dtype:
            return self.read(dtype=dtype, fmt=fmt, size=size)
        return self.read(decode=decode, size=size)

    @overload
    def read(  # pyright: ignore[reportOverlappingOverload]  # pragma: no cover
        self,
        *,
        decode: Literal[True] = True,
        dtype: None = None,
        fmt: MessageFormat | None = ...,
        size: int | None = ...,
    ) -> str: ...

    @overload
    def read(  # pragma: no cover
        self,
        *,
        decode: Literal[False] = False,
        dtype: None = None,
        fmt: MessageFormat | None = ...,
        size: int | None = ...,
    ) -> bytes: ...

    @overload
    def read(  # pragma: no cover
        self,
        *,
        decode: bool = ...,
        dtype: MessageDataType = ...,
        fmt: MessageFormat | None = ...,
        size: int | None = ...,
    ) -> NumpyArray1D: ...

    def read(
        self,
        *,
        decode: bool = True,
        dtype: MessageDataType | None = None,
        fmt: MessageFormat | None = None,
        size: int | None = None,
    ) -> bytes | str | NumpyArray1D:
        """Read a message from the equipment.

        This method will block until one of the following conditions is fulfilled:

        1. `size` bytes have been received &mdash; only if `size` is not `None`.
        2. the [read_termination][msl.equipment.interfaces.message_based.MessageBased.read_termination]
           byte(s) is(are) received &mdash; only if
           [read_termination][msl.equipment.interfaces.message_based.MessageBased.read_termination]
           is not `None`.
        3. a timeout occurs &mdash; only if [timeout][msl.equipment.interfaces.message_based.MessageBased.timeout]
           is not `None`. If a timeout occurs, an
           [MSLTimeoutError][msl.equipment.interfaces.message_based.MSLTimeoutError] is raised.
        4. [max_read_size][msl.equipment.interfaces.message_based.MessageBased.max_read_size]
           bytes have been received. If the maximum number of bytes have been read, an
           [MSLConnectionError][msl.equipment.exceptions.MSLConnectionError] is raised.

        !!! tip
            You may also want to set the [rstrip][msl.equipment.interfaces.message_based.MessageBased.rstrip]
            value for the class instance.

        Args:
            decode: Whether to decode the message (i.e., convert the message to a [str][])
                or keep the message as [bytes][]. Ignored if `dtype` is not `None`.
            dtype: The data type of the elements in the message. Can be any object
                that numpy [dtype][numpy.dtype] supports. See [from_bytes][msl.equipment.utils.from_bytes]
                for more details. For messages that are of scalar type (i.e., a single number)
                it is more efficient to not specify `dtype` but to pass the returned message to the
                [int][] or [float][] class to convert the message to the appropriate numeric type.
            fmt: The format that the message data is in. Ignored if `dtype` is `None`.
                 See [from_bytes][msl.equipment.utils.from_bytes] for more details.
            size: The number of bytes to read. Ignored if the value is `None`.

        Returns:
            The message from the equipment. If `dtype` is specified, then the message is returned
                as a numpy [ndarray][numpy.ndarray], if `decode` is `True` then the message
                is returned as a [str][], otherwise the message is returned as [bytes][].
        """
        if size is not None and size > self._max_read_size:
            msg = f"max_read_size is {self._max_read_size} bytes, requesting {size} bytes"
            raise MSLConnectionError(self, msg)

        try:
            message = self._read(size)
        except (serial.SerialTimeoutException, socket.timeout, TimeoutError):
            raise MSLTimeoutError(self) from None
        except Exception as e:  # noqa: BLE001
            msg = f"{e.__class__.__name__}: {e}"
            raise MSLConnectionError(self, msg) from None

        if size is None:
            if dtype:
                logger.debug("%s.read(dtype=%r, fmt=%r) -> %r", self, dtype, fmt, message)
            else:
                logger.debug("%s.read() -> %r", self, message)
        else:
            if len(message) != size:
                msg = f"received {len(message)} bytes, requested {size} bytes"
                raise MSLConnectionError(self, msg)
            logger.debug("%s.read(size=%s) -> %r", self, size, message)

        if self._rstrip:
            message = message.rstrip()

        if dtype:
            return from_bytes(message, fmt=fmt, dtype=dtype)

        if decode:
            return message.decode(encoding=self._encoding)

        return message

    @property
    def read_termination(self) -> bytes | None:
        """The termination character sequence that is used for a
        [read][msl.equipment.interfaces.message_based.MessageBased.read] operation.

        Reading stops when the equipment stops sending data or the `read_termination`
        character sequence is detected. If you set the `read_termination` to be equal
        to a variable of type [str][], it will be encoded as [bytes][].
        """  # noqa: D205
        return self._read_termination

    @read_termination.setter
    def read_termination(self, termination: str | bytes | None) -> None:  # pyright: ignore[reportPropertyTypeMismatch]
        if termination is None or isinstance(termination, bytes):
            self._read_termination = termination
        else:
            self._read_termination = termination.encode(self._encoding)

    @property
    def rstrip(self) -> bool:
        """Whether to remove trailing whitespace from [read][msl.equipment.interfaces.message_based.MessageBased.read] messages."""  # noqa: E501
        return self._rstrip

    @rstrip.setter
    def rstrip(self, value: bool) -> None:
        self._rstrip = bool(value)

    @property
    def timeout(self) -> float | None:
        """The timeout, in seconds, for [read][msl.equipment.interfaces.message_based.MessageBased.read]
        and [write][msl.equipment.interfaces.message_based.MessageBased.write] operations.

        A value &lt;0 will set the timeout to be `None` (blocking mode).
        """  # noqa: D205
        return self._timeout

    @timeout.setter
    def timeout(self, value: float | None) -> None:
        if value is None or value < 0:
            self._timeout = None
        else:
            self._timeout = float(value)
        self._set_interface_timeout()

    def write(
        self,
        message: bytes | str,
        *,
        data: Sequence1D | None = None,
        dtype: MessageDataType = "<f",
        fmt: MessageFormat | None = "ieee",
    ) -> int:
        """Write a message to the equipment.

        Args:
            message: The message to write to the equipment.
            data: The data to append to `message`. See [to_bytes][msl.equipment.utils.to_bytes]
                for more details.
            dtype: The data type to use to convert each element in `data` to bytes. Ignored
                if `data` is `None`. See [to_bytes][msl.equipment.utils.to_bytes] for more details.
            fmt: The format to use to convert `data` to bytes. Ignored if `data` is `None`.
                See [to_bytes][msl.equipment.utils.to_bytes] for more details.

        Returns:
            The number of bytes written.
        """
        if not isinstance(message, bytes):
            message = message.encode(encoding=self._encoding)

        if data is not None:
            message += to_bytes(data, fmt=fmt, dtype=dtype)

        if self._write_termination and not message.endswith(self._write_termination):
            message += self._write_termination

        logger.debug("%s.write(%r)", self, message)

        try:
            return self._write(message)
        except (serial.SerialTimeoutException, socket.timeout, TimeoutError):
            raise MSLTimeoutError(self) from None
        except Exception as e:  # noqa: BLE001
            raise MSLConnectionError(self, str(e)) from None

    @property
    def write_termination(self) -> bytes | None:
        """The termination character sequence that is appended to
        [write][msl.equipment.interfaces.message_based.MessageBased.write] messages.

        If you set the `write_termination` to be equal to a variable of type
        [str][], it will be encoded as [bytes][].
        """  # noqa: D205
        return self._write_termination

    @write_termination.setter
    def write_termination(self, termination: str | bytes | None) -> None:  # pyright: ignore[reportPropertyTypeMismatch]
        if termination is None or isinstance(termination, bytes):
            self._write_termination = termination
        else:
            self._write_termination = termination.encode(self._encoding)


class MSLTimeoutError(TimeoutError):
    """A timeout exception for I/O operations."""

    def __init__(self, interface: MessageBased, message: str = "") -> None:
        """A timeout exception for I/O operations.

        Args:
            interface: A message-based interface subclass.
            message: An optional message to append to the generic timeout error message.
        """
        msg = f"Timeout occurred after {interface.timeout} second(s). {message}"
        logger.error("%r %s", interface, msg)
        super().__init__(f"{interface!r}\n{msg}")
