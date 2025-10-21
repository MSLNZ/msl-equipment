"""Example showing how to communicate with a TC Series Temperature Controller from Electron Dynamics Ltd."""

from __future__ import annotations

from typing import TYPE_CHECKING

from msl.equipment import Connection
from msl.equipment.resources import electron_dynamics as ed

if TYPE_CHECKING:
    from msl.equipment.resources import TCSeries


connection = Connection(
    "COM5",  # update for your controller
    manufacturer="Electron Dynamics",
    model="TC Lite",
)

# Connect to the Temperature Controller
tc: TCSeries = connection.connect()

# Get all available information about the Temperature Controller
print(f"alarm: {tc.get_alarm()}")
print(f"control: {tc.get_control()}")
print(f"output: {tc.get_output()}")
print(f"sensor: {tc.get_sensor()}")
print(f"setpoint: {tc.get_setpoint()}")
print(f"status: {tc.get_status()}")

# Set the sensor to be PT100
tc.set_sensor(ed.Sensor(type=ed.SensorType.PT100, x2=0, x=0.722, c=0.02, unit=ed.Unit.C, averaging=False))

# Disconnect from the Controller
tc.disconnect()
