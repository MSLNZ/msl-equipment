"""
Uses Prologix_ hardware to establish a connection to the equipment.

.. _Prologix: https://prologix.biz/
"""
from .connection import Connection
from .connection_serial import ConnectionSerial
from .connection_socket import ConnectionSocket
from .constants import REGEX_PROLOGIX


class ConnectionPrologix(Connection):

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

            'eoi': int, 0 or 1
            'eos': int, 0, 1, 2 or 3
            'eot_char': int, an ASCII value less than 256
            'eot_enable': int, 0 or 1
            'mode': int, 0 or 1 [default: 1]
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

        info = ConnectionPrologix.parse_address(record.connection.address)
        if info is None:
            self.raise_exception('Invalid Prologix address {!r}'.format(record.connection.address))

        pad = info['pad']
        if pad < 0 or pad > 30:
            self.raise_exception('Invalid primary address {}'.format(pad))

        sad = info['sad']
        if sad is not None:
            if sad < 96 or sad > 126:
                self.raise_exception('Invalid secondary address {}'.format(sad))
            self._addr = '++addr {} {}'.format(pad, sad)
        else:
            self._addr = '++addr {}'.format(pad)

        self._query_auto = True
        self._controller_name = info['name']

        try:
            self._controller = ConnectionPrologix.controllers[self._controller_name]
        except KeyError:
            self._controller = info['class'](record)
            ConnectionPrologix.controllers[self._controller_name] = self._controller

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
        """:class:`str`: The encoding that is used for :meth:`.read` and :meth:`.write` operations."""
        return self._controller.encoding

    @encoding.setter
    def encoding(self, encoding):
        self._controller.encoding = encoding

    @property
    def encoding_errors(self):
        """:class:`str`: The error handling scheme to use when encoding and decoding messages.

        For example: `strict`, `ignore`, `replace`, `xmlcharrefreplace`, `backslashreplace`
        """
        return self._controller.encoding_errors

    @encoding_errors.setter
    def encoding_errors(self, value):
        self._controller.encoding_errors = value

    @property
    def read_termination(self):
        """:class:`bytes` or :data:`None`: The termination character sequence
        that is used for the :meth:`.read` method.

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
        is appended to :meth:`.write` messages.

        If you set the `write_termination` to be equal to a variable of type
        :class:`str` it will automatically be encoded.
        """
        return self._controller.write_termination

    @write_termination.setter
    def write_termination(self, termination):
        self._controller.write_termination = termination

    @property
    def max_read_size(self):
        """:class:`int`: The maximum number of bytes that can be :meth:`.read`."""
        return self._controller.max_read_size

    @max_read_size.setter
    def max_read_size(self, size):
        self._controller.max_read_size = size

    @property
    def timeout(self):
        """:class:`float` or :data:`None`: The timeout, in seconds, for :meth:`.read` and :meth:`.write` operations."""
        return self._controller.timeout

    @timeout.setter
    def timeout(self, value):
        self._controller.timeout = value

    @property
    def rstrip(self):
        """:class:`bool`: Whether to remove trailing whitespace from :meth:`.read` messages."""
        return self._controller.rstrip

    @rstrip.setter
    def rstrip(self, value):
        self._controller.rstrip = value

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

    def read(self, **kwargs):
        """Read a message from the equipment.

        Parameters
        ----------
        **kwargs
            All keyword arguments are passed to
            :meth:`~msl.equipment.connection_message_based.ConnectionMessageBased.read`.

        Returns
        -------
        :class:`str`, :class:`bytes` or :class:`~numpy.ndarray`
            The message from the equipment. If `dtype` is specified, then the
            message is returned as an :class:`~numpy.ndarray`, if `decode` is
            :data:`True` then the message is returned as a :class:`str`,
            otherwise the message is returned as :class:`bytes`.
        """
        self._ensure_gpib_address_selected()
        return self._controller.read(**kwargs)

    def write(self, message, **kwargs):
        """Write a message to the equipment.

        Parameters
        ----------
        message : :class:`str` or :class:`bytes`
            The message to write to the equipment.
        **kwargs
            All keyword arguments are passed to
            :meth:`~msl.equipment.connection_message_based.ConnectionMessageBased.write`.

        Returns
        -------
        :class:`int`
            The number of bytes written.
        """
        self._ensure_gpib_address_selected()
        return self._controller.write(message, **kwargs)

    def query(self, message, **kwargs):
        """Convenience method for performing a :meth:`.write` followed by a :meth:`.read`.

        Parameters
        ----------
        message : :class:`str` or :class:`bytes`
            The message to write to the equipment.
        **kwargs
            All keyword arguments are passed to
            :meth:`~msl.equipment.connection_message_based.ConnectionMessageBased.query`.

        Returns
        -------
        :class:`str`, :class:`bytes` or :class:`~numpy.ndarray`
            The message from the equipment. If `dtype` is specified, then the
            message is returned as an :class:`~numpy.ndarray`, if `decode` is
            :data:`True` then the message is returned as a :class:`str`,
            otherwise the message is returned as :class:`bytes`.
        """
        if self._query_auto:
            self._controller.write(b'++auto 1')

        reply = self._controller.query(message, **kwargs)

        if self._query_auto:
            self._controller.write(b'++auto 0')

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

    @staticmethod
    def parse_address(address):
        """Parse the address to determine the connection class and the GPIB address.

        Parameters
        ----------
        address : :class:`str`
            The address of a :class:`~msl.equipment.record_types.ConnectionRecord`.

        Returns
        -------
        :class:`dict` or :data:`None`
            If `address` is valid for a Prologix connection then the key-value pairs are:

            * class, :class:`.ConnectionSocket` or :class:`.ConnectionSerial`
                The underlying connection class to use (not instantiated).
            * name, :class:`str`
                The name of the connection class.
            * pad, :class:`int`
                The primary GPIB address.
            * sad, :class:`int` or :data:`None`
                The secondary GPIB address.

            otherwise :data:`None` is returned.
        """
        match = REGEX_PROLOGIX.match(address)
        if match is None:
            return

        d = match.groupdict()
        cls = ConnectionSocket if d['port'] else ConnectionSerial
        sad = None if d['sad'] is None else int(d['sad'])
        return {'class': cls, 'name': d['name'], 'pad': int(d['pad']), 'sad': sad}

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


def find_prologix(hosts=None, timeout=1):
    """Find all Prologix ENET-GPIB devices that are on the network.

    To resolve the MAC address of a Prologix device, the ``arp`` program
    must be installed. On Linux, install ``net-tools``. On Windows and macOS,
    ``arp`` should already be installed.

    Parameters
    ----------
    hosts : :class:`list` of :class:`str`, optional
        The IP address(es) on the computer to use to look for Prologix
        ENET-GPIB devices. If not specified, then use all network interfaces.
    timeout : :class:`float`, optional
        The maximum number of seconds to wait for a reply.

    Returns
    -------
    :class:`dict`
        The information about the Prologix ENET-GPIB devices that were found.
    """
    import re
    import socket
    import subprocess
    import sys
    import threading

    if not hosts:
        from .utils import ipv4_addresses
        all_ips = ipv4_addresses()
    else:
        all_ips = hosts

    if sys.platform == 'win32':
        mac_regex = re.compile(r'([0-9a-fA-F]{2}(?:-[0-9a-fA-F]{2}){5})')
        arp_option = ['-a']
    elif sys.platform == 'darwin':
        # the 'arp' command on macOS prints the MAC address
        # using %x instead of %02x, so leading 0's are missing
        mac_regex = re.compile(r'([0-9a-fA-F]{1,2}(?::[0-9a-fA-F]{1,2}){5})')
        arp_option = ['-n']
    else:
        mac_regex = re.compile(r'([0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5})')
        arp_option = ['-n']

    version_regex = re.compile(r'(\d{2}(?:\.\d{2}){3})')

    def check(host):
        host_str = '{}.{}.{}.{}'.format(*host)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        sock.settimeout(timeout)
        if sock.connect_ex((host_str, 1234)) != 0:
            sock.close()
            return

        sock.sendall(b'++ver\r\n')
        try:
            reply = sock.recv(256)
        except socket.timeout:
            sock.close()
            return

        if not reply.startswith(b'Prologix'):
            sock.close()
            return

        description = 'Prologix ENET-GPIB'

        addresses = set()
        addresses.add(host_str)

        # determine the firmware version number
        match = version_regex.search(reply.decode())
        if match:
            description += ', version={}'.format(match.group(1))

        # determine the MAC address
        try:
            pid = subprocess.Popen(['arp'] + arp_option + [host_str],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except OSError:
            pass
        else:
            stdout, stderr = pid.communicate()
            match = mac_regex.search(stdout.decode())
            if match:
                mac = match.groups()[0]
                if sys.platform == 'darwin':
                    # the 'arp' command on macOS prints the MAC address
                    # using %x instead of %02x, so leading 0's are missing
                    bits = []
                    for bit in mac.split(':'):
                        if len(bit) == 1:
                            bits.append('0'+bit)
                        else:
                            bits.append(bit)
                    mac = ':'.join(bits)

                description += ', MAC address={}'.format(mac)
                addresses.add('prologix-' + mac.replace(':', '-'))

        devices[host] = {
            'description': description,
            'addresses': ['Prologix::{}::1234::<GPIB address>'.format(a) for a in sorted(addresses)]
        }

        sock.close()

    ips = []
    for ip in all_ips:
        ip_split = ip.split('.')
        subnet = list(int(item) for item in ip_split[:3])
        ips.extend(tuple(subnet + [i]) for i in range(2, 255))

    # TODO use asyncio instead of threading when dropping Python 2.7 support

    devices = {}
    threads = [threading.Thread(target=check, args=(ip,)) for ip in ips]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return dict((k, devices[k]) for k in sorted(devices))
