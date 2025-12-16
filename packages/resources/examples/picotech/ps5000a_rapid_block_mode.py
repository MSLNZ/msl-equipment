"""Acquire PicoScope data in Rapid-Block Mode."""

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

print("Example :: Using rapid-block mode")

# Choose the number of captures to acquire
num_captures = 4

# connect to the PicoScope
scope: PicoScope = connection.connect()

# Enable Channel A and set the voltage range to be +/- 10V
scope.set_channel("A", range="10V")

# Enable Channel B and set the voltage range to be +/- 1V
scope.set_channel("B", range="1V")

# Request to sample the voltages every 1 ms, for 10 ms
# Returns the sampling interval and the number of samples that will be acquired
actual_dt, num_samples = scope.set_timebase(1e-3, 10e-3)
print(f"The actual time between samples is {actual_dt} seconds and there will be {num_samples} samples per capture")

# Channel A is the trigger source with a trigger threshold value of 0.0 V and a timeout of 0.1 second
scope.set_trigger("A", threshold=0.0, timeout=0.1)

# The number of memory segments to use must be >= the number of captures
_ = scope.memory_segments(num_captures)

# Set the number of captures
scope.set_no_of_captures(num_captures)

# Start acquisition
wait_time = scope.run_block()
print(f"Acquiring the samples should take approximately {wait_time} seconds")

# Wait until all requested samples are acquired (polls scope to see if it is ready)
scope.wait_until_ready()

# Set the data buffer for each capture and for each channel
actual_num_captures = scope.get_no_of_captures()
print(f"The actual number of captures collected is {actual_num_captures}")
for index in range(actual_num_captures):
    for ch in scope.channel.values():
        scope.set_data_buffer(ch.channel, buffer=ch.buffer[index : index + 1], segment=index)

# Fill the data buffer of Channels A and B
num_samples_per_capture, overflows_per_capture = scope.get_values_bulk()
print(f"{num_samples_per_capture=}, {overflows_per_capture=}")

# Get the trigger time offset, in seconds, for each capture
trigger_offsets = scope.get_values_trigger_time_offset_bulk64()
print(f"{trigger_offsets=}")

# Stop the oscilloscope from sampling data
scope.stop()

print("The voltages for Channel A are:")
print(scope.channel["A"].volts)

print("The raw ADU counts for Channel A are:")
print(scope.channel["A"].adu)

print("The voltages for Channel B are:")
print(scope.channel["B"].volts)

print("The raw ADU counts for Channel B are:")
print(scope.channel["B"].adu)

# Disconnect from the scope
scope.disconnect()
