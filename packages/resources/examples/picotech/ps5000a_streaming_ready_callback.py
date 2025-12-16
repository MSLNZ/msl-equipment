"""Acquire PicoScope data in Streaming Mode."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from msl.equipment import Connection
from msl.equipment.resources import picoscope as ps

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


@ps.streaming_ready
def my_streaming_ready(
    handle: int,
    num_samples: int,
    start_index: int,
    overflow: int,
    trigger_at: int,
    triggered: int,
    auto_stop: int,
    _: None,
) -> None:
    """Called when a stream is ready."""
    print(f"{handle=}, {num_samples=}, {start_index=}, {overflow=}, {trigger_at=}, {triggered=}, {auto_stop=}")
    scope.streaming_done = bool(auto_stop)


print("Example :: Using streaming mode")

# Connect to the PicoScope
scope: PicoScope = connection.connect()

# Enable Channel A and set the voltage range to be +/- 10V
scope.set_channel(ps.Channel.A, range=ps.Range.R_10V)

# Request to sample the voltage every 1 ms, for 5 s
# Returns the sampling interval and the number of samples that will be acquired
actual_dt, num_samples = scope.set_timebase(1e-3, 5)
print(f"The actual time between samples is {actual_dt} seconds and there will be {num_samples} samples")

# Channel A is the trigger source with a trigger threshold value of 0.0 V and a timeout of 0.1 second
scope.set_trigger(ps.Channel.A, threshold=0.0, timeout=0.1)

# Set the data buffer for Channel A to hold the samples
scope.set_data_buffer(channel=ps.Channel.A)

# Start streaming mode
_ = scope.run_streaming()
while not scope.streaming_done:
    scope.get_streaming_latest_values(my_streaming_ready)

print("Stopping the PicoScope")
scope.stop()

print("The voltages are:")
print(scope.channel["A"].volts)

print("The raw ADU counts are:")
print(scope.channel["A"].adu)

# Disconnect from the scope
scope.disconnect()
