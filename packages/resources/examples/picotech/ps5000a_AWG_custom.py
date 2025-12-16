"""This example outputs a custom waveform and samples the waveform on Channel A.

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

print("Example :: Custom AWG waveform")

# Connect to the PicoScope
scope: PicoScope = connection.connect()

# Enable Channel A and set the voltage range to be +/- 2V
scope.set_channel("A", range="2V")

# Request to sample voltage every 10 ms, for 5 s
# Returns the sampling interval and the number of samples that will be acquired
duration = 5.0
actual_dt, num_samples = scope.set_timebase(10e-3, duration)
print(f"The actual time between samples is {actual_dt} seconds and there will be {num_samples} samples")

# Use Channel A as the trigger source at 0.4V as a falling edge trigger event
scope.set_trigger("A", threshold=0.4, direction="falling")

# Simulate the Lennard-Jones Potential as a waveform
x = np.linspace(0.89, 2, 500)
awg = (1 / x) ** 12 - 2 * (1 / x) ** 6
waveform_adu = scope.set_sig_gen_arbitrary(awg, repetition_rate=1e3, index_mode="quad")
print(f"The waveform in ADU counts is {waveform_adu}")

# Start acquisition
_ = scope.run_block(pre_trigger=2.5)

# Wait until all requested samples are collected
print(f"Waiting approximately {duration} seconds for the AWG samples...")
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

# Calculate the timestamps
t0 = -scope.pre_trigger
t1 = (actual_dt * num_samples) - scope.pre_trigger
times = np.arange(t0, t1, actual_dt)

volts = scope.channel["A"].volts

print("The AWG output:")
for t, v in zip(times, volts):
    print(f"{t:.2e} {v:f}")
