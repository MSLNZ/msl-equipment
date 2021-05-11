"""
This example records a sine-wave that is created from the Arbitrary Waveform Generator (AWG).

The output of the AWG must be connected to Channel A.
"""
import os

import numpy as np

# if matplotlib is available then plot the results
try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

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

print('Example :: Acquire AWG internal waveform')

# connect to the PicoScope
scope = record.connect()

# configure the PicoScope
scope.set_channel('A', scale='10V')  # enable Channel A and set the voltage range to be +/-10V
dt, num_samples = scope.set_timebase(1e-6, 100e-6)  # sample the voltage on Channel A every 1 us, for 100 us
scope.set_trigger('A', 1.0, timeout=-1)  # use Channel A as the trigger source at 1V, wait forever for a trigger event
scope.set_sig_gen_builtin_v2(start_frequency=10e3, pk_to_pk=2.0, offset_voltage=0.4)  # create a sine wave

scope.run_block()  # start acquisition
scope.wait_until_ready()  # wait until all requested samples are collected
scope.set_data_buffer('A')  # set the data buffer for Channel A
scope.get_values()  # fill the data buffer of Channel A with the values saved in the PicoScope's internal memory
scope.stop()  # stop the oscilloscope from sampling data

print('The AWG data output')
t = np.arange(-scope.pre_trigger, dt*num_samples-scope.pre_trigger, dt)
for i, v in enumerate(scope.channel['A'].volts):
    print('{0:.2e}, {1:f}'.format(i*scope.dt, v))

if plt is not None:
    plt.plot(t, scope.channel['A'].volts, 'bo')
    plt.show()
