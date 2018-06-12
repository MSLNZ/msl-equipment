"""
OMEGA iTHX Series Temperature and Humidity Chart Recorder.

This class is compatible with the following model numbers:

* iTHX-W3
* iTHX-D3
* iTHX-SD
* iTHX-M
* iTHX-W
* iTHX-2

"""
import re
import socket
try:
    ConnectionResetError
except NameError:
    # for Python 2.7
    ConnectionResetError = socket.error

from msl.equipment.exceptions import OmegaError
from msl.equipment.connection_tcpip import ConnectionTCPIPSocket
from msl.equipment.resources import register


@register(manufacturer='OMEGA', model='iTHX-[2DMSW][3D]*')
class iTHX(ConnectionTCPIPSocket):

    def __init__(self, record):
        """OMEGA iTHX Series Temperature and Humidity Chart Recorder.

        Do not instantiate this class directly. Use the :meth:`~.EquipmentRecord.connect`
        method to connect to the equipment.

        Parameters
        ----------
        record : :class:`~.EquipmentRecord`
            A record from an :ref:`equipment_database`.
        """
        ConnectionTCPIPSocket.__init__(self, record)
        self.set_exception_class(OmegaError)

    def temperature(self, probe=1, celsius=True):
        """Read the temperature.

        Parameters
        ----------
        probe : :class:`int`, optional
            The probe number to read the temperature of (for iTHX's that contain multiple probes).
        celsius : class:`bool`, optional
            :obj:`True` to return the temperature in celsius, :obj:`False` for fahrenheit.

        Returns
        -------
        :class:`float` or :class:`tuple` of :class:`float`
            The current temperature.
        """
        msg = 'TC' if celsius else 'TF'
        return self._get(msg, probe)

    def humidity(self, probe=1):
        """Read the percent humidity.

        Parameters
        ----------
        probe : :class:`int`, optional
            The probe number to read the humidity of (for iTHX's that contain multiple probes).

        Returns
        -------
        :class:`float` or :class:`tuple` of :class:`float`
            The current percent humidity.
        """
        return self._get('H', probe)

    def dew_point(self, probe=1, celsius=True):
        """Read the dew point.

        Parameters
        ----------
        probe : :class:`int`, optional
            The probe number to read the dew point of (for iTHX's that contain multiple probes).
        celsius : class:`bool`, optional
            :obj:`True` to return the dew point in celsius, :obj:`False` for fahrenheit.

        Returns
        -------
        :class:`float` or :class:`tuple` of :class:`float`
            The current dew point.
        """
        msg = 'D' if celsius else 'DF'
        return self._get(msg, probe)

    def temperature_humidity(self, probe=1, celsius=True):
        """Read the temperature and the humidity.

        Parameters
        ----------
        probe : :class:`int`, optional
            The probe number to read the temperature and humidity of (for iTHX's that contain multiple probes).
        celsius : class:`bool`, optional
            :obj:`True` to return the temperature in celsius, :obj:`False` for fahrenheit.

        Returns
        -------
        :class:`float`
            The current temperature.
        :class:`float`
            The current humidity.
        """
        msg = 'B' if celsius else 'BF'
        # since the returned bytes are of the form b'019.4\r,057.0\r'
        # the _get method would stop reading bytes at the first instance of '\r'
        # therefore, we will specify the number of bytes to read to get both values
        return self._get(msg, probe, size=13)

    def temperature_humidity_dew_point(self, probe=1, celsius=True):
        """Read the temperature, the humidity and the dew point.

        Parameters
        ----------
        probe : :class:`int`, optional
            The probe number to read the temperature, humidity and dew point of
            (for iTHX's that contain multiple probes).
        celsius : class:`bool`, optional
            :obj:`True` to return the temperature and dew point in celsius, :obj:`False` for fahrenheit.

        Returns
        -------
        :class:`float`
            The current temperature.
        :class:`float`
            The current humidity.
        :class:`float`
            The current dew point.
        """
        t, h = self.temperature_humidity(probe=probe, celsius=celsius)
        return t, h, self.dew_point(probe=probe, celsius=celsius)

    def _get(self, message, probe, size=None):
        if not 1 <= probe <= 3:
            self.raise_exception('Invalid probe number, {}. Must be either 1, 2, or 3'.format(probe))

        command = '*SR' + message
        if probe > 1:
            command += str(probe)

        try:
            ret = self.query(command, size=size)
        except ConnectionResetError:
            # for some reason the socket closes if a certain amount of time passes and no
            # messages have been sent. For example, querying the temperature, humidity and
            # dew point every ~60 seconds raised:
            #   [Errno 10054] An existing connection was forcibly closed by the remote host
            self._socket.close()  # officially close it from Python's point of view...
            self._socket = socket.socket(family=self._family, type=self._type)
            self._socket.settimeout(self._timeout)
            ret = self._socket.connect_ex((self._address, self._port))
            if ret == 0:
                return self._get(message, probe, size=size)
            else:
                self.raise_exception('Cannot re-connect to {}'.format(self.equipment_record.connection))
        else:
            values = tuple(float(v) for v in re.split(r'[,;]', ret))
            if len(values) == 1:
                return values[0]
            else:
                return values
