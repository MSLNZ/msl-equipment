"""
Acquire PicoScope data in Block Mode.
"""

# this "if" statement is used so that Sphinx does not execute this script when the docs are being built
if __name__ == '__main__':

    from msl.examples.equipment.resources.picoscope import record  # import the PicoScope EquipmentRecord

    print('Example :: Block Mode')

    scope = record.connect()  # establish a connection to the PicoScope
    scope.set_channel('A', scale='1V')  # enable Channel A and set the voltage range to be +/-1V
    scope.set_timebase(1e-3, 20e-3)  # sample the voltage on Channel A every 1 ms, for 20 ms
    scope.set_trigger('A', 0.0)  # Channel A is the trigger source with a trigger threshold value of 0.0 V
    scope.run_block()  # start acquisition
    scope.wait_until_ready()  # wait until all requested samples are collected
    scope.set_data_buffer('A')  # set the data buffer for Channel A
    scope.get_values()  # fill the data buffer of Channel A with the values saved in the PicoScope's internal memory
    print(scope.get_trigger_time_offset64())
    scope.stop()  # stop the oscilloscope from sampling data

    print('The time between samples is {} seconds'.format(scope.dt))
    print('The voltages are:\n{}'.format(scope.channel['A'].volts))
