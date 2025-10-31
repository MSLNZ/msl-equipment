"""Control a TEC (Peltier-based) oven from [Raicol Crystals](https://raicol.com/){:target="_blank"}."""

from __future__ import annotations

from typing import TYPE_CHECKING

from msl.equipment.interfaces import MSLConnectionError, Serial

if TYPE_CHECKING:
    from msl.equipment.schema import Equipment


class RaicolTEC(Serial, manufacturer=r"Raicol", model=r"TEC"):
    """Control a TEC (Peltier-based) oven from [Raicol Crystals](https://raicol.com/){:target="_blank"}."""

    def __init__(self, equipment: Equipment) -> None:
        """Control a TEC (Peltier-based) oven from Raicol Crystals.

        Args:
            equipment: An [Equipment][] instance.
        """
        super().__init__(equipment)
        self.write_termination: bytes = b"\n"

    def get_setpoint(self) -> float:
        """Get the setpoint temperature.

        Returns:
            The setpoint temperature, in Celsius.
        """
        return float(self.query("Get_T_Set", size=6)[2:])

    def off(self) -> None:
        """Turn the TEC off."""
        reply = self.query("OFF", size=4)
        if reply != "ofOK":
            msg = "Cannot turn the TEC off"
            raise MSLConnectionError(self, msg)

    def on(self) -> None:
        """Turn the TEC on."""
        reply = self.query("ON", size=4)
        if reply != "onOK":
            msg = "Cannot turn the TEC on"
            raise MSLConnectionError(self, msg)

    def set_setpoint(self, temperature: float) -> None:
        """Set the setpoint temperature.

        Args:
            temperature: The setpoint temperature, in Celsius. Must be in the range [20.1, 60.0].
        """
        t = round(temperature, 1)
        if t < 20.1 or t > 60.0:  # noqa: PLR2004
            msg = f"The setpoint temperature must be between 20.1 and 60.0, got {t}"
            raise ValueError(msg)

        reply = self.query(f"Set_T{t:.1f}", size=4, delay=0.05)
        if reply != "stOK":
            msg = "Cannot change the setpoint temperature"
            raise MSLConnectionError(self, msg)

    def temperature(self) -> float:
        """Returns the current temperature of the oven.

        The temperature is measured by a PT1000 sensor that is located near the crystal in the metallic mount.

        Returns:
            The temperature of the oven, in Celsius.
        """
        return float(self.query("Data_T", size=7)[2:])
