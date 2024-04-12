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
from msl.equipment.connection_socket import ConnectionSocket
from msl.equipment.constants import Interface


@register(manufacturer=r'Iso.*Tech.*', model=r'milli.*K.*', flags=re.IGNORECASE)
class MilliK:

    def __new__(cls, record: EquipmentRecord) -> ConnectionSerial | ConnectionSocket:
        """Establishes a connection to an IsoTech MilliK Precision Thermometer for different interfaces:

        * :obj:`.Interface.SERIAL`
        * :obj:`.Interface.SOCKET`

        Note that millisKanners only have an RS232 serial interface.

        Do not instantiate this class directly. Use the :meth:`~.EquipmentRecord.connect`
        method to connect to the equipment.

        :param record: A record from an :ref:`equipment-database`.
        """
        interface = record.connection.interface
        if interface == Interface.SOCKET:
            base = ConnectionSocket
        elif interface == Interface.SERIAL:
            base = ConnectionSerial
        else:
            raise IsoTechError(f"Unknown interface for connection for {record.connection.interface}")

        dict_ = dict((k, v) for k, v in vars(cls).items() if not k.startswith('__'))
        type_ = type(cls.__name__, (base,), dict_)
        instance = type_(record)
        instance.set_exception_class(IsoTechError)

        instance.rstrip = True
        instance.read_termination = '\r'
        instance.write_termination = '\r'
        instance.write('millik:remote')  # use REMOTE mode to speed up communications

        instance._connected_devices, instance._num_devices, instance._channel_numbers = _find_channel_numbers(instance)

        instance.channel_configuration = {}
        """A list of configured channel numbers with their measurement mode, range, current, and wiring settings."""

        return instance

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

    def configure_resistance_measurement(self, channel: int, meas_range: float, *, norm: bool = True, fourwire: bool = True)\
            -> None:
        r"""Configure the milliK to measure resistance for the specified channel.

        :param channel: The channel to configure for resistance measurement.
        :param meas_range: The measurement range in ohms. Selects from 115 Ohms, 460 Ohms and 500 kOhms.
        :param norm: The sense current to use for measurement. Defaults to use normal (1 mA) sense current,
            unless False in which case it uses root2*1 mA to determine self-heating effects.
            Thermistors always use 2 μA.
        :param fourwire: The wiring arrangement eg 3 or 4 wire.
        :return: Returns the internal values set for range, current, and wiring.
        """
        if channel not in self.channel_numbers:
            self.raise_exception(f"Channel {channel} is not available in the current measurement setup")
        current = 'NORM' if norm else 'ROOT2'
        wire = 4 if fourwire else 3
        message = f'sens:chan {channel};sens:res:rang {meas_range};sens:curr {current};sens:res:wir {wire}'
        self.write(message)

        channel_set = self.query('sens:chan?')
        assert int(channel_set) == channel

        range_set = self.query('sens:res:rang?')
        if range_set == 'Error: Invalid range':
            self.raise_exception(range_set)
        assert float(range_set) >= float(meas_range)

        current_set = float(self.query('sens:curr?'))

        wire_set = int(self.query('sens:res:wir?'))
        assert wire_set == wire

        self.log_info(f'milliK Channel {channel} set to use {range_set} Ohms, {current_set} A, and {wire_set}-wire configuration')

        self.channel_configuration[channel] = ['resistance', meas_range, current, wire]

    def read_channel(self, channel: int, n: int = 1) -> float | list[float]:
        """Initiate and report a measurement using the conditions defined by :meth:`.configure_resistance_measurement`.

        :param channel: The channel to read.
        :param n: The number of readings to make.
        :return: A list of n readings, or a single float value if only one reading is requested.
        """
        if channel not in self.channel_configuration:
            self.raise_exception(f"Please first configure channel {channel} before attempting to read values")

        # TODO assuming resistance for now; voltage or current measurement will need a different call.
        mode, meas_range, current, wire = self.channel_configuration[channel]
        assert mode == 'resistance'

        readings = [float(self.query(f'meas:res{channel}? {meas_range},{current}, {wire}')) for _ in range(n)]

        if len(readings) == 1:
            return readings[0]

        return readings

    def read_all_channels(self, n: int = 1) -> tuple[list[int], list[float]]:
        """Read from all configured channels using the conditions defined by :meth:`.configure_resistance_measurement`.

        :param n: The number of readings to average for each returned value.
        :return: A tuple of lists of channel numbers and readings from all configured channels.
        """
        channels = sorted(self.channel_configuration)
        results = []
        for c in channels:
            readings = self.read_channel(c, n)
            if n == 1:  # readings is a single float value
                results.append(readings)
            else:       # average multiple readings
                results.append(sum(readings)/len(readings))

        return channels, results

    def disconnect(self) -> None:
        """Return the milliK device to LOCAL mode before disconnecting from the device."""
        try:
            if self.serial.is_open:
                self.write('millik:local')
                self.serial.close()
                self.log_debug('Disconnected from %s', self.equipment_record.connection)
        except AttributeError:
            if self.socket is not None:
                self.write('millik:local')
                self.socket.close()
                self.log_debug('Disconnected from %s', self.equipment_record.connection)
                self._socket = None


def _find_channel_numbers(instance) -> tuple[list[str], int, list[int]]:
    """Find the number of millisKanners connected, if any, and hence the valid channel numbers.
    Up to 4 millisKanners can be connected to a single milliK.
    Returns a list of the :attr:`.connected_devices`, an integer for :attr:`.num_devices`,
    and a list of the :attr:`.channel_numbers`.
    """
    num_devices = 1
    channel_numbers = [1, 2]
    connected_devices = [instance.query('mill:list?')]  # returns only first line of string response
    while 'milliK' not in connected_devices[-1].split(','):  # the last device will be the milliK
        connected_devices.append(instance.read())
        channel_numbers += list(range(num_devices*10, num_devices*10+8))
        num_devices += 1
    if num_devices > 1:
        channel_numbers.pop(1)  # removes channel 2 which is used to connect to the millisKanner daisy-chain

    return connected_devices, num_devices, channel_numbers
