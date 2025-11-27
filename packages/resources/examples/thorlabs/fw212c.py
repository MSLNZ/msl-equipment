"""Example showing how to communicate with a FW102C/FW212C Motorized Filter Wheel."""

from __future__ import annotations

from typing import TYPE_CHECKING

from msl.equipment import Connection

if TYPE_CHECKING:
    from msl.equipment.resources import FWxx2C


connection = Connection(
    "COM6",
    manufacturer="Thorlabs",
    model="FW212C",  # alternatively FW102C (can also include the NEB suffix)
)

# Connect to the filter wheel
wheel: FWxx2C = connection.connect()

# Print the mode settings
print(f"Is in fast speed mode? {wheel.fast_mode}")
print(f"Are sensors always on? {wheel.sensor_mode}")
print(f"Is in output trigger mode? {wheel.output_mode}")

# Make the filter wheel return to the first position if it is at
# the last position, otherwise increment to the next position
print(f"Initial position is {wheel.position}")

if wheel.position == wheel.position_count:
    wheel.position = 1
else:
    wheel.position += 1

print(f"Final position is {wheel.position}")

# Disconnect from the filter wheel
wheel.disconnect()
