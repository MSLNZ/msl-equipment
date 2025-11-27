"""Communicate with a FW102C/FW212C Motorized Filter Wheel from [Thorlabs](https://www.thorlabs.com/){:target="_blank"}."""

# cSpell: ignore pcount
from __future__ import annotations

from typing import TYPE_CHECKING

from msl.equipment.interfaces import Serial

if TYPE_CHECKING:
    from msl.equipment.schema import Equipment


class FWxx2C(Serial, manufacturer=r"Thorlabs", model=r"FW(10|21)2C"):
    """Communicate with a FW102C/FW212C Motorized Filter Wheel from [Thorlabs](https://www.thorlabs.com/){:target="_blank"}."""

    def __init__(self, equipment: Equipment) -> None:
        """Communicate with a FW102C/FW212C Motorized Filter Wheel from Thorlabs.

        Args:
            equipment: An [Equipment][] instance.
        """
        assert equipment.connection is not None  # noqa: S101
        equipment.connection.properties.setdefault("baud_rate", 115200)
        equipment.connection.properties.setdefault("termination", b"\r")
        super().__init__(equipment)

        # The communication protocol is designed for a terminal interface
        # (the command that was written is echoed back). We always need to
        # do an extra read(), so we use query() where a write() would seem
        # appropriate and do another read() to get the requested value.
        _ = self.query("pcount?")
        self._pcount: int = int(self.read())

    @property
    def fast_mode(self) -> bool:
        """Whether the filter wheel speed mode is fast or slow."""
        _ = self.query("speed?")
        return bool(int(self.read()))

    @fast_mode.setter
    def fast_mode(self, value: bool) -> None:
        _ = self.query(f"speed={int(bool(value))}")

    @property
    def firmware(self) -> str:
        """Returns the version number of the firmware."""
        _ = self.query("*idn?")
        return self.read().split()[-1]

    @property
    def output_mode(self) -> bool:
        """Whether the filter wheel trigger mode is an output or input.

        In output mode, the filter wheel generates an active-high pulse when
        the position changes. In input mode, the filter wheel responds to an
        active-low pulse by advancing the position by 1.
        """
        _ = self.query("trig?")
        return bool(int(self.read()))

    @output_mode.setter
    def output_mode(self, value: bool) -> None:
        _ = self.query(f"trig={int(bool(value))}")

    @property
    def position(self) -> int:
        """Get/Set the filter wheel position."""
        _ = self.query("pos?")
        return int(self.read())

    @position.setter
    def position(self, value: int) -> None:
        if value < 1 or value > self._pcount:
            msg = f"Invalid filter wheel position {value}, must be in the range [1, {self._pcount}]"
            raise ValueError(msg)
        _ = self.query(f"pos={value}")

    @property
    def position_count(self) -> int:
        """Returns the number of positions that the filter wheel supports."""
        return self._pcount

    def save(self) -> None:
        """Save the current settings as default on power up."""
        _ = self.query("save")

    @property
    def sensor_mode(self) -> bool:
        """Whether the filter wheel sensor mode is on or off.

        If `True`, sensors remain on; otherwise sensors turn off when the
        filter wheel is idle to eliminate stray light.
        """
        _ = self.query("sensors?")
        return bool(int(self.read()))

    @sensor_mode.setter
    def sensor_mode(self, value: bool) -> None:
        _ = self.query(f"sensors={int(bool(value))}")
