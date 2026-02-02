"""Example showing how to communicate with a SuperK laser system."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from msl.equipment import Connection

if TYPE_CHECKING:
    from msl.equipment.resources import SuperK

connection = Connection(
    "COM4",  # update for your device
    # "TCP::192.168.1.2::10001",  # example address if using ethernet
    manufacturer="NKT",
    model="SuperK FIANIUM",  # update for your device
    timeout=5,
)

# Connect to the SuperK laser
superk: SuperK = connection.connect()

# Get info about the modules that are in the laser system
print("The following modules are available:")
for module in superk.scan_modules():
    print("  ", module)

# Lock the front panel (if supported)
superk.lock_front_panel = True

# Get the user text that is saved in the firmware
print(f"User text: {superk.user_text!r}")

# Get the user-setup parameters (only if the laser system is FIANIUM)
if superk.is_fianium:
    print(f"User setup: {superk.user_setup}")

# Get the pulse-picker ratio
print(f"Pulse-picker ratio: {superk.pulse_picker_ratio}")

# Get the operating mode
print(f"Operating mode: {superk.operating_mode!r}")

# Get the temperature
print(f"Temperature: {superk.temperature} \u00b0C")

# Set the output level to 5.5 %
superk.output = 5.5

# Get the output level
print(f"Output level {superk.output} %")

# Turn the laser on
print("Turn laser on")
superk.emission = True

print("Sleeping for 5 seconds...")
time.sleep(5)

# Print the status bits (bit 0 should be 1 to represent that the laser is on)
print(f"The status bits: 0b{superk.status:016b}")

# Turn the laser off
print("Turn laser off")
superk.emission = False

# Unlock the front panel (if supported)
superk.lock_front_panel = False

# Disconnect from the laser
superk.disconnect()
