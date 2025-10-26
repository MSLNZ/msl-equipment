"""Example showing how to communicate with an IsoTech millisKanner (via a milliK)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from msl.equipment import Connection

if TYPE_CHECKING:
    from msl.equipment.resources import MilliK

connection = Connection(
    "COM6",  # could also be a Socket, e.g., "TCP::10.12.102.30::1000"
    manufacturer="IsoTech",
    model="milliK",
)

# Connect to the milliK device (automatically configures for REMOTE mode)
thermometer: MilliK = connection.connect()

# Print information about the device
print("Number of devices connected:", thermometer.num_devices)
print("Connected devices:", thermometer.connected_devices)
print("Available channel numbers:", thermometer.channel_numbers)

# Configure channels using the largest resistance value that is expected for that channel
resistances = [13000, 470, 220, 820, 3300, 100, 1800, 100]
for i, r in enumerate(resistances, start=10):  # here the sensors are all on the first millisKanner only
    thermometer.configure_resistance_measurement(channel=i, resistance=r)

# Read resistance for a specific channel, returning 5 readings
print("Resistance values for Channel 13:", thermometer.read_channel(13, n=5))

# Once the desired channels have been configured, you can yield values from them all
# Here, we request the average resistance of 5 readings for every configured channel
for ch, resistance in thermometer.read_all_channels(n=5):
    print(f"Channel {ch}:", resistance)

# Disconnect from the milliK device (automatically configures for LOCAL mode)
thermometer.disconnect()
