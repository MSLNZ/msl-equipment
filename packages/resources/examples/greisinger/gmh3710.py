"""Example showing how to communicate with an GMH3710 thermometer from Greisinger, GHM Group."""

from __future__ import annotations

from typing import TYPE_CHECKING

from msl.equipment import Connection

if TYPE_CHECKING:
    from msl.equipment.resources import GMH3000

connection = Connection(
    "COM4",  # change for your thermometer
    manufacturer="Greisinger",
    model="GMH3710-GE",
    timeout=2,
    # gmh_address=11  # Optional: change for your thermometer, default gmh_address is 1
)

thermometer: GMH3000 = connection.connect()

# Read information about the device
unit = thermometer.unit()
print("Current value", thermometer.value(), unit)
print("Minimum value", thermometer.min_value(), unit)
print("Maximum value", thermometer.max_value(), unit)
print("Measurement range", thermometer.measurement_range())
print("Display range", thermometer.display_range())
print("Scale correction", thermometer.scale_correction())
print("Offset correction", thermometer.offset_correction())
print("Channel count", thermometer.channel_count())
print("Power-off time", thermometer.power_off_time())
print("Resolution", thermometer.resolution())
print("ID (serial) number", thermometer.id_number())
print("Firmware version", thermometer.firmware_version())

# Check if the battery is low
bit_mask = thermometer.status()
print(f"System status: {bit_mask}")
if bit_mask & 1 << 15:
    print("Warning! Battery is low")

# Clears the minimum and maximum values that are stored in the device
# thermometer.clear_min_value()
# thermometer.clear_max_value()

# Sets the power-off time to 30 minutes
# thermometer.set_power_off_time(30)

# Disconnect from the device
thermometer.disconnect()
