"""Example showing how to communicate with an IsoTech milliK Precision Thermometer."""

from __future__ import annotations

from typing import TYPE_CHECKING

from msl.equipment import Connection

if TYPE_CHECKING:
    from msl.equipment.resources import MilliK


connection = Connection(
    "TCP::10.12.102.30::1000",  # could also be a Serial port, e.g., "COM4"
    manufacturer="IsoTech",
    model="milliK",
    timeout=5,
)

# Connect to the milliK device (automatically configures for REMOTE mode)
thermometer: MilliK = connection.connect()

# Print information about the device
print("Number of devices connected:", thermometer.num_devices)
print("Connected devices:", thermometer.connected_devices)
print("Available channel numbers:", thermometer.channel_numbers)

# Configure channel 1 for resistance measurements
# Specify the largest resistance value that is expected to be measured
thermometer.configure_resistance_measurement(channel=1, resistance=130)

# Configure channel 2 for voltage measurements with reference junction compensation
# enabled for a Type K thermocouple
thermometer.configure_voltage_measurement(channel=2, rjc=True, thermocouple="K")

# Read measurement data for a specific channel, returning n readings
print("Resistance value for Channel 1:", thermometer.read_channel(1))
print("Voltage values for Channel 2:", thermometer.read_channel(2, n=5))

# Read a value from all configured channels
for channel, value in thermometer.read_all_channels():
    print(f"Channel {channel}:", value)

# Disconnect from the milliK device (automatically configures for LOCAL mode)
thermometer.disconnect()
