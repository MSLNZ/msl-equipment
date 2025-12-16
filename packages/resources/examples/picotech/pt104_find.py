"""Print the PT-104 Data Logger's that are connected to the computer."""

import os

from msl.equipment.resources import PT104

# Optional: Ensure that the Pico Technology SDK directory is available on PATH (if not already)
# Alternatively, you can specify the full path to the library file as an argument to enumerate_units()
os.environ["PATH"] += os.pathsep + r"C:\Program Files\Pico Technology\SDK\lib"

print("The following PT-104's were found:")
for unit in PT104.enumerate_units():
    print(f"  {unit}")
