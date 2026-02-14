"""Communicate with a BSC201 controller that has a rotation stage attached."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from msl.equipment import Connection

if TYPE_CHECKING:
    from msl.equipment.resources import BSC

# You may want to replace "FTDI2" with "FTDI" if you are not using the Kinesis or XA software.
# Using "FTDI2" requires the D2XX driver to be installed for the motion controller.
# Using "FTDI" requires a libusb-compatible driver to be installed for the motion controller.
# Update 40876748 with the serial number of your motion controller.
connection = Connection(
    "FTDI2::0x0403::0xfaf0::40876748",
    manufacturer="Thorlabs",
    model="BSC201",
    serial="40876748",
    timeout=5,
    # stage="NR360S/M",  # If not using Thorlabs software on the computer, the actuator/stage must be specified
)


def callback(position: float, encoder: int, status: int) -> None:
    """Receives the position (in mm or degrees), encoder counts and motor status."""
    print(f"  Callback {position:9.6f} {encoder:7d} 0b{status:032b}")


# Connect to the motion controller
stage: BSC = connection.connect()

# BSC201 supports only one channel but BSC202 and BSC203 support multiple channels.
# The default channel is 1 in the BSC class methods, so explicitly specifying the
# channel in this example is not necessary.
channel = 1

# Print information about the stage
print(stage.get_home_parameters(channel))
print(stage.get_limit_parameters(channel))
print(stage.get_move_parameters(channel))
print(stage.hardware_info())
print(f"Backlash={stage.get_backlash(channel)} {stage.unit}")

# Optional: Set a callback function that is called while the stage is moving
stage.set_callback(callback)

# Enable the motor if it is not already enabled
if not stage.is_enabled(channel):
    stage.enable()

# Home the stage if it is not already homed
if not stage.is_homed(channel):
    print("Homing stage...")
    stage.home()

# Move to 10 (absolute move)
print(f"Move to 10 {stage.unit}")
stage.move_to(10, channel=channel)

# Move by 5 (relative move)
print(f"Move by 5 {stage.unit}")
stage.move_by(5, channel=channel)

# Move by -5 (relative move)
print(f"Move by -5 {stage.unit}")
stage.move_by(-5, channel=channel)

# Move to 0 (absolute move), but don't wait until the stage has finished moving
print(f"Move to 0 {stage.unit}")
stage.move_to(0, channel=channel, wait=False)

# Do other stuff while the stage is moving...
print("Pretend to do other stuff, sleeping...")
time.sleep(1)

# Wait until the stage has finished moving
print("Waiting...")
stage.wait_until_moved(channel)

# Get the current position
print(f"At: {stage.position(channel)} {stage.unit} [encoder={stage.encoder(channel)}]")

# Disconnect from the motion controller
stage.disconnect()
