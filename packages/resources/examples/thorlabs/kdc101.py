"""Communicate with a KDC101 motor controller that has an actuator attached."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from msl.equipment import Connection

if TYPE_CHECKING:
    from msl.equipment.resources import KDC

# You may want to replace "FTDI2" with "FTDI" if you are not using the Kinesis or XA software.
# Using "FTDI2" requires the D2XX driver to be installed for the motor controller.
# Using "FTDI" requires a libusb-compatible driver to be installed for the motor controller.
# Update 27251265 with the serial number of your motor controller.
connection = Connection(
    "FTDI2::0x0403::0xfaf0::27251265",
    manufacturer="Thorlabs",
    model="KDC101",
    serial="27251265",
    timeout=5,
    # actuator="Z825B",  # If not using Thorlabs software on the computer, the actuator/stage must be specified
    # init=True,  # If you want to initialise the motor to default parameters
)


def callback(position: float, encoder: int, status: int) -> None:
    """Receives the position (in mm or degrees), encoder counts and motor status."""
    print(f"  Callback {position:9.6f} {encoder:7d} 0b{status:032b}")


# Connect to the motor controller
motor: KDC = connection.connect()

# Print information about the motor
print(motor.get_home_parameters())
print(motor.get_limit_parameters())
print(motor.get_move_parameters())
print(motor.hardware_info())
print(f"Backlash={motor.get_backlash()} {motor.unit}")

# Optional: Set a callback function that is called while the actuator is moving
motor.set_callback(callback)

# Enable the motor if it is not already enabled
if not motor.is_enabled():
    motor.enable()

# Home the actuator if it is not already homed
if not motor.is_homed():
    print("Homing actuator...")
    motor.home()

# Move to 2 mm (absolute move)
print(f"Move to 2 {motor.unit}")
motor.move_to(2)

# Move by 1 mm (relative move)
print(f"Move by 1 {motor.unit}")
motor.move_by(1)

# Move by -1 mm (relative move)
print(f"Move by -1 {motor.unit}")
motor.move_by(-1)

# Move to 0 mm (absolute move), but don't wait until the actuator has finished moving
print(f"Move to 0 {motor.unit}")
motor.move_to(0, wait=False)

# Do other stuff while the actuator is moving...
print("Pretend to do other stuff, sleeping...")
time.sleep(1)

# Wait until the actuator has finished moving
print("Waiting...")
motor.wait_until_moved()

# Get the current position
print(f"At: {motor.position()} {motor.unit} [encoder={motor.encoder()}]")

# Disconnect from the motor controller
motor.disconnect()
