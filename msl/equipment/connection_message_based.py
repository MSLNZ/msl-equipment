"""
Base class for equipment that use message-based communication.
"""
import time
import socket

from .connection import Connection
from .exceptions import MSLTimeoutError
from .constants import LF, CR
from .utils import to_bytes


class ConnectionMessageBased(Connection):

    CR = CR
    """:class:`bytes`: The carriage-return character."""

    LF = LF
    """:class:`bytes`: The line-feed character."""

    def __init__(self, record):
        """Base class for equipment that use message-based communication.

        The :data:`~msl.equipment.record_types.ConnectionRecord.backend`
        value must be equal to :data:`~msl.equipment.constants.Backend.MSL`
        to use this class for the communication system. This is achieved by
        setting the value in the **Backend** field for a connection record
        in the :ref:`connections-database` to be ``MSL``.

        Do not instantiate this class directly. Use the
        :meth:`~.EquipmentRecord.connect` method to connect to the equipment.

        Parameters
        ----------
        record : :class:`.EquipmentRecord`
            A record from an :ref:`equipment-database`.
        """
        super(ConnectionMessageBased, self).__init__(record)

        self._encoding = 'utf-8'
        p = record.connection.properties

        try:
            termination = p['termination']
        except KeyError:
            self.read_termination = p.get('read_termination', ConnectionMessageBased.LF)
            self.write_termination = p.get('write_termination', ConnectionMessageBased.CR + ConnectionMessageBased.LF)
        else:
            self.read_termination = termination
            self.write_termination = termination

        self.max_read_size = p.get('max_read_size', 2 ** 16)

        self.timeout = p.get('timeout', None)

        self.encoding = p.get('encoding', self._encoding)

        self.encoding_errors = p.get('encoding_errors', 'strict')

    @property
    def encoding(self):
        """:class:`str`: The encoding that is used for :meth:`read` and :meth:`write` operations."""
        return self._encoding

    @encoding.setter
    def encoding(self, encoding):
        """Set the encoding to use for :meth:`read` and :meth:`write` operations."""
        if self._read_termination is None and self._write_termination is None:
            _ = 'test encoding'.encode(encoding).decode(encoding)
        self._encoding = encoding
        if self._read_termination is not None:
            self.read_termination = self._read_termination.decode(encoding)
        if self._write_termination is not None:
            self.write_termination = self._write_termination.decode(encoding)

    @property
    def encoding_errors(self):
        """:class:`str`: The error handling scheme to use when encoding and decoding messages.

        For example: 'strict', 'ignore', 'replace', 'xmlcharrefreplace', 'backslashreplace', ...
        """
        return self._encoding_errors

    @encoding_errors.setter
    def encoding_errors(self, value):
        name = str(value).lower()

        if name not in ('strict', 'ignore', 'replace', 'xmlcharrefreplace', 'backslashreplace'):
            err = None
            try:
                u'\u03B2'.encode('ascii', errors=name)
            except LookupError:
                # TODO This avoids nested exceptions. When dropping Python 2.7 support
                #  we can use "raise Exception() from None"
                err = 'unknown encoding error handler {!r}'.format(value)

            if err is not None:
                self.raise_exception(err)

        self._encoding_errors = name

    @property
    def read_termination(self):
        """:class:`bytes` or :data:`None`: The termination character sequence
        that is used for the :meth:`read` method.

        Reading stops when the equipment stops sending data or the `read_termination`
        character sequence is detected. If you set the `read_termination` to be equal
        to a variable of type :class:`str` it will automatically be encoded.
        """
        return self._read_termination

    @read_termination.setter
    def read_termination(self, termination):
        self._read_termination = self._encode_termination(termination)

    @property
    def write_termination(self):
        """:class:`bytes` or :data:`None`: The termination character sequence that
        is appended to :meth:`write` messages.

        If you set the `write_termination` to be equal to a variable of type
        :class:`str` it will automatically be encoded.
        """
        return self._write_termination

    @write_termination.setter
    def write_termination(self, termination):
        self._write_termination = self._encode_termination(termination)

    @property
    def max_read_size(self):
        """:class:`int`: The maximum number of bytes that can be :meth:`read`."""
        return self._max_read_size

    @max_read_size.setter
    def max_read_size(self, size):
        """The maximum number of bytes that can be :meth:`read`."""
        max_size = int(size)
        if max_size < 1:
            raise ValueError('The maximum number of bytes to read must be > 0, got {}'.format(size))
        self._max_read_size = max_size

    @property
    def timeout(self):
        r""":class:`float` or :data:`None`: The timeout, in seconds, for :meth:`read` and :meth:`write` operations.

        A value :math:`\lt` 0 will set the timeout to be :data:`None` (blocking mode).
        """
        return self._timeout

    @timeout.setter
    def timeout(self, value):
        if value is not None:
            self._timeout = float(value)
            if self._timeout < 0:
                self._timeout = None
        else:
            self._timeout = None
        self._set_backend_timeout()

    def _set_backend_timeout(self):
        # Some connections (e.g. pyserial, socket) need to be notified of the timeout change.
        # The connection subclass must override this method to notify the backend.
        pass

    def raise_timeout(self, append_msg=''):
        """Raise a :exc:`~.exceptions.MSLTimeoutError`.

        Parameters
        ----------
        append_msg : :class:`str`, optional
            A message to append to the generic timeout message.
        """
        msg = 'Timeout occurred after {} seconds. {}'.format(self._timeout, append_msg)
        self.log_error('%r %s', self, msg)
        raise MSLTimeoutError('{!r}\n{}'.format(self, msg))

    def read(self, size=None):
        """Read a message from the equipment.

        Parameters
        ----------
        size : :class:`int`, optional
            The number of bytes to read. This method will block until at least
            one of the following conditions are fulfilled:

            1. the :obj:`.read_termination` byte is received (only if
               :obj:`.read_termination` is not :data:`None`).
            2. a timeout occurs (only if :obj:`.timeout` is not :data:`None`). Raises
               :exc:`~msl.equipment.exceptions.MSLTimeoutError` if this occurs.
            3. `size` bytes have been received (only if `size` is not :data:`None`).
            4. :obj:`.max_read_size` bytes have been received. Raises
               :exc:`~msl.equipment.exceptions.MSLConnectionError` if this occurs.

        Returns
        -------
        :class:`str`
            The message from the equipment.
        """
        if size is not None and size > self._max_read_size:
            self.raise_exception('max_read_size is {} bytes, requesting {} bytes'.format(
                self._max_read_size, size))

        message = self._read(size)

        if size is None:
            self.log_debug('%s.read() -> %r', self, message)
        else:
            if len(message) != size:
                self.raise_exception('received {} bytes, requested {} bytes'.format(
                    len(message), size))
            self.log_debug('%s.read(%s) -> %r', self, size, message)

        return message.decode(encoding=self._encoding, errors=self.encoding_errors)

    def _read(self, size):
        """The subclass must override this method."""
        raise NotImplementedError

    def write(self, message, values=None, dtype='<f', header='ieee'):
        """Write a message to the equipment.

        See :func:`~msl.equipment.utils.to_bytes` for more details about the
        `value`, `dtype` and `header` parameters.

        Parameters
        ----------
        message : :class:`str` or :class:`bytes`
            The message to write to the equipment.
        values : :class:`list`, :class:`tuple` or :class:`numpy.ndarray`, optional
            Command-dependent values to append to `message`. Typically, this
            parameter is a 1-d array of numbers, and it is referred to as the
            `block data` for a `SCPI` command.
        dtype : :class:`str` or :class:`numpy.dtype`, optional
            The data type to cast each element in `values` to bytes.
        header : :class:`str`, optional
            The style of header to include before the byte representation
            of `values`.

        Returns
        -------
        :class:`int`
            The number of bytes written.
        """
        if isinstance(message, str):
            message = message.encode(encoding=self._encoding, errors=self._encoding_errors)

        if values:
            message += to_bytes(values, dtype=dtype, header=header)

        if self._write_termination and not message.endswith(self._write_termination):
            message += self._write_termination

        self.log_debug('%s.write(%r)', self, message)

        error = None
        timeout_error = None
        try:
            return self._write(message)
        except socket.timeout:
            # TODO in 3.10 socket.timeout became a deprecated alias of TimeoutError
            #  Want to raise MSLTimeoutError not socket.timeout
            timeout_error = True
        except Exception as e:
            error = e  # avoid a nested exception traceback

        if timeout_error:
            self.raise_timeout()

        self.raise_exception(error)

    def _write(self, message):
        """The subclass must override this method."""
        raise NotImplementedError

    def query(self, message, delay=0.0, size=None, **kwargs):
        """Convenience method for performing a :meth:`write` followed by a :meth:`read`.

        Parameters
        ----------
        message : :class:`str`
            The message to write to the equipment.
        delay : :class:`float`, optional
            The time delay, in seconds, to wait between :meth:`write` and
            :meth:`read` operations.
        size : :class:`int`, optional
            The number of bytes to read.
        **kwargs
            All additional keyword arguments are passed to :meth:`write`.

        Returns
        -------
        :class:`str`
            The response from the equipment.
        """
        self.write(message, **kwargs)
        if delay > 0.0:
            time.sleep(delay)
        return self.read(size=size)

    def _encode_termination(self, termination):
        # convenience method for setting a termination encoding
        if termination is not None:
            try:
                return termination.encode(self._encoding)
            except AttributeError:
                return termination  # `termination` is already encoded
