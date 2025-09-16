"""Implementation of the VXI-11_ protocol.

VXI-11 is a client-service model to send messages through a network.
The messages are formatted using the Remote Procedure Call protocol RFC-1057
and are encoded/decoded using the eXternal Data Representation standard RFC-1014.

# References

* [VXI-11] &mdash; *TCP/IP Instrument Protocol Specification (Revision 1.0)*, **VXIbus Consortium**, July 1995.
* [RFC-1057] &mdash; *RPC: Remote Procedure Call Protocol Specification (Version 2)*, **Sun Microsystems**, June 1988.
* [RFC-1014] &mdash; *XDR: External Data Representation Standard*, **Sun Microsystems**, June 1987.

[VXI-11]: http://www.vxibus.org/specifications.html
[RFC-1057]: https://www.rfc-editor.org/rfc/rfc1057
[RFC-1014]: https://www.rfc-editor.org/rfc/rfc1014
"""

from __future__ import annotations

import os
import random
import select
import socket
import threading
import time
from dataclasses import dataclass
from enum import IntEnum
from struct import pack, unpack
from typing import overload

from .utils import LXIDevice, ipv4_addresses, logger, parse_lxi_webserver

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
PMAP_PORT = 11111 if os.getenv("MSL_EQUIPMENT_TESTING") else 111


# RPC enums
class MessageType(IntEnum):
    """**RPC:** The message type."""

    CALL = 0
    REPLY = 1


class ReplyStatus(IntEnum):
    """**RPC:** Message reply status."""

    MSG_ACCEPTED = 0
    MSG_DENIED = 1


class AcceptStatus(IntEnum):
    """**RPC:** Message accepted status."""

    SUCCESS = 0
    PROG_UNAVAIL = 1
    PROG_MISMATCH = 2
    PROC_UNAVAIL = 3
    GARBAGE_ARGS = 4


class RejectStatus(IntEnum):
    """**RPC:** Message rejected status."""

    RPC_MISMATCH = 0
    AUTH_ERROR = 1


class AuthStatus(IntEnum):
    """**RPC:** Authorization status."""

    AUTH_BADCRED = 1
    AUTH_REJECTEDCRED = 2
    AUTH_BADVERF = 3
    AUTH_REJECTEDVERF = 4
    AUTH_TOOWEAK = 5


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

        Parameters
        ----------
        text : :class:`memoryview`, :class:`bytes` or :class:`str`
            The data to append.
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
        return

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
    def unpack_opaque(data: bytes) -> bytes: ...

    @overload
    @staticmethod
    def unpack_opaque(data: bytearray) -> bytearray: ...

    @overload
    @staticmethod
    def unpack_opaque(data: memoryview) -> memoryview: ...

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

    def check_reply(self, message: memoryview) -> memoryview | None:
        """Checks the message for errors and returns the procedure-specific data.

        Args:
            message: The reply from an RPC message.

        Returns:
            The reply or `None` if the transaction id does not match the
                value that was used in the corresponding `write` call.
        """
        xid, m_type, status = unpack(">3I", message[:12])
        if xid != self._xid:
            # data in read buffer is due to an interrupt?
            return None

        if m_type != MessageType.REPLY:
            msg = f"RPC message type is not {MessageType.REPLY!r}, got {m_type}"
            raise RuntimeError(msg)

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


class CoreClient(VXIClient):
    """Communicate with the `Device Core` program on the remote device."""

    def __init__(self, host: str) -> None:
        """Communicate with the `Device Core` program on the remote device.

        Args:
            host: The hostname or IP address of the remote device.
        """
        super().__init__(host)

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

    def device_unlock(self, lid: int) -> None:
        """Release a lock acquired by `device_lock`.

        Args:
            lid: Link id from `create_link`.
        """
        self.init(DEVICE_CORE, DEVICE_CORE_VERSION, DEVICE_UNLOCK)
        self.append(pack(">l", lid))
        self.write()
        _ = self.read_reply()

    def device_enable_srq(self, *, lid: int, enable: bool, handle: bytes) -> None:
        """Enable or disable the sending of `device_intr_srq` RPCs by the network instrument server.

        Args:
            lid: Link id from `create_link`.
            enable: Whether to enable or disable interrupts.
            handle: Host specific data (maximum length is 40 characters).
        """
        if len(handle) > 40:  # noqa: PLR2004
            msg = "The handle must be <= 40 characters"
            raise ValueError(msg)
        self.init(DEVICE_CORE, DEVICE_CORE_VERSION, DEVICE_ENABLE_SRQ)
        self.append(pack(">2l", lid, enable))
        self.append_opaque(handle)
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
        data_size: int,
        data_in: bytes | str,
    ) -> bytes:
        """Allows for a variety of operations to be executed.

        Args:
            lid: Link id from `create_link`.
            flags: Operation flags to use.
            io_timeout: Time, in milliseconds, to wait for I/O to complete.
            lock_timeout: Time, in milliseconds, to wait on a lock.
            cmd: Which command to execute.
            network_order: Whether to use the client's byte order.
            data_size: Size of individual data elements.
            data_in: Data input parameters.

        Returns:
            The results defined by `cmd`.
        """
        self.init(DEVICE_CORE, DEVICE_CORE_VERSION, DEVICE_DOCMD)
        self.append(pack(">7l", lid, flags, io_timeout, lock_timeout, cmd, network_order, data_size))
        self.append_opaque(data_in)
        self.write()
        return bytes(self.unpack_opaque(self.read_reply()))

    def destroy_link(self, lid: int) -> None:
        """Destroy the link.

        Args:
            lid: Link id from `create_link`.
        """
        self.init(DEVICE_CORE, DEVICE_CORE_VERSION, DESTROY_LINK)
        self.append(pack(">l", lid))
        self.write()
        _ = self.read_reply()

    def create_intr_chan(
        self, *, host_addr: int, host_port: int, prog_num: int, prog_vers: int, prog_family: int
    ) -> None:
        """Inform the network instrument server to establish an interrupt channel.

        Args:
            host_addr: Host servicing the interrupt.
            host_port: Valid port number on the client.
            prog_num: Program number.
            prog_vers: Program version number.
            prog_family: The underlying socket protocol family type (`IPPROTO_TCP` or `IPPROTO_UDP`).
        """
        self.init(DEVICE_CORE, DEVICE_CORE_VERSION, CREATE_INTR_CHAN)
        self.append(pack(">5L", host_addr, host_port, prog_num, prog_vers, prog_family))
        self.write()
        _ = self.read_reply()

    def destroy_intr_chan(self) -> None:
        """Inform the network instrument server to close its interrupt channel."""
        self.init(DEVICE_CORE, DEVICE_CORE_VERSION, DESTROY_INTR_CHAN)
        self.write()
        _ = self.read_reply()


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
