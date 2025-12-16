"""This example samples a sine wave that is created by the Arbitrary Waveform Generator (AWG).

The output of the AWG must be connected to Channel A.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import numpy as np

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

print("Example :: Builtin AWG waveform")

# Connect to the PicoScope
scope: PicoScope = connection.connect()

# Enable Channel A and set the voltage range to be +/- 10V
scope.set_channel("A", range="10V")

# Request to sample voltage every 1 us, for 200 us
# Returns the sampling interval and the number of samples that will be acquired
actual_dt, num_samples = scope.set_timebase(1e-6, 200e-6)
print(f"The actual time between samples is {actual_dt} seconds and there will be {num_samples} samples")

# Use Channel A as the trigger source at 1V and wait forever for a trigger event
scope.set_trigger("A", threshold=1.0, timeout=None)

# Create a sine wave
scope.set_sig_gen_builtin_v2(start_frequency=10e3, peak_to_peak=2.0, offset_voltage=0.4)

# Start acquisition
_ = scope.run_block()

# Wait until all requested samples are collected
scope.wait_until_ready()

# Set the data buffer for Channel A
scope.set_data_buffer("A")

# Fill the data buffer of Channel A with the values saved in the PicoScope's internal memory
num_acquired, overflow_mask = scope.get_values()
print(f"Number of samples acquired is {num_acquired}")
print(f"Overflow bit mask => {overflow_mask}")

# Stop the oscilloscope from sampling data
scope.stop()

# Calculate the timestamps.
# In this example pre_trigger=0 since it was not specified when run_block() was called
# so adjusting the times by `pre_trigger` seconds is not necessary.
t0 = -scope.pre_trigger
t1 = (actual_dt * num_samples) - scope.pre_trigger
times = np.arange(t0, t1, actual_dt)

volts = scope.channel["A"].volts

print("The AWG output:")
for t, v in zip(times, volts):
    print(f"{t:.2e} {v:f}")

# Disconnect from the scope
scope.disconnect()
