"""Communicate with a K10CR1/M rotation stage."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from msl.equipment import Connection

if TYPE_CHECKING:
    from msl.equipment.resources import K10CR

# You may want to replace "FTDI2" with "FTDI" if you are not using the Kinesis or XA software.
# Using "FTDI2" requires the D2XX library to be available on PATH.
# Update 55264734 with the serial number of your device.
connection = Connection(
    "FTDI2::0x0403::0xfaf0::55264734",
    manufacturer="Thorlabs",
    model="K10CR1/M",
    serial="55264734",
    timeout=5,
)


def callback(position: float, status: int) -> None:
    """Handles updates of the position (in degrees) and status (a 32-bit bitmap of states that the stage is in)."""
    print("  Callback", position, bin(status))


stage: K10CR = connection.connect()

# Print information about the stage
print(stage.get_home_parameters())
print(stage.get_limit_parameters())
print(stage.get_move_parameters())
print(stage.hardware_info())
print(f"Backlash={stage.get_backlash()}{stage.unit}")

# Optional: Set a callback function that is called while the stage is moving
stage.set_callback(callback)

# Enable the motor if it is not already enabled
if not stage.is_enabled():
    stage.enable()

# Home the stage if it is not already homed
if not stage.is_homed():
    print("Homing stage...")
    stage.home()

# Move to 10 degrees (absolute move)
print(f"Move to 10{stage.unit}")
stage.move_to(10)

# Move by 5 degrees (relative move)
print(f"Move by 5{stage.unit}")
stage.move_by(5)

# Move by -5 degrees (relative move)
print(f"Move by -5{stage.unit}")
stage.move_by(-5)

# Move to -10 degrees (absolute move), but don't wait until the stage has finished moving
print(f"Move to -10{stage.unit}")
stage.move_to(-10, wait=False)

# Do other stuff while the stage is moving...
print("Pretend to do other stuff, sleeping...")
time.sleep(1)

# Wait until the stage has finished moving
print("Waiting...")
stage.wait_until_moved()

# Get the current position
print(f"At: {stage.position()}{stage.unit}")

# Disconnect from the stage
stage.disconnect()
