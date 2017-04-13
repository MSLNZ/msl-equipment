"""
This example records a sine-wave that is created from the Arbitrary Waveform Generator.
"""
from msl.examples.equipment.picoscope import record  # import the PicoScope EquipmentRecord

print('Example :: Acquire AWG')

scope = record.connect()  # establish a connection to the PicoScope
scope.set_channel('A', scale='10V')  # enable Channel A and set the voltage range to be +/-10V
scope.set_timebase(1e-6, 100e-6)  # sample the voltage on Channel A every 1 us, for 100 us
scope.set_trigger('A', 1.0, timeout=-1)  # use Channel A as the trigger source at 1V, wait forever for a trigger event
scope.set_sig_gen_built_in_v2(start_frequency=10e3, pk_to_pk=2.0, offset_voltage=0.4)  # create a sine wave
scope.run_block()  # start acquisition
scope.wait_until_ready()  # wait until all requested samples are collected
scope.set_data_buffer('A')  # set the data buffer for Channel A
scope.get_values()  # fill the data buffer of Channel A with the values saved in the PicoScope's internal memory
scope.stop()  # stop the oscilloscope from sampling data

print('The AWG data output')
for i, v in enumerate(scope.channel['A'].volts):
    print('{0:.2e}, {1:f}'.format(i*scope.dt, v))
