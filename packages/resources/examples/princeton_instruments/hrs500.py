"""Example showing how to communicate with a HRS-500 monochromator from Princeton Instruments."""

from __future__ import annotations

from typing import TYPE_CHECKING

from msl.equipment import Connection, MSLConnectionError

if TYPE_CHECKING:
    from msl.equipment.resources import PrincetonInstruments


connection = Connection(
    "COM4",  # update for your device
    manufacturer="Princeton Instruments",
    model="HRS-500",  # update for your device
    # You can also add "C:\Program Files (x86)\Princeton Instruments" to your PATH environment variable
    # and not specify sdk_path
    sdk_path=r"C:\Program Files (x86)\Princeton Instruments\ARC_Instrument_x64.dll",
)

# Connect to the monochromator
mono: PrincetonInstruments = connection.connect()

# Print some information about the monochromator
print(f"Model: {mono.get_mono_model()}")
print(f"Serial: {mono.get_mono_serial()}")
print(f"Focal length: {mono.get_mono_focal_length()}")
print(f"Half angle: {mono.get_mono_half_angle()}")
print(f"Detector angle: {mono.get_mono_detector_angle()}")
print(f"Is double Monochromator? {mono.get_mono_double()}")
print(f"Is subtractive double Monochromator? {mono.get_mono_double_subtractive()}")
print(f"Turret: {mono.get_mono_turret()}")
print(f"Max number of Turrets: {mono.get_mono_turret_max()}")
print(f"Grating: {mono.get_mono_grating()}")
print(f"Max number of Gratings: {mono.get_mono_grating_max()}")

# Grating information
print(f"Turret gratings: {mono.get_mono_turret_gratings()}")
for index in range(1, mono.get_mono_turret_gratings() + 1):
    density = mono.get_mono_grating_density(index)
    blaze = mono.get_mono_grating_blaze(index)
    print(f"Grating: {index}, Density: {density}, Blaze: {blaze}")

# Diverter Mirror information
for index in range(1, 5):
    try:
        _ = mono.get_mono_diverter_valid(index)
    except MSLConnectionError:
        print(f"Diverter mirror {index} is not valid")
    else:
        position = mono.get_mono_diverter_pos(index)
        print(f"Diverter mirror {index} is motorized and at position {position}")

# Slit information
for index in range(1, 9):
    try:
        name = mono.mono_slit_name(index)
        typ = mono.get_mono_slit_type(index)
        width = mono.get_mono_slit_width(index)
        max_width = mono.get_mono_slit_width_max(index)
    except MSLConnectionError:
        print("Slit {}: 'Invalid Slit'")
    else:
        print(f"Slit {index}: Name={name!r}, Type={typ!r}, Width={width} um, Max={max_width} um")

# Filter wheel information
if mono.get_mono_filter_present():
    pos = mono.get_mono_filter_position()
    min_pos = mono.get_mono_filter_min_pos()
    max_pos = mono.get_mono_filter_max_pos()
    print(f"Filter wheel at position {pos} (Min: {min_pos}, Max: {max_pos})")
else:
    print("The Monochromator does not have a filter wheel.")

# Shutter information
if mono.get_mono_shutter_valid():
    if mono.get_mono_shutter_open():
        print("Shutter is open")
    else:
        print("Shutter is closed")
else:
    print("The Monochromator does not have a shutter.")

# Wavelength information
nm = mono.get_mono_wavelength_nm()
min_nm = mono.get_mono_wavelength_min_nm()
cut_off_nm = mono.get_mono_wavelength_cutoff_nm()
print(f"Wavelength at {nm} nm (Min: {min_nm} nm, Max: {cut_off_nm} nm)")

# Set the wavelength to 550 nm
print("Setting the wavelength to 550 nm...")
mono.set_mono_wavelength_nm(550)
print(f"  Wavelength at {mono.get_mono_wavelength_nm()} nm")

# Set the filter wheel to position 3
if mono.get_mono_filter_present():
    print("Setting the Filter Wheel to position 3...")
    mono.set_mono_filter_position(3)
    print(f"  Filter wheel at position {mono.get_mono_filter_position()}")

# Set the Front Entrance slit to be a width of 1000 um
print("Setting Slit 2 (Front Entrance) to a width of 1000 um...")
mono.set_mono_slit_width(2, 1000)
print(f"  Slit 2 is at {mono.get_mono_slit_width(2)} um")

# Set the grating to position 2
print("Setting the Grating to position 2...")
mono.set_mono_grating(2)
index = mono.get_mono_grating()
density = mono.get_mono_grating_density(index)
blaze = mono.get_mono_grating_blaze(index)
print(f"  Grating at position {index} -> Density: {density}, Blaze: {blaze}")

# Disconnect from the monochromator
mono.disconnect()
