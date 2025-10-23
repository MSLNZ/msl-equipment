"""A Switched Integrator Amplifier (SIA) designed by the [Czech Metrology Institute]{:target="_blank"}.

[Czech Metrology Institute]: https://cmi.gov.cz/?language=en
"""

from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

from msl.equipment.interfaces import Serial
from msl.equipment.utils import to_enum

if TYPE_CHECKING:
    from msl.equipment.schema import Equipment


class IntegrationTime(IntEnum):
    """The amount of time to integrate the photodiode signal.

    Attributes:
        TIME_50us (int): 5
        TIME_100us (int): 6
        TIME_1ms (int): 7
        TIME_10ms (int): 8
        TIME_20ms (int): 9
        TIME_100ms (int): 10
        TIME_200ms (int): 11
        TIME_500ms (int): 12
        TIME_1s (int): 13
        TIME_2s (int): 14
    """

    TIME_50us = 5
    TIME_100us = 6
    TIME_1ms = 7
    TIME_10ms = 8
    TIME_20ms = 9
    TIME_100ms = 10
    TIME_200ms = 11
    TIME_500ms = 12
    TIME_1s = 13
    TIME_2s = 14


class PreScale(IntEnum):
    """Pre-scale factor for the microprocessor frequency.

    Attributes:
        PS_0 (int): 0
        PS_1 (int): 1
        PS_2 (int): 2
        PS_3 (int): 3
        PS_4 (int): 4
        PS_5 (int): 5
        PS_6 (int): 6
        PS_7 (int): 7
    """

    PS_0 = 0
    PS_1 = 1
    PS_2 = 2
    PS_3 = 3
    PS_4 = 4
    PS_5 = 5
    PS_6 = 6
    PS_7 = 7


class SIA3(Serial, manufacturer=r"C.*M.*I", model=r"SIA3"):
    """A Switched Integrator Amplifier (SIA) designed by the [Czech Metrology Institute]{:target="_blank"}.

    [Czech Metrology Institute]: https://cmi.gov.cz/?language=en
    """

    def __init__(self, equipment: Equipment) -> None:
        """A Switched Integrator Amplifier (SIA) designed by the Czech Metrology Institute.

        Args:
            equipment: An [Equipment][] instance.
        """
        assert equipment.connection is not None  # noqa: S101
        if not equipment.connection.properties:
            # then use the default connection properties
            equipment.connection.properties = {
                "baud_rate": 14400,
                "termination": None,
                "timeout": 10.0,
            }
        super().__init__(equipment)

    def set_integration_time(self, time: str | int | IntegrationTime) -> None:
        """Set the integration time (i.e., the gain).

        Args:
            time: The integration time. The following are equivalent to set the
                integration time to 10 milliseconds:

                * `set_integration_time("10ms")`
                * `set_integration_time(8)`
                * `set_integration_time(cmi.IntegrationTime.TIME_10ms)`
        """
        value = to_enum(time, IntegrationTime, prefix="TIME_")
        self._send_byte(7)
        self._send_byte(value)

    def set_ps(self, ps: int | PreScale) -> None:
        """Set the timer pre-scale value.

        The timer pre-scale value divides the microprocessor internal frequency
        by something similar to $2^{PS}$. Therefore, to reach a 2-second integration time
        the `ps` value must be set to the maximum value of 7.

        Args:
            ps: The timer pre-scale value. The following are equivalent to set the
                pre-scale value to 7

                * `set_ps(7)`
                * `set_ps(cmi.PreScale.PS_7)`
        """
        value = to_enum(ps, PreScale, prefix="PS_")
        self._send_byte(1)
        self._send_byte(4)
        self._send_byte(value)
        self._send_byte(value)

    def _send_byte(self, byte: int) -> None:
        _ = self.write(chr(byte))
