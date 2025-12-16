"""This example handles post-collection data returned by the driver.

It registers a DataReady callback function that the driver calls when the data has been collected.
"""

from __future__ import annotations

import os
import time
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


@ps.data_ready
def my_data_ready(handle: int, status: int, num_samples: int, overflow: int, _: None) -> None:
    """Called when post-data collection is ready."""
    print(f"Callback: Data ready! {handle=}, {status=}, {num_samples=}, {overflow=}")
    print("The voltages are:")
    print(scope.channel["A"].volts)


print("Example :: Using block mode with a DataReady callback")

# Connect to the PicoScope
scope: PicoScope = connection.connect()

# Enable Channel A and set the voltage range to be +/- 1V
scope.set_channel(ps.Channel.A, range=ps.Range.R_1V)

# Request to sample the voltage every 1 ms, for 100 ms
actual_dt, num_samples = scope.set_timebase(1e-3, 100e-3)
print(f"The actual time between samples is {actual_dt} seconds and there will be {num_samples} samples")

# Channel A is the trigger source with a trigger threshold value of 0.0 V and a timeout of 0.1 second
scope.set_trigger(ps.Channel.A, threshold=0.0, timeout=0.1)

print("Start data acquisition...")
_ = scope.run_block()
scope.wait_until_ready()

# Set the data buffer for Channel A
scope.set_data_buffer("A")

print("Start data-ready callback...")
scope.get_values_async(my_data_ready)

# Sleep to make sure the callback function gets called before this script terminates
time.sleep(0.1)

# Stop the oscilloscope from sampling data
scope.stop()

# Disconnect from the scope
scope.disconnect()
