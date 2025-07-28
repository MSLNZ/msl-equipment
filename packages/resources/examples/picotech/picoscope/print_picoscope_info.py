"""
This example prints the information about a PicoScope.
"""
import os

from msl.equipment import (
    EquipmentRecord,
    ConnectionRecord,
    Backend,
)

record = EquipmentRecord(
    manufacturer='Pico Technology',
    model='5244B',  # update for your PicoScope
    serial='DY135/055',  # update for your PicoScope
    connection=ConnectionRecord(
        backend=Backend.MSL,
        address='SDK::ps5000a.dll',  # update for your PicoScope
        properties={
            'resolution': '14bit',  # only used for a ps5000a series PicoScope
            'auto_select_power': True,  # for PicoScopes that can be powered by an AC adaptor or a USB cable
        },
    )
)

# optional: ensure that the PicoTech DLLs are available on PATH
os.environ['PATH'] += os.pathsep + r'C:\Program Files\Pico Technology\SDK\lib'

# connect to the PicoScope
scope = record.connect()

print('Summary for {}'.format(record))

# print all information that is available about the PicoScope
print(scope.get_unit_info())

# use the enum value to get the calibration date, do not print the member-name prefix
print('\nThe PicoScope was calibrated on {}'.format(scope.get_unit_info(5, False)))

# use the enum member name to get the calibration date
print(scope.get_unit_info('cal_date'))

print('The current power source is ' + scope.current_power_source())
if scope.IS_PS5000A:
    print('The device resolution is {!r}'.format(scope.get_device_resolution()))  # only valid for ps5000a scopes
print('The maximum ADU value is {}'.format(scope.maximum_value()))
print('The minimum ADU value is {}'.format(scope.minimum_value()))
print('The voltage-offset range for a +/-1V voltage range is {}'.format(scope.get_analogue_offset('1V', 'dc')))
print('The voltage ranges available for channel A are: {}'.format(scope.get_channel_information('A')))
print('The maximum down-sampling ratio that can be used for a given number of samples in a given down-sampling '
      'mode is {}'.format(scope.get_max_down_sample_ratio(1000, mode='aggregate')))
print('The maximum number of segments allowed is {}'.format(scope.get_max_segments()))
print('AWG range of allowed sample values and waveform buffer sizes {}'.format(scope.sig_gen_arbitrary_min_max_values()))
