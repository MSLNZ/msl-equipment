"""
This example prints a list of all PicoScopes
that are connected to the computer.
"""
import os

from msl.equipment.resources.picotech.picoscope import enumerate_units

# optional: ensure that the PicoTech DLLs are available on PATH
os.environ['PATH'] += os.pathsep + r'C:\Program Files\Pico Technology\SDK\lib'

units = enumerate_units()
print('The following PicoScope\'s were found: {}'.format(units))
