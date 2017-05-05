"""
Acquire PicoScope data in Streaming Mode.
"""

# this "if" statement is used so that Sphinx does not execute this script when the docs are being built
if __name__ == '__main__':

    from msl.equipment.resources.picotech.picoscope import callbacks
    from msl.examples.equipment.resources.picoscope import record  # import the PicoScope EquipmentRecord

    streaming_done = False

    @callbacks.ps5000aStreamingReady
    def my_streaming_ready(handle, num_samples, start_index, overflow, trigger_at, triggered, auto_stop, p_parameter):
        print('StreamingReady Callback: handle={}, num_samples={}, start_index={}, overflow={}, trigger_at={}, '
              'triggered={}, auto_stop={}, p_parameter={}'.format(handle, num_samples, start_index, overflow,
                                                                  trigger_at, triggered, auto_stop, p_parameter))
        global streaming_done
        streaming_done = bool(auto_stop)

    print('Example :: Streaming Mode')
    scope = record.connect()  # establish a connection to the PicoScope
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
