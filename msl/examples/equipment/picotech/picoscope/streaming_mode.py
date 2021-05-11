"""
Acquire PicoScope data in Streaming Mode.
"""
import os

from msl.equipment import (
    EquipmentRecord,
    ConnectionRecord,
    Backend,
)
from msl.equipment.resources.picotech.picoscope import callbacks

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


@callbacks.ps5000aStreamingReady
def my_streaming_ready(handle, num_samples, start_index, overflow, trigger_at, triggered, auto_stop, pointer):
    print('StreamingReady Callback: handle={}, num_samples={}, start_index={}, overflow={}, trigger_at={}, '
          'triggered={}, auto_stop={}, pointer={}'.format(handle, num_samples, start_index, overflow,
                                                          trigger_at, triggered, auto_stop, pointer))
    global streaming_done
    streaming_done = bool(auto_stop)


streaming_done = False

print('Example :: Streaming Mode')

# connect to the PicoScope
scope = record.connect()

# configure the PicoScope
scope.set_channel('A', scale='10V')  # enable Channel A and set the voltage range to be +/-10V
scope.set_timebase(1e-3, 5)  # sample the voltage on Channel A every 1 ms, for 5 s
scope.set_trigger('A', 0.0)  # Channel A is the trigger source with a trigger threshold value of 0.0 V
scope.set_data_buffer('A')  # set the data buffer for Channel A

scope.run_streaming()  # start streaming mode
while not streaming_done:
    scope.wait_until_ready()  # wait until the latest streaming values are ready
    scope.get_streaming_latest_values(my_streaming_ready)  # get the latest streaming values
print('Stopping the PicoScope')
scope.stop()  # stop the oscilloscope from sampling data

print('The time between samples is {} seconds'.format(scope.dt))
print('The Channel A voltages are:\n{}'.format(scope.channel['A'].volts))
