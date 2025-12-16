"""Acquire PicoScope data in Block Mode."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from msl.equipment import Connection

if TYPE_CHECKING:
    from msl.equipment.resources import PicoScope

connection = Connection(
    "SDK::ps5000a",  # Alternatively, specify the full path to the SDK, "SDK::path/to/lib/ps5000a"
    manufacturer="Pico Technology",
    model="5244B",  # Update for your PicoScope
    serial="DY135/055",  # Update for your PicoScope
    # resolution="16bit",  # Optional: Specify the device resolution (bit depth)
)

# Optional: Ensure that the Pico Technology SDK directory is available on PATH (if not already)
os.environ["PATH"] += os.pathsep + r"C:\Program Files\Pico Technology\SDK\lib"

print("Example :: Using block mode")

# Connect to the PicoScope
scope: PicoScope = connection.connect()

# Enable Channel A and set the voltage range to be +/- 1V
scope.set_channel("A", range="1V")

# Request to sample the voltage every 1 ms, for 20 ms
# Returns the sampling interval and the number of samples that will be acquired
actual_dt, num_samples = scope.set_timebase(1e-3, 20e-3)
print(f"The actual time between samples is {actual_dt} seconds and there will be {num_samples} samples")

# Channel A is the trigger source with a trigger threshold value of 0.0 V and a timeout of 0.1 second
scope.set_trigger("A", threshold=0.0, timeout=0.1)

# Start acquisition
wait_time = scope.run_block()
print(f"Acquiring the samples should take approximately {wait_time} seconds")

# Wait until all requested samples are acquired (polls scope to see if it is ready)
scope.wait_until_ready()

# Set the data buffer for Channel A
scope.set_data_buffer("A")

# Fill the data buffer of Channel A with the values saved in the PicoScope's internal memory
num_acquired, overflow_mask = scope.get_values()
print(f"Number of samples acquired is {num_acquired}")
print(f"Overflow bit mask => {overflow_mask}")

# Get the time when the trigger occurred
trigger_time = scope.get_trigger_time_offset64()
print(f"Trigger occurred at {trigger_time} seconds")

# Stop the oscilloscope from sampling data
scope.stop()

print("The voltages are:")
print(scope.channel["A"].volts)

print("The raw ADU counts are:")
print(scope.channel["A"].adu)

# Disconnect from the scope
scope.disconnect()
