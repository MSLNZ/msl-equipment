"""
IsoTech milliK Precision Thermometer, with any number of connected millisKanners
"""
from __future__ import annotations
import re

from msl.equipment.resources import register
from msl.equipment.exceptions import IsotechError
from msl.equipment.connection_serial import ConnectionSerial


@register(manufacturer=r'Iso.*Tech.*', model=r'milli.*K.*', flags=re.IGNORECASE)
class MilliK(ConnectionSerial):

    def __init__(self, record) -> None:
        """IsoTech MilliK Precision Thermometer.

        Do not instantiate this class directly. Use the :meth:`~.EquipmentRecord.connect`
        method to connect to the equipment.

        Parameters
        ----------
        record : :class:`~.EquipmentRecord`
            A record from an :ref:`equipment-database`.
        """
        super(MilliK, self).__init__(record)

        self.set_exception_class(IsotechError)

        self._connected_devices = None
        self._num_devices = 0
        self._channel_numbers = []

        self.detect_channel_numbers()
        self.write('millik:remote')  # use REMOTE mode to speed up communications

    @property
    def connected_devices(self) -> list:
        """A list of information about the connected devices, as returned from the instrument(s) by the *IDN? command:
        manufacturuer, model, serial number, firmware version
        e.g. ['Isothermal Technology,millisKanner,21-P2593,2.01', 'Isothermal Technology,milliK,21-P2460,4.0.0']
        """
        return self._connected_devices

    @property
    def num_devices(self) -> int:
        """The number of connected devices"""
        return self._num_devices

    @property
    def channel_numbers(self) -> list:
        """A list of available channel numbers: e.g. [1, 2] for a single milliK,
        or [1, 10, 11, 12, 13, 14, 15, 16, 17] for a milliK connected to a single millisKanner, etc"""
        return self._channel_numbers

    def detect_channel_numbers(self) -> tuple[list, int, list]:
        """Find the number of millisKanners connected, if any, and hence the valid channel numbers.
        Up to 4 millisKanners can be connected to a single milliK.

        Returns
        -------
        A list of the connected_devices, an integer for num_devices, ands a list of the channel_numbers
        """
        num_devices = 1
        channel_numbers = [1, 2]
        connected_devices = [self._get('mill:list?')]  # returns only first line of string response
        while 'milliK' not in connected_devices[-1].split(','):  # the last device will be the milliK
            connected_devices.append(self.read().rstrip())
            channel_numbers += list(range(num_devices*10, num_devices*10+8))
            num_devices += 1
        if num_devices > 1:
            channel_numbers.pop(1)  # removes channel 2 as this is used to connect millisKanner

        self._connected_devices = connected_devices
        self._num_devices = num_devices
        self._channel_numbers = channel_numbers

        return connected_devices, num_devices, channel_numbers

    def resistance(self, channel, resis=200, current='norm', wire=4) -> float:
        """Read the resistance, e.g. of a PRT or thermistor.

        Parameters
        ----------
        channel : :class:`int`
            The channel to read the resistance of
        resis : :class:`int`, optional
            The measurement range in ohms of probe being read
        current : :class:`str`, optional
            :data:`norm` to return normal (1 mA) sense current,
            :data:`root2` for root2.
            The sense current of the probe being read
        wire : :class:`int`, optional
            The wiring arrangement eg 3 or 4 wire

        Returns
        -------
        :class:`float` or :class:`tuple` of :class:`float`
            The resistance.
        """
        message = f'meas:res{channel}? {resis},{current},{wire}'
        result = float(self._get(message))
        if abs(result) > resis:
            return float(0)
        return result

    def read_all_channels(self, resis=200, current='norm', wire=4) -> list[float, ...]:
        """Read the resistance of all available channels.
        Note that this method currently assumes the same probe type (e.g. PRT or thermistor) for all channels.
        An update will be necessary if mixed probe types are used.

        Parameters
        ----------
        resis : :class:`int`, optional
            The measurement range in ohms of probe being read
        current : :class:`str`, optional
            :data:`norm` to return normal (1 mA) sense current,
            :data:`root2` for root2.
            The sense current of the probe being read
        wire : :class:`int`, optional
            The wiring arrangement eg 3 or 4 wire

        Returns
        -------
        :class:`list`
            A list of resistance values from all channels.
        """
        results = []
        if not self.connected_devices:
            self.detect_channel_numbers()

        for c in self.channel_numbers:
            data = self.resistance(c, resis=resis, current=current, wire=wire)
            results.extend([data])

        return results

    def close_connection(self):
        """Return milliK to LOCAL mode"""
        self.write('millik:local')
        self.disconnect()

    def _get(self, message) -> str:
        try:
            ret = self.query(message).rstrip()
        except ConnectionResetError:
            return self._get(message)  # retry
        else:
            return ret
