"""
This example registers a **BlockReady** callback that the SDK driver calls when 
block-mode data is ready.
"""
import time
from msl.equipment.resources.picotech.picoscope import callbacks
from msl.examples.equipment.picoscope import record  # import the PicoScope EquipmentRecord

print('Example :: Block Mode with BlockReady callback')

# All PicoScope's have the same BlockReady function signature, so use the generic callback
@callbacks.BlockReady
def my_block_ready(handle, status, pParameter):
    print('BlockReady Callback: Data acquisition is done! '
          'handle={}, status={}, pointer={}'.format(handle, status, pParameter))

    scope.set_data_buffer('A')  # set the data buffer for Channel A
    scope.get_values()  # fill the data buffer of Channel A with the values saved in the PicoScope's internal memory

    print('The time between samples is {} seconds'.format(scope.dt))
    print('The voltages are:\n{}'.format(scope.channel['A'].volts))

scope = record.connect()  # establish a connection to the PicoScope
scope.set_channel('A', scale='1V')  # enable Channel A and set the voltage range to be +/-1V
scope.set_timebase(1e-3, 20e-3)  # sample the voltage on Channel A every 1 ms, for 20 ms
scope.set_trigger('A', 0.0)  # Channel A is the trigger source with a trigger threshold value of 0.0 V

print('Start data acquisition...')
scope.run_block(callback=my_block_ready)  # pass in a callback to be notified when data acquisition is finished

time.sleep(1)  # do this here only to make sure the callback gets called before this script terminates

print('Stopping the PicoScope')
scope.stop()  # stop the oscilloscope from sampling data
