"""Print some information about a 5000A Series PicoScope."""

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
)

# Optional: Ensure that the Pico Technology SDK directory is available on PATH (if not already)
os.environ["PATH"] += os.pathsep + r"C:\Program Files\Pico Technology\SDK\lib"

# Connect to the PicoScope
scope: PicoScope = connection.connect()

scope.ping_unit()

# Print all information about the PicoScope
print(scope.get_unit_info())

# Use the enum value to get the calibration date and do not print the member-name prefix
info = scope.get_unit_info(5, prefix=False)
print(f"The PicoScope was calibrated on {info}")

# Use the enum member name to get the calibration date
print(scope.get_unit_info("cal_date"))

# Set the resolution
scope.set_device_resolution("16bit")

resolution = scope.get_device_resolution()
print(f"The device resolution is {resolution!r}")

max_adu = scope.maximum_value()
print(f"The maximum ADU value is {max_adu}")

min_adu = scope.minimum_value()
print(f"The minimum ADU value is {min_adu}")

offset = scope.get_analogue_offset("1V")
print(f"The voltage-offset range for a +/-1V voltage range is {offset}")

ranges = [ps.Range(r) for r in scope.get_channel_information("A", info="ranges")]
print(f"The voltage ranges available for channel A are {ranges}")

ratio = scope.get_max_down_sample_ratio(1000, mode="aggregate")
print(f"The maximum down-sampling ratio mode is {ratio!r}")

max_segments = scope.get_max_segments()
print(f"The maximum number of segments allowed is {max_segments}")

sizes = scope.sig_gen_arbitrary_min_max_values()
print(f"AWG range of allowed sample values and waveform buffer sizes {sizes}")

print(f"Output edge detection mode enabled? {scope.query_output_edge_detect()}")
print(f"Trigger enabled, PWQ enabled? {scope.is_trigger_or_pulse_width_qualifier_enabled()}")

flags = scope.channel_combinations_stateless(dt=12.3e-9, resolution="15bit")
print(f"Combination flags: {flags!r}")

index, nearest_dt = scope.nearest_sample_interval_stateless(flags=flags, dt=12.3e-9, resolution="15bit")
print(f"Nearest (rounded up) sample interval to 12.3 ns is {nearest_dt} seconds [timebase {index=}]")

min_dt = scope.get_minimum_timebase_stateless(flags=ps.ChannelFlags.A | ps.ChannelFlags.B, resolution="15bit")
print(f"Minimum sample interval for enabling 15-bit resolution with Ch A and B is {min_dt} seconds")

current, latest, is_update_required = scope.check_for_update()
print(f"Firmware versions: {current=}, {latest=}, {is_update_required=}")

# Disconnect from the scope
scope.disconnect()
