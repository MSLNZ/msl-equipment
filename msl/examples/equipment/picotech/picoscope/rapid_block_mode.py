"""
Acquire PicoScope data in Rapid-Block Mode.
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

print('Example :: Rapid-Block Mode')

num_captures = 4  # the number of captures
print('The number of captures requested is {}'.format(num_captures))

# connect to the PicoScope
scope = record.connect()

# configure the PicoScope
scope.set_channel('A', scale='10V')  # enable Channel A and set the voltage range to be +/-10V
scope.set_channel('B', scale='10V')  # enable Channel B and set the voltage range to be +/-10V
scope.set_timebase(1e-3, 10e-3)  # sample the voltage on Channel A every 1 ms, for 10 ms
scope.set_trigger('A', 0.0)  # Channel A is the trigger source with a trigger threshold value of 0.0 V
scope.memory_segments(num_captures)  # the number of memory segments to use must be >= the number of captures
scope.set_no_of_captures(num_captures)  # set the number of captures

scope.run_block()  # start acquisition
scope.wait_until_ready()  # wait until all requested samples are collected
print('The number of captures collected is {}'.format(scope.get_no_of_captures()))
for index in range(num_captures):  # set the data buffer for each capture and for each channel
    for ch in scope.channel.values():
        scope.set_data_buffer(ch.channel, ch.buffer[index:index+1], segment_index=index)
scope.get_values_bulk() # fill the data buffer of Channels A and B
scope.stop()  # stop the oscilloscope from sampling data

print('The time between samples is {} seconds'.format(scope.dt))
print('The Channel A voltages in each capture are:\n{}'.format(scope.channel['A'].volts))
print('The Channel B voltages in each capture are:\n{}'.format(scope.channel['B'].volts))

print('The Channel A raw Analog-to-Digital Unit values in each capture are:\n{}'.format(scope.channel['A'].raw))
print('The Channel B raw ADU values in each capture are:\n{}'.format(scope.channel['B'].raw))
