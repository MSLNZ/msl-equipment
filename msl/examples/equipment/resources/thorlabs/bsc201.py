"""
This example communicates with a Thorlabs Benchtop Stepper Motor Controller (BSC201).
"""

# this "if" statement is used so that Sphinx does not execute this script when the docs are being built
if __name__ == '__main__':
    import os
    import time
    from pprint import pprint

    from msl.equipment import EquipmentRecord, ConnectionRecord, Backend

    # ensure that the Kinesis folder is available on PATH
    os.environ['PATH'] += os.pathsep + 'C:/Program Files/Thorlabs/Kinesis'

    # rather than reading the EquipmentRecord from a database we can create it manually
    record = EquipmentRecord(
        manufacturer='Thorlabs',
        model='BSC201',
        serial='40876748',  # update the serial number for your BSC201
        connection=ConnectionRecord(
            address='SDK::Thorlabs.MotionControl.Benchtop.StepperMotor.dll',
            backend=Backend.MSL,
        )
    )

    def wait(value):
        motor.clear_message_queue(channel)
        message_type, message_id, _ = motor.wait_for_message(channel)
        while message_type != 2 or message_id != value:
            position = motor.get_position(channel)
            print('  at position {} [device units]'.format(position))
            message_type, message_id, _ = motor.wait_for_message(channel)

    # connect to the Benchtop Stepper Motor
    motor = record.connect()
    print('Connected to {}'.format(motor))

    # set the channel number of the Benchtop Stepper Motor to communicate with
    channel = 1

    # the SBC_Open(serialNo) function in Kinesis is non-blocking and therefore we
    # should add a delay for Kinesis to establish communication with the serial port
    time.sleep(1)

    # start polling at 200 ms
    motor.start_polling(channel, 200)

    # home the device
    print('Homing...')
    motor.home(channel)
    wait(0)
    print('Homing done. At position {} [device units]'.format(motor.get_position(channel)))

    # move to position 100000
    print('Moving to 100000...')
    motor.move_to_position(channel, 100000)
    wait(1)
    print('Moving done. At position {} [device units]'.format(motor.get_position(channel)))

    # move by a relative amount of -5000
    print('Moving by -5000...')
    motor.move_relative(channel, -5000)
    wait(1)
    print('Moving done. At position {} [device units]'.format(motor.get_position(channel)))

    # jog forwards
    print('Jogging forwards by {} [device units]'.format(motor.get_jog_step_size(channel)))
    motor.move_jog(channel, 'Forwards')
    wait(1)
    print('Jogging done. At position {} [device units]'.format(motor.get_position(channel)))

    # stop polling and close the connection
    motor.stop_polling(channel)
    motor.disconnect()

    # you can access the default settings for the motor to pass to the set_*() methods
    print('\nThe default motor settings are:')
    pprint(motor.settings)
