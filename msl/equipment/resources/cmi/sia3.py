"""
Establishes a connection to the Switched Integrator Amplifier
(SIA3 board) that is designed by the `Czech Metrology Institute`_.

.. _Czech Metrology Institute: https://www.cmi.cz/?language=en
"""
from enum import IntEnum

from msl.equipment.connection_serial import ConnectionSerial
from msl.equipment.exceptions import CMIError
from msl.equipment.resources import register


class IntegrationTime(IntEnum):
    """The amount of time to integrate the photo-diode signal."""
    TIME_50u = 5
    TIME_100u = 6
    TIME_1m = 7
    TIME_10m = 8
    TIME_20m = 9
    TIME_100m = 10
    TIME_200m = 11
    TIME_500m = 12
    TIME_1 = 13
    TIME_2 = 14


@register(manufacturer=r'C.*M.*I', model=r'SIA3')
class SIA3(ConnectionSerial):

    GAIN = IntegrationTime  #: The gain (i.e., the integration time)

    def __init__(self, record):
        """
        Establishes a connection to the Switched Integrator Amplifier
        (SIA3 board) that is designed by the `Czech Metrology Institute`_.

        Do not instantiate this class directly. Use the :meth:`~.EquipmentRecord.connect`
        method to connect to the equipment.

        .. _Czech Metrology Institute: https://www.cmi.cz/?language=en

        Parameters
        ----------
        record : :class:`~.EquipmentRecord`
            A record from an :ref:`equipment-database`.
        """
        if not record.connection.properties:
            # then use the default connection properties
            record.connection.properties = {
                'baud_rate': 14400,
                'termination': None,
                'timeout': 10.0,
            }
        super(SIA3, self).__init__(record)
        self.set_exception_class(CMIError)

    def set_integration_time(self, time):
        """Set the integration time (i.e., the gain).

        Parameters
        ----------
        time : :class:`.IntegrationTime`
            The integration time as a :class:`.IntegrationTime` enum value or member name,
            e.g., ``sia.set_integration_time('10m')``, ``sia.set_integration_time(sia.GAIN.TIME_10m)``
            and ``sia.set_integration_time(8)`` are all equivalent statements.
        """
        self._send_byte(7)
        self._send_byte(self.convert_to_enum(time, IntegrationTime, prefix='TIME_'))

    def set_ps(self, ps):
        """Set the timer pre-scale value.

        The timer pre-scale value divides the microprocessor internal frequency
        by something similar to 2^PS. Therefore, to reach a 2 second integration time
        the `ps` value must be set to the maximum value of 7.

        Parameters
        ----------
        ps : :class:`int`
            The timer pre-scale value. Must be in the range [0, 7].

        Raises
        ------
        ValueError
            If the value of `ps` is invalid.
        """
        _ps = int(ps)
        if _ps < 0 or _ps > 7:
            raise ValueError('Invalid PS value of {}. Must be 0 <= PS <= 7.'.format(ps))
        self._send_byte(1)
        self._send_byte(4)
        self._send_byte(_ps)
        self._send_byte(_ps)

    def _send_byte(self, byte):
        self.write(chr(byte))
