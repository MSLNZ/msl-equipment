"""
This example prints a list of all the PicoScopes that are connected to the computer. 
"""
from msl.equipment.resources.picotech.picoscope import enumerate_units

units = enumerate_units()
print('The following serial numbers were found: {}'.format(units))
