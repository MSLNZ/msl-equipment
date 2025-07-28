"""
Acquire PicoScope data in Block Mode.
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

print('Example :: Block Mode')

# connect to the PicoScope
scope = record.connect()

# configure the PicoScope
scope.set_channel('A', scale='1V')  # enable Channel A and set the voltage range to be +/-1V
scope.set_timebase(1e-3, 20e-3)  # sample the voltage on Channel A every 1 ms, for 20 ms
scope.set_trigger('A', 0.0)  # Channel A is the trigger source with a trigger threshold value of 0.0 V

scope.run_block()  # start acquisition
scope.wait_until_ready()  # wait until all requested samples are collected
scope.set_data_buffer('A')  # set the data buffer for Channel A
scope.get_values()  # fill the data buffer of Channel A with the values saved in the PicoScope's internal memory
print(scope.get_trigger_time_offset64())
scope.stop()  # stop the oscilloscope from sampling data

print('The time between samples is {} seconds'.format(scope.dt))
print('The voltages are:\n{}'.format(scope.channel['A'].volts))
