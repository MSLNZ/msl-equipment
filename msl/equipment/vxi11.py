"""
Implementation of the VXI-11_ protocol.

VXI-11_ is a client-service model to send messages through a network.
The messages are formatted using the Remote Procedure Call protocol [RFC-1057_]
and are encoded/decoded using the eXternal Data Representation standard [RFC-1014_].

References
----------
* VXI-11_ -- *TCP/IP Instrument Protocol Specification (Revision 1.0)*, **VXIbus Consortium**, July 1995.
* RFC-1057_ -- *RPC: Remote Procedure Call Protocol Specification (Version 2)*, **Sun Microsystems**, June 1988.
* RFC-1014_ -- *XDR: External Data Representation Standard*, **Sun Microsystems**, June 1987.

.. _VXI-11: http://www.vxibus.org/specifications.html
.. _RFC-1057: https://www.rfc-editor.org/rfc/rfc1057
.. _RFC-1014: https://www.rfc-editor.org/rfc/rfc1014
"""
from __future__ import annotations

import os
import random
import socket
from enum import IntEnum
from struct import pack
from struct import unpack

from .utils import parse_lxi_webserver

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
    """`VXI-11:` Additional information concerning how a request is carried out."""
    NULL = 0x00
    WAITLOCK = 0x01
    END = 0x08
    TERMCHRSET = 0x80


# VXI-11 error codes, see Table B.2 in the document
VXI_ERROR_CODES = {
    0: 'No error',
    1: 'Syntax error',
    3: 'Device not accessible',
    4: 'Invalid link identifier',
    5: 'Parameter error',
    6: 'Channel not established',
    8: 'Operation not supported',
    9: 'Out of resources',
    11: 'Device locked by another link',
    12: 'No lock held by this link',
    15: 'I/O timeout',
    17: 'I/O error',
    21: 'Invalid address',
    23: 'Abort',
    29: 'Channel already established'
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
if os.getenv('MSL_EQUIPMENT_TESTING'):
    PMAP_PORT = 11111
else:
    PMAP_PORT = 111


# RPC enums
class MessageType(IntEnum):
    """`RPC:` The message type."""
    CALL = 0
    REPLY = 1


class ReplyStatus(IntEnum):
    """`RPC:` Message reply status."""
    MSG_ACCEPTED = 0
    MSG_DENIED = 1


class AcceptStatus(IntEnum):
    """`RPC:` Message accepted status."""
    SUCCESS = 0
    PROG_UNAVAIL = 1
    PROG_MISMATCH = 2
    PROC_UNAVAIL = 3
    GARBAGE_ARGS = 4


class RejectStatus(IntEnum):
    """`RPC:` Message rejected status."""
    RPC_MISMATCH = 0
    AUTH_ERROR = 1


class AuthStatus(IntEnum):
    """`RPC:` Authorization status."""
    AUTH_BADCRED = 1
    AUTH_REJECTEDCRED = 2
    AUTH_BADVERF = 3
    AUTH_REJECTEDVERF = 4
    AUTH_TOOWEAK = 5


class RPCClient(object):
    
    def __init__(self, host):
        """Remote Procedure Call implementation for a client.

        Parameters
        ----------
        host : :class:`str`
            The hostname or IP address of the remote device.
        """
        super(RPCClient, self).__init__()
        self._host = host
        self._sock = None
        self._xid = 0  # transaction identifier
        self._buffer = bytearray()
        self._chunk_size = 4096

    def append(self, data):
        """Append data to the body of the current RPC message.

        Parameters
        ----------
        data : :class:`bytes` or :class:`memoryview`
            The data to append.
        """
        self._buffer.extend(data)

    def append_opaque(self, text):
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
            encoded = memoryview(text.encode('ascii'))  # must be an ASCII message

        n = len(encoded)
        self.append(pack('>L', n))

        data = encoded[:n]
        self.append(data)

        n = ((n + 3) // 4) * 4
        self.append((n - len(data)) * b'\0')

    @property
    def chunk_size(self):
        """:class:`int`: The maximum number of bytes to receive at a time from the socket."""
        return self._chunk_size

    @chunk_size.setter
    def chunk_size(self, size):
        self._chunk_size = int(size)

    def close(self):
        """Close the RPC socket, if one is open."""
        if self._sock:
            self._sock.close()
            self._sock = None

    def connect(self, port, timeout=10):
        """Connect to a specific port on the device.

        Parameters
        ----------
        port : :class:`int`
            The port number to connect to.
        timeout : :class:`float` or :data:`None`, optional
            The maximum number of seconds to wait for the connection to be
            established.
        """
        self.close()
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.settimeout(timeout)
        self._sock.connect((self._host, port))

    def get_buffer(self):
        """Get the data in the buffer.

        Returns
        -------
        :class:`bytearray`
            The data in the current RPC message.
        """
        return self._buffer

    def get_port(self, prog, vers, prot, timeout=10):
        """Call the Port Mapper procedure to determine which port to use for a program.

        This method will automatically open and close the socket connection.

        Parameters
        ----------
        prog : :class:`int`
            The program number to get the port number of.
        vers : :class:`int`
            The version number of `prog`.
        prot : :class:`int`
            The socket protocol family type to use when sending requests to `prog`
            (``IPPROTO_TCP`` or ``IPPROTO_UDP``).
        timeout : :class:`float` or :data:`None`, optional
            The maximum number of seconds to wait to get the port value.

        Returns
        -------
        :class:`int`
            The port number that corresponds to `prog`.
        """
        try:
            self.connect(PMAP_PORT, timeout=timeout)
            self.init(PMAP_PROG, PMAP_VERS, PMAPPROC_GETPORT)
            self.append(pack('>4I', prog, vers, prot, 0))
            self.write()
            port, = unpack('>L', self.read())
        finally:
            self.close()

        if port == 0:
            raise RuntimeError(
                'Could not determine the port from the Port Mapper procedure')
        return port

    def init(self, prog, vers, proc):
        """Construct a new RPC message.

        Parameters
        ----------
        prog : :class:`int`
            The program number.
        vers : :class:`int`
            The version number of program.
        proc : :class:`int`
            The procedure number within the program to be called.
        """
        # increment and wrap to 0 on uint32 overflow
        xid = (self._xid + 1) & 0xFFFFFFFF

        # The VXI-11 document, Section B.4.5 (Security Control), states
        # that authentication is not used. That is where the two 0's come from
        self._buffer = bytearray(pack('>6I2Q', xid, MessageType.CALL, RPC_VERS, prog, vers, proc, 0, 0))
        self._xid = xid

    def interrupt_handler(self):
        """Override this method to be notified of a service interrupt.

        This method gets called if an interrupt is received during a
        :meth:`.read`. It does not continuously poll the device.
        """
        return

    def read(self):
        """Read an RPC message, check for errors, and return the procedure-specific data.

        Returns
        -------
        :class:`memoryview`
            The procedure-specific data.
        """
        # RFC-1057, Section 10 describes that RPC messages are sent in fragments
        last_fragment = False
        message = bytearray()
        recv = self._sock.recv
        recv_into = self._sock.recv_into
        chunk_size = self._chunk_size
        while not last_fragment:
            header = recv(4)
            if len(header) < 4:
                raise EOFError('The RPC reply header is < 4 bytes')
            h, = unpack('>I', header)
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

    def set_timeout(self, timeout):
        """Set the socket timeout value.

        Parameters
        ----------
        timeout : :class:`float`
            The timeout, in seconds, to use for the socket.
        """
        self._sock.settimeout(timeout)

    @property
    def socket(self):
        """:class:`~socket.socket`: The reference to the socket."""
        return self._sock

    @staticmethod
    def unpack_opaque(data):
        """Unpack and return a variable-length string.

        Parameters
        ----------
        data : :class:`bytes`, :class:`bytearray` or :class:`memoryview`
            The data to unpack.

        Returns
        -------
        :class:`bytes`, :class:`bytearray` or :class:`memoryview`
            The unpacked data.
        """
        # mimic the builtin xdrlib.Unpacker class
        # don't use xdrlib since it became deprecated in Python 3.11
        if not data:
            return b''
        n, = unpack('>L', data[:4])
        return data[4:4+n]

    def write(self):
        """Write the RPC message that is in the buffer."""
        # RFC-1057, Section 10 describes that RPC messages are sent in fragments
        fragment_size = 0x7FFFFFFF  # (2**31) - 1
        remaining = len(self._buffer)
        view = memoryview(self._buffer)
        sendall = self._sock.sendall
        while remaining > 0:
            if remaining <= fragment_size:  # then it is the last fragment
                fragment_size = remaining | 0x80000000
            data = bytearray(pack('>I', fragment_size))
            data.extend(view[:fragment_size])
            sendall(data)
            view = view[fragment_size:]
            remaining -= fragment_size

    def check_reply(self, message):
        """Checks the message for errors and returns the procedure-specific data.

        Parameters
        ----------
        message : :class:`memoryview`
            The reply from an RPC message.

        Returns
        -------
        :class:`memoryview` or :data:`None`
            The reply or :data:`None` if the transaction id does not match the
            value that was used in the corresponding :meth:`.write` call.
        """
        xid, mtype, status = unpack('>3I', message[:12])
        if xid != self._xid:
            # data in read buffer is due to an interrupt?
            return

        if mtype != MessageType.REPLY:
            raise RuntimeError('RPC message type is not {!r}, got {}'.format(
                MessageType.REPLY, mtype))

        if status == ReplyStatus.MSG_ACCEPTED:
            verf, status = unpack('>QI', message[12:24])
            assert verf == 0  # VXI-11 does not use authentication
            if status == AcceptStatus.SUCCESS:
                return message[24:]  # procedure-specific data
            elif status == AcceptStatus.PROG_MISMATCH:
                low, high = unpack('>2I', message[24:32])
                raise RuntimeError('RPC call failed: {!r}: low={}, high={}'.format(
                    AcceptStatus.PROG_MISMATCH, low, high))
            else:
                # cases include PROG_UNAVAIL, PROC_UNAVAIL, and GARBAGE_ARGS
                raise RuntimeError('RPC call failed: {!r}'.format(
                    AcceptStatus(status)))
        elif status == ReplyStatus.MSG_DENIED:
            status, = unpack('>I', message[12:16])
            if status == RejectStatus.RPC_MISMATCH:
                low, high = unpack('>2I', message[16:24])
                raise RuntimeError('RPC call failed: {!r}: low={}, high={}'.format(
                    RejectStatus(status), low, high))
            elif status == RejectStatus.AUTH_ERROR:
                raise RuntimeError('RPC authentication failed: {!r}'.format(
                    AuthStatus(status)))
            else:
                raise RuntimeError('RPC MSG_DENIED reply status is not '
                                   'RPC_MISMATCH nor AUTH_ERROR')
        else:
            raise RuntimeError('RPC reply is not MSG_ACCEPTED nor MSG_DENIED')


class VXIClient(RPCClient):

    def __init__(self, host):
        """Base class for a VXI-11 program.

        Parameters
        ----------
        host : :class:`str`
            The hostname or IP address of the remote device.
        """
        super(VXIClient, self).__init__(host)

    def read_reply(self):
        """Check the RPC message for an error and return the remaining data.

        Returns
        -------
        :class:`memoryview`
            The reply data.
        """
        reply = self.read()
        error, = unpack('>L', reply[:4])
        if error == 0:
            return reply[4:]
        msg = VXI_ERROR_CODES.get(error, 'Undefined error')
        raise RuntimeError('{} [error={}]'.format(msg, error))


class CoreClient(VXIClient):

    def __init__(self, host):
        """Communicate with the `Device Core` program on the remote device.

        Parameters
        ----------
        host : :class:`str`
            The hostname or IP address of the remote device.
        """
        super(CoreClient, self).__init__(host)

    def create_link(self, device, lock_device, lock_timeout):
        """Create a link.

        Parameters
        ----------
        device : :class:`bytes` or :class:`str`
            Name of the device to link with.
        lock_device : :class:`bool`
            Whether to attempt to lock the device.
        lock_timeout : :class:`int`
            Time, in milliseconds, to wait on a lock.

        Returns
        -------
        :class:`int`
            The link ID.
        :class:`int`
            The port number of the `Device Async` program (see :class:`.AsyncClient`).
        :class:`int`
            The maximum data size the device will accept on a :meth:`.device_write`.
        """
        self.init(DEVICE_CORE, DEVICE_CORE_VERSION, CREATE_LINK)
        self.append(pack('>3l', random.getrandbits(31), lock_device, lock_timeout))
        self.append_opaque(device)
        self.write()
        lid, abort_port, max_recv_size = unpack('>3L', self.read_reply())
        return lid, abort_port, max_recv_size

    def device_write(self, lid, io_timeout, lock_timeout, flags, data):
        """Write data to the specified device.

        Parameters
        ----------
        lid : :class:`int`
            Link id from :meth:`.create_link`.
        io_timeout : :class:`int`
            Time, in milliseconds, to wait for I/O to complete.
        lock_timeout : :class:`int`
            Time, in milliseconds, to wait on a lock.
        flags : :class:`int` or :class:`OperationFlag`
            Operation flags to use.
        data : :class:`memoryview`, :class:`bytes` or :class:`str`
            The data to write.

        Returns
        -------
        :class:`int`
            The number of bytes written.
        """
        self.init(DEVICE_CORE, DEVICE_CORE_VERSION, DEVICE_WRITE)
        self.append(pack('>4l', lid, io_timeout, lock_timeout, flags))
        self.append_opaque(data)
        self.write()
        size, = unpack('>L', self.read_reply())
        return size

    def device_read(self, lid, request_size, io_timeout, lock_timeout, flags, term_char):
        """Read data from the device.

        Parameters
        ----------
        lid : :class:`int`
            Link id from :meth:`.create_link`.
        request_size : :class:`int`
            The number of bytes requested.
        io_timeout : :class:`int`
            Time, in milliseconds, to wait for I/O to complete.
        lock_timeout : :class:`int`
            Time, in milliseconds, to wait on a lock.
        flags : :class:`int` or :class:`OperationFlag`
            Operation flags to use.
        term_char : :class:`int`
            The termination character. Valid only if `flags` is
            :attr:`~OperationFlag.TERMCHRSET`.

        Returns
        -------
        :class:`int`
            The reason(s) the read completed.
        :class:`memoryview`
            A view of the data (the RPC header is removed).
        """
        self.init(DEVICE_CORE, DEVICE_CORE_VERSION, DEVICE_READ)
        self.append(pack('>6l', lid, request_size, io_timeout, lock_timeout, flags, term_char))
        self.write()
        reply = self.read_reply()
        reason, = unpack('>L', reply[:4])
        return reason, self.unpack_opaque(reply[4:])

    def device_readstb(self, lid, flags, lock_timeout, io_timeout):
        """Read the status byte from the device.

        Parameters
        ----------
        lid : :class:`int`
            Link id from :meth:`.create_link`.
        flags : :class:`int` or :class:`OperationFlag`
            Operation flags to use.
        lock_timeout : :class:`int`
            Time, in milliseconds, to wait on a lock.
        io_timeout : :class:`int`
            Time, in milliseconds, to wait for I/O to complete.

        Returns
        -------
        :class:`int`
            The status byte.
        """
        self.init(DEVICE_CORE, DEVICE_CORE_VERSION, DEVICE_READSTB)
        self.append(pack('>4l', lid, flags, lock_timeout, io_timeout))
        self.write()
        stb, = unpack('>L', self.read_reply())
        return stb

    def device_trigger(self, lid, flags, lock_timeout, io_timeout):
        """Send a trigger to the device.

        Parameters
        ----------
        lid : :class:`int`
            Link id from :meth:`.create_link`.
        flags : :class:`int` or :class:`OperationFlag`
            Operation flags to use.
        lock_timeout : :class:`int`
            Time, in milliseconds, to wait on a lock.
        io_timeout : :class:`int`
            Time, in milliseconds, to wait for I/O to complete.
        """
        self.init(DEVICE_CORE, DEVICE_CORE_VERSION, DEVICE_TRIGGER)
        self.append(pack('>4l', lid, flags, lock_timeout, io_timeout))
        self.write()
        self.read_reply()

    def device_clear(self, lid, flags, lock_timeout, io_timeout):
        """Send the `clear` command to the device.

        Parameters
        ----------
        lid : :class:`int`
            Link id from :meth:`.create_link`.
        flags : :class:`int` or :class:`OperationFlag`
            Operation flags to use.
        lock_timeout : :class:`int`
            Time, in milliseconds, to wait on a lock.
        io_timeout : :class:`int`
            Time, in milliseconds, to wait for I/O to complete.
        """
        self.init(DEVICE_CORE, DEVICE_CORE_VERSION, DEVICE_CLEAR)
        self.append(pack('>4l', lid, flags, lock_timeout, io_timeout))
        self.write()
        self.read_reply()

    def device_remote(self, lid, flags, lock_timeout, io_timeout):
        """Place the device in a remote state wherein all programmable local
        controls are disabled.

        Parameters
        ----------
        lid : :class:`int`
            Link id from :meth:`.create_link`.
        flags : :class:`int` or :class:`OperationFlag`
            Operation flags to use.
        lock_timeout : :class:`int`
            Time, in milliseconds, to wait on a lock.
        io_timeout : :class:`int`
            Time, in milliseconds, to wait for I/O to complete.
        """
        self.init(DEVICE_CORE, DEVICE_CORE_VERSION, DEVICE_REMOTE)
        self.append(pack('>4l', lid, flags, lock_timeout, io_timeout))
        self.write()
        self.read_reply()

    def device_local(self, lid, flags, lock_timeout, io_timeout):
        """Place the device in a local state wherein all programmable local
        controls are enabled.

        Parameters
        ----------
        lid : :class:`int`
            Link id from :meth:`.create_link`.
        flags : :class:`int` or :class:`OperationFlag`
            Operation flags to use.
        lock_timeout : :class:`int`
            Time, in milliseconds, to wait on a lock.
        io_timeout : :class:`int`
            Time, in milliseconds, to wait for I/O to complete.
        """
        self.init(DEVICE_CORE, DEVICE_CORE_VERSION, DEVICE_LOCAL)
        self.append(pack('>4l', lid, flags, lock_timeout, io_timeout))
        self.write()
        self.read_reply()

    def device_lock(self, lid, flags, lock_timeout):
        """Acquire a device's lock.

        Parameters
        ----------
        lid : :class:`int`
            Link id from :meth:`.create_link`.
        flags : :class:`int` or :class:`OperationFlag`
            Operation flags to use.
        lock_timeout : :class:`int`
            Time, in milliseconds, to wait on a lock.
        """
        self.init(DEVICE_CORE, DEVICE_CORE_VERSION, DEVICE_LOCK)
        self.append(pack('>3l', lid, flags, lock_timeout))
        self.write()
        self.read_reply()

    def device_unlock(self, lid):
        """Release a lock acquired by :meth:`.device_lock`.

        Parameters
        ----------
        lid : :class:`int`
            Link id from :meth:`.create_link`.
        """
        self.init(DEVICE_CORE, DEVICE_CORE_VERSION, DEVICE_UNLOCK)
        self.append(pack('>l', lid))
        self.write()
        self.read_reply()

    def device_enable_srq(self, lid, enable, handle):
        """Enable or disable the sending of `device_intr_srq` RPCs by the
        network instrument server.

        Parameters
        ----------
        lid : :class:`int`
            Link id from :meth:`.create_link`.
        enable : :class:`bool`
            Whether to enable or disable interrupts.
        handle : :class:`bytes`
            Host specific data (maximum length is 40 characters).
        """
        if len(handle) > 40:
            raise ValueError('The handle must be <= 40 characters')
        self.init(DEVICE_CORE, DEVICE_CORE_VERSION, DEVICE_ENABLE_SRQ)
        self.append(pack('>2l', lid, enable))
        self.append_opaque(handle)
        self.write()
        self.read_reply()

    def device_docmd(self, lid, flags, io_timeout, lock_timeout, cmd,
                     network_order, datasize, data_in):
        """Allows for a variety of operations to be executed.

        Parameters
        ----------
        lid : :class:`int`
            Link id from :meth:`.create_link`.
        flags : :class:`int` or :class:`OperationFlag`
            Operation flags to use.
        io_timeout : :class:`int`
            Time, in milliseconds, to wait for I/O to complete.
        lock_timeout : :class:`int`
            Time, in milliseconds, to wait on a lock.
        cmd : :class:`int`
            Which command to execute.
        network_order : :class:`bool`
            Client's byte order.
        datasize : :class:`int`
            Size of individual data elements.
        data_in : :class:`bytes` or :class:`str`
            Data input parameters.

        Returns
        -------
        :class:`bytes`
            The results defined by `cmd`.
        """
        self.init(DEVICE_CORE, DEVICE_CORE_VERSION, DEVICE_DOCMD)
        self.append(pack('>7l', lid, flags, io_timeout, lock_timeout, cmd, network_order, datasize))
        self.append_opaque(data_in)
        self.write()
        return bytes(self.unpack_opaque(self.read_reply()))

    def destroy_link(self, lid):
        """Destroy the link.

        Parameters
        ----------
        lid : :class:`int`
            Link id from :meth:`.create_link`.
        """
        self.init(DEVICE_CORE, DEVICE_CORE_VERSION, DESTROY_LINK)
        self.append(pack('>l', lid))
        self.write()
        self.read_reply()

    def create_intr_chan(self, host_addr, host_port, prog_num, prog_vers, prog_family):
        """Inform the network instrument server to establish an interrupt channel.

        Parameters
        ----------
        host_addr : :class:`int`
            Host servicing the interrupt.
        host_port : :class:`int`
            Valid port number on the client.
        prog_num : :class:`int`
            Program number.
        prog_vers : :class:`int`
            Program version number.
        prog_family : :class:`int`
            The underlying socket protocol family type
            (``IPPROTO_TCP`` or ``IPPROTO_UDP``).
        """
        self.init(DEVICE_CORE, DEVICE_CORE_VERSION, CREATE_INTR_CHAN)
        self.append(pack('>5L', host_addr, host_port, prog_num, prog_vers, prog_family))
        self.write()
        self.read_reply()

    def destroy_intr_chan(self):
        """Inform the network instrument server to close its interrupt channel."""
        self.init(DEVICE_CORE, DEVICE_CORE_VERSION, DESTROY_INTR_CHAN)
        self.write()
        self.read_reply()


class AsyncClient(VXIClient):

    def __init__(self, host):
        """Communicate with the `Device Async` program on the remote device.

        Parameters
        ----------
        host : :class:`str`
            The hostname or IP address of the remote device.
        """
        super(AsyncClient, self).__init__(host)

    def device_abort(self, lid):
        """Stops an in-progress call.

        Parameters
        ----------
        lid : :class:`int`
            Link id from :meth:`~.CoreClient.create_link`.
        """
        self.init(DEVICE_ASYNC, DEVICE_ASYNC_VERSION, DEVICE_ABORT)
        self.append(pack('>l', lid))
        self.write()
        self.read_reply()


def find_vxi11(hosts=None, timeout=1):
    """Find all VXI-11 devices that are on the network.

    The RPC port-mapper protocol (RFC-1057_, Appendix A) broadcasts a message
    via UDP to port 111 for VXI-11 device discovery.

    Parameters
    ----------
    hosts : :class:`list` of :class:`str`, optional
        The IP address(es) on the computer to use to broadcast the message.
        If not specified, then broadcast on all network interfaces.
    timeout : :class:`float`, optional
        The maximum number of seconds to wait for a reply.

    Returns
    -------
    :class:`dict`
        The information about the VXI-11 devices that were found.
    """
    import select
    import threading
    import time

    from .utils import logger

    if not hosts:
        from .utils import ipv4_addresses
        all_ips = ipv4_addresses()
    else:
        all_ips = hosts

    logger.debug('find VXI-11 devices on the following interfaces: %s', all_ips)

    def broadcast(host):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.bind((host, 0))
        sock.sendto(broadcast_msg, ('255.255.255.255', PMAP_PORT))
        select_timeout = min(timeout*0.1, 0.1)
        t0 = time.time()
        while True:
            r, w, x = select.select([sock], [], [], select_timeout)
            if time.time() - t0 > timeout:
                break
            if not r:
                continue

            reply, (ip_address, port) = sock.recvfrom(1024)
            try:
                assert port == 111
                port, = unpack('>L', client.check_reply(memoryview(reply)))
                assert port > 0
            except:
                continue

            try:
                lxi = parse_lxi_webserver(ip_address, timeout=timeout)
            except:
                lxi = {}

            device = {}
            addresses = set()
            addresses.add('TCPIP::{}::inst0::INSTR'.format(ip_address))

            if 'title' in lxi:
                # The XML document does not exist, the homepage was parsed
                device['description'] = lxi['title']
            elif 'Manufacturer' in lxi:
                # The XML document exists
                md = lxi['ManufacturerDescription']
                description = []
                for item in ('Manufacturer', 'Model', 'SerialNumber'):
                    if lxi[item] not in md:
                        description.append(lxi[item])
                description.append(md)
                device['description'] = ', '.join(description)

                for interface in lxi['Interfaces']:
                    if interface['InterfaceType'] != 'LXI':
                        continue
                    for address in interface['InstrumentAddressStrings']:
                        addresses.add(address)
                    addresses.add('TCPIP::{}::inst0::INSTR'.format(interface['Hostname']))
            else:
                device['description'] = 'Unknown LXI device'

            device['webserver'] = 'http://{}'.format(ip_address)
            device['addresses'] = sorted(addresses)

            key = tuple(int(s) for s in ip_address.split('.'))
            devices[key] = device

        sock.close()

    # construct the broadcast message
    client = RPCClient('')
    client.init(PMAP_PROG, PMAP_VERS, PMAPPROC_GETPORT)
    client.append(pack('>4I', DEVICE_CORE, DEVICE_CORE_VERSION, socket.IPPROTO_TCP, 0))
    broadcast_msg = client.get_buffer()

    # TODO use asyncio instead of threading when dropping Python 2.7 support

    devices = {}
    threads = [threading.Thread(target=broadcast, args=(ip,)) for ip in all_ips]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return dict((k, devices[k]) for k in sorted(devices))
