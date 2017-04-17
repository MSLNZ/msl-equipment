"""
This example outputs a custom waveform and records the waveform on Channel A.

The output of the AWG must be connected to Channel A.
"""
import numpy as np

from msl.examples.equipment.picoscope import record  # import the PicoScope EquipmentRecord

print('Example :: Acquire AWG custom waveform')

scope = record.connect()  # establish a connection to the PicoScope
scope.set_channel('A', scale='2V')  # enable Channel A and set the voltage range to be +/-2V
dt, num_samples = scope.set_timebase(10e-3, 5.0)  # sample the voltage on Channel A every 10 ms for 5 s
scope.set_trigger('A', -0.2, timeout=5.0, direction='falling')  # use Channel A as the trigger source

# simulate the Lennard-Jones Potential
x = np.linspace(0.88, 2, 500)
awg = (1/x)**12 - 2*(1/x)**6
scope.set_sig_gen_arbitrary(awg, sample_frequency=1e3, index_mode='quad', pk_to_pk=2.0)

scope.run_block(pre_trigger=2.5)  # start acquisition
scope.wait_until_ready()  # wait until all requested samples are collected
scope.set_data_buffer('A')  # set the data buffer for Channel A
scope.get_values()  # fill the data buffer of Channel A with the values saved in the PicoScope's internal memory
scope.stop()  # stop the oscilloscope from sampling data

print('Channel A input')
t = np.arange(-scope.pre_trigger, dt*num_samples-scope.pre_trigger, dt)
for i in range(num_samples):
    print('{0:f}, {1:f}'.format(t[i], scope.channel['A'].volts[i]))

# if pyqtgraph is available then plot the Lennard-Jones Potential (the AWG signal) and Channel A
try:
    import sys
    import pyqtgraph as pg
    app = pg.mkQApp()
    w = pg.PlotWidget()
    w.addItem(pg.PlotCurveItem(x=x-0.9, y=awg, pen='r'))
    w.addItem(pg.ScatterPlotItem(x=t, y=scope.channel['A'].volts, symbol='o'))
    w.show()
    sys.exit(app.exec_())
except ImportError:
    pass
