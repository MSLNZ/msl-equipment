"""Example showing how to communicate with a SpectraPro HRS-500 monochromator from Princeton Instruments."""

from __future__ import annotations

from time import sleep
from typing import TYPE_CHECKING

from msl.equipment import Connection

if TYPE_CHECKING:
    from msl.equipment.resources import SpectraPro


connection = Connection(
    "COM7",  # update for your device
    manufacturer="Princeton Instruments",
    model="SpectraPro HRS-500-M",  # update for your device
)

# Connect to the monochromator
mono: SpectraPro = connection.connect()

# Get information about the monochromator
print("Info:", mono.info())
print("Wavelength:", mono.wavelength, "nm")
print("Scan rate:", mono.scan_rate, "nm/min")
print("Filter-wheel position:", mono.get_filter_wheel_position())
print("Grating position:", mono.get_grating_position())
print("Turret:", mono.turret)
print("Gratings:", mono.gratings())

motorised_slits = mono.motorised_slits()
for slit in motorised_slits:
    print(f"{slit} width:", mono.get_slit_width(slit), "um")

motorised_mirrors = mono.motorised_mirrors()
for mirror in motorised_mirrors:
    print(f"{mirror} position:", mono.get_mirror_position(mirror))

# Set the grating position
print("\nSetting the grating to position 1")
mono.set_grating_position(1)

# Home the filter wheel
print("Homing the filter wheel")
mono.home_filter_wheel()

# Set the filter-wheel position
print("Setting the filter wheel to position 1")
mono.set_filter_wheel_position(1)

# Home the FRONT-EXIT slit
if mono.Slit.FRONT_EXIT in motorised_slits:
    print("Homing the front-exit slit")
    mono.home_slit(mono.Slit.FRONT_EXIT)

# Set the width of the FRONT-EXIT slit
if mono.Slit.FRONT_EXIT in motorised_slits:
    print("Moving the front-exit slit to 500 um")
    mono.set_slit_width(mono.Slit.FRONT_EXIT, 500)

# Set entrance mirror position to the front
if mono.Mirror.ENTRANCE in motorised_mirrors:
    print("Setting the entrance mirror to the FRONT position")
    mono.set_mirror_position(mono.Mirror.ENTRANCE, "front")

# Set the wavelength (moves at the maximum motor speed)
print("Setting the wavelength to 550 nm (maximum speed)")
mono.wavelength = 550
print(f"Wavelength at {mono.wavelength} nm")


# Set a callback function, for the scan_to() and reset() methods
def my_callback(wavelength: float) -> None:
    """Called with the current wavelength value."""
    print("  Callback", wavelength)


mono.set_callback(my_callback)

# Set the scan rate and then move to a specified wavelength at this rate, invoking the callback function
print("Scanning to 600 nm at a rate of 1000 nm/min")
mono.scan_rate = 1000  # nm/min
mono.scan_to(600)
print(f"Wavelength at {mono.wavelength} nm")

# Move to a specified wavelength at the scan rate and don't wait for the scan to finish
print("Scanning to 500 nm (not waiting)")
mono.scan_to(500, wait=False)

# Pretend to do other stuff
for _ in range(5):
    print("  sleeping for 1 second")
    sleep(1)

# Other stuff done, now make sure the monochromator has finished moving
mono.wait_until_ready()
print(f"Wavelength at {mono.wavelength} nm")

# Reset the monochromator to the start-up settings, invoking the callback function
print("Resetting")
mono.reset()

# Disconnect from the monochromator
mono.disconnect()
