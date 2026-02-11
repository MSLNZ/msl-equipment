"""Communicate with an MFF101/M flip mount."""

from __future__ import annotations

from typing import TYPE_CHECKING

from msl.equipment import Connection

if TYPE_CHECKING:
    from msl.equipment.resources import MFF

# You may want to replace "FTDI2" with "FTDI" if you are not using the Kinesis or XA software.
# Using "FTDI2" requires the D2XX driver to be installed for the flip mount.
# Using "FTDI" requires a libusb-compatible driver to be installed for the flip mount.
# Update 37870963 with the serial number of your flip mount.
connection = Connection(
    "FTDI2::0x0403::0xfaf0::37870963",
    manufacturer="Thorlabs",
    model="MFF101/M",
    serial="37870963",
    timeout=5,
)

# Connect to the flip mount
flipper: MFF = connection.connect()

# Print information about the flip mount
print(flipper.get_parameters())
print(flipper.hardware_info())

# Enable the motor if it is not already enabled
if not flipper.is_enabled():
    flipper.enable()

# Get the original position
original = flipper.position()
print(f"At: {original}")

# Toggle the position
print("Toggle...")
flipper.toggle()

# Get the new position
print(f"At: {flipper.position()}")

# Move back to the original position
flipper.move_to(original)
print(f"At: {flipper.position()}")

# Disconnect from the flip mount
flipper.disconnect()
