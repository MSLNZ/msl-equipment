"""
Acquire PicoScope data in Rapid-Block Mode.
"""

# this "if" statement is used so that Sphinx does not execute this script when the docs are being built
if __name__ == '__main__':

    from msl.examples.equipment.resources.picotech.picoscope import record  # import the PicoScope EquipmentRecord

    print('Example :: Rapid-Block Mode')

    num_captures = 4  # the number of captures
    print('The number of captures requested is {}'.format(num_captures))

    scope = record.connect()  # establish a connection to the PicoScope
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
