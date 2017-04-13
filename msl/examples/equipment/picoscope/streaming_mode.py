"""
Acquire PicoScope data in Streaming Mode.
"""
import _thread
import time
from msl.examples.equipment.picoscope import record  # import the PicoScope EquipmentRecord
from msl.equipment.resources.picotech.picoscope import callbacks


@callbacks.ps5000aStreamingReady
def my_streaming_ready(handle, num_samples, start_index, overflow, trigger_at, triggered, auto_stop, p_parameter):
    print('StreamingReady Callback: handle={}, num_samples={}, start_index={}, overflow={}, trigger_at={}, '
          'triggered={}, auto_stop={}, p_parameter={}'.format(handle, num_samples, start_index, overflow,
                                                              trigger_at, triggered, auto_stop, p_parameter))


#def print_array():
#    while True:
#        print(scope.channel['A'].volts)


print('Example :: Streaming Mode')

scope = record.connect()  # establish a connection to the PicoScope
scope.set_channel('A', scale='10V')  # enable Channel A and set the voltage range to be +/-1V
scope.set_timebase(1e-6, 5)  # sample the voltage on Channel A every 1 ms, for 20 ms

scope.set_trigger('A', 0.0)  # Channel A is the trigger source with a trigger threshold value of 0.0 V
scope.set_data_buffer('A')  # set the data buffer for Channel A

print(scope.channel['A'].volts)

scope.run_streaming(auto_stop=False)
scope.get_streaming_latest_values(my_streaming_ready)
#_thread.start_new_thread(print_array, ())

time.sleep(6)

print(scope.channel['A'].volts)

time.sleep(1)

scope.stop()
