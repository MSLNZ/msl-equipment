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
    "SDK::usbpt104",
    manufacturer="PicoTech",
    model="PT-104",
    serial="JO332/224",  # Change for your device
    ip_address="192.168.1.20:1875",  # Optional: Define if connecting via ethernet (change value for your device)
    open_via_ip=False,  # Optional: True: connect via ethernet, False: connect via USB (default)
)

# Optional: Ensure that the Pico Technology SDK is available on PATH (if not already)
os.environ["PATH"] += os.pathsep + r"C:\Program Files\Pico Technology\SDK\lib"

# Connect to the PT-104
pt104: PT104 = connection.connect()

# Get all available information about the PT-104
info = pt104.get_unit_info()
print(info)

# Only get the date that the PT-104 was last calibrated
info = pt104.get_unit_info("cal_date", prefix=False)
print(f"The PT-104 was last calibrated on {info}")

# Get the details of the ethernet connection
enabled, ip_address, port = pt104.get_ip_details()
print(f"Ethernet enabled? {enabled}")
print(f"Address: {ip_address}:{port}")

# Configure channel 1 to be single-ended voltage from 0 to 2.5 V
pt104.set_channel(1, pt104.Type.SINGLE_ENDED_TO_2500MV, 2)

# Configure channel 2 to be a PT100 in a 4-wire arrangement
pt104.set_channel(2, pt104.Type.PT100, 4)

for i in range(10):
    # Wait for the samples to be available
    # A measurement cycle takes about 1 second per active channel
    # 2 channels are active, so we should wait at least 2 seconds
    time.sleep(3)

    # Read the value of channel 1
    ch1 = pt104.get_value(1)

    # Read the value of channel 2
    ch2 = pt104.get_value(2)

    # For the SINGLE_ENDED_TO_2500MV configuration, the scaling factor is 10 nV
    print(f"Loop {i}, Voltage={ch1 * 10e-9}")

    # For the PT100 configuration, the scaling factor is 1/1000 deg C
    print(f"Loop {i}, Temperature={ch2 * 1e-3}")

# Disconnect from the Data Logger
pt104.disconnect()
