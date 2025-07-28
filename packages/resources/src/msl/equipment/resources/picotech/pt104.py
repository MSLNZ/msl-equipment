"""
Pico Technology PT-104 Platinum Resistance Data Logger.
"""
from __future__ import annotations

from ctypes import POINTER
from ctypes import addressof
from ctypes import byref
from ctypes import c_int16
from ctypes import c_int32
from ctypes import c_int8
from ctypes import c_uint16
from ctypes import c_uint32
from ctypes import string_at
from enum import IntEnum

from msl.loadlib import LoadLibrary

from msl.equipment.connection_sdk import ConnectionSDK
from msl.equipment.constants import IS_WINDOWS
from msl.equipment.exceptions import PicoTechError
from msl.equipment.resources import register
from . import c_enum
from .errors import ERROR_CODES_API
from .errors import PICO_INFO
from .errors import PICO_NOT_FOUND
from .errors import PICO_OK
from .picoscope.enums import PicoScopeInfoApi


class Pt104DataType(IntEnum):
    """
    The allowed data types for a PT-104 Data Logger.
    """
    OFF = 0
    PT100 = 1
    PT1000 = 2
    RESISTANCE_TO_375R = 3
    RESISTANCE_TO_10K = 4
    DIFFERENTIAL_TO_115MV = 5
    DIFFERENTIAL_TO_2500MV = 6
    SINGLE_ENDED_TO_115MV = 7
    SINGLE_ENDED_TO_2500MV = 8
    MAX_DATA_TYPES = 9


def enumerate_units(comm_type='all'):
    """Find PT-104 Platinum Resistance Data Logger's.

    This routine returns a list of all the attached PT-104 devices of the specified
    communication type.

    Note
    ----
    You cannot call this function after you have opened a connection to a Data Logger.

    Parameters
    ----------
    comm_type : :class:`str`, optional
        The communication type used by the PT-104. Can be any of the following values:
        ``'usb'``, ``'ethernet'``, ``'enet'``, ``'all'``

    Returns
    -------
    :class:`list` of :class:`str`
        A list of serial numbers of the PT-104 Data Loggers that were found.
    """
    length = c_uint32(1023)
    details = (c_int8 * length.value)()

    t = comm_type.lower()
    if t == 'usb':
        t_val = 0x00000001
    elif t == 'ethernet' or t == 'enet':
        t_val = 0x00000002
    elif t == 'all':
        t_val = 0xFFFFFFFF
    else:
        raise PicoTechError('Invalid communication type {}'.format(comm_type))

    libtype = 'windll' if IS_WINDOWS else 'cdll'
    sdk = LoadLibrary('usbpt104', libtype)
    result = sdk.lib.UsbPt104Enumerate(byref(details), byref(length), t_val)
    if result != PICO_OK:
        if result == PICO_NOT_FOUND:
            err_name, err_msg = 'PICO_NOT_FOUND', 'Are you sure that a PT-104 is connected to the computer?'
        else:
            err_name, err_msg = ERROR_CODES_API.get(result, ('UnhandledError', 'Error code 0x{:x}'.format(result)))
        raise PicoTechError('Cannot enumerate units.\n{}: {}'.format(err_name, err_msg))
    return string_at(addressof(details)).decode('utf-8').split(',')


@register(manufacturer=r'Pico\s*Tech', model=r'PT[-]?104')
class PT104(ConnectionSDK):

    MIN_WIRES = 2
    MAX_WIRES = 4
    DataType = Pt104DataType

    def __init__(self, record):
        """Uses the PicoTech SDK to communicate with a PT-104 Platinum Resistance Data Logger.

        The :attr:`~msl.equipment.record_types.ConnectionRecord.properties`
        for a PT-104 connection supports the following key-value pairs in the
        :ref:`connections-database`::

            'ip_address': str, The IP address and port number of the PT-104 (e.g., '192.168.1.201:1234')
            'open_via_ip': bool, Whether to connect to the PT-104 by Ethernet. Default is to connect by USB.

        Do not instantiate this class directly. Use the :meth:`~.EquipmentRecord.connect`
        method to connect to the equipment.

        Parameters
        ----------
        record : :class:`~.EquipmentRecord`
            A record from an :ref:`equipment-database`.
        """
        self._handle = None
        libtype = 'windll' if IS_WINDOWS else 'cdll'
        super(PT104, self).__init__(record, libtype)
        self.set_exception_class(PicoTechError)

        self.sdk.UsbPt104OpenUnit.argtypes = [POINTER(c_int16), POINTER(c_int8)]
        self.sdk.UsbPt104OpenUnit.errcheck = self._check
        self.sdk.UsbPt104OpenUnitViaIp.argtypes = [POINTER(c_int16), POINTER(c_int8), POINTER(c_int8)]
        self.sdk.UsbPt104OpenUnitViaIp.errcheck = self._check
        self.sdk.UsbPt104CloseUnit.argtypes = [c_int16]
        self.sdk.UsbPt104CloseUnit.errcheck = self._check
        self.sdk.UsbPt104GetUnitInfo.argtypes = [c_int16, POINTER(c_int8), c_int16, POINTER(c_int16), PICO_INFO]
        self.sdk.UsbPt104GetUnitInfo.errcheck = self._check
        self.sdk.UsbPt104GetValue.argtypes = [c_int16, c_enum, POINTER(c_int32), c_int16]
        self.sdk.UsbPt104GetValue.errcheck = self._check
        self.sdk.UsbPt104IpDetails.argtypes = [c_int16, POINTER(c_int16), POINTER(c_int8),
                                               POINTER(c_uint16), POINTER(c_uint16), c_enum]
        self.sdk.UsbPt104IpDetails.errcheck = self._check
        self.sdk.UsbPt104SetChannel.argtypes = [c_int16, c_enum, c_enum, c_int16]
        self.sdk.UsbPt104SetChannel.errcheck = self._check
        self.sdk.UsbPt104SetMains.argtypes = [c_int16, c_uint16]
        self.sdk.UsbPt104SetMains.errcheck = self._check

        self._IP_ADDRESS = record.connection.properties.get('ip_address', None)
        if self._IP_ADDRESS and record.connection.properties.get('open_via_ip', False):
            self.open_via_ip(self._IP_ADDRESS)
        else:
            self.open()

    def _check(self, result, func, arguments):
        self.log_errcheck(result, func, arguments)
        if result != PICO_OK:
            conn = self.equipment_record.connection
            error_name, msg = ERROR_CODES_API.get(result, ('UnhandledError', 'Error code 0x{:x}'.format(result)))
            error_msg = msg.format(model=conn.model, serial=conn.serial)
            self.raise_exception('{}: {}'.format(error_name, error_msg))

    def disconnect(self):
        """Disconnect from the PT-104 Data Logger."""
        if self._handle:
            self.sdk.UsbPt104CloseUnit(self._handle)
            self.log_debug('Disconnected from %s', self.equipment_record.connection)
            self._handle = None

    def get_ip_details(self):
        """Reads the IP details of the PT-104 Data Logger.

        Returns
        -------
        :class:`dict`
            The IP details.
        """
        enabled = c_int16()
        address = c_int8(127)
        length = c_uint16(address.value)
        port = c_uint16()
        self.sdk.UsbPt104IpDetails(self._handle, byref(enabled), byref(address), byref(length), byref(port), 0)
        return {
            'enabled': bool(enabled.value),
            'ip_address': string_at(addressof(address)).decode(),
            'port': port.value
        }

    def get_unit_info(self, info=None, include_name=True):
        """Retrieves information about the PT-104 Data Logger.

        If the device fails to open, or no device is opened only the driver version is available.

        Parameters
        ----------
        info : :class:`~.enums.PicoScopeInfoApi`, optional
            An enum value or member name. If :data:`None` then request all information from the PT-104.
        include_name : :class:`bool`, optional
            If :data:`True` then includes the enum member name as a prefix.
            For example, returns ``'CAL_DATE: 09Aug16'`` if `include_name` is :data:`True` else ``'09Aug16'``.

        Returns
        -------
        :class:`str`
            The requested information from the PT-104 Data Logger.
        """
        if info is None:
            values = [PicoScopeInfoApi(i) for i in range(7)]  # only the first 7 items are supported by the SDK
        else:
            values = [self.convert_to_enum(info, PicoScopeInfoApi, to_upper=True)]

        string = c_int8(127)
        required_size = c_int16()

        msg = ''
        for value in values:
            name = '{}: '.format(value.name) if include_name else ''
            self.sdk.UsbPt104GetUnitInfo(self._handle, byref(string), string.value, byref(required_size), value)
            msg += '{}{}\n'.format(name, string_at(addressof(string)).decode())
        return msg[:-1]

    def get_value(self, channel, filtered=False):
        """Get the most recent reading for the specified channel.

        Once you open the driver and define some channels, the driver begins to take
        continuous readings from the PT-104 Data Logger.

        The scaling of measurements is as follows:

        +-----------------------+----------------------+
        |         Range         |     Scaling          |
        +=======================+======================+
        | Temperature           | value * 1/1000 deg C |
        +-----------------------+----------------------+
        | Voltage (0 to 2.5 V)  | value * 10 nV        |
        +-----------------------+----------------------+
        | Voltage (0 to 115 mV) | value * 1 nV         |
        +-----------------------+----------------------+
        | Resistance            | value * 1 mOhm       |
        +-----------------------+----------------------+

        Parameters
        ----------
        channel : :class:`int`
            The number of the channel to read, from 1 to 4 in differential
            mode or 1 to 8 in single-ended mode.
        filtered : :class:`bool`, optional
            If set to :data:`True`, the driver returns a low-pass filtered value
            of the temperature. The time constant of the filter depends on the
            channel parameters as set by :meth:`.set_channel`, and on how many
            channels are active.

        Returns
        -------
        :class:`float`
            The latest reading for the specified channel.
        """
        value = c_int32()
        self.sdk.UsbPt104GetValue(self._handle, channel, byref(value), int(filtered))
        return value.value

    def open(self):
        """Open the connection to the PT-104 via USB."""
        if self._handle:
            self.disconnect()

        handle = c_int16()
        s = self.equipment_record.serial
        serial = (c_int8 * len(s)).from_buffer_copy(s.encode())
        self.sdk.UsbPt104OpenUnit(byref(handle), serial)
        self._handle = handle.value

    def open_via_ip(self, address=None):
        """Open the connection to the PT-104 via ETHERNET.

        Parameters
        ----------
        address : :class:`str`, optional
            The IP address and port number to use to connect to the PT-104.
            For example, ``'192.168.1.201:1234'``. If :data:`None` then uses the
            ``'ip_address'`` value of the :attr:`~msl.equipment.record_types.ConnectionRecord.properties`
        """
        if self._handle:
            self.disconnect()

        handle = c_int16()
        ip = self._IP_ADDRESS if address is None else address
        if ip is None:
            self.raise_exception('You must either specify the IP address in the '
                                 'Connection Database or when calling this function')

        address = (c_int8 * len(ip)).from_buffer_copy(ip.encode())
        self.sdk.UsbPt104OpenUnitViaIp(byref(handle), None, address)
        self._handle = handle.value

    def set_channel(self, channel, data_type, num_wires):
        """Configure a single channel of the PT-104 Data Logger.

        The fewer channels selected, the more frequently they will be updated. Measurement
        takes about 1 second per active channel.

        If a call to the :meth:`.set_channel` method has a data type of single-ended, then the specified
        channel's 'sister' channel is also enabled. For example, enabling 3 also enables 7.

        Parameters
        ----------
        channel : :class:`int`
            The channel you want to set the details for. It should be between 1 and 4
            if using single-ended inputs in voltage mode.
        data_type : :attr:`.DataType`
            The type of reading you require. Can be an enum value or member name.
        num_wires : :class:`int`
            The number of wires the PT100 or PT1000 sensor has (2, 3 or 4)
        """
        typ = self.convert_to_enum(data_type, Pt104DataType, to_upper=True)
        if num_wires < self.MIN_WIRES or num_wires > self.MAX_WIRES:
            self.raise_exception('The num_wires value is {}. It must be 2, 3 or 4.'.format(num_wires))
        self.sdk.UsbPt104SetChannel(self._handle, channel, typ, num_wires)

    def set_ip_details(self, enabled, ip_address=None, port=None):
        """Writes the IP details to the device.

        Parameters
        ----------
        enabled : :class:`bool`
            Whether to enable or disable Ethernet communication for this device.
        ip_address : :class:`str`, optional
            The new IP address. If :data:`None` then do not change the IP address.
        port : :class:`int`, optional
            The new port number. If :data:`None` then do not change the port number.
        """
        if ip_address is None or port is None:
            details = self.get_ip_details()
            if ip_address is None:
                ip_address = details['ip_address']
            if port is None:
                port = details['port']

        enabled = c_int16(bool(enabled))
        address = (c_int8 * len(ip_address)).from_buffer_copy(ip_address.encode())
        length = c_uint16(len(ip_address))
        port = c_uint16(port)
        self.sdk.UsbPt104IpDetails(self._handle, enabled, address, length, port, 1)

    def set_mains(self, hertz):
        """Inform the driver of the local mains (line) frequency.

        This helps the driver to filter out electrical noise.

        Parameters
        ----------
        hertz : :class:`int`
            Either 50 or 60.
        """
        if hertz not in {50, 60}:
            self.raise_exception('The mains frequency must be 50 or 60. Got {}'.format(hertz))
        self.sdk.UsbPt104SetMains(self._handle, 0 if hertz == 50 else 1)
