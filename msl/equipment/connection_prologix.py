"""
Uses Prologix_ hardware to establish a connection to the equipment.

.. _Prologix: https://prologix.biz/
"""
from .connection_message_based import ConnectionMessageBased
from .connection_socket import ConnectionSocket
from .connection_serial import ConnectionSerial


def _parse_address(address):
    """Parse the address to determine the connection class and GPIB address.

    Parameters
    ----------
    address : :class:`str`
        A :class:`~msl.equipment.record_types.ConnectionRecord` address.

    Returns
    -------
    :class:`ConnectionSocket` or :class:`ConnectionSerial` or :data:`None`
        The underlying connection class to use (not instantiated).
    :class:`str` or :data:`None`
        The serial port or IP address.
    :class:`str` or :data:`None`
        The primary GPIB address.
    :class:`str` or :data:`None`
        The secondary GPIB address.
    """
    cls, name, primary, secondary = None, None, None, None

    addr_split = address.split('::')

    if '::1234::' in address:  # the TCP port is specified
        cls = ConnectionSocket
        name, _ = ConnectionSocket.host_and_port_from_address(address)
        if len(addr_split) == 4:
            primary = addr_split[-1]
        elif len(addr_split) == 5:
            primary, secondary = addr_split[-2], addr_split[-1]

    port = ConnectionSerial.port_from_address(address)
    if port is not None:
        cls = ConnectionSerial
        name = port
        if len(addr_split) == 3:
            primary = addr_split[-1]
        elif len(addr_split) == 4:
            primary, secondary = addr_split[-2], addr_split[-1]

    return cls, name, primary, secondary


class ConnectionPrologix(ConnectionMessageBased):

    controllers = {}
    """A :class:`dict` of all Prologix_ Controllers that are being used to communicate with GPIB devices."""

    selected_addresses = {}
    """A :class:`dict` of the currently-selected GPIB address for all Prologix_ Controllers."""

    def __init__(self, record):
        """Uses Prologix_ hardware to establish a connection to the equipment.

        For the GPIB-ETHERNET Controller, the format of the
        :attr:`~msl.equipment.record_types.ConnectionRecord.address` is
        ``Prologix::HOST::1234::PAD[::SAD]``, where PAD (Primary Address)
        is a decimal value between 0 and 30 and SAD (Secondary Address) is a decimal
        value between 96 and 126. SAD is optional. For example,
        ``Prologix::192.168.1.110::1234::6`` or ``Prologix::192.168.1.110::1234::6::96``.

        For the GPIB-USB Controller, the format of the
        :attr:`~msl.equipment.record_types.ConnectionRecord.address` is
        ``Prologix::PORT::PAD[::SAD]``, where PAD (Primary Address)
        is a decimal value between 0 and 30 and SAD (Secondary Address) is a decimal
        value between 96 and 126. SAD is optional. For example,
        ``Prologix::COM3::6`` or ``Prologix::/dev/ttyUSB0::6::112``.

        The :attr:`~msl.equipment.record_types.ConnectionRecord.properties`
        for a Prologix_ connection supports the following key-value pairs in the
        :ref:`connections-database` and any of the key-value pairs supported by
        :class:`.ConnectionSerial` or :class:`.ConnectionSocket` (depending on
        whether a GPIB-USB or a GPIB-ETHERNET Controller is used)::

            'mode': int, 0 or 1 [default: 1]
            'eoi': int, 0 or 1
            'eos': int, 0, 1, 2 or 3
            'eot_enable': int, 0 or 1
            'eot_char': int, an ASCII value less than 256
            'read_tmo_ms': int, a timeout value between 1 and 3000 milliseconds

        The :attr:`~msl.equipment.record_types.ConnectionRecord.backend`
        value must be equal to :attr:`~msl.equipment.constants.Backend.MSL`
        to use this class for the communication system. This is achieved by setting the
        value in the **Backend** field for a connection record in the :ref:`connections-database`
        to be ``MSL``.

        Do not instantiate this class directly. Use the
        :meth:`~.EquipmentRecord.connect` method to connect to the equipment.

        Parameters
        ----------
        record : :class:`.EquipmentRecord`
            A record from an :ref:`equipment-database`.
        """
        super(ConnectionPrologix, self).__init__(record)

        cls, name, primary, secondary = _parse_address(record.connection.address)

        if cls is None:
            self.raise_exception('Invalid address {!r}'.format(record.connection.address))

        pad = int(primary)
        if pad < 0 or pad > 30:
            self.raise_exception('Invalid primary address {}'.format(primary))

        if secondary:
            sad = int(secondary)
            if sad < 96 or sad > 126:
                self.raise_exception('Invalid secondary address {}'.format(sad))
            self._addr = '++addr {} {}'.format(pad, sad)
        else:
            self._addr = '++addr {}'.format(pad)

        self._query_auto = True
        self._controller_name = name

        try:
            self._controller = ConnectionPrologix.controllers[name]
        except KeyError:
            self._controller = cls(record)
            ConnectionPrologix.controllers[name] = self._controller

        props = record.connection.properties

        # default is CONTROLLER mode
        self._controller.write('++mode {}'.format(props.get('mode', 1)))

        # set the options provided by the user
        for option in ['eoi', 'eos', 'eot_enable', 'eot_char', 'read_tmo_ms']:
            value = props.get(option, None)
            if value is not None:
                self._controller.write('++{} {}'.format(option, value))

        # set this equipment record as the currently-selected GPIB address for the Controller
        self._select_gpib_address()

    @property
    def encoding(self):
        """:class:`str`: The encoding that is used for :meth:`read` and :meth:`write` operations."""
        return self._controller.encoding

    @encoding.setter
    def encoding(self, encoding):
        self._controller.encoding = encoding

    @property
    def read_termination(self):
        """:class:`bytes` or :data:`None`: The termination character sequence
        that is used for the :meth:`read` method.

        Reading stops when the equipment stops sending data or the `read_termination`
        character sequence is detected. If you set the `read_termination` to be equal
        to a variable of type :class:`str` it will automatically be encoded.
        """
        return self._controller.read_termination

    @read_termination.setter
    def read_termination(self, termination):
        self._controller.read_termination = termination

    @property
    def write_termination(self):
        """:class:`bytes` or :data:`None`: The termination character sequence that
        is appended to :meth:`write` messages.

        If you set the `write_termination` to be equal to a variable of type
        :class:`str` it will automatically be encoded.
        """
        return self._controller.write_termination

    @write_termination.setter
    def write_termination(self, termination):
        self._controller.write_termination = termination

    @property
    def max_read_size(self):
        """:class:`int`: The maximum number of bytes that can be :meth:`read`."""
        return self._controller.max_read_size

    @max_read_size.setter
    def max_read_size(self, size):
        self._controller.max_read_size = size

    @property
    def timeout(self):
        """:class:`float` or :data:`None`: The timeout, in seconds, for :meth:`read` and :meth:`write` operations."""
        return self._controller.timeout

    @timeout.setter
    def timeout(self, value):
        self._controller.timeout = value

    @property
    def controller(self):
        """:class:`.ConnectionSerial` or :class:`.ConnectionSocket`:
        The connection to the Prologix_ Controller for this equipment.

        Depends on whether a GPIB-USB or a GPIB-ETHERNET Controller
        is being used to communicate with the equipment.
        """
        return self._controller

    def disconnect(self):
        """
        Calling this method does not close the underlying :class:`.ConnectionSerial`
        or :class:`.ConnectionSocket` connection to the Prologix_ Controller since
        the connection to the Prologix_ Controller may still be required to send
        messages to other devices via GPIB.

        Calling this method sets the :attr:`.controller` to be :data:`None`.
        """
        self._controller = None

    def group_execute_trigger(self, *addresses):
        """Send the Group Execute Trigger command to equipment at the specified addresses.

        Up to 15 addresses may be specified. If no address is specified then the
        Group Execute Trigger command is issued to the currently-addressed equipment.

        Parameters
        ----------
        addresses
            The primary (and optional secondary) GPIB addresses. If a secondary
            address is specified then it must follow its corresponding primary address.
            For example:

            * group_execute_trigger(1, 11, 17) :math:`\\rightarrow` primary, primary, primary

            * group_execute_trigger(3, 96, 12, 21) :math:`\\rightarrow` primary, secondary, primary, primary

        Returns
        -------
        :class:`int`
            The number of bytes written.
        """
        command = '++trg'
        if addresses:
            command += ' ' + ' '.join(str(a) for a in addresses)
        return self._controller.write(command)

    def read(self, size=None):
        """Read the response from the equipment.

        Parameters
        ----------
        size : :class:`int`, optional
            The number of bytes to read.

        Returns
        -------
        :class:`str`
            The response from the equipment.
        """
        self._ensure_gpib_address_selected()
        return self._controller.read(size=size)

    def write(self, msg):
        """Write a message to the equipment.

        Parameters
        ----------
        msg : :class:`str`
            The message to write to the equipment.

        Returns
        -------
        :class:`int`
            The number of bytes written.
        """
        self._ensure_gpib_address_selected()
        return self._controller.write(msg)

    def query(self, msg, delay=0.0, size=None):
        """Convenience method for performing a :meth:`.write` followed by a :meth:`.read`.

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
        if self._query_auto:
            self._controller.write('++auto 1')

        reply = super(ConnectionPrologix, self).query(msg, delay=delay, size=size)

        if self._query_auto:
            self._controller.write('++auto 0')

        return reply

    @property
    def query_auto(self):
        """:class:`bool`: Whether to send ``++auto 1`` before and ``++auto 0``
        after a :meth:`.query` to the Prologix_ Controller.
        """
        return self._query_auto

    @query_auto.setter
    def query_auto(self, enabled):
        self._query_auto = bool(enabled)

    def version(self):
        """Get the version of the Prologix_ Controller.

        Returns
        -------
        :class:`str`
            The type of the Controller (GPIB-USB or GPIB-ETHERNET) and
            the version of the firmware.
        """
        return self._controller.query('++ver').rstrip()

    def _ensure_gpib_address_selected(self):
        """
        Make sure that the connection to the equipment for this instance of the
        ConnectionPrologix class is the equipment that the message will be sent to.
        """
        if self._addr != ConnectionPrologix.selected_addresses[self._controller_name]:
            self._select_gpib_address()

    def _select_gpib_address(self):
        """
        Set the currently-selected GPIB address for a Controller to be the GPIB
        address of the equipment that this instance of the ConnectionPrologix class
        belongs to.
        """
        ConnectionPrologix.selected_addresses[self._controller_name] = self._addr
        self._controller.write(self._addr)
