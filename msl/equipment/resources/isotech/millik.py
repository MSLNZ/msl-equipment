"""
IsoTech milliK Precision Thermometer, with any number of connected millisKanners
"""
from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from msl.equipment import EquipmentRecord
from msl.equipment.resources import register
from msl.equipment.exceptions import IsoTechError
from msl.equipment.connection_serial import ConnectionSerial


@register(manufacturer=r'Iso.*Tech.*', model=r'milli.*K.*', flags=re.IGNORECASE)
class MilliK(ConnectionSerial):

    def __init__(self, record: EquipmentRecord) -> None:
        """IsoTech MilliK Precision Thermometer.

        Do not instantiate this class directly. Use the :meth:`~.EquipmentRecord.connect`
        method to connect to the equipment.

        :param record: A record from an :ref:`equipment-database`.
        """
        super(MilliK, self).__init__(record)

        self.set_exception_class(IsoTechError)
        self.rstrip = True

        self._connected_devices: list[str] = []
        self._num_devices = 0
        self._channel_numbers: list[int] = []

        self.detect_channel_numbers()
        self.write('millik:remote')  # use REMOTE mode to speed up communications

    @property
    def connected_devices(self) -> list[str]:
        """A list of information about the connected devices (manufacturer, model, serial number, firmware version),
        e.g. ['Isothermal Technology,millisKanner,21-P2593,2.01', 'Isothermal Technology,milliK,21-P2460,4.0.0'].
        """
        # These are the strings that would be returned from each instrument by the *IDN? command
        return self._connected_devices

    @property
    def num_devices(self) -> int:
        """The number of connected devices."""
        return self._num_devices

    @property
    def channel_numbers(self) -> list[int]:
        """A list of available channel numbers, e.g. [1, 2] for a single milliK,
        or [1, 10, 11, 12, 13, 14, 15, 16, 17] for a milliK connected to a single millisKanner, etc.
        """
        return self._channel_numbers

    def detect_channel_numbers(self) -> tuple[list[str], int, list[int]]:
        """Find the number of millisKanners connected, if any, and hence the valid channel numbers.
        Up to 4 millisKanners can be connected to a single milliK.
        Returns a list of the :attr:`.connected_devices`, an integer for :attr:`.num_devices`,
        and a list of the :attr:`.channel_numbers`.
        """
        num_devices = 1
        channel_numbers = [1, 2]
        connected_devices = [self.query('mill:list?')]  # returns only first line of string response
        while 'milliK' not in connected_devices[-1].split(','):  # the last device will be the milliK
            connected_devices.append(self.read())
            channel_numbers += list(range(num_devices*10, num_devices*10+8))
            num_devices += 1
        if num_devices > 1:
            channel_numbers.pop(1)  # removes channel 2 which is used to connect to the millisKanner daisy-chain

        self._connected_devices = connected_devices
        self._num_devices = num_devices
        self._channel_numbers = channel_numbers

        return connected_devices, num_devices, channel_numbers

    def configure_resistance_measurement(self, range: float, *, norm: bool = True, fourwire: bool = True) \
            -> tuple[float, float, int]:
        """Configure the sense mode for the milliK to measure resistance.

        :param range: The measurement range in ohms. Selects from 115 Ohms, 460 Ohms and 500 kOhms.
        :param norm: The sense current to use for measurement. Defaults to use normal (1 mA) sense current,
            unless False in which case it uses root2*1 mA to determine self-heating effects.
            Thermistors always use 2 :math:`\\mu`A.
        :param fourwire: The wiring arrangement eg 3 or 4 wire.
        :return: Returns the internal values set for range, current, and wiring.
        """
        current = 'NORM' if norm else 'ROOT2'
        wire = 4 if fourwire else 3
        message = f'sens:res:rang {range};sens:curr {current};sens:res:wir {wire};'
        self.write(message)

        range_set = self.query('sens:res:rang?')
        if range_set == 'Error: Invalid range':
            self.raise_exception(range_set)
        assert float(range_set) >= float(range)

        current_set = float(self.query('sens:curr?'))

        wire_set = int(self.query('sens:res:wir?'))
        assert wire_set == wire

        self.log_info(f'milliK set to use {range_set} Ohms, {current_set} A, and {wire_set}-wire configuration')

        return float(range_set), current_set, wire_set

    def read_channel(self, channel: int, n: int = 1) -> float | list[float]:
        """Initiate and report a measurement using the conditions defined by previous sense commands.

        :param channel: The channel to read.
        :param n: The number of readings to make.
        :return: A list of n readings, or a single float value if only one reading is requested.
        """
        if channel not in self.channel_numbers:
            self.raise_exception(f"Channel {channel} is not available in the current measurement setup")
        readings = []
        # for some reason an extra value gets put into the buffer for each requested reading so two reads are necessary
        r1 = float(self.query(f'sense:channel {channel};read:scal? {n}'))
        r2 = float(self.read())
        readings.append((r1 + r2)/2)

        for i in range(n - 1):
            r1 = float(self.read())
            r2 = float(self.read())
            readings.append((r1 + r2) / 2)

        if len(readings) == 1:
            return readings[0]
        return readings

    def read_all_channels(self, n: int = 1) -> list[float]:
        """Read from all available channels using the conditions defined by previous sense commands.
        Note that this method currently assumes the same sensor type (e.g. PRT or thermistor) for all channels.

        :param n: The number of readings to average for each returned value.
        :return: A list of values from all channels (in the order they appear in :attr:`.channel_numbers`).
        """
        results = []
        for c in self.channel_numbers:
            readings = self.read_channel(c, n)
            if n == 1:  # readings is a single float value
                results.append(readings)
            else:       # average multiple readings
                results.append(sum(readings)/len(readings))

        return results

    def disconnect(self) -> None:
        """Return the milliK device to LOCAL mode."""
        if self.serial.is_open:
            self.write('millik:local')
        super().disconnect()
