from enum import IntEnum

from msl.equipment.connection_msl import ConnectionSerial


class IntegrationTime(IntEnum):
    """The amount of time to integrate the photodiode signal."""
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


class SIA3(ConnectionSerial):

    GAIN = IntegrationTime  #: The gain (i.e., the integration time)

    def __init__(self, record):
        """
        Establishes a connection to the Switched Integrator Amplifier
        (SIA3 board) that is designed by the Czech Metrology Institute.

        Parameters
        ----------
        record : :class:`~msl.equipment.record_types.EquipmentRecord`
            An equipment record from an **Equipment-Register**
            :class:`~msl.equipment.database.Database`.
        """
        ConnectionSerial.__init__(self, record)

    def set_integration_time(self, t):
        """Set the integration time (i.e., the gain).

        Parameters
        ----------
        t : :class:`.IntegrationTime`
            The integration time as a :class:`.IntegrationTime` enum value or member name.
        """
        self._send_byte(7)
        self._send_byte(self.convert_to_enum(t, IntegrationTime, prefix='TIME_'))

    def set_ps(self, ps):
        """Set the PS.

        Parameters
        ----------
        ps : int
            The PS to use. Value must be in the range [0, 7].

        Raises
        ------
        ValueError:
            If the value of `ps` is invalid.
        """
        _ps = int(ps)
        if _ps < 0 or _ps > 7:
            raise ValueError('Invalid ps of {}. Must be 0 <= ps <= 7.'.format(ps))
        self._send_byte(1)
        self._send_byte(4)
        self._send_byte(_ps)
        self._send_byte(_ps)

    def _send_byte(self, byte):
        self.write(chr(byte))

