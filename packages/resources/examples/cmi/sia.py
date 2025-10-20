"""Example showing how to communicate with a Switched Integrator Amplifier (SIA)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from msl.equipment import Connection
from msl.equipment.resources import cmi

if TYPE_CHECKING:
    from msl.equipment.resources import SIA3

connection = Connection(
    "COM3",  # update for your amplifier
    manufacturer="CMI",
    model="SIA3",
)

# Connect to the amplifier
sia: SIA3 = connection.connect()

# These are equivalent to set the pre-scale factor to 7
sia.set_ps(cmi.PreScale.PS_7)  # use the enum
sia.set_ps(7)  # use the enum value

# These are equivalent to set the integration time to 2 seconds
sia.set_integration_time(cmi.IntegrationTime.TIME_2s)  # use the enum
sia.set_integration_time("2s")  # use the last part of the enum member name
sia.set_integration_time(14)  # use the enum value

# Disconnect from the amplifier
sia.disconnect()
