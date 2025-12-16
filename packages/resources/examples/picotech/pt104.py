"""Example showing how to communicate with a PT-104 Data Logger.

This examples assumes that a voltage is applied to channel 1 and a PT100 is connected to channel 2.
"""

from __future__ import annotations

import os
import time
from typing import TYPE_CHECKING

from msl.equipment import Connection

if TYPE_CHECKING:
    from msl.equipment.resources import PT104


connection = Connection(
    "SDK::usbpt104",  # Alternatively, specify the full path to the SDK, "SDK::path/to/lib/usbpt104"
    manufacturer="PicoTech",
    model="PT-104",
    serial="JO332/224",  # Change for your device
    ip_address="192.168.1.20:1875",  # Optional: Specify the IP address and port (change for your device)
    # open_via_ip=True,  # Optional: True: connect via ethernet, False: connect via USB (default)
)

# Optional: Ensure that the Pico Technology SDK is available on PATH (if not already)
os.environ["PATH"] += os.pathsep + r"C:\Program Files\Pico Technology\SDK\lib"

# Connect to the PT-104
pt104: PT104 = connection.connect()

# Get all available information about the PT-104
print(pt104.get_unit_info())

# Use the enum value to get the calibration date and do not print the member-name prefix
info = pt104.get_unit_info(5, prefix=False)
print(f"The PT-104 was calibrated on {info}")

# Use the enum member name to get the MAC address
print(pt104.get_unit_info("mac_address"))

# Get the details of the ethernet connection
enabled, ip_address, port = pt104.get_ip_details()
print(f"Ethernet enabled? {enabled}")
print(f"Address: {ip_address}:{port}")

# Set channel 1 to measure the resistance of a PT1000 in a 4-wire arrangement
pt104.set_channel(1, pt104.Mode.RESISTANCE_TO_10K, 4)

# Set channel 2 to measure the temperature of a PT100 in a 4-wire arrangement
pt104.set_channel(2, pt104.Mode.PT100, 4)

# Wait for the samples to be available
# A measurement cycle takes about 1 second per active channel
# 2 channels are active, so we should wait at least 2 seconds
time.sleep(3)

# Read the values
ch1 = pt104.get_value(1)
ch2 = pt104.get_value(2)
print(f"Resistance={ch1}, Temperature={ch2}")

# Disconnect from the Data Logger
pt104.disconnect()
