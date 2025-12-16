"""Print the PicoScopes that are connected to the computer."""

import os

from msl.equipment.resources import PicoScope

# Optional: Ensure that the Pico Technology SDK directory is available on PATH (if not already)
# Alternatively, you can specify the full path to the library file as an argument to enumerate_units()
os.environ["PATH"] += os.pathsep + r"C:\Program Files\Pico Technology\SDK\lib"

print("The following PicoScope's were found:")
for unit in PicoScope.enumerate_units("ps5000a"):
    print(f"  {unit}")
