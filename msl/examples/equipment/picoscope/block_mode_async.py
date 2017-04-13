"""
This example handles post-collection data returned by the driver after a call to 
**GetValuesAsync**. It registers a **DataReady** callback function that the driver 
calls when the data has been collected.
"""
import time
from msl.equipment.resources.picotech.picoscope import callbacks
from msl.examples.equipment.picoscope import record  # import the PicoScope EquipmentRecord

print('Example :: Block Mode with DataReady callback')

# not all PicoScope's have the same DataReady function signature,
# so we have to specify the PicoScope SDK prefix, for example, 'ps5000a'
@callbacks.ps5000aDataReady
def my_data_ready(handle, status, num_samples, overflow, pParameter):
    print('DataReady Callback: Data transfer is done! '
          'handle={}, status={}, num_samples={}, overflow={}, pointer={}'
          .format(handle, status, num_samples, overflow, pParameter))

    print('The time between samples is {} seconds'.format(scope.dt))
    print('The voltages are:\n{}'.format(scope.channel['A'].volts))

scope = record.connect()  # establish a connection to the PicoScope
scope.set_channel('A', scale='1V')  # enable Channel A and set the voltage range to be +/-1V
scope.set_timebase(1e-3, 20e-3)  # sample the voltage on Channel A every 1 ms, for 20 ms
scope.set_trigger('A', 0.0)  # Channel A is the trigger source with a trigger threshold value of 0.0 V

print('Start data acquisition...')
scope.run_block()  # start acquisition
scope.wait_until_ready()  # wait until all requested samples are collected

scope.set_data_buffer('A', scope.channel['A'].buffer)  # set the data buffer for Channel A

print('Start async callback')
scope.get_values_async(my_data_ready)  # get the PicoScope data by a callback
time.sleep(1)  # do this here only to make sure the callback gets called before this script terminates

print('Stopping the PicoScope')
scope.stop()  # stop the oscilloscope from sampling data
