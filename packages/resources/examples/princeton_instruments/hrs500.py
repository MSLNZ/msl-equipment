"""
Example showing how to communicate with a HRS-500 monochromator from Princeton Instruments.
"""
from msl.equipment import (
    EquipmentRecord,
    ConnectionRecord,
    Backend,
)
from msl.equipment.exceptions import PrincetonInstrumentsError

record = EquipmentRecord(
    manufacturer='Princeton Instruments',
    model='HRS-500',  # update for your device
    connection=ConnectionRecord(
        address='COM4',  # update for your device
        backend=Backend.MSL,
        properties={
            'sdk_path': r'C:\Program Files (x86)\Princeton Instruments\ARC_Instrument_x64.dll',  # update
        }
    )
)

# Connect to the monochromator
mono = record.connect()

# Print some information about the monochromator
print('Model: {}'.format(mono.get_mono_model()))
print('Serial: {}'.format(mono.get_mono_serial()))
print('Focal length: {}'.format(mono.get_mono_focal_length()))
print('Half angle: {}'.format(mono.get_mono_half_angle()))
print('Detector angle: {}'.format(mono.get_mono_detector_angle()))
print('Is double Monochromator? {}'.format(mono.get_mono_double()))
print('Is subtractive double Monochromator? {}'.format(mono.get_mono_double_subtractive()))
print('Turret: {}'.format(mono.get_mono_turret()))
print('Max number of Turrets: {}'.format(mono.get_mono_turret_max()))
print('Grating: {}'.format(mono.get_mono_grating()))
print('Max number of Gratings: {}'.format(mono.get_mono_grating_max()))
# Grating information
print('Turret gratings: {}'.format(mono.get_mono_turret_gratings()))
for index in range(1, mono.get_mono_turret_gratings()+1):
    density = mono.get_mono_grating_density(index)
    blaze = mono.get_mono_grating_blaze(index)
    print('Grating: {}, Density: {}, Blaze: {}'.format(index, density, blaze))
# Diverter Mirror information
for index in range(1, 5):
    try:
        mono.get_mono_diverter_valid(index)
    except PrincetonInstrumentsError:
        print('Diverter mirror {} is not valid'.format(index))
    else:
        position = mono.get_mono_diverter_pos(index)
        print('Diverter mirror {} is motorized and at position {}'.format(index, position))
# Slit information
for index in range(1, 9):
    try:
        name = mono.mono_slit_name(index)
        typ = mono.get_mono_slit_type(index)
        width = mono.get_mono_slit_width(index)
        max_width = mono.get_mono_slit_width_max(index)
    except PrincetonInstrumentsError:
        print("Slit {}: 'Invalid Slit'")
    else:
        print('Slit {}: Name={!r}, Type={!r}, Width={} um, Max={} um'.format(index, name, typ, width, max_width))
# Filter wheel information
if mono.get_mono_filter_present():
    pos = mono.get_mono_filter_position()
    min_pos = mono.get_mono_filter_min_pos()
    max_pos = mono.get_mono_filter_max_pos()
    print('Filter wheel at position {} (Min: {}, Max: {})'.format(pos, min_pos, max_pos))
else:
    print('The Monochromator does not have a filter wheel.')
# Shutter information
if mono.get_mono_shutter_valid():
    if mono.get_mono_shutter_open():
        print('Shutter is open')
    else:
        print('Shutter is closed')
else:
    print('The Monochromator does not have a shutter.')
# Wavelength information
nm = mono.get_mono_wavelength_nm()
min_nm = mono.get_mono_wavelength_min_nm()
cutoff_nm = mono.get_mono_wavelength_cutoff_nm()
print('Wavelength at {} nm (Min: {} nm, Max: {} nm)'.format(nm, min_nm, cutoff_nm))

# Set the wavelength to 550 nm
print('Setting the wavelength to 550 nm...')
mono.set_mono_wavelength_nm(550)
print('  Wavelength at {} nm'.format(mono.get_mono_wavelength_nm()))

# Set the filter wheel to position 3
if mono.get_mono_filter_present():
    print('Setting the Filter Wheel to position 3...')
    mono.set_mono_filter_position(3)
    print('  Filter wheel at position {}'.format(mono.get_mono_filter_position()))

# Set the Front Entrance slit to be a width of 1000 um
print('Setting Slit 2 (Front Entrance) to a width of 1000 um...')
mono.set_mono_slit_width(2, 1000)
print('  Slit 2 is at {} um'.format(mono.get_mono_slit_width(2)))

# Set the grating to position 2
print('Setting the Grating to position 2...')
mono.set_mono_grating(2)
index = mono.get_mono_grating()
density = mono.get_mono_grating_density(index)
blaze = mono.get_mono_grating_blaze(index)
print('  Grating at position {} -> Density: {}, Blaze: {}'.format(index, density, blaze))

# Disconnect from the monochromator
mono.disconnect()
