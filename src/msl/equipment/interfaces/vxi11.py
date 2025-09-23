"""Implementation of the [VXI-11] protocol.

[VXI-11] is a client-service model to send messages through a network.
The messages are formatted using the Remote Procedure Call protocol [RFC-1057]
and are encoded/decoded using the eXternal Data Representation standard [RFC-1014].

# References

* [VXI-11] &mdash; *TCP/IP Instrument Protocol Specification (Revision 1.0)*, **VXIbus Consortium**, July 1995.
* [RFC-1057] &mdash; *RPC: Remote Procedure Call Protocol Specification (Version 2)*, **Sun Microsystems**, June 1988.
* [RFC-1014] &mdash; *XDR: External Data Representation Standard*, **Sun Microsystems**, June 1987.

[VXI-11]: http://www.vxibus.org/specifications.html
[RFC-1057]: https://www.rfc-editor.org/rfc/rfc1057
[RFC-1014]: https://www.rfc-editor.org/rfc/rfc1014
"""

from __future__ import annotations

import contextlib
import random
import re
import select
import socket
import threading
import time
from dataclasses import dataclass
from enum import IntEnum
from struct import Struct, pack, unpack
from typing import TYPE_CHECKING, overload

from msl.equipment.utils import LXIDevice, ipv4_addresses, logger, parse_lxi_webserver

from .message_based import MessageBased, MSLConnectionError, MSLTimeoutError

if TYPE_CHECKING:
    from msl.equipment.schema import Equipment


REGEX = re.compile(
    r"TCPIP(?P<board>\d*)::(?P<host>[^\s:]+)(::(?!hislip)(?P<name>([^\s:]+\d+(\[.+])?)))?(::INSTR)?$",
    flags=re.IGNORECASE,
)

ONE_DAY = 86400.0  # use 1 day as equivalent to waiting forever for a lock

# VXI-11 program numbers
DEVICE_ASYNC = 0x0607B0
DEVICE_CORE = 0x0607AF
DEVICE_INTR = 0x0607B1

# VXI-11 version numbers
DEVICE_ASYNC_VERSION = 1
DEVICE_CORE_VERSION = 1
DEVICE_INTR_VERSION = 1

# VXI-11 procedure numbers
DEVICE_ABORT = 1
CREATE_LINK = 10
DEVICE_WRITE = 11
DEVICE_READ = 12
DEVICE_READSTB = 13
DEVICE_TRIGGER = 14
DEVICE_CLEAR = 15
DEVICE_REMOTE = 16
DEVICE_LOCAL = 17
DEVICE_LOCK = 18
DEVICE_UNLOCK = 19
DEVICE_ENABLE_SRQ = 20
DEVICE_DOCMD = 22
DESTROY_LINK = 23
CREATE_INTR_CHAN = 25
DESTROY_INTR_CHAN = 26
DEVICE_INTR_SRQ = 30

# VXI-11 constants
RX_REQCNT = 1
RX_CHR = 2
RX_END = 4


# VXI-11 Operation Flags, see Section B.5.3 in the document
class OperationFlag(IntEnum):
    """**VXI-11:** Additional information concerning how a request is carried out."""

    NULL = 0x00
    WAITLOCK = 0x01
    END = 0x08
    TERMCHRSET = 0x80


# VXI-11 error codes, see Table B.2 in the document
VXI_ERROR_CODES = {
    0: "No error",
    1: "Syntax error",
    3: "Device not accessible",
    4: "Invalid link identifier",
    5: "Parameter error",
    6: "Channel not established",
    8: "Operation not supported",
    9: "Out of resources",
    11: "Device locked by another link",
    12: "No lock held by this link",
    15: "I/O timeout",
    17: "I/O error",
    21: "Invalid address",
    23: "Abort",
    29: "Channel already established",
}

# RPC program numbers
PMAP_PROG = 100000

# RPC version numbers
RPC_VERS = 2
PMAP_VERS = 2

# RPC procedure numbers
PMAPPROC_NULL = 0
PMAPPROC_SET = 1
PMAPPROC_UNSET = 2
PMAPPROC_GETPORT = 3
PMAPPROC_DUMP = 4
PMAPPROC_CALLIT = 5

# RPC constants
PMAP_PORT = 111


# RPC enums
class AcceptStatus(IntEnum):
    """**RPC:** Message accepted status."""

    SUCCESS = 0
    PROG_UNAVAIL = 1
    PROG_MISMATCH = 2
    PROC_UNAVAIL = 3
    GARBAGE_ARGS = 4


class AuthStatus(IntEnum):
    """**RPC:** Authorization status."""

    AUTH_BADCRED = 1
    AUTH_REJECTEDCRED = 2
    AUTH_BADVERF = 3
    AUTH_REJECTEDVERF = 4
    AUTH_TOOWEAK = 5


class MessageType(IntEnum):
    """**RPC:** The message type."""

    CALL = 0
    REPLY = 1


class RejectStatus(IntEnum):
    """**RPC:** Message rejected status."""

    RPC_MISMATCH = 0
    AUTH_ERROR = 1


class ReplyStatus(IntEnum):
    """**RPC:** Message reply status."""

    MSG_ACCEPTED = 0
    MSG_DENIED = 1


class RPCClient:
    """Remote Procedure Call implementation for a client."""

    def __init__(self, host: str) -> None:
        """Remote Procedure Call implementation for a client.

        Args:
            host: The hostname or IP address of the remote device.
        """
        super().__init__()
        self._host: str = host
        self._sock: socket.socket | None = None
        self._xid: int = 0  # transaction identifier
        self._buffer: bytearray = bytearray()
        self._chunk_size: int = 4096

    def append(self, data: bytes | memoryview) -> None:
        """Append data to the body of the current RPC message.

        Args:
            data: The data to append.
        """
        self._buffer.extend(data)

    def append_opaque(self, text: bytes | memoryview | str) -> None:
        """Append a variable-length string to the body of the current RPC message.

        Args:
            text: The data to append.
        """
        # mimic the builtin xdrlib.Packer class
        # don't use xdrlib since it became deprecated in Python 3.11
        if not text:
            return

        if isinstance(text, memoryview):
            encoded = text
        elif isinstance(text, bytes):
            encoded = memoryview(text)
        else:
            encoded = memoryview(text.encode("ascii"))  # must be an ASCII message

        n = len(encoded)
        self.append(pack(">L", n))

        data = encoded[:n]
        self.append(data)

        n = ((n + 3) // 4) * 4
        self.append((n - len(data)) * b"\0")

    def check_reply(self, message: memoryview) -> memoryview | None:
        """Checks the message for errors and returns the procedure-specific data.

        Args:
            message: The reply from an RPC message.

        Returns:
            The reply or `None` if the transaction id does not match the
                value that was used in the corresponding `write` call.
        """
        xid, m_type = unpack(">2I", message[:8])
        if xid != self._xid:
            # data in read buffer is due to an interrupt?
            return None

        if m_type != MessageType.REPLY:
            msg = f"RPC message type is not {MessageType.REPLY!r}, got {m_type}"
            raise RuntimeError(msg)

        (status,) = unpack(">I", message[8:12])
        if status == ReplyStatus.MSG_ACCEPTED:
            verify, status = unpack(">QI", message[12:24])
            assert verify == 0  # VXI-11 does not use authentication  # noqa: S101
            if status == AcceptStatus.SUCCESS:
                return message[24:]  # procedure-specific data

            if status == AcceptStatus.PROG_MISMATCH:
                low, high = unpack(">2I", message[24:32])
                msg = f"RPC call failed: {AcceptStatus.PROG_MISMATCH!r}: low={low}, high={high}"
                raise RuntimeError(msg)

            # cases include PROG_UNAVAIL, PROC_UNAVAIL, and GARBAGE_ARGS
            msg = f"RPC call failed: {AcceptStatus(status)!r}"
            raise RuntimeError(msg)

        if status == ReplyStatus.MSG_DENIED:
            (status,) = unpack(">I", message[12:16])
            if status == RejectStatus.RPC_MISMATCH:
                low, high = unpack(">2I", message[16:24])
                msg = f"RPC call failed: {RejectStatus(status)!r}: low={low}, high={high}"
                raise RuntimeError(msg)

            if status == RejectStatus.AUTH_ERROR:
                msg = f"RPC authentication failed: {AuthStatus(status)!r}"
                raise RuntimeError(msg)

            msg = "RPC MSG_DENIED reply status is not RPC_MISMATCH nor AUTH_ERROR"
            raise RuntimeError(msg)

        msg = "RPC reply is not MSG_ACCEPTED nor MSG_DENIED"
        raise RuntimeError(msg)

    @property
    def chunk_size(self) -> int:
        """Returns the maximum number of bytes to receive at a time from the socket."""
        return self._chunk_size

    @chunk_size.setter
    def chunk_size(self, size: int) -> None:
        self._chunk_size = int(size)

    def close(self) -> None:
        """Close the RPC socket, if one is open."""
        if self._sock is not None:
            self._sock.close()
            self._sock = None

    def connect(self, port: int, timeout: float | None = 10) -> None:
        """Connect to a specific port on the device.

        Args:
            port: The port number to connect to.
            timeout: The maximum number of seconds to wait for the connection to be established.
        """
        self.close()
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.settimeout(timeout)
        self._sock.connect((self._host, port))

    def get_buffer(self) -> bytearray:
        """Get the data in the buffer.

        Returns:
            The data in the current RPC message.
        """
        return self._buffer

    def get_port(self, program: int, version: int, protocol: int, timeout: float | None = 10) -> int:
        """Call the Port Mapper procedure to determine which port to use for a program.

        This method will automatically open and close the socket connection.

        Args:
            program: The program number to get the port number of.
            version: The version number of `prog`.
            protocol: The socket protocol family type to use when sending requests to `prog`
                (`IPPROTO_TCP` or `IPPROTO_UDP`).
            timeout: The maximum number of seconds to wait to get the port value.

        Returns:
            The port number that corresponds to `prog`.
        """
        port: int
        try:
            self.connect(PMAP_PORT, timeout=timeout)
            self.init(PMAP_PROG, PMAP_VERS, PMAPPROC_GETPORT)
            self.append(pack(">4I", program, version, protocol, 0))
            self.write()
            (port,) = unpack(">L", self.read())
        finally:
            self.close()

        if port == 0:
            msg = "Could not determine the port from the Port Mapper procedure"
            raise RuntimeError(msg)
        return port

    def init(self, prog: int, vers: int, proc: int) -> None:
        """Construct a new RPC message.

        Args:
            prog: The program number.
            vers: The version number of program.
            proc: The procedure number within the program to be called.
        """
        # increment and wrap to 0 on uint32 overflow
        xid = (self._xid + 1) & 0xFFFFFFFF

        # The VXI-11 document, Section B.4.5 (Security Control), states
        # that authentication is not used. That is where the two 0's come from
        self._buffer = bytearray(pack(">6I2Q", xid, MessageType.CALL, RPC_VERS, prog, vers, proc, 0, 0))
        self._xid = xid

    def interrupt_handler(self) -> None:
        """Override this method to be notified of a service interrupt.

        This method gets called if an interrupt is received during a `read`.
        It does not continuously poll the device.
        """

    def read(self) -> memoryview:
        """Read an RPC message, check for errors, and return the procedure-specific data.

        Returns:
            The procedure-specific data.
        """
        if self._sock is None:
            msg = "The socket is disconnected"
            raise RuntimeError(msg)

        # RFC-1057, Section 10 describes that RPC messages are sent in fragments
        last_fragment = False
        message = bytearray()
        recv = self._sock.recv
        recv_into = self._sock.recv_into
        chunk_size = self._chunk_size
        while not last_fragment:
            header = recv(4)
            if len(header) < 4:  # noqa: PLR2004
                msg = "The RPC reply header is < 4 bytes"
                raise EOFError(msg)
            (h,) = unpack(">I", header)
            last_fragment = (h & 0x80000000) != 0
            fragment_size = h & 0x7FFFFFFF
            fragment = bytearray(fragment_size)  # preallocate
            view = memoryview(fragment)  # avoids unnecessarily copying of slices
            size = 0
            while size < fragment_size:
                request_size = min(chunk_size, fragment_size - size)
                received_size = recv_into(view, request_size)
                view = view[received_size:]
                size += received_size
            message.extend(fragment)
        reply = self.check_reply(memoryview(message))
        if reply is None:
            # Unexpected transaction id (xid), most likely from reading an interrupt.
            # Recursively read from the device until the corrected xid is received.
            self.interrupt_handler()
            return self.read()
        return reply

    def set_timeout(self, timeout: float | None) -> None:
        """Set the socket timeout value.

        Args:
            timeout: The timeout, in seconds, to use for the socket.
        """
        if self._sock is None:
            msg = "The socket is disconnected"
            raise RuntimeError(msg)
        self._sock.settimeout(timeout)

    @property
    def socket(self) -> socket.socket | None:
        """Returns the reference to the socket."""
        return self._sock

    @overload
    @staticmethod
    def unpack_opaque(data: bytes) -> bytes: ...  # pragma: no cover

    @overload
    @staticmethod
    def unpack_opaque(data: bytearray) -> bytearray: ...  # pragma: no cover

    @overload
    @staticmethod
    def unpack_opaque(data: memoryview) -> memoryview: ...  # pragma: no cover

    @staticmethod
    def unpack_opaque(data: bytes | bytearray | memoryview) -> bytes | bytearray | memoryview:
        """Unpack and return a variable-length string.

        Args:
            data: The data to unpack.

        Returns:
            The unpacked data.
        """
        # mimic the builtin xdrlib.Unpacker class
        # don't use xdrlib since it became deprecated in Python 3.11
        if not data:
            return b""
        (n,) = unpack(">L", data[:4])
        return data[4 : 4 + n]

    def write(self) -> None:
        """Write the RPC message that is in the buffer."""
        # RFC-1057, Section 10 describes that RPC messages are sent in fragments
        if self._sock is None:
            msg = "The socket is disconnected"
            raise RuntimeError(msg)

        fragment_size = 0x7FFFFFFF  # (2**31) - 1
        remaining = len(self._buffer)
        view = memoryview(self._buffer)
        sendall = self._sock.sendall
        while remaining > 0:
            if remaining <= fragment_size:  # then it is the last fragment
                fragment_size = remaining | 0x80000000
            data = bytearray(pack(">I", fragment_size))
            data.extend(view[:fragment_size])
            sendall(data)
            view = view[fragment_size:]
            remaining -= fragment_size


class VXIClient(RPCClient):
    """Base class for a VXI-11 program."""

    def __init__(self, host: str) -> None:
        """Base class for a VXI-11 program.

        Args:
            host: The hostname or IP address of the remote device.
        """
        super().__init__(host)

    def read_reply(self) -> memoryview:
        """Check the RPC message for an error and return the remaining data.

        Returns:
            The reply data.
        """
        reply = self.read()
        (error,) = unpack(">L", reply[:4])
        if error == 0:
            return reply[4:]
        text = VXI_ERROR_CODES.get(error, "Undefined error")
        msg = f"{text} [error={error}]"
        raise RuntimeError(msg)


class AsyncClient(VXIClient):
    """Communicate with the `Device Async` program on the remote device."""

    def __init__(self, host: str) -> None:
        """Communicate with the `Device Async` program on the remote device.

        Args:
            host: The hostname or IP address of the remote device.
        """
        super().__init__(host)

    def device_abort(self, lid: int) -> None:
        """Stops an in-progress call.

        Args:
            lid: Link id from `CoreClient.create_link`.
        """
        self.init(DEVICE_ASYNC, DEVICE_ASYNC_VERSION, DEVICE_ABORT)
        self.append(pack(">l", lid))
        self.write()
        _ = self.read_reply()


class CoreClient(VXIClient):
    """Communicate with the `Device Core` program on the remote device."""

    def __init__(self, host: str) -> None:
        """Communicate with the `Device Core` program on the remote device.

        Args:
            host: The hostname or IP address of the remote device.
        """
        super().__init__(host)

    def create_intr_chan(
        self, *, host_addr: int, host_port: int, prog_num: int, prog_vers: int, prog_family: int
    ) -> None:
        """Inform the network instrument server to establish an interrupt channel.

        Args:
            host_addr: Address of the host servicing the interrupt.
            host_port: Valid port number on the client.
            prog_num: Program number.
            prog_vers: Program version number.
            prog_family: The underlying socket protocol family type (`IPPROTO_TCP` or `IPPROTO_UDP`).
        """
        self.init(DEVICE_CORE, DEVICE_CORE_VERSION, CREATE_INTR_CHAN)
        self.append(pack(">5L", host_addr, host_port, prog_num, prog_vers, prog_family))
        self.write()
        _ = self.read_reply()

    def create_link(self, *, device: bytes | str, lock_device: bool, lock_timeout: int) -> tuple[int, int, int]:
        """Create a link.

        Args:
            device: Name of the device to link with.
            lock_device: Whether to attempt to lock the device.
            lock_timeout: Time, in milliseconds, to wait on a lock.

        Returns:
            The link ID, the port number of the `Device Async` program (see `AsyncClient`),
                and the maximum data size the device will accept on a `device_write`.
        """
        self.init(DEVICE_CORE, DEVICE_CORE_VERSION, CREATE_LINK)
        self.append(pack(">3l", random.getrandbits(31), lock_device, lock_timeout))
        self.append_opaque(device)
        self.write()
        lid, abort_port, max_recv_size = unpack(">3L", self.read_reply())
        return lid, abort_port, max_recv_size

    def destroy_intr_chan(self) -> None:
        """Inform the network instrument server to close its interrupt channel."""
        self.init(DEVICE_CORE, DEVICE_CORE_VERSION, DESTROY_INTR_CHAN)
        self.write()
        _ = self.read_reply()

    def destroy_link(self, lid: int) -> None:
        """Destroy the link.

        Args:
            lid: Link id from `create_link`.
        """
        self.init(DEVICE_CORE, DEVICE_CORE_VERSION, DESTROY_LINK)
        self.append(pack(">l", lid))
        self.write()
        _ = self.read_reply()

    def device_clear(self, *, lid: int, flags: int | OperationFlag, lock_timeout: int, io_timeout: int) -> None:
        """Send the `clear` command to the device.

        Args:
            lid: Link id from `create_link`.
            flags: Operation flags to use.
            lock_timeout: Time, in milliseconds, to wait on a lock.
            io_timeout: Time, in milliseconds, to wait for I/O to complete.
        """
        self.init(DEVICE_CORE, DEVICE_CORE_VERSION, DEVICE_CLEAR)
        self.append(pack(">4l", lid, flags, lock_timeout, io_timeout))
        self.write()
        _ = self.read_reply()

    def device_docmd(  # noqa: PLR0913
        self,
        *,
        lid: int,
        flags: int | OperationFlag,
        io_timeout: int,
        lock_timeout: int,
        cmd: int,
        network_order: bool,
        size: int,
        data: bytes | str,
    ) -> bytes:
        """Allows for a variety of operations to be executed.

        Args:
            lid: Link id from `create_link`.
            flags: Operation flags to use.
            io_timeout: Time, in milliseconds, to wait for I/O to complete.
            lock_timeout: Time, in milliseconds, to wait on a lock.
            cmd: Which command to execute.
            network_order: Whether to use the client's byte order.
            size: Size of individual data elements.
            data: Data input parameters.

        Returns:
            The results defined by `cmd`.
        """
        self.init(DEVICE_CORE, DEVICE_CORE_VERSION, DEVICE_DOCMD)
        self.append(pack(">7l", lid, flags, io_timeout, lock_timeout, cmd, network_order, size))
        self.append_opaque(data)
        self.write()
        return bytes(self.unpack_opaque(self.read_reply()))

    def device_enable_srq(self, *, lid: int, state: bool, handle: bytes) -> None:
        """Enable or disable the sending of `device_intr_srq` RPCs by the network instrument server.

        Args:
            lid: Link id from `create_link`.
            state: Whether to enable or disable interrupts.
            handle: Host specific data (maximum length is 40 characters).
        """
        if len(handle) > 40:  # noqa: PLR2004
            msg = "The handle must be <= 40 characters"
            raise ValueError(msg)
        self.init(DEVICE_CORE, DEVICE_CORE_VERSION, DEVICE_ENABLE_SRQ)
        self.append(pack(">2l", lid, state))
        self.append_opaque(handle)
        self.write()
        _ = self.read_reply()

    def device_local(self, *, lid: int, flags: int | OperationFlag, lock_timeout: int, io_timeout: int) -> None:
        """Place the device in a local state wherein all programmable local controls are enabled.

        Args:
            lid: Link id from `create_link`.
            flags: Operation flags to use.
            lock_timeout: Time, in milliseconds, to wait on a lock.
            io_timeout: Time, in milliseconds, to wait for I/O to complete.
        """
        self.init(DEVICE_CORE, DEVICE_CORE_VERSION, DEVICE_LOCAL)
        self.append(pack(">4l", lid, flags, lock_timeout, io_timeout))
        self.write()
        _ = self.read_reply()

    def device_lock(self, *, lid: int, flags: int | OperationFlag, lock_timeout: int) -> None:
        """Acquire a device's lock.

        Args:
            lid: Link id from `create_link`.
            flags: Operation flags to use.
            lock_timeout: Time, in milliseconds, to wait on a lock.
        """
        self.init(DEVICE_CORE, DEVICE_CORE_VERSION, DEVICE_LOCK)
        self.append(pack(">3l", lid, flags, lock_timeout))
        self.write()
        _ = self.read_reply()

    def device_read(  # noqa: PLR0913
        self,
        *,
        lid: int,
        request_size: int,
        io_timeout: int,
        lock_timeout: int,
        flags: int | OperationFlag,
        term_char: int,
    ) -> tuple[int, memoryview]:
        """Read data from the device.

        Args:
            lid: Link id from `create_link`.
            request_size: The number of bytes requested.
            io_timeout: Time, in milliseconds, to wait for I/O to complete.
            lock_timeout: Time, in milliseconds, to wait on a lock.
            flags: Operation flags to use.
            term_char: The termination character. Valid only if `flags` is `OperationFlag.TERMCHRSET`.

        Returns:
            The reason(s) the read completed and a view of the data (the RPC header is removed).
        """
        reason: int
        self.init(DEVICE_CORE, DEVICE_CORE_VERSION, DEVICE_READ)
        self.append(pack(">6l", lid, request_size, io_timeout, lock_timeout, flags, term_char))
        self.write()
        reply = self.read_reply()
        (reason,) = unpack(">L", reply[:4])
        return reason, self.unpack_opaque(reply[4:])

    def device_readstb(self, *, lid: int, flags: int | OperationFlag, lock_timeout: int, io_timeout: int) -> int:
        """Read the status byte from the device.

        Args:
            lid: Link id from `create_link`.
            flags: Operation flags to use.
            lock_timeout: Time, in milliseconds, to wait on a lock.
            io_timeout: Time, in milliseconds, to wait for I/O to complete.

        Returns:
            The status byte.
        """
        stb: int
        self.init(DEVICE_CORE, DEVICE_CORE_VERSION, DEVICE_READSTB)
        self.append(pack(">4l", lid, flags, lock_timeout, io_timeout))
        self.write()
        (stb,) = unpack(">L", self.read_reply())
        return stb

    def device_remote(self, *, lid: int, flags: int | OperationFlag, lock_timeout: int, io_timeout: int) -> None:
        """Place the device in a remote state wherein all programmable local controls are disabled.

        Args:
            lid: Link id from `create_link`.
            flags: Operation flags to use.
            lock_timeout: Time, in milliseconds, to wait on a lock.
            io_timeout: Time, in milliseconds, to wait for I/O to complete.
        """
        self.init(DEVICE_CORE, DEVICE_CORE_VERSION, DEVICE_REMOTE)
        self.append(pack(">4l", lid, flags, lock_timeout, io_timeout))
        self.write()
        _ = self.read_reply()

    def device_trigger(self, *, lid: int, flags: int | OperationFlag, lock_timeout: int, io_timeout: int) -> None:
        """Send a trigger to the device.

        Args:
            lid: Link id from `create_link`.
            flags: Operation flags to use.
            lock_timeout: Time, in milliseconds, to wait on a lock.
            io_timeout: Time, in milliseconds, to wait for I/O to complete.
        """
        self.init(DEVICE_CORE, DEVICE_CORE_VERSION, DEVICE_TRIGGER)
        self.append(pack(">4l", lid, flags, lock_timeout, io_timeout))
        self.write()
        _ = self.read_reply()

    def device_unlock(self, lid: int) -> None:
        """Release a lock acquired by `device_lock`.

        Args:
            lid: Link id from `create_link`.
        """
        self.init(DEVICE_CORE, DEVICE_CORE_VERSION, DEVICE_UNLOCK)
        self.append(pack(">l", lid))
        self.write()
        _ = self.read_reply()

    def device_write(
        self,
        *,
        lid: int,
        io_timeout: int,
        lock_timeout: int,
        flags: int | OperationFlag,
        data: bytes | memoryview | str,
    ) -> int:
        """Write data to the specified device.

        Args:
            lid: Link id from `create_link`.
            io_timeout: Time, in milliseconds, to wait for I/O to complete.
            lock_timeout: Time, in milliseconds, to wait on a lock.
            flags: Operation flags to use.
            data: The data to write.

        Returns:
            The number of bytes written.
        """
        size: int
        self.init(DEVICE_CORE, DEVICE_CORE_VERSION, DEVICE_WRITE)
        self.append(pack(">4l", lid, io_timeout, lock_timeout, flags))
        self.append_opaque(data)
        self.write()
        (size,) = unpack(">L", self.read_reply())
        return size


class VXI11(MessageBased, regex=REGEX):
    """Base class for the [VXI-11](http://www.vxibus.org/specifications.html) communication protocol."""

    def __init__(self, equipment: Equipment) -> None:
        """Base class for the [VXI-11](http://www.vxibus.org/specifications.html) communication protocol.

        Args:
            equipment: An [Equipment][] instance.

        A [Connection][msl.equipment.schema.Connection] instance supports the following _properties_
        for the [VXI-11](http://www.vxibus.org/specifications.html) communication protocol, as well
        as the _properties_ defined in [MessageBased][msl.equipment.interfaces.message_based.MessageBased].

        Attributes: Connection Properties:
            buffer_size (int): The maximum number of bytes to read at a time. _Default: `4096`_
            lock_timeout (float): The timeout (in seconds) to wait for a lock (0 means wait forever). _Default: `0`_
            port (int): The port to use instead of calling the RPC Port Mapper function.
        """
        # the following must be defined before calling super()
        self._core_client: CoreClient | None = None
        self._abort_client: AsyncClient | None = None
        self._lock_timeout: float = 0  # updated in lock_timeout.setter
        super().__init__(equipment)

        assert equipment.connection is not None  # noqa: S101
        info = parse_vxi_address(equipment.connection.address)
        if info is None:
            msg = f"Invalid VXI-11 address {equipment.connection.address!r}"
            raise ValueError(msg)

        self._info: ParsedVXI11Address = info

        props = equipment.connection.properties
        self._buffer_size: int = props.get("buffer_size", 4096)
        self._core_port: int = props.get("port", -1)  # updated in _connect if -1
        self._abort_port: int = -1  # updated in _connect
        self._max_recv_size: int = -1  # updated in _connect
        self._link_id: int = -1  # updated in _connect
        self._io_timeout_ms: int = -1  # updated in _set_interface_timeout
        self._lock_timeout_ms: int = -1  # updated in lock_timeout.setter
        self.lock_timeout = props.get("lock_timeout", 0)

        # A non-empty read_termination value is applied by default in
        # MessageBased if the user did not specify one. Set it back
        # to None if a read-termination character was not explicitly specified.
        if "read_termination" not in props and "termination" not in props:
            self.read_termination = None  # pyright: ignore[reportUnannotatedClassAttribute]

        # VXI-11 does not support write-termination characters
        self.write_termination = None  # pyright: ignore[reportUnannotatedClassAttribute]

        self._connect()
        self._set_interface_timeout()

    def _connect(self) -> None:
        try:
            if self._core_port == -1:
                cc = CoreClient(self._info.host)
                self._core_port = cc.get_port(
                    DEVICE_CORE, DEVICE_CORE_VERSION, socket.IPPROTO_TCP, timeout=self.timeout
                )

            self._core_client = CoreClient(self._info.host)
            self._core_client.chunk_size = self._buffer_size
            self._core_client.connect(self._core_port, timeout=self.timeout)

            params = self._core_client.create_link(
                device=self._info.name, lock_device=False, lock_timeout=self._lock_timeout_ms
            )
            self._link_id, self._abort_port, max_recv_size = params
            self._max_recv_size = min(max_recv_size, 65536)
        except (socket.timeout, TimeoutError):
            raise MSLTimeoutError(self) from None
        except Exception as e:  # noqa: BLE001
            msg = f"Cannot connect to {self._info.host}:{self._core_port}\n{e.__class__.__name__}: {e}"
            raise MSLConnectionError(self, msg) from None

    def _init_flag(self) -> int:
        # initialize the flag
        if self._lock_timeout_ms > 0:
            return OperationFlag.WAITLOCK
        return OperationFlag.NULL

    def _read(self, size: int | None) -> bytes:  # pyright: ignore[reportImplicitOverride]
        """Overrides method in MessageBased."""
        assert self._core_client is not None  # noqa: S101
        request_size = self._buffer_size if size is None else min(size, self._buffer_size)

        term_char = 0
        flags = self._init_flag()

        if self._read_termination:
            term_char = ord(self._read_termination)
            flags |= OperationFlag.TERMCHRSET

        now = time.time
        io_timeout = self._io_timeout_ms
        reason = 0
        done_flag = RX_END | RX_CHR
        msg = bytearray()
        t0 = now()
        while reason & done_flag == 0:
            try:
                reason, data = self._core_client.device_read(
                    lid=self._link_id,
                    request_size=request_size,
                    io_timeout=io_timeout,
                    lock_timeout=self._lock_timeout_ms,
                    flags=flags,
                    term_char=term_char,
                )
            except Exception as e:
                if VXI_ERROR_CODES[15] in str(e):
                    raise TimeoutError from None
                raise
            else:
                msg.extend(data)
                if size is not None:
                    size -= len(data)
                    if size <= 0:
                        break
                    request_size = min(size, self._buffer_size)

            if len(msg) > self._max_read_size:
                error = f"len(message) [{len(msg)}] > max_read_size [{self._max_read_size}]"
                raise RuntimeError(error)

            # decrease io_timeout before reading the next chunk so that the
            # total time to receive all data preserves what was specified
            if self._io_timeout_ms > 0:
                io_timeout = max(0, self._io_timeout_ms - int((now() - t0) * 1000))

        return bytes(msg)

    def _set_interface_timeout(self) -> None:  # pyright: ignore[reportImplicitOverride]
        # Overrides method in MessageBased
        if self._timeout is None:
            # use 1 day as equivalent to a socket in blocking mode
            self._io_timeout_ms = 86400000
        else:
            self._io_timeout_ms = int(self._timeout * 1000)
        self._set_socket_timeout()

    def _set_socket_timeout(self) -> None:
        if self._timeout is None:  # noqa: SIM108
            # the socket is put in blocking mode
            timeout = None
        else:
            # the socket timeout value must be > io_timeout + lock_timeout
            timeout = 1 + self._timeout + self._lock_timeout

        if self._core_client is not None:
            self._core_client.set_timeout(timeout)

        if self._abort_client is not None:
            self._abort_client.set_timeout(timeout)

    def _write(self, message: bytes) -> int:  # pyright: ignore[reportImplicitOverride]
        """Overrides method in MessageBased."""
        assert self._core_client is not None  # noqa: S101
        flags = self._init_flag()
        offset = 0
        num = len(message)
        view = memoryview(message)  # avoids unnecessarily copying of slices
        while num > 0:
            if num <= self._max_recv_size:
                flags |= OperationFlag.END

            block = view[offset : offset + self._max_recv_size]

            try:
                size = self._core_client.device_write(
                    lid=self._link_id,
                    io_timeout=self._io_timeout_ms,
                    lock_timeout=self._lock_timeout_ms,
                    flags=flags,
                    data=block,
                )
            except Exception as e:
                if VXI_ERROR_CODES[15] in str(e):
                    raise TimeoutError from None
                raise
            else:
                if size < len(block):
                    error = "The number of bytes written is less than expected"
                    raise RuntimeError(error)

                offset += size
                num -= size

        return offset

    def abort(self) -> None:
        """Stop an in-progress request."""
        if self._abort_client is None:
            self._abort_client = AsyncClient(self._info.host)
            self._abort_client.connect(self._abort_port, timeout=self.timeout)
        self._abort_client.device_abort(self._link_id)

    def clear(self) -> None:
        """Send the `clear` command to the device."""
        if self._core_client is None:
            raise MSLConnectionError(self, "not connected to VXI-11 device")

        self._core_client.device_clear(
            lid=self._link_id,
            flags=self._init_flag(),
            lock_timeout=self._lock_timeout_ms,
            io_timeout=self._io_timeout_ms,
        )

    def create_intr_chan(self, host_addr: int, host_port: int, prog_num: int, prog_vers: int, prog_family: int) -> None:
        """Inform the network instrument server to establish an interrupt channel.

        Args:
            host_addr: Address of the host servicing the interrupt.
            host_port: Valid port number on the client.
            prog_num: Program number.
            prog_vers: Program version number.
            prog_family: The underlying socket protocol family type (`IPPROTO_TCP` or `IPPROTO_UDP`).
        """
        if self._core_client is None:
            raise MSLConnectionError(self, "not connected to VXI-11 device")

        self._core_client.create_intr_chan(
            host_addr=host_addr, host_port=host_port, prog_num=prog_num, prog_vers=prog_vers, prog_family=prog_family
        )

    def destroy_intr_chan(self) -> None:
        """Inform the network instrument server to close its interrupt channel."""
        if self._core_client is None:
            raise MSLConnectionError(self, "not connected to VXI-11 device")

        self._core_client.destroy_intr_chan()

    def destroy_link(self) -> None:
        """Destroy the link with the device."""
        if self._core_client is None:
            raise MSLConnectionError(self, "not connected to VXI-11 device")

        self._core_client.destroy_link(self._link_id)

    def disconnect(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Unlink and close the sockets."""
        if self._abort_client is None and self._core_client is None:
            return

        if self._abort_client is not None:
            self._abort_client.close()
            self._abort_client = None

        if self._core_client is not None:
            if self._link_id != -1:
                with contextlib.suppress(ConnectionError):
                    self._core_client.destroy_link(self._link_id)
                self._link_id = -1

            self._core_client.close()
            self._core_client = None

        super().disconnect()

    def docmd(self, cmd: int, value: float, fmt: str) -> bytes:
        """Allows for a variety of commands to be executed.

        Args:
            cmd: An IEEE 488 command messages. For example, to send the Group Execute Trigger
                command, _GET_, the value of `cmd` is `0x08`.
            value: The value to use with `cmd`. Can be of type [bool][], [int][] or [float][].
            fmt: How to format `value`. See [format-characters][] for more details. Do not
                include the byte-order character. Network (big-endian) order is always used.

        Returns:
            The results defined by `cmd`.
        """
        if self._core_client is None:
            raise MSLConnectionError(self, "not connected to VXI-11 device")

        # always use network (big-endian) byte order
        s = Struct("!" + fmt.lstrip("@=<>!"))
        return self._core_client.device_docmd(
            lid=self._link_id,
            flags=self._init_flag(),
            io_timeout=self._io_timeout_ms,
            lock_timeout=self._lock_timeout_ms,
            cmd=cmd,
            network_order=True,
            size=s.size,
            data=s.pack(value),
        )

    def enable_sqr(self, *, state: bool, handle: bytes) -> None:
        """Enable or disable the sending of `device_intr_srq` RPCs by the network instrument server.

        Args:
            state: Whether to enable or disable interrupts.
            handle: Host specific data (maximum length is 40 characters).
        """
        if self._core_client is None:
            raise MSLConnectionError(self, "not connected to VXI-11 device")

        self._core_client.device_enable_srq(lid=self._link_id, state=state, handle=handle)

    def local(self) -> None:
        """Place the device in a local state wherein all programmable local controls are enabled."""
        if self._core_client is None:
            raise MSLConnectionError(self, "not connected to VXI-11 device")

        self._core_client.device_local(
            lid=self._link_id,
            flags=self._init_flag(),
            lock_timeout=self._lock_timeout_ms,
            io_timeout=self._io_timeout_ms,
        )

    def lock(self) -> None:
        """Acquire the device's lock."""
        if self._core_client is None:
            raise MSLConnectionError(self, "not connected to VXI-11 device")

        self._core_client.device_lock(lid=self._link_id, flags=self._init_flag(), lock_timeout=self._lock_timeout_ms)

    @property
    def lock_timeout(self) -> float:
        """The time, in seconds, to wait to acquire a lock.

        Setting the value to &le;0 (or `None`) means _wait forever_.
        """
        if self._lock_timeout == ONE_DAY:
            return 0.0
        return self._lock_timeout

    @lock_timeout.setter
    def lock_timeout(self, value: float | None) -> None:  # pyright: ignore[reportPropertyTypeMismatch]
        if value is None or value < 0:
            self._lock_timeout = ONE_DAY
        else:
            self._lock_timeout = float(value)
        self._lock_timeout_ms = int(self._lock_timeout * 1000)
        self._set_socket_timeout()

    def read_stb(self) -> int:
        """Read the status byte from the device.

        Returns:
            The status byte.
        """
        if self._core_client is None:
            raise MSLConnectionError(self, "not connected to VXI-11 device")

        return self._core_client.device_readstb(
            lid=self._link_id,
            flags=self._init_flag(),
            lock_timeout=self._lock_timeout_ms,
            io_timeout=self._io_timeout_ms,
        )

    def reconnect(self, max_attempts: int = 1) -> None:
        """Reconnect to the equipment.

        Args:
            max_attempts: The maximum number of attempts to try to reconnect with the equipment.
                If &lt;1, keep trying until a connection is successful. If the maximum number
                of attempts has been reached then an exception is raise.
        """
        attempt = 0
        while True:
            attempt += 1
            try:
                return self._connect()
            except (MSLConnectionError, MSLTimeoutError):
                if 0 < max_attempts <= attempt:
                    raise

    def remote(self) -> None:
        """Place the device in a remote state wherein all programmable local controls are disabled."""
        if self._core_client is None:
            raise MSLConnectionError(self, "not connected to VXI-11 device")

        self._core_client.device_remote(
            lid=self._link_id,
            flags=self._init_flag(),
            lock_timeout=self._lock_timeout_ms,
            io_timeout=self._io_timeout_ms,
        )

    @property
    def socket(self) -> socket.socket | None:
        """Returns the reference to the underlying socket."""
        if self._core_client is None:
            return None
        return self._core_client.socket

    def trigger(self) -> None:
        """Send a trigger to the device."""
        if self._core_client is None:
            raise MSLConnectionError(self, "not connected to VXI-11 device")

        self._core_client.device_trigger(
            lid=self._link_id,
            flags=self._init_flag(),
            lock_timeout=self._lock_timeout_ms,
            io_timeout=self._io_timeout_ms,
        )

    def unlock(self) -> None:
        """Release the lock acquired by [lock][msl.equipment.interfaces.vxi11.VXI11.lock]."""
        if self._core_client is None:
            raise MSLConnectionError(self, "not connected to VXI-11 device")

        self._core_client.device_unlock(self._link_id)


@dataclass
class ParsedVXI11Address:
    """The parsed result of a VISA-style address for the VXI-11 interface.

    Args:
        board: Board number.
        host: The IP address or hostname of the device.
        name: The LAN device name.
    """

    board: int
    host: str
    name: str


def parse_vxi_address(address: str) -> ParsedVXI11Address | None:
    """Get the board number, host and LAN device name from an address.

    Args:
        address: The VISA-style address to use for the connection.

    Returns:
        The parsed address or `None` if `address` is not valid for the VXI-11 interface.
    """
    match = REGEX.match(address)
    if not match:
        return None

    board = int(match["board"] or 0)
    name = match["name"] or "inst0"
    return ParsedVXI11Address(board, match["host"], name)


@dataclass
class _VXI11Device:
    """A device that support the VXI-11 protocol."""

    webserver: str
    description: str
    addresses: list[str]


def find_vxi11(  # noqa: C901, PLR0915
    *,
    ip: list[str] | None = None,
    timeout: float = 1,
) -> dict[str, _VXI11Device]:
    """Find all VXI-11 devices that are on the network.

    The RPC port-mapper protocol (RFC-1057, Appendix A) broadcasts a message
    via UDP to port 111 for VXI-11 device discovery.

    Args:
        ip: The IP address(es) on the local computer to use to broadcast the
            discovery message. If not specified, broadcast on all network interfaces.
        timeout: The maximum number of seconds to wait for a reply.

    Returns:
        The information about the VXI-11 devices that were found.
    """
    all_ips = ipv4_addresses() if not ip else set(ip)

    logger.debug("find VXI-11 devices: interfaces:=%s, timeout=%s", all_ips, timeout)

    def broadcast(host: str) -> None:  # noqa: C901
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.bind((host, 0))
        _ = sock.sendto(broadcast_msg, ("255.255.255.255", PMAP_PORT))
        select_timeout = min(timeout * 0.1, 0.1)
        t0 = time.time()
        while True:
            r, _, _ = select.select([sock], [], [], select_timeout)
            if time.time() - t0 > timeout:
                break
            if not r:
                continue

            reply, (ip_address, port) = sock.recvfrom(1024)
            if port != PMAP_PORT:
                continue

            view = client.check_reply(memoryview(reply))
            if view is None:
                continue

            (port,) = unpack(">L", view)
            if port == 0:  # not a VXI-11 device
                continue

            try:
                lxi = parse_lxi_webserver(ip_address, timeout=timeout)
            except Exception as e:  # noqa: BLE001
                logger.warning("%s: %s [%s:%s]", e.__class__.__name__, e, ip_address, port)
                lxi = LXIDevice()

            addresses: set[str] = set()
            addresses.add(f"TCPIP::{ip_address}::inst0::INSTR")

            description = lxi.description
            if not description:
                options = [lxi.manufacturer, lxi.model, lxi.serial]
                description = ", ".join(item for item in options if item)

            for interface in lxi.interfaces:
                if interface.type != "LXI":
                    continue
                for address in interface.addresses:
                    addresses.add(address)
                if interface.hostname:
                    addresses.add(f"TCPIP::{interface.hostname}::inst0::INSTR")

            key = tuple(int(s) for s in ip_address.split("."))
            devices[key] = _VXI11Device(
                webserver=f"http://{ip_address}",
                description=description or "Unknown LXI device",
                addresses=sorted(addresses),
            )

        sock.close()

    # construct the broadcast message
    client = RPCClient("")
    client.init(PMAP_PROG, PMAP_VERS, PMAPPROC_GETPORT)
    client.append(pack(">4I", DEVICE_CORE, DEVICE_CORE_VERSION, socket.IPPROTO_TCP, 0))
    broadcast_msg = client.get_buffer()

    devices: dict[tuple[int, ...], _VXI11Device] = {}
    threads = [threading.Thread(target=broadcast, args=(ip,)) for ip in all_ips]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return {".".join(str(v) for v in k): devices[k] for k in sorted(devices)}
