"""
Load the 32-bit ``OL756SDKActiveXCtrl`` library using :ref:`msl-loadlib-welcome`.
"""
import os

from msl.loadlib import (
    Client64,
    Server32Error,
    ConnectionTimeoutError,
)

from msl.equipment.resources import register
from msl.equipment.connection import Connection
from msl.equipment.exceptions import OptronicLaboratoriesError


@register(manufacturer=r'Optronic Laboratories', model=r'756')
class OL756(Connection):

    def __init__(self, record=None):
        """A wrapper around the the ``OL756SDKActiveXCtrl`` library.

        .. attention::

           See the :class:`.ol756ocx_32.OL756` class for all available methods.

        This class can be used with either a 32- or 64-bit Python interpreter
        to call the 32-bit functions in the ``OL756SDKActiveXCtrl`` library.

        The :attr:`~msl.equipment.record_types.ConnectionRecord.properties`
        for an OL756 connection supports the following key-value pairs in the
        :ref:`connections-database`::

            'mode': int, connection mode (0=RS232, 1=USB) [default: 1]
            'com_port': int, the COM port number (RS232 mode only) [default: 1]

        Do not instantiate this class directly. Use the :meth:`~.EquipmentRecord.connect`
        method to connect to the equipment.

        Parameters
        ----------
        record : :class:`~.EquipmentRecord`
            A record from an :ref:`equipment-database`.
        """
        super(OL756, self).__init__(record)
        self.set_exception_class(OptronicLaboratoriesError)

        self._client = None
        error = None
        try:
            self._client = Client64(
                os.path.join(os.path.dirname(__file__), 'ol756ocx_32.py'),
                prog_id=record.connection.address[5:],
                mode=record.connection.properties.get('mode', 1),
                com_port=record.connection.properties.get('com_port', 1),
            )
        except ConnectionTimeoutError as e:
            error = e.reason

        if error:
            self.raise_exception('Cannot initialize the OL756 SDK.\n{}'.format(error))

        self._request32 = self._client.request32

        if self._request32('mode') == -1:
            self.disconnect()
            self.raise_exception(
                'Cannot connect to the OL756 spectroradiometer. '
                'Is it turned on and connected to the computer?'
            )

        self.log_debug('Connected to {}'.format(record.connection))

    def __getattr__(self, attr):
        def send(*args, **kwargs):
            try:
                self.log_debug('{}.{}({}, {})'.format(self.__class__.__name__, attr, args, kwargs))
                return self._request32(attr, *args, **kwargs)
            except Server32Error as e:
                error = e
            self.raise_exception(error)
        return send

    def disconnect(self):
        """Disconnect from the OL756 spectroradiometer."""
        if not self._client:
            return

        try:
            self._request32('connect_to_ol756', -1)
        except:
            pass

        try:
            stdout, stderr = self._client.shutdown_server32()
            stdout.close()
            stderr.close()
        except:
            pass

        self._client = None
        self.log_debug('Disconnected from {}'.format(self.equipment_record.connection))
