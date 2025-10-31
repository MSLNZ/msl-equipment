"""Example showing how to control a TEC (Peltier-based) oven from Raicol Crystals."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from msl.equipment import Connection

if TYPE_CHECKING:
    from msl.equipment.resources import RaicolTEC

connection = Connection(
    "COM4",  # update for your oven
    manufacturer="Raicol Crystals",
    model="TEC 20-60",
)

# connect to the TEC controller
tec: RaicolTEC = connection.connect()

# set the setpoint temperature, in Celsius
tec.set_setpoint(25.0)

# get the setpoint temperature
print("setpoint=", tec.get_setpoint())

# turn the TEC on
tec.on()

# read the current temperature
for _ in range(30):
    time.sleep(1)
    print("temperature=", tec.temperature())

# turn the TEC off
tec.off()

# disconnect from the TEC controller
tec.disconnect()
