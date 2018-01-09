"""
Establishes a connection to the Switched Integrator Amplifier
(SIA3 board) that is designed by the `Czech Metrology Institute`_.

.. _Czech Metrology Institute: https://www.cmi.cz/?language=en
"""
from enum import IntEnum

from msl.equipment import constants
from msl.equipment.connection_msl import ConnectionSerial
from msl.equipment.exceptions import CMIError


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
            A record from an :ref:`equipment_database`.
        """
        if len(record.connection.properties) == 0:
            # then use the default connection properties
            record.connection.properties = {
                'baud_rate': 14400,
                'data_bits': constants.DataBits.EIGHT,
                'parity': constants.Parity.NONE,
                'stop_bits': constants.StopBits.ONE,
                'write_timeout': 10.0,
                'xon_xoff': False,
                'rts_cts': False,
                'dsr_dtr': False,
                'write_termination': None,
            }
        ConnectionSerial.__init__(self, record)
        self.set_exception_class(CMIError)

    def set_integration_time(self, time):
        """Set the integration time (i.e., the gain).

        Parameters
        ----------
        time : :class:`.IntegrationTime`
            The integration time as a :class:`.IntegrationTime` enum value or member name.
        """
        self._send_byte(7)
        self._send_byte(self.convert_to_enum(time, IntegrationTime, prefix='TIME_'))

    def set_ps(self, ps):
        """Set the PS.

        Parameters
        ----------
        ps : int
            The PS to use. The value must be in the range [0, 7].

        Raises
        ------
        ValueError:
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
