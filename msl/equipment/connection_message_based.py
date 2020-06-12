"""
Base class for equipment that use message-based communication.
"""
import time

from .connection import Connection
from .exceptions import MSLTimeoutError
from .constants import LF, CR


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
        self._encoding_errors = 'strict'
        self._read_termination = ConnectionMessageBased.LF
        self._write_termination = ConnectionMessageBased.CR + ConnectionMessageBased.LF
        self._max_read_size = 2 ** 16
        self._timeout = None

    @property
    def encoding(self):
        """:class:`str`: The encoding that is used for :meth:`read` and :meth:`write` operations."""
        return self._encoding

    @encoding.setter
    def encoding(self, encoding):
        """Set the encoding to use for :meth:`read` and :meth:`write` operations."""
        _ = 'test encoding'.encode(encoding).decode(encoding)

        # re-encoding the read/write termination values ensure that the termination
        # sequence can be encoded using the new encoding
        if self._read_termination is not None:
            read_term = self._read_termination.decode(self._encoding)
        if self._write_termination is not None:
            write_term = self._write_termination.decode(self._encoding)

        self._encoding = encoding

        if self._read_termination is not None:
            self.read_termination = read_term
        if self._write_termination is not None:
            self.write_termination = write_term

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
        self._read_termination = self._set_termination_encoding(termination)

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
        self._write_termination = self._set_termination_encoding(termination)

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
        """:class:`float` or :data:`None`: The timeout, in seconds, for :meth:`read` and :meth:`write` operations."""
        return self._timeout

    @timeout.setter
    def timeout(self, value):
        self._timeout = value

    def raise_timeout(self, append_msg=''):
        """Raise a :exc:`~.exceptions.MSLTimeoutError`.

        Parameters
        ----------
        append_msg : :class:`str`, optional
            A message to append to the generic timeout message.
        """
        msg = 'Timeout occurred after {} seconds'.format(self.timeout)
        if append_msg:
            msg += str(append_msg)
        self.log_error('{!r} {}'.format(self, msg))
        raise MSLTimeoutError('{!r}\n{}'.format(self, msg))

    def read(self, size=None):
        """Read the response from the equipment.

        .. attention::
           The subclass must override this method.

        Parameters
        ----------
        size : :class:`int`, optional
            The number of bytes to read.

        Returns
        -------
        :class:`str`
            The response from the equipment.
        """
        raise NotImplementedError

    def write(self, msg):
        """Write a message to the equipment.

        .. attention::
           The subclass must override this method.

        Parameters
        ----------
        msg : :class:`str`
            The message to write to the equipment.

        Returns
        -------
        :class:`int`
            The number of bytes written.
        """
        raise NotImplementedError

    def query(self, msg, delay=0.0, size=None):
        """Convenience method for performing a :meth:`write` followed by a :meth:`read`.

        Parameters
        ----------
        msg : :class:`str`
            The message to write to the equipment.
        delay : :class:`float`, optional
            The time delay, in seconds, to wait between :meth:`write` and
            :meth:`read` operations.
        size : :class:`int`, optional
            The number of bytes to read.

        Returns
        -------
        :class:`str`
            The response from the equipment.
        """
        self.write(msg)
        if delay > 0.0:
            time.sleep(delay)
        return self.read(size=size)

    def _set_timeout_value(self, value):
        # convenience method for setting the timeout value
        if value is not None:
            self._timeout = float(value)
            if self._timeout == 0:
                self._timeout = None
            elif self._timeout < 0:
                raise ValueError('Not a valid timeout value: {}'.format(value))
        else:
            self._timeout = None

    def _set_termination_encoding(self, termination):
        # convenience method for setting the termination encoding
        try:
            return termination.encode(self._encoding)
        except AttributeError:
            return termination  # `termination` is already encoded

    def _encode(self, message):
        # convenience method for preparing the message for a write operation
        if isinstance(message, bytes):
            data = message
        else:
            data = message.encode(encoding=self._encoding, errors=self._encoding_errors)
        if self._write_termination is not None and not data.endswith(self._write_termination):
            data += self._write_termination
        self.log_debug('{}.write({!r})'.format(self, data))
        return data

    def _decode(self, size, message):
        # convenience method for processing the message from a read operation
        if size is None:
            self.log_debug('{}.read() -> {!r}'.format(self, message))
        else:
            self.log_debug('{}.read({}) -> {!r}'.format(self, size, message))
        return message.decode(encoding=self._encoding, errors=self._encoding_errors)
